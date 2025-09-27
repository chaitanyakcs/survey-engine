#!/usr/bin/env python3
"""
Survey Engine with WebSocket Support and RAG Integration
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
from sqlalchemy import create_engine, Column, Integer, String, JSON, Float, DateTime, Text, UUID as SQLAlchemyUUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from src.database import get_db
from src.config import settings
from pgvector.sqlalchemy import Vector
import replicate
import json
import uuid
import asyncio
import uvicorn
from datetime import datetime
import os
import re
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Replicate
replicate_token = os.getenv("REPLICATE_API_TOKEN", "")
if replicate_token:
    replicate.api_token = replicate_token

# Use shared database configuration from src.database
from src.database import engine, SessionLocal, Base

# Use shared database models from src.database
from src.database import GoldenRFQSurveyPair, RFQ, Survey

# Import API routers
from src.api import annotations
from src.api.rules import router as rules_router
from src.api.human_reviews import router as human_reviews_router

# Initialize embedding model lazily
embedding_model = None
embedding_model_loading = False
embedding_model_task = None

async def get_embedding_model():
    """Lazy load the embedding model only when needed - TEMPORARILY DISABLED"""
    logger.info("🚫 [Model] ML model loading temporarily disabled for debugging")
    return None  # Return None to indicate no model available

# Use shared database dependency from src.database

app = FastAPI(
    title="Survey Generation Engine - WebSocket Edition",
    description="Real-time RFQ to Survey generation with progress tracking",
    version="0.2.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(annotations.router, prefix="/api/v1")
app.include_router(rules_router, prefix="/api/v1")
app.include_router(human_reviews_router)

class RFQSubmissionRequest(BaseModel):
    title: Optional[str] = None
    description: str
    product_category: Optional[str] = None
    target_segment: Optional[str] = None
    research_goal: Optional[str] = None

class RFQSubmissionResponse(BaseModel):
    workflow_id: str
    survey_id: str
    status: str

class SurveyResponse(BaseModel):
    survey_id: str
    title: str
    description: str
    estimated_time: int
    confidence_score: float
    methodologies: List[str]
    golden_examples: List[dict]
    questions: List[dict]
    metadata: dict

class GoldenExampleRequest(BaseModel):
    rfq_text: str
    survey_json: dict
    methodology_tags: List[str]
    industry_category: str
    research_goal: str
    quality_score: Optional[float] = None

class GoldenExampleResponse(BaseModel):
    id: str
    rfq_text: str
    survey_json: dict
    methodology_tags: List[str]
    industry_category: str
    research_goal: str
    quality_score: float
    usage_count: int
    created_at: str
    
# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, workflow_id: str):
        logger.info(f"🔌 [WebSocket] Accepting connection for workflow_id={workflow_id}")
        await websocket.accept()
        self.active_connections[workflow_id] = websocket
        logger.info(f"✅ [WebSocket] Connection established for workflow_id={workflow_id}. Total active: {len(self.active_connections)}")

    def disconnect(self, workflow_id: str):
        if workflow_id in self.active_connections:
            logger.info(f"🔌❌ [WebSocket] Disconnecting workflow_id={workflow_id}")
            del self.active_connections[workflow_id]
            logger.info(f"🔌❌ [WebSocket] Connection closed for workflow_id={workflow_id}. Total active: {len(self.active_connections)}")
        else:
            logger.warning(f"⚠️ [WebSocket] Attempted to disconnect non-existent workflow_id={workflow_id}")

    async def send_progress(self, workflow_id: str, message: dict):
        if workflow_id in self.active_connections:
            try:
                logger.debug(f"📨 [WebSocket] Sending message to workflow_id={workflow_id}: {message.get('type', 'unknown')}")
                await self.active_connections[workflow_id].send_json(message)
            except Exception as e:
                logger.error(f"❌ [WebSocket] Failed to send message to workflow_id={workflow_id}: {str(e)}")
                self.disconnect(workflow_id)
        else:
            logger.warning(f"⚠️ [WebSocket] Attempted to send to non-existent workflow_id={workflow_id}")

manager = ConnectionManager()

# In-memory workflow storage (replace with Redis/DB in production)
workflows: Dict[str, dict] = {}
surveys: Dict[str, dict] = {}
golden_examples: Dict[str, dict] = {}

# RAG Retrieval Functions
async def get_embedding(text: str, workflow_id: str = None, manager = None) -> List[float]:
    """Generate embedding for text using SentenceTransformer - TEMPORARILY DISABLED"""
    logger.info("🚫 [Embedding] ML model loading temporarily disabled for debugging")
    
    try:
        if workflow_id and manager:
            await manager.send_progress(workflow_id, {
                "type": "progress",
                "step": "generating_embeddings",
                "percent": 15,
                "message": "Generating semantic embeddings for RFQ text... (using fallback)"
            })
            
        # Add a small delay to make the progress visible
        await asyncio.sleep(0.5)
        
        # Return zero vector as fallback (no ML model loading)
        logger.info("🔄 [Embedding] Using zero vector fallback instead of ML model")
        return [0.0] * 384
    except Exception as e:
        logger.error(f"❌ [Embedding] Fallback embedding generation failed: {e}")
        # Return zero vector as fallback
        return [0.0] * 384

def calculate_cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """Calculate cosine similarity between two embeddings"""
    try:
        a = np.array(embedding1)
        b = np.array(embedding2)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    except:
        return 0.0

async def retrieve_golden_examples(rfq_embedding: List[float], db: Session, max_examples: int = 3, workflow_id: str = None, manager = None) -> List[Dict]:
    """Retrieve most similar golden examples using vector similarity"""
    try:
        if workflow_id and manager:
            await manager.send_progress(workflow_id, {
                "type": "progress",
                "step": "searching_golden_examples",
                "percent": 30,
                "message": "Searching golden examples database using vector similarity..."
            })
            
        # Add delay to make progress visible
        await asyncio.sleep(0.7)
        
        golden_pairs = db.query(GoldenRFQSurveyPair).all()
        
        if workflow_id and manager:
            await manager.send_progress(workflow_id, {
                "type": "progress",
                "step": "calculating_similarities",
                "percent": 35,
                "message": f"Calculating similarity scores for {len(golden_pairs)} golden examples..."
            })
            
        # Add another delay for similarity calculation
        await asyncio.sleep(0.5)
        
        similarities = []
        for pair in golden_pairs:
            if pair.rfq_embedding is not None:
                similarity = calculate_cosine_similarity(rfq_embedding, pair.rfq_embedding)
                similarities.append({
                    "pair": pair,
                    "similarity": similarity
                })
        
        # Sort by similarity and return top examples
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        golden_examples = []
        for item in similarities[:max_examples]:
            pair = item["pair"]
            golden_examples.append({
                "id": str(pair.id),
                "rfq_text": pair.rfq_text,
                "survey_json": pair.survey_json,
                "methodology_tags": pair.methodology_tags,
                "industry_category": pair.industry_category,
                "research_goal": pair.research_goal,
                "quality_score": pair.quality_score,
                "similarity_score": item["similarity"]
            })
            
            # Update usage count
            pair.usage_count += 1
            db.commit()
        
        if workflow_id and manager and golden_examples:
            await manager.send_progress(workflow_id, {
                "type": "progress", 
                "step": "golden_examples_found",
                "percent": 40,
                "message": f"Found {len(golden_examples)} relevant examples (similarity: {golden_examples[0]['similarity_score']:.2f})"
            })
        
        return golden_examples
    
    except Exception as e:
        print(f"Golden retrieval failed: {e}")
        return []

# Removed: generate_survey_with_rag - now handled by LangGraph workflow

# Removed: generate_survey_with_golden_context - now handled by LangGraph workflow

def initialize_sample_golden_examples():
    """Initialize some sample golden examples"""
    sample_examples = [
        {
            "id": "golden-coffee-machines",
            "rfq_text": "We need market research for premium coffee machines in the $500-2000 range. Key areas: brand preference, feature importance, price sensitivity using Van Westendorp methodology, and purchase drivers.",
            "survey_json": {
                "title": "Premium Coffee Machine Market Research",
                "description": "Understanding consumer preferences for high-end coffee machines",
                "estimated_time": 12,
                "questions": [
                    {
                        "id": "q1",
                        "text": "Have you purchased a coffee machine in the past 2 years?",
                        "type": "multiple_choice",
                        "options": ["Yes", "No, but considering", "No, not interested"],
                        "required": True,
                        "category": "screening"
                    },
                    {
                        "id": "q2",
                        "text": "At what price would you consider this coffee machine too expensive to purchase?",
                        "type": "text",
                        "required": True,
                        "category": "pricing",
                        "methodology": "van_westendorp"
                    }
                ],
                "metadata": {
                    "target_responses": 300,
                    "methodology": ["van_westendorp", "conjoint"]
                }
            },
            "methodology_tags": ["van_westendorp", "conjoint", "pricing", "brand_preference"],
            "industry_category": "Consumer Electronics",
            "research_goal": "pricing",
            "quality_score": 0.92,
            "usage_count": 15,
            "created_at": "2024-01-15T10:30:00"
        },
        {
            "id": "golden-b2b-saas-platform",
            "rfq_text": "B2B SaaS platform evaluation study. Need to understand decision-making process, key stakeholders, feature priorities, security requirements, and total cost of ownership considerations for mid-market companies.",
            "survey_json": {
                "title": "B2B SaaS Evaluation Survey – Mid-Market Decision Dynamics",
                "description": "Understanding how mid-market companies evaluate and select B2B SaaS platforms",
                "estimated_time": 15,
                "questions": [
                    {
                        "id": "q1",
                        "text": "What is your role in software purchasing decisions at your company?",
                        "type": "multiple_choice",
                        "options": ["Final decision maker", "Influencer/evaluator", "End user providing input", "Other"],
                        "required": True,
                        "category": "screening"
                    },
                    {
                        "id": "q2",
                        "text": "Rank these factors by importance in your SaaS evaluation process",
                        "type": "ranking",
                        "options": ["Security & compliance", "Total cost of ownership", "Feature functionality", "Integration capabilities", "Vendor support", "Scalability"],
                        "required": True,
                        "category": "core"
                    }
                ],
                "metadata": {
                    "target_responses": 200,
                    "methodology": ["maxdiff", "conjoint", "segmentation"]
                }
            },
            "methodology_tags": ["maxdiff", "conjoint", "segmentation", "b2b_decision_mapping"],
            "industry_category": "B2B Technology",
            "research_goal": "feature_prioritization",
            "quality_score": 0.89,
            "usage_count": 8,
            "created_at": "2024-02-20T14:15:00"
        },
        {
            "id": "golden-luxury-ev",
            "rfq_text": "Luxury electric vehicle consumer journey research. Focus on the $80k+ EV segment, understanding purchase consideration factors, charging infrastructure concerns, brand perception, and the decision timeline from consideration to purchase.",
            "survey_json": {
                "title": "Luxury EV Consumer Journey Study ($80k+ Segment)",
                "description": "Deep dive into luxury electric vehicle purchase decisions and consumer journey",
                "estimated_time": 18,
                "questions": [
                    {
                        "id": "q1",
                        "text": "Are you currently in the market for a luxury vehicle ($80k+)?",
                        "type": "multiple_choice",
                        "options": ["Yes, actively shopping", "Considering within 12 months", "Considering within 2 years", "Not considering"],
                        "required": True,
                        "category": "screening"
                    },
                    {
                        "id": "q2",
                        "text": "Which luxury EV brands would you consider?",
                        "type": "multiple_choice",
                        "options": ["Tesla Model S/X", "BMW iX/i7", "Mercedes EQS", "Audi e-tron GT", "Lucid Air", "Genesis GV60/GV70", "Other"],
                        "required": True,
                        "category": "core",
                        "multiple_select": True
                    }
                ],
                "metadata": {
                    "target_responses": 250,
                    "methodology": ["conjoint", "journey_mapping", "brand_perception"]
                }
            },
            "methodology_tags": ["conjoint", "journey_mapping", "brand_perception", "luxury_segmentation"],
            "industry_category": "Automotive",
            "research_goal": "purchase_journey",
            "quality_score": 0.87,
            "usage_count": 12,
            "created_at": "2024-03-10T16:45:00"
        }
    ]
    
    for example in sample_examples:
        golden_examples[example["id"]] = example

# Initialize sample data
initialize_sample_golden_examples()

async def send_progress_with_retry(workflow_id: str, message: dict, max_retries: int = 3):
    """
    Send progress message with retry logic to handle connection issues
    """
    for attempt in range(max_retries):
        try:
            await manager.send_progress(workflow_id, message)
            logger.debug(f"✅ [WebSocket] Progress sent successfully for workflow_id={workflow_id}, attempt={attempt + 1}")
            return
        except Exception as e:
            logger.warning(f"⚠️ [WebSocket] Failed to send progress for workflow_id={workflow_id}, attempt={attempt + 1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)  # Wait 1 second before retry
            else:
                logger.error(f"❌ [WebSocket] Failed to send progress after {max_retries} attempts for workflow_id={workflow_id}")
                # Don't raise exception, just log the failure

async def execute_workflow_async(workflow_id: str, workflow_data: dict):
    """
    Execute workflow within WebSocket context to maintain connection
    """
    db = next(get_db())
    try:
        request = workflow_data.get('request', {})
        survey_id = workflow_data.get('survey_id')
        
        # Step 1: Initialize workflow
        from src.services.progress_tracker import get_progress_tracker
        progress_tracker = get_progress_tracker(workflow_id)
        progress_data = progress_tracker.get_progress_data("initializing_workflow")
        await send_progress_with_retry(workflow_id, progress_data)
        
        # Import and use the proper LangGraph workflow
        from src.services.workflow_service import WorkflowService
        
        # Create workflow service instance
        workflow_service = WorkflowService(db)
        
        # Execute the LangGraph workflow
        logger.info(f"🚀 [WebSocket] Starting LangGraph workflow execution for workflow_id={workflow_id}")
        result = await workflow_service.process_rfq(
            title=request.get('title'),
            description=request.get('description', ''),
            product_category=request.get('product_category'),
            target_segment=request.get('target_segment'),
            research_goal=request.get('research_goal'),
            workflow_id=workflow_id,  # Pass the workflow_id to ensure consistency
            survey_id=survey_id  # Pass the survey_id to use existing survey
        )
        
        logger.info(f"✅ [WebSocket] LangGraph workflow completed: survey_id={result.survey_id}, status={result.status}")
        
        # Send completion message with retry logic
        await send_progress_with_retry(workflow_id, {
            "type": "completed",
            "survey_id": result.survey_id,
            "status": result.status,
            "message": "Survey generation completed successfully!"
        })
        
        # Close the WebSocket connection after a short delay to allow client to process the completion message
        logger.info(f"✅ [WebSocket] Workflow completed for workflow_id={workflow_id}, closing connection in 3 seconds")
        await asyncio.sleep(3)  # Give client time to process completion message
        
        # Close the WebSocket connection
        if workflow_id in manager.active_connections:
            websocket = manager.active_connections[workflow_id]
            try:
                await websocket.close(code=1000, reason="Workflow completed")
                logger.info(f"🔌 [WebSocket] Connection closed for workflow_id={workflow_id}")
            except Exception as close_error:
                logger.warning(f"⚠️ [WebSocket] Error closing connection for workflow_id={workflow_id}: {close_error}")
        
        # Clean up workflow data
        if workflow_id in workflows:
            del workflows[workflow_id]
            logger.info(f"🧹 [WebSocket] Cleaned up workflow data for workflow_id={workflow_id}")
            
    except Exception as e:
        logger.error(f"❌ [WebSocket] Workflow execution failed for workflow_id={workflow_id}: {str(e)}", exc_info=True)
        await send_progress_with_retry(workflow_id, {
            "type": "error",
            "message": f"Workflow execution failed: {str(e)}"
        })
        
        # Close the WebSocket connection on error as well
        if workflow_id in manager.active_connections:
            websocket = manager.active_connections[workflow_id]
            try:
                await websocket.close(code=1011, reason="Workflow failed")
                logger.info(f"🔌 [WebSocket] Connection closed due to error for workflow_id={workflow_id}")
            except Exception as close_error:
                logger.warning(f"⚠️ [WebSocket] Error closing connection for workflow_id={workflow_id}: {close_error}")
        
        # Clean up workflow data
        if workflow_id in workflows:
            del workflows[workflow_id]
            logger.info(f"🧹 [WebSocket] Cleaned up workflow data for workflow_id={workflow_id}")
    finally:
        db.close()

async def generate_survey_async(workflow_id: str, survey_id: str, request: dict):
    """
    Generate survey using LangGraph workflow with real-time progress updates
    """
    db = next(get_db())
    try:
        # Step 1: Initialize workflow
        from src.services.progress_tracker import get_progress_tracker
        progress_tracker = get_progress_tracker(workflow_id)
        progress_data = progress_tracker.get_progress_data("initializing_workflow")
        await manager.send_progress(workflow_id, progress_data)
        
        # Import and use the proper LangGraph workflow
        from src.services.workflow_service import WorkflowService
        
        # Create workflow service instance
        workflow_service = WorkflowService(db)
        
        # Execute the LangGraph workflow
        logger.info(f"🚀 [WebSocket] Starting LangGraph workflow execution for workflow_id={workflow_id}")
        result = await workflow_service.process_rfq(
            title=request.get('title'),
            description=request.get('description', ''),
            product_category=request.get('product_category'),
            target_segment=request.get('target_segment'),
            research_goal=request.get('research_goal'),
            workflow_id=workflow_id,  # Pass the workflow_id to ensure consistency
            survey_id=survey_id  # Pass the survey_id to use existing survey
        )
        
        logger.info(f"✅ [WebSocket] LangGraph workflow completed: survey_id={result.survey_id}, status={result.status}")
        
        # Extract results from workflow
        survey_id = result.survey_id
        used_golden_examples = result.golden_examples_used
        similarity_scores = []  # Will be populated by workflow nodes
        
        # Step 2: Post-processing and validation
        await manager.send_progress(workflow_id, {
            "type": "progress",
            "step": "post_processing",
            "percent": 80,
            "message": "Processing survey results and calculating quality scores..."
        })
        
        # Get the completed survey from database
        survey_record = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey_record:
            logger.error(f"❌ [WebSocket] Survey record not found: {survey_id}")
            raise Exception(f"Survey record not found: {survey_id}")
        
        # Extract survey data from the workflow result
        survey_data = survey_record.final_output or survey_record.raw_output
        if not survey_data:
            logger.error(f"❌ [WebSocket] No survey data found in record: {survey_id}")
            raise Exception(f"No survey data found in record: {survey_id}")
        
        # Calculate confidence score based on golden examples used
        confidence_score = 0.70  # Base confidence
        if used_golden_examples > 0:
            confidence_score = min(0.95, 0.70 + (used_golden_examples * 0.05))
            
        # Step 3: Finalization
        await manager.send_progress(workflow_id, {
            "type": "progress",
            "step": "finalizing",
            "percent": 95,
            "message": "Finalizing survey generation..."
        })
        
        # Update survey status to completed
        survey_record.status = "completed"
        db.commit()
        logger.info(f"✅ [WebSocket] Updated survey record status to completed: {survey_id}")
        
        # Store completed survey in memory for WebSocket responses
        survey_response_data = {
            "survey_id": survey_id,
            "title": survey_data.get("title", request.get('title') or "Generated Survey"),
            "description": survey_data.get("description", "AI-generated market research survey"),
            "estimated_time": survey_data.get("estimated_time", 10),
            "confidence_score": confidence_score,
            "methodologies": survey_data.get("metadata", {}).get("methodology", ["general_survey"]),
            "golden_examples": [],  # Will be populated by workflow nodes
            "questions": survey_data.get("questions", []),
            "metadata": {
                **survey_data.get("metadata", {}),
                "golden_examples_count": used_golden_examples,
                "workflow_status": result.status
            },
            "created_at": datetime.now().isoformat()
        }
        surveys[survey_id] = survey_response_data
        
        # Update workflow status
        workflows[workflow_id]["status"] = "completed"
        workflows[workflow_id]["completed_at"] = datetime.now().isoformat()
        workflows[workflow_id]["golden_examples_used"] = len(used_golden_examples)
        
        # Send completion message
        await manager.send_progress(workflow_id, {
            "type": "completed",
            "survey_id": survey_id,
            "status": "generated"
        })
        
    except Exception as e:
        workflows[workflow_id]["status"] = "failed"
        workflows[workflow_id]["error"] = str(e)
        
        await manager.send_progress(workflow_id, {
            "type": "error",
            "message": f"Generation failed: {str(e)}"
        })
    finally:
        db.close()

# Removed: generate_survey_with_gpt5 - now handled by LangGraph workflow

def generate_fallback_survey(request: RFQSubmissionRequest) -> dict:
    """Generate fallback survey using templates"""
    return {
        "title": f"{request.title or 'Market Research Survey'}",
        "description": f"Survey for {request.description[:100]}...",
        "estimated_time": 8,
        "questions": [
            {
                "id": "q1",
                "text": f"How familiar are you with {request.product_category or 'this product category'}?",
                "type": "multiple_choice",
                "options": ["Very familiar", "Somewhat familiar", "Not familiar"],
                "required": True,
                "category": "screening"
            },
            {
                "id": "q2", 
                "text": "What factors are most important in your purchasing decisions?",
                "type": "multiple_choice",
                "options": ["Price", "Quality", "Brand", "Features", "Reviews"],
                "required": True,
                "category": "core"
            },
            {
                "id": "q3",
                "text": "How likely are you to recommend this type of product to others?",
                "type": "scale",
                "options": ["1", "2", "3", "4", "5"],
                "scale_labels": {"1": "Not likely", "5": "Very likely"},
                "required": True,
                "category": "core"
            }
        ],
        "metadata": {
            "target_responses": 150,
            "methodology": ["general_survey"]
        }
    }

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Survey Generation Engine - WebSocket Edition", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.2.0"}

@app.get("/ready")
async def readiness_check():
    """Readiness check that doesn't depend on ML models"""
    return {"status": "ready", "message": "WebSocket server ready to accept connections"}

@app.post("/api/v1/rfq/")
async def process_rfq(request: dict):
    """
    Process RFQ through the complete LangGraph workflow
    """
    logger.info(f"📝 [WebSocket RFQ] Starting RFQ processing: title='{request.get('title', 'Unknown')}'")
    
    try:
        from src.services.workflow_service import WorkflowService
        from src.database import get_db
        
        # Get database session
        db = next(get_db())
        
        # Initialize workflow service
        workflow_service = WorkflowService(db)
        
        # Process RFQ through workflow
        result = await workflow_service.process_rfq_workflow(
            title=request.get('title'),
            description=request.get('description'),
            product_category=request.get('product_category'),
            target_segment=request.get('target_segment'),
            research_goal=request.get('research_goal'),
            workflow_id=request.get('workflow_id')
        )
        
        logger.info(f"✅ [WebSocket RFQ] Workflow completed: {result.status}")
        return {"status": "success", "result": result}
        
    except Exception as e:
        logger.error(f"❌ [WebSocket RFQ] Workflow failed: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

@app.post("/internal/broadcast/{workflow_id}")
async def broadcast_progress(workflow_id: str, message: dict):
    """
    Internal endpoint for WorkflowService to send progress updates
    """
    logger.info(f"📡 [WebSocket Broadcast] Received progress update for workflow_id={workflow_id}: {message.get('type', 'unknown')}")
    
    try:
        # Send progress update to connected WebSocket clients
        await manager.send_progress(workflow_id, message)
        logger.info(f"✅ [WebSocket Broadcast] Progress update sent to clients for workflow_id={workflow_id}")
        return {"status": "success", "message": "Progress update sent"}
    except Exception as e:
        logger.error(f"❌ [WebSocket Broadcast] Failed to send progress update for workflow_id={workflow_id}: {str(e)}")
        return {"status": "error", "message": str(e)}


@app.websocket("/ws/survey/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: str):
    logger.info(f"🌐 [WebSocket Endpoint] New WebSocket connection request for workflow_id={workflow_id}")
    
    await manager.connect(websocket, workflow_id)
    
    try:
        logger.info(f"🔄 [WebSocket Endpoint] Starting message loop for workflow_id={workflow_id}")
        
        # Check if this workflow_id has pending work and start it asynchronously
        if workflow_id in workflows:
            workflow_data = workflows[workflow_id]
            logger.info(f"🚀 [WebSocket] Found pending workflow for workflow_id={workflow_id}, starting async execution")
            
            # Start workflow asynchronously (non-blocking)
            asyncio.create_task(execute_workflow_async(workflow_id, workflow_data))
        
        while True:
            message = await websocket.receive_text()  # Keep connection alive
            logger.debug(f"📨 [WebSocket Endpoint] Received message from workflow_id={workflow_id}: {message}")
            
            # Handle keep-alive ping messages
            try:
                import json
                data = json.loads(message)
                if data.get('type') == 'ping':
                    logger.debug(f"🏓 [WebSocket] Received ping from workflow_id={workflow_id}")
                    await websocket.send_text(json.dumps({'type': 'pong'}))
                    continue
            except (json.JSONDecodeError, KeyError):
                # Not a JSON message or not a ping, ignore
                pass
    except WebSocketDisconnect as e:
        logger.warning(f"🔌❌ [WebSocket Endpoint] Client disconnected workflow_id={workflow_id}: {str(e)}")
        manager.disconnect(workflow_id)
    except Exception as e:
        logger.error(f"❌ [WebSocket Endpoint] Unexpected error for workflow_id={workflow_id}: {str(e)}", exc_info=True)
        manager.disconnect(workflow_id)



@app.post("/internal/broadcast/{workflow_id}")
async def internal_broadcast_progress(workflow_id: str, message: dict):
    """
    Internal endpoint for FastAPI to broadcast progress updates via WebSocket
    """
    logger.info(f"🔄 [Internal Broadcast] Received broadcast request for workflow_id={workflow_id}: {message.get('type', 'unknown')}")
    
    await manager.send_progress(workflow_id, message)
    
    logger.debug(f"📤 [Internal Broadcast] Message broadcasted for workflow_id={workflow_id}")
    return {"status": "broadcasted"}





if __name__ == "__main__":
    # Start the server with multiple workers to handle concurrent connections
    logger.info("🚀 [WebSocket] Starting WebSocket server on 0.0.0.0:8000")
    logger.info("🔧 [WebSocket] Server configuration: host=0.0.0.0, port=8000, workers=1")
    logger.info("🔧 [WebSocket] Database URL: " + str(settings.database_url))
    logger.info("🔧 [WebSocket] Debug mode: " + str(settings.debug))
    
    # Test database connection
    try:
        logger.info("🔧 [WebSocket] Testing database connection...")
        from sqlalchemy import text
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✅ [WebSocket] Database connection successful")
    except Exception as e:
        logger.error(f"❌ [WebSocket] Database connection failed: {str(e)}", exc_info=True)
        raise
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, workers=1, loop="asyncio")
    except Exception as e:
        logger.error(f"❌ [WebSocket] Failed to start server: {str(e)}", exc_info=True)
        raise