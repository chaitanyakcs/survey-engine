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

# Initialize Replicate
replicate_token = os.getenv("REPLICATE_API_TOKEN", "")
if replicate_token:
    replicate.api_token = replicate_token

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chaitanya@localhost:5432/survey_engine_db")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class GoldenRFQSurveyPair(Base):
    __tablename__ = "golden_rfq_survey_pairs"
    
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_text = Column(Text, nullable=False)
    rfq_embedding = Column(Vector(384), nullable=False)
    survey_json = Column(JSON, nullable=False)
    methodology_tags = Column(ARRAY(String), nullable=True)
    industry_category = Column(String(100), nullable=False)
    research_goal = Column(String(100), nullable=False)
    quality_score = Column(Float, default=0.8)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class RFQ(Base):
    __tablename__ = "rfqs"
    
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200))
    description = Column(Text, nullable=False)
    product_category = Column(String(100))
    target_segment = Column(String(100))
    research_goal = Column(String(100))
    embedding = Column(Vector(384))
    created_at = Column(DateTime, default=datetime.utcnow)

class Survey(Base):
    __tablename__ = "surveys"
    
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id = Column(SQLAlchemyUUID(as_uuid=True), nullable=False)
    status = Column(String(20), default="draft")
    raw_output = Column(JSON)
    final_output = Column(JSON)
    model_version = Column(String(50))
    golden_similarity_score = Column(Float)
    used_golden_examples = Column(ARRAY(SQLAlchemyUUID(as_uuid=True)))
    created_at = Column(DateTime, default=datetime.utcnow)

