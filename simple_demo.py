#!/usr/bin/env python3
"""
Simple Demo: RFQ to Survey Generation
Shows how the system works without external dependencies
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import uuid
import uvicorn

app = FastAPI(
    title="Survey Generation Engine - Simple Demo",
    description="RFQ to Survey generation demo (no external dependencies)",
    version="0.1.0"
)

class RFQSubmissionRequest(BaseModel):
    title: Optional[str] = None
    description: str
    product_category: Optional[str] = None
    target_segment: Optional[str] = None
    research_goal: Optional[str] = None

class RFQSubmissionResponse(BaseModel):
    survey_id: str
    estimated_completion_time: int
    reference_examples_used: int
    status: str
    generated_survey: Optional[Dict[str, Any]] = None
    processing_method: str

@app.get("/")
async def root():
    return {
        "message": "Survey Generation Engine - Simple Demo",
        "status": "running",
        "note": "This demo shows RFQ processing without external dependencies"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0", "mode": "demo"}

@app.post("/api/v1/rfq/", response_model=RFQSubmissionResponse)
async def submit_rfq(request: RFQSubmissionRequest):
    """
    Submit RFQ for survey generation
    
    HOW IT WORKS WITHOUT REFERENCE DATA:
    1. Analyzes RFQ text for key themes
    2. Maps to survey question templates
    3. Generates structured survey JSON
    4. In full system: would use GPT-5 + reference examples for higher quality
    """
    try:
        survey_id = str(uuid.uuid4())
        
        # Simulate the workflow without external dependencies
        survey = generate_intelligent_survey(request)
        
        return RFQSubmissionResponse(
            survey_id=survey_id,
            estimated_completion_time=30,
            reference_examples_used=0,  # No reference data in this demo
            status="generated_with_templates",
            generated_survey=survey,
            processing_method="rule_based_templates"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process RFQ: {str(e)}")

def generate_intelligent_survey(request: RFQSubmissionRequest) -> Dict[str, Any]:
    """
    Intelligent survey generation using rule-based templates
    (In full system: GPT-5 + reference examples would make this much smarter)
    """
    
    # Analyze RFQ for key themes
    description_lower = request.description.lower()
    themes = {
        'pricing': any(word in description_lower for word in ['price', 'cost', 'expensive', 'cheap', 'budget', '$']),
        'features': any(word in description_lower for word in ['feature', 'function', 'capability', 'specs']),
        'brand': any(word in description_lower for word in ['brand', 'company', 'manufacturer']),
        'quality': any(word in description_lower for word in ['quality', 'reliable', 'durable', 'performance']),
        'usage': any(word in description_lower for word in ['use', 'usage', 'behavior', 'habit']),
        'satisfaction': any(word in description_lower for word in ['satisfaction', 'happy', 'pleased', 'experience'])
    }
    
    # Generate questions based on detected themes
    questions = []
    question_id = 1
    
    # Always start with screening
    questions.append({
        "id": f"q{question_id}",
        "text": f"Have you purchased or considered purchasing {request.product_category or 'this type of product'} in the past 12 months?",
        "type": "multiple_choice",
        "options": ["Yes, I have purchased", "Yes, I have considered", "No, but interested", "No, not interested"],
        "required": True,
        "category": "screening"
    })
    question_id += 1
    
    # Add theme-specific questions
    if themes['pricing']:
        questions.extend([
            {
                "id": f"q{question_id}",
                "text": "What price range are you comfortable with for this product?",
                "type": "multiple_choice",
                "options": ["Under $100", "$100-$300", "$300-$500", "$500-$1000", "Over $1000"],
                "required": True,
                "category": "pricing"
            }
        ])
        question_id += 1
        
        # Add Van Westendorp pricing if budget mentioned
        if any(word in description_lower for word in ['$', 'budget', 'range']):
            questions.extend([
                {
                    "id": f"q{question_id}",
                    "text": "At what price would this product be too expensive?",
                    "type": "text",
                    "required": True,
                    "category": "pricing",
                    "methodology": "van_westendorp"
                },
                {
                    "id": f"q{question_id + 1}",
                    "text": "At what price would this product be too cheap (questionable quality)?",
                    "type": "text", 
                    "required": True,
                    "category": "pricing",
                    "methodology": "van_westendorp"
                }
            ])
            question_id += 2
    
    if themes['features']:
        questions.append({
            "id": f"q{question_id}",
            "text": "Which features are most important to you? (Select top 3)",
            "type": "multiple_choice",
            "options": ["Ease of use", "Durability", "Design/appearance", "Performance", "Energy efficiency", "Brand reputation"],
            "required": True,
            "category": "features",
            "multiple_select": True,
            "max_selections": 3
        })
        question_id += 1
    
    if themes['brand']:
        questions.append({
            "id": f"q{question_id}",
            "text": "How important is brand reputation in your decision?",
            "type": "scale",
            "options": ["1", "2", "3", "4", "5"],
            "scale_labels": {"1": "Not important", "5": "Very important"},
            "required": True,
            "category": "brand"
        })
        question_id += 1
    
    if themes['usage']:
        questions.append({
            "id": f"q{question_id}",
            "text": f"How often do you plan to use this {request.product_category or 'product'}?",
            "type": "multiple_choice",
            "options": ["Daily", "Weekly", "Monthly", "Occasionally", "Rarely"],
            "required": True,
            "category": "usage"
        })
        question_id += 1
    
    # Always end with demographics
    questions.extend([
        {
            "id": f"q{question_id}",
            "text": "What is your age range?",
            "type": "multiple_choice",
            "options": ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
            "required": True,
            "category": "demographic"
        },
        {
            "id": f"q{question_id + 1}",
            "text": "What is your household income range?",
            "type": "multiple_choice", 
            "options": ["Under $25k", "$25k-$50k", "$50k-$75k", "$75k-$100k", "$100k-$150k", "Over $150k"],
            "required": False,
            "category": "demographic"
        }
    ])
    
    # Detect methodology from research goal
    methodologies = ["general_survey"]
    if request.research_goal:
        goal_lower = request.research_goal.lower()
        if "pricing" in goal_lower or "price" in goal_lower:
            methodologies.append("pricing_research")
        if "conjoint" in goal_lower:
            methodologies.append("conjoint")
    
    return {
        "title": request.title or f"{request.product_category or 'Product'} Research Survey",
        "description": f"Market research survey based on: {request.description[:150]}{'...' if len(request.description) > 150 else ''}",
        "estimated_time": min(15, max(5, len(questions) * 1.5)),
        "questions": questions,
        "metadata": {
            "target_responses": 200,
            "methodology": methodologies,
            "detected_themes": [theme for theme, detected in themes.items() if detected],
            "generation_method": "intelligent_templates",
            "rfq_analysis": {
                "product_category": request.product_category,
                "research_goal": request.research_goal,
                "target_segment": request.target_segment,
                "theme_count": sum(themes.values())
            },
            "notes": [
                "Generated using intelligent templates without reference examples",
                "In full system: GPT-5 + reference examples would provide higher quality",
                f"Detected {sum(themes.values())} key themes in RFQ"
            ]
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
        "message": "Survey generated successfully",
        "note": "In full system: would retrieve from database with validation results and similarity scores"
    }

@app.get("/demo/how-it-works")
async def how_it_works():
    """
    Explains how the system works without reference data
    """
    return {
        "title": "How Survey Generation Works",
        "without_reference_data": {
            "method": "Intelligent template-based generation",
            "steps": [
                "1. Parse RFQ text for key themes (pricing, features, quality, etc.)",
                "2. Map themes to question templates",
                "3. Generate structured survey with appropriate question types",
                "4. Apply methodology rules (Van Westendorp for pricing, etc.)",
                "5. Add screening and demographic questions"
            ],
            "quality": "Good baseline quality, covers essential research areas"
        },
        "with_reference_examples": {
            "method": "AI-powered generation with few-shot learning", 
            "steps": [
                "1. Generate embedding for RFQ",
                "2. Retrieve similar reference examples from database",
                "3. Use reference examples as few-shot prompts for GPT-5",
                "4. Generate survey following proven patterns",
                "5. Validate against methodology rules and reference similarity"
            ],
            "quality": "High quality, follows proven survey structures"
        },
        "example_improvements_with_references": [
            "Better question wording and flow",
            "Industry-specific terminology", 
            "Proven survey structures",
            "Higher methodology compliance",
            "More natural language"
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting Survey Engine - Simple Demo")
    print("📊 API Docs: http://localhost:8000/docs")  
    print("🏥 Health Check: http://localhost:8000/health")
    print("❓ How it works: http://localhost:8000/demo/how-it-works")
    print("\n📝 Test RFQ Submission:")
    print('curl -X POST "http://localhost:8000/api/v1/rfq/" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"title": "Coffee Machine Study", "description": "Research consumer preferences for premium coffee machines in $500-2000 range, focusing on price sensitivity and feature importance", "product_category": "appliances", "research_goal": "pricing_research"}\'')
    
    uvicorn.run(app, host="0.0.0.0", port=8000)