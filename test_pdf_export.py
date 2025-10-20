#!/usr/bin/env python3
"""
Test script for PDF export functionality
"""
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

from src.services.export.pdf_renderer import PdfSurveyRenderer

def test_pdf_export():
    """Test PDF export with sample survey data"""
    
    # Sample survey data
    sample_survey = {
        "title": "Customer Satisfaction Survey",
        "description": "A comprehensive survey to understand customer satisfaction levels",
        "sections": [
            {
                "title": "Demographics",
                "description": "Basic demographic information",
                "questions": [
                    {
                        "id": "q1",
                        "type": "multiple_choice",
                        "text": "What is your age range?",
                        "options": ["18-24", "25-34", "35-44", "45-54", "55+"]
                    },
                    {
                        "id": "q2",
                        "type": "scale",
                        "text": "How satisfied are you with our service?",
                        "min_label": "Very Dissatisfied",
                        "max_label": "Very Satisfied"
                    }
                ]
            },
            {
                "title": "Product Feedback",
                "description": "Your feedback on our products",
                "questions": [
                    {
                        "id": "q3",
                        "type": "text",
                        "text": "What do you like most about our product?",
                        "placeholder": "Please share your thoughts..."
                    },
                    {
                        "id": "q4",
                        "type": "matrix_likert",
                        "text": "Please rate the following aspects:",
                        "statements": ["Quality", "Price", "Customer Service", "Delivery Speed"],
                        "scale_labels": ["Poor", "Fair", "Good", "Very Good", "Excellent"]
                    }
                ]
            }
        ]
    }
    
    try:
        print("🧪 Testing PDF export functionality...")
        
        # Create PDF renderer
        renderer = PdfSurveyRenderer()
        print("✅ PDF renderer created successfully")
        
        # Export survey to PDF
        pdf_data = renderer.render_survey(sample_survey)
        print(f"✅ PDF generated successfully ({len(pdf_data)} bytes)")
        
        # Save to file for inspection
        output_file = "test_survey_export.pdf"
        with open(output_file, "wb") as f:
            f.write(pdf_data)
        print(f"✅ PDF saved to {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing PDF export: {e}")
        return False

if __name__ == "__main__":
    success = test_pdf_export()
    if success:
        print("🎉 PDF export test completed successfully!")
    else:
        print("💥 PDF export test failed!")
        sys.exit(1)
