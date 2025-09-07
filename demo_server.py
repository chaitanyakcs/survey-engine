#!/usr/bin/env python3
"""
Demo Survey Engine - Shows RFQ processing with GPT-5 via Replicate
Works without reference data by using built-in survey templates
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, Dict, List
import replicate
import json
import uuid
import asyncio
import uvicorn
from datetime import datetime

# Initialize Replicate (will use token from environment)
import os
import re
replicate_token = os.getenv("REPLICATE_API_TOKEN", "")
if replicate_token:
    replicate.api_token = replicate_token

app = FastAPI(
    title="Survey Generation Engine - Demo",
    description="RFQ to Survey generation using GPT-5 via Replicate",
    version="0.1.0"
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

def extract_json_from_response(response_text: str) -> dict:
    """
    Robustly extract JSON from GPT response text
    """
    # Try multiple extraction strategies
    strategies = [
        # Strategy 1: Find complete JSON blocks with proper bracket matching
        lambda text: extract_balanced_json(text),
        # Strategy 2: Look for JSON between markdown code blocks
        lambda text: extract_json_from_codeblock(text),
        # Strategy 3: Clean and parse the entire response
        lambda text: clean_and_parse_json(text)
    ]
    
    for strategy in strategies:
        try:
            result = strategy(response_text)
            if result and validate_survey_json(result):
                return result
        except Exception:
            continue
    
    return None

def extract_balanced_json(text: str) -> dict:
    """Extract JSON with proper bracket balancing"""
    start_idx = text.find('{')
    if start_idx == -1:
        return None
    
    bracket_count = 0
    for i, char in enumerate(text[start_idx:], start_idx):
        if char == '{':
            bracket_count += 1
        elif char == '}':
            bracket_count -= 1
            if bracket_count == 0:
                json_text = text[start_idx:i+1]
                return json.loads(json_text)
    
    return None

def extract_json_from_codeblock(text: str) -> dict:
    """Extract JSON from markdown code blocks"""
    # Look for ```json or ``` blocks
    patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```\s*(\{.*?\})\s*```'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    
    return None

def clean_and_parse_json(text: str) -> dict:
    """Clean text and attempt JSON parsing"""
    # Remove common prefixes/suffixes
    text = re.sub(r'^[^{]*', '', text)
    text = re.sub(r'[^}]*$', '', text)
    
    if text.startswith('{') and text.endswith('}'):
        return json.loads(text)
    
    return None

def validate_survey_json(data: dict) -> bool:
    """Validate that JSON has required survey structure"""
    required_keys = ['title', 'questions']
    if not all(key in data for key in required_keys):
        return False
    
    if not isinstance(data['questions'], list) or len(data['questions']) == 0:
        return False
    
    # Validate each question has required fields
    for q in data['questions']:
        if not isinstance(q, dict) or 'text' not in q or 'type' not in q:
            return False
    
    return True

def enhance_methodology_detection(survey: dict, rfq_description: str) -> dict:
    """
    Enhance methodology detection by analyzing RFQ text and survey content
    """
    methodology_keywords = {
        'van_westendorp': ['van westendorp', 'price sensitivity method', 'psm', 'too expensive', 'too cheap'],
        'conjoint_analysis': ['conjoint', 'trade-off', 'feature trade', 'attribute importance'],
        'maxdiff': ['maxdiff', 'max diff', 'most important', 'least important', 'priority ranking'],
        'choice_conjoint': ['choice-based conjoint', 'choice conjoint', 'choice experiment'],
        'gabor_granger': ['gabor granger', 'purchase intent', 'price point'],
        'turf_analysis': ['turf', 'total unduplicated reach'],
        'kano_model': ['kano', 'feature satisfaction', 'must-have'],
        'nps': ['net promoter', 'nps', 'recommend'],
        'discrete_choice': ['discrete choice', 'choice modeling'],
        'implicit_testing': ['implicit', 'association test'],
        'brand_perception': ['brand perception', 'brand mapping', 'competitive positioning'],
        'journey_mapping': ['customer journey', 'journey mapping', 'touchpoint'],
        'behavioral_economics': ['behavioral economics', 'nudging', 'bias'],
        'social_desirability': ['social desirability', 'bias correction']
    }
    
    detected_methodologies = set()
    rfq_lower = rfq_description.lower()
    
    # Check RFQ description for methodology keywords
    for methodology, keywords in methodology_keywords.items():
        if any(keyword in rfq_lower for keyword in keywords):
            detected_methodologies.add(methodology)
    
    # Analyze survey questions for methodology indicators
    for question in survey.get('questions', []):
        q_text = question.get('text', '').lower()
        q_type = question.get('type', '')
        
        # Van Westendorp detection
        if any(phrase in q_text for phrase in ['too expensive', 'too cheap', 'price would', 'quality']):
            detected_methodologies.add('van_westendorp')
        
        # NPS detection
        if 'recommend' in q_text and q_type == 'scale':
            detected_methodologies.add('nps')
        
        # MaxDiff detection  
        if any(phrase in q_text for phrase in ['most important', 'least important', 'priority']):
            detected_methodologies.add('maxdiff')
        
        # Conjoint detection
        if question.get('methodology') == 'conjoint' or 'trade-off' in q_text:
            detected_methodologies.add('conjoint_analysis')
        
        # Scale questions often indicate advanced methodology
        if q_type == 'scale' and any(word in q_text for word in ['satisfaction', 'likelihood', 'importance']):
            detected_methodologies.add('scale_based_research')
    
    # Update survey metadata
    if 'metadata' not in survey:
        survey['metadata'] = {}
    
    current_methodologies = set(survey['metadata'].get('methodology', ['general_survey']))
    all_methodologies = current_methodologies.union(detected_methodologies)
    
    # Remove generic methodology if specific ones are detected
    if len(all_methodologies) > 1 and 'general_survey' in all_methodologies:
        all_methodologies.remove('general_survey')
    
    survey['metadata']['methodology'] = list(all_methodologies)
    
    # Add methodology tags to questions where appropriate
    for question in survey.get('questions', []):
        q_text = question.get('text', '').lower()
        
        if 'too expensive' in q_text or 'too cheap' in q_text:
            question['methodology'] = 'van_westendorp'
        elif 'recommend' in q_text and question.get('type') == 'scale':
            question['methodology'] = 'net_promoter_score'
        elif 'most important' in q_text or 'least important' in q_text:
            question['methodology'] = 'maxdiff'
    
    return survey

@app.get("/")
async def root():
    return {"message": "Survey Generation Engine", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}

@app.post("/api/v1/rfq/", response_model=RFQSubmissionResponse)
async def submit_rfq(request: RFQSubmissionRequest):
    """
    Submit RFQ for survey generation
    Works without reference data using built-in templates
    """
    try:
        survey_id = str(uuid.uuid4())
        
        # Generate survey using GPT-5 via Replicate
        if replicate_token:
            survey = await generate_survey_with_gpt5(request)
            status = "generated"
        else:
            survey = generate_fallback_survey(request)
            status = "fallback_generated"
        
        return RFQSubmissionResponse(
            survey_id=survey_id,
            estimated_completion_time=30,
            reference_examples_used=0,  # No reference data needed
            status=status,
            generated_survey=survey
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process RFQ: {str(e)}")

async def generate_survey_with_gpt5(request: RFQSubmissionRequest) -> dict:
    """
    Generate survey using GPT-5 via Replicate
    """
    # Build prompt without reference examples
    prompt = f"""
You are an expert survey designer. Create a comprehensive market research survey based on this RFQ.

RFQ DETAILS:
Title: {request.title or 'Market Research Survey'}
Description: {request.description}
Product Category: {request.product_category or 'General'}
Target Segment: {request.target_segment or 'General consumers'}
Research Goal: {request.research_goal or 'Market insights'}

REQUIREMENTS:
1. Create 8-12 questions covering key research areas
2. Include screening, core research, and demographic questions
3. Use appropriate question types (multiple choice, scale, text)
4. Focus on the research goals mentioned
5. Return valid JSON with this exact structure:

{{
    "title": "Survey Title",
    "description": "Brief survey description",
    "estimated_time": 8,
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
        "methodology": ["general_survey"]
    }}
}}

Generate the survey JSON now:
"""

    try:
        # Use GPT-5 via Replicate
        output = await replicate.async_run(
            "openai/gpt-5",
            input={
                "prompt": prompt,
                "temperature": 0.7,
                "max_tokens": 2000,
                "top_p": 0.9
            }
        )
        
        # Handle Replicate output format
        if isinstance(output, list):
            response_text = "".join(output)
        else:
            response_text = str(output)
        
        # Extract and parse JSON more robustly
        survey = extract_json_from_response(response_text)
        if survey:
            # Enhance methodology detection
            survey = enhance_methodology_detection(survey, request.description)
            return survey
        else:
            return generate_fallback_survey(request)
            
    except Exception as e:
        print(f"GPT-5 generation failed: {e}")
        return generate_fallback_survey(request)

def generate_fallback_survey(request: RFQSubmissionRequest) -> dict:
    """
    Generate fallback survey using built-in templates (no AI needed)
    """
    return {
        "title": f"{request.title or 'Market Research'} Survey",
        "description": f"Survey based on: {request.description[:100]}...",
        "estimated_time": 8,
        "questions": [
            {
                "id": "q1",
                "text": f"How familiar are you with {request.product_category or 'this product category'}?",
                "type": "multiple_choice",
                "options": ["Very familiar", "Somewhat familiar", "Not familiar", "Never heard of it"],
                "required": True,
                "category": "screening"
            },
            {
                "id": "q2", 
                "text": "What is your primary reason for considering this type of product?",
                "type": "multiple_choice",
                "options": ["Quality", "Price", "Brand reputation", "Features", "Convenience"],
                "required": True,
                "category": "core"
            },
            {
                "id": "q3",
                "text": "How important is price when making your decision?",
                "type": "scale",
                "options": ["1", "2", "3", "4", "5"],
                "scale_labels": {"1": "Not important", "5": "Very important"},
                "required": True,
                "category": "pricing"
            },
            {
                "id": "q4",
                "text": "What is your age range?",
                "type": "multiple_choice", 
                "options": ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
                "required": True,
                "category": "demographic"
            }
        ],
        "metadata": {
            "target_responses": 200,
            "methodology": ["general_survey"],
            "generation_method": "template_based",
            "note": "Generated using fallback templates - add Replicate token for AI generation"
        }
    }

@app.get("/api/v1/survey/{survey_id}")
async def get_survey(survey_id: str):
    """
    Retrieve survey (demo endpoint)
    """
    return {
        "survey_id": survey_id,
        "status": "completed",
        "message": "In the full system, this would return the complete survey data from the database"
    }

if __name__ == "__main__":
    print("🚀 Starting Survey Engine Demo Server")
    print(f"🔑 Replicate Token: {'✅ Set' if replicate_token else '❌ Missing'}")
    print("📊 API Docs: http://localhost:8000/docs")
    print("🏥 Health Check: http://localhost:8000/health")
    print("\n📝 Test RFQ Submission:")
    print('curl -X POST "http://localhost:8000/api/v1/rfq/" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"title": "Coffee Study", "description": "Research coffee preferences", "research_goal": "pricing"}\'')
    
    uvicorn.run(app, host="0.0.0.0", port=8000)