# Initialize embedding model
embedding_model = None
try:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Embedding model loaded successfully")
except Exception as e:
    print(f"Failed to load embedding model: {e}")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(
    title="Survey Generation Engine - WebSocket Edition",
    description="Real-time RFQ to Survey generation with progress tracking",
    version="0.2.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

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
        await websocket.accept()
        self.active_connections[workflow_id] = websocket

    def disconnect(self, workflow_id: str):
        if workflow_id in self.active_connections:
            del self.active_connections[workflow_id]

    async def send_progress(self, workflow_id: str, message: dict):
        if workflow_id in self.active_connections:
            try:
                await self.active_connections[workflow_id].send_json(message)
            except Exception:
                self.disconnect(workflow_id)

manager = ConnectionManager()

# In-memory workflow storage (replace with Redis/DB in production)
workflows: Dict[str, dict] = {}
surveys: Dict[str, dict] = {}
golden_examples: Dict[str, dict] = {}

# RAG Retrieval Functions
async def get_embedding(text: str, workflow_id: str = None, manager = None) -> List[float]:
    """Generate embedding for text using SentenceTransformer"""
    if embedding_model is None:
        raise ValueError("Embedding model not initialized")
    
    try:
        if workflow_id and manager:
            await manager.send_progress(workflow_id, {
                "type": "progress",
                "step": "generating_embeddings",
                "percent": 15,
                "message": "Generating semantic embeddings for RFQ text..."
            })
            
        # Add a small delay to make the progress visible
        await asyncio.sleep(0.8)
        
        # Clean and prepare text
        cleaned_text = re.sub(r'\s+', ' ', text.strip())
        
        # Generate embedding
        embedding = embedding_model.encode(cleaned_text, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        print(f"Embedding generation failed: {e}")
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

async def generate_survey_with_rag(request: RFQSubmissionRequest, db: Session, workflow_id: str = None, manager = None) -> Dict:
    """Generate survey using RAG with golden examples"""
    try:
        # Generate embedding for RFQ
        rfq_embedding = await get_embedding(request.description, workflow_id, manager)
        
        # Retrieve golden examples
        golden_examples = await retrieve_golden_examples(rfq_embedding, db, 3, workflow_id, manager)
        
        # Build context with golden examples
        if workflow_id and manager:
            await manager.send_progress(workflow_id, {
                "type": "progress",
                "step": "building_context",
                "percent": 50,
                "message": "Building RAG context with retrieved golden examples..."
            })
            
        await asyncio.sleep(0.5)  # Simulate context building time
        
        context = {
            "rfq": {
                "description": request.description,
                "product_category": request.product_category,
                "target_segment": request.target_segment,
                "research_goal": request.research_goal
            },
            "golden_examples": golden_examples,
            "retrieved_methodologies": list(set([
                tag for example in golden_examples 
                for tag in example.get("methodology_tags", [])
            ]))
        }
        
        # Generate survey with enhanced prompt
        if workflow_id and manager:
            if replicate_token and golden_examples:
                await manager.send_progress(workflow_id, {
                    "type": "progress",
                    "step": "generating_with_ai",
                    "percent": 65,
                    "message": "Generating survey with AI using golden examples context..."
                })
                survey = await generate_survey_with_golden_context(context, workflow_id, manager)
            elif replicate_token:
                await manager.send_progress(workflow_id, {
                    "type": "progress", 
                    "step": "generating_with_ai",
                    "percent": 65,
                    "message": "Generating survey with AI (no golden examples found)..."
                })
                survey = await generate_survey_with_gpt5(request)
            else:
                await manager.send_progress(workflow_id, {
                    "type": "progress",
                    "step": "generating_fallback",
                    "percent": 65,
                    "message": "Generating survey using fallback templates..."
                })
                survey = generate_fallback_survey(request)
        else:
            # Original logic without progress updates
            if replicate_token and golden_examples:
                survey = await generate_survey_with_golden_context(context)
            elif replicate_token:
                survey = await generate_survey_with_gpt5(request)
            else:
                survey = generate_fallback_survey(request)
        
        return {
            "survey": survey,
            "golden_examples_used": golden_examples,
            "similarity_scores": [ex.get("similarity_score", 0) for ex in golden_examples]
        }
        
    except Exception as e:
        print(f"RAG generation failed: {e}")
        # Fallback to original generation
        return {
            "survey": generate_fallback_survey(request),
            "golden_examples_used": [],
            "similarity_scores": []
        }

async def generate_survey_with_golden_context(context: Dict, workflow_id: str = None, manager = None) -> Dict:
    """Generate survey using GPT-5 with golden examples context"""
    rfq = context["rfq"]
    golden_examples = context["golden_examples"]
    methodologies = context["retrieved_methodologies"]
    
    # Build enhanced prompt with golden examples
    golden_context = ""
    for i, example in enumerate(golden_examples[:2], 1):  # Use top 2 examples
        golden_context += f"\nGOLDEN EXAMPLE {i} (similarity: {example.get('similarity_score', 0):.3f}):\n"
        golden_context += f"RFQ: {example['rfq_text'][:200]}...\n"
        golden_context += f"Survey Questions: {len(example['survey_json'].get('questions', []))} questions\n"
        golden_context += f"Methodologies: {', '.join(example['methodology_tags'])}\n"
    
    prompt = f"""You are an expert survey designer with access to high-quality examples. Create a comprehensive market research survey based on this RFQ, leveraging insights from similar successful surveys.

RFQ DETAILS:
Description: {rfq['description']}
Product Category: {rfq.get('product_category', 'General')}
Target Segment: {rfq.get('target_segment', 'General consumers')}
Research Goal: {rfq.get('research_goal', 'Market insights')}

RELEVANT GOLDEN EXAMPLES:
{golden_context}

SUGGESTED METHODOLOGIES: {', '.join(methodologies)}

REQUIREMENTS:
1. Create 8-15 questions covering key research areas
2. Use methodologies from golden examples where appropriate
3. Include screening, core research, and demographic questions
4. Adapt question types and structures from successful examples
5. Return valid JSON with this exact structure:

{{
    "title": "Survey Title",
    "description": "Brief survey description", 
    "estimated_time": 12,
    "questions": [
        {{
            "id": "q1",
            "text": "Question text here",
            "type": "multiple_choice",
            "options": ["Option 1", "Option 2", "Option 3"],
            "required": true,
            "category": "screening"
        }}
    ],
    "metadata": {{
        "target_responses": 200,
        "methodology": ["methodology_tags"]
    }}
}}

Generate the survey JSON now:
"""
    
    output = await replicate.async_run(
        "openai/gpt-5",
        input={
            "prompt": prompt,
            "temperature": 0.7,
            "max_tokens": 3000,
            "top_p": 0.9
        }
    )
    
    # Handle output format
    if isinstance(output, list):
        response_text = "".join(output)
    else:
        response_text = str(output)
    
    # Extract JSON with balanced bracket parsing
    start_idx = response_text.find('{')
    if start_idx == -1:
        raise ValueError("No JSON found in response")
    
    bracket_count = 0
    for i, char in enumerate(response_text[start_idx:], start_idx):
        if char == '{':
            bracket_count += 1
        elif char == '}':
            bracket_count -= 1
            if bracket_count == 0:
                json_text = response_text[start_idx:i+1]
                return json.loads(json_text)
    
    raise ValueError("Invalid JSON structure")

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

async def generate_survey_async(workflow_id: str, survey_id: str, request: RFQSubmissionRequest):
    """
    Generate survey with real-time progress updates and RAG integration
    """
    db = next(get_db())
    try:
        # Step 1: Initialize workflow
        await manager.send_progress(workflow_id, {
            "type": "progress",
            "step": "initializing_workflow",
            "percent": 5,
            "message": "Initializing survey generation workflow..."
        })
        
        # Call RAG-enhanced generation (handles all RAG phases internally)
        rag_result = await generate_survey_with_rag(request, db, workflow_id, manager)
        survey = rag_result["survey"]
        used_golden_examples = rag_result["golden_examples_used"]
        similarity_scores = rag_result["similarity_scores"]
        
        # Step 2: Post-processing and validation
        await manager.send_progress(workflow_id, {
            "type": "progress",
            "step": "post_processing",
            "percent": 80,
            "message": "Processing survey results and calculating quality scores..."
        })
        
        # Store RFQ in database
        rfq_embedding = await get_embedding(request.description)  # Generate again for DB storage
        rfq_record = RFQ(
            title=request.title,
            description=request.description,
            product_category=request.product_category,
            target_segment=request.target_segment,
            research_goal=request.research_goal,
            embedding=rfq_embedding
        )
        db.add(rfq_record)
        db.commit()
        db.refresh(rfq_record)
        
        # Calculate confidence score based on similarity
        if similarity_scores:
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            confidence_score = min(0.95, 0.70 + (avg_similarity * 0.25))
        else:
            confidence_score = 0.70
            
        # Step 5: Validation & Scoring
        await manager.send_progress(workflow_id, {
            "type": "progress",
            "step": "validation_scoring",
            "percent": 80,
            "message": "Validating and scoring survey quality..."
        })
        
        # Create survey record in database
        # Convert string IDs to UUIDs for the array field
        used_example_uuids = []
        for ex in used_golden_examples:
            try:
                used_example_uuids.append(uuid.UUID(ex["id"]))
            except (ValueError, KeyError):
                pass  # Skip invalid UUIDs
        
        survey_record = Survey(
            rfq_id=rfq_record.id,
            status="generated",
            raw_output=survey,
            final_output=survey,
            model_version="gpt-5-rag" if replicate_token else "fallback-rag",
            golden_similarity_score=float(similarity_scores[0]) if similarity_scores else None,
            used_golden_examples=used_example_uuids
        )
        db.add(survey_record)
        db.commit()
        
        # Step 6: Finalizing
        await manager.send_progress(workflow_id, {
            "type": "progress",
            "step": "finalizing",
            "percent": 95,
            "message": "Persisting and finalizing..."
        })
        
        # Store completed survey
        survey_data = {
            "survey_id": survey_id,
            "title": survey.get("title", request.title or "Generated Survey"),
            "description": survey.get("description", "AI-generated market research survey"),
            "estimated_time": survey.get("estimated_time", 10),
            "confidence_score": confidence_score,
            "methodologies": survey.get("metadata", {}).get("methodology", ["general_survey"]),
            "golden_examples": [{"id": ex["id"], "title": ex.get("rfq_text", "")[:50] + "...", "category": ex.get("industry_category", "General")} for ex in used_golden_examples[:3]],
            "questions": survey.get("questions", []),
            "metadata": {
                **survey.get("metadata", {}),
                "rag_similarity_scores": similarity_scores,
                "golden_examples_count": len(used_golden_examples)
            },
            "created_at": datetime.now().isoformat()
        }
        surveys[survey_id] = survey_data
        
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

async def generate_survey_with_gpt5(request: RFQSubmissionRequest) -> dict:
    """Generate survey using GPT-5 via Replicate"""
    prompt = f"""
You are an expert survey designer. Create a comprehensive market research survey based on this RFQ.

RFQ DETAILS:
Title: {request.title or 'Market Research Survey'}
Description: {request.description}
Product Category: {request.product_category or 'General'}
Target Segment: {request.target_segment or 'General consumers'}
Research Goal: {request.research_goal or 'Market insights'}

REQUIREMENTS:
1. Create 8-15 questions covering key research areas
2. Include screening, core research, and demographic questions
3. Use appropriate question types (multiple choice, scale, text)
4. Focus on the research goals mentioned
5. Return valid JSON with this exact structure:

{{
    "title": "Survey Title",
    "description": "Brief survey description", 
    "estimated_time": 12,
    "questions": [
        {{
            "id": "q1",
            "text": "Question text here",
            "type": "multiple_choice",
            "options": ["Option 1", "Option 2", "Option 3"],
            "required": true,
            "category": "screening"
        }}
    ],
    "metadata": {{
        "target_responses": 200,
        "methodology": ["methodology_tags"]
    }}
}}

Generate the survey JSON now:
"""
    
    output = await replicate.async_run(
        "openai/gpt-5",
        input={
            "prompt": prompt,
            "temperature": 0.7,
            "max_tokens": 3000,
            "top_p": 0.9
        }
    )
    
    # Handle output format
    if isinstance(output, list):
        response_text = "".join(output)
    else:
        response_text = str(output)
    
    # Extract JSON with balanced bracket parsing
    start_idx = response_text.find('{')
    if start_idx == -1:
        raise ValueError("No JSON found in response")
    
    bracket_count = 0
    for i, char in enumerate(response_text[start_idx:], start_idx):
        if char == '{':
            bracket_count += 1
        elif char == '}':
            bracket_count -= 1
            if bracket_count == 0:
                json_text = response_text[start_idx:i+1]
                return json.loads(json_text)
    
    raise ValueError("Invalid JSON structure")

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

@app.post("/api/v1/rfq/", response_model=RFQSubmissionResponse)
async def submit_rfq(request: RFQSubmissionRequest):
    """
    Start RFQ processing workflow
    """
    workflow_id = f"survey-gen-{str(uuid.uuid4())}"
    survey_id = f"survey-{str(uuid.uuid4())}"
    
    # Store workflow state
    workflows[workflow_id] = {
        "survey_id": survey_id,
        "request": request.dict(),
        "status": "started",
        "created_at": datetime.now().isoformat()
    }
    
    # Start async generation
    asyncio.create_task(generate_survey_async(workflow_id, survey_id, request))
    
    return RFQSubmissionResponse(
        workflow_id=workflow_id,
        survey_id=survey_id,
        status="started"
    )

@app.websocket("/ws/survey/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: str):
    await manager.connect(websocket, workflow_id)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(workflow_id)

@app.get("/api/v1/survey/{survey_id}", response_model=SurveyResponse)
async def get_survey(survey_id: str):
    """
    Fetch completed survey with rich metadata
    """
    if survey_id not in surveys:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    return SurveyResponse(**surveys[survey_id])

@app.get("/api/v1/workflow/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """
    Get workflow status
    """
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflows[workflow_id]

# Golden Examples Management API Endpoints
@app.get("/api/v1/golden-examples/search")
async def search_golden_examples(
    industry: Optional[str] = None,
    methodology: Optional[str] = None,
    research_goal: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Search golden examples by criteria
    """
    query = db.query(GoldenRFQSurveyPair)
    
    if industry:
        query = query.filter(GoldenRFQSurveyPair.industry_category.ilike(f"%{industry}%"))
    if research_goal:
        query = query.filter(GoldenRFQSurveyPair.research_goal.ilike(f"%{research_goal}%"))
    
    examples = query.all()
    
    # Filter by methodology if specified
    if methodology:
        examples = [ex for ex in examples if any(methodology.lower() in tag.lower() for tag in ex.methodology_tags)]
    
    result_examples = []
    for example in examples:
        result_examples.append({
            "id": str(example.id),
            "rfq_text": example.rfq_text,
            "survey_json": example.survey_json,
            "methodology_tags": example.methodology_tags,
            "industry_category": example.industry_category,
            "research_goal": example.research_goal,
            "quality_score": example.quality_score,
            "usage_count": example.usage_count,
            "created_at": example.created_at.isoformat()
        })
    
    return {
        "examples": result_examples,
        "count": len(result_examples)
    }

@app.get("/api/v1/golden-examples")
async def get_golden_examples(db: Session = Depends(get_db)):
    """
    Get all golden examples
    """
    examples = db.query(GoldenRFQSurveyPair).all()
    
    result_examples = []
    for example in examples:
        result_examples.append({
            "id": str(example.id),
            "rfq_text": example.rfq_text,
            "survey_json": example.survey_json,
            "methodology_tags": example.methodology_tags,
            "industry_category": example.industry_category,
            "research_goal": example.research_goal,
            "quality_score": example.quality_score,
            "usage_count": example.usage_count,
            "created_at": example.created_at.isoformat()
        })
    
    return {
        "examples": result_examples,
        "count": len(result_examples)
    }

@app.post("/api/v1/golden-examples", response_model=GoldenExampleResponse)
async def create_golden_example(request: GoldenExampleRequest, db: Session = Depends(get_db)):
    """
    Create a new golden example
    """
    # Generate embedding for the RFQ text
    rfq_embedding = await get_embedding(request.rfq_text)
    
    # Create new golden example
    new_example = GoldenRFQSurveyPair(
        rfq_text=request.rfq_text,
        rfq_embedding=rfq_embedding,
        survey_json=request.survey_json,
        methodology_tags=list(request.methodology_tags),  # Ensure it's a Python list
        industry_category=request.industry_category,
        research_goal=request.research_goal,
        quality_score=request.quality_score or 0.8,
        usage_count=0
    )
    
    db.add(new_example)
    db.commit()
    db.refresh(new_example)
    
    return GoldenExampleResponse(
        id=str(new_example.id),
        rfq_text=new_example.rfq_text,
        survey_json=new_example.survey_json,
        methodology_tags=new_example.methodology_tags,
        industry_category=new_example.industry_category,
        research_goal=new_example.research_goal,
        quality_score=new_example.quality_score,
        usage_count=new_example.usage_count,
        created_at=new_example.created_at.isoformat()
    )

@app.get("/api/v1/golden-examples/{example_id}", response_model=GoldenExampleResponse)
async def get_golden_example(example_id: str, db: Session = Depends(get_db)):
    """
    Get a specific golden example
    """
    try:
        example_uuid = uuid.UUID(example_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid example ID format")
    
    example = db.query(GoldenRFQSurveyPair).filter(GoldenRFQSurveyPair.id == example_uuid).first()
    if not example:
        raise HTTPException(status_code=404, detail="Golden example not found")
    
    return GoldenExampleResponse(
        id=str(example.id),
        rfq_text=example.rfq_text,
        survey_json=example.survey_json,
        methodology_tags=example.methodology_tags,
        industry_category=example.industry_category,
        research_goal=example.research_goal,
        quality_score=example.quality_score,
        usage_count=example.usage_count,
        created_at=example.created_at.isoformat()
    )

@app.put("/api/v1/golden-examples/{example_id}", response_model=GoldenExampleResponse)
async def update_golden_example(example_id: str, request: GoldenExampleRequest, db: Session = Depends(get_db)):
    """
    Update a golden example
    """
    try:
        example_uuid = uuid.UUID(example_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid example ID format")
    
    example = db.query(GoldenRFQSurveyPair).filter(GoldenRFQSurveyPair.id == example_uuid).first()
    if not example:
        raise HTTPException(status_code=404, detail="Golden example not found")
    
    # Update fields
    example.rfq_text = request.rfq_text
    example.survey_json = request.survey_json
    example.methodology_tags = request.methodology_tags
    example.industry_category = request.industry_category
    example.research_goal = request.research_goal
    if request.quality_score is not None:
        example.quality_score = request.quality_score
    
    # Regenerate embedding if RFQ text changed
    rfq_embedding = await get_embedding(request.rfq_text)
    example.rfq_embedding = rfq_embedding
    
    db.commit()
    db.refresh(example)
    
    return GoldenExampleResponse(
        id=str(example.id),
        rfq_text=example.rfq_text,
        survey_json=example.survey_json,
        methodology_tags=example.methodology_tags,
        industry_category=example.industry_category,
        research_goal=example.research_goal,
        quality_score=example.quality_score,
        usage_count=example.usage_count,
        created_at=example.created_at.isoformat()
    )

@app.delete("/api/v1/golden-examples/{example_id}")
async def delete_golden_example(example_id: str, db: Session = Depends(get_db)):
    """
    Delete a golden example
    """
    try:
        example_uuid = uuid.UUID(example_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid example ID format")
    
    example = db.query(GoldenRFQSurveyPair).filter(GoldenRFQSurveyPair.id == example_uuid).first()
    if not example:
        raise HTTPException(status_code=404, detail="Golden example not found")
    
    db.delete(example)
    db.commit()
    
    return {"message": "Golden example deleted successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)