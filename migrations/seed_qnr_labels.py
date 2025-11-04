"""
QNR Labels Seed Script
Hardcoded data from QNR Labelling Oct 22, 2024 version
No file dependencies - all data embedded for Railway compatibility
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Hardcoded QNR label data from CSVs
QNR_LABELS_DATA = {
    'sample_plan': [
        {'name': 'Study_Intro', 'description': 'Thanks for agreeing, inform eligibility, state LOI', 'mandatory': True, 'label_type': 'Text', 'applicable_labels': []},
    ],
    'screener': [
        {'name': 'Category_Usage_Frequency', 'description': 'How often you use', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Medical_Conditions_General', 'description': 'Multiselect', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': ['Consumer Health', 'Healthcare', 'MedTech', 'Patients']},
        {'name': 'CoI_Check', 'description': 'Conflict of Interest check. Terminate', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Category_Usage_Financial', 'description': 'How much you spend now and in future', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Demog_Basic', 'description': 'Age, Gender. Check categories specific to country', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Recent_Participation', 'description': 'Participated in Market Research study recently. Terminate', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Medical_Conditions_Study', 'description': 'Current, Past and future', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': ['Consumer Health', 'Healthcare', 'MedTech', 'Patients']},
        {'name': 'Category_Usage_Consider', 'description': 'are you considering in the future', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'User_Categorization_Logic', 'description': 'User/Non-User, Continue/Terminate, Other categorization rules', 'mandatory': True, 'label_type': 'Rules', 'applicable_labels': []},
        {'name': 'Confidentiality_Agreement', 'description': '', 'mandatory': True, 'label_type': 'Text', 'applicable_labels': []},
        {'name': 'Category_Usage_Adnl', 'description': 'Where will you use and how', 'mandatory': False, 'label_type': '', 'applicable_labels': []},
        {'name': 'Socio_HH_Dur', 'description': 'Socio economic - durables owned household', 'mandatory': False, 'label_type': '', 'applicable_labels': []},
        {'name': 'Category_Awareness', 'description': 'What products have you heard of', 'mandatory': False, 'label_type': '', 'applicable_labels': []},
        {'name': 'Category_Usage', 'description': 'What products have you used, consumed', 'mandatory': False, 'label_type': '', 'applicable_labels': []},
        {'name': 'Category_Restrict', 'description': 'Would never consume/use', 'mandatory': False, 'label_type': '', 'applicable_labels': []},
        {'name': 'Mobility_Travel', 'description': 'Travel related questions', 'mandatory': False, 'label_type': '', 'applicable_labels': []},
        {'name': 'Psychog_Leisure', 'description': 'Psychograpic questions. What are the leisure activities done', 'mandatory': False, 'label_type': '', 'applicable_labels': []},
        {'name': 'Socio_Pers_Dur', 'description': 'Socio economic - durables owned personal', 'mandatory': False, 'label_type': '', 'applicable_labels': []},
        {'name': 'Online_Activity', 'description': 'how much time do you approximately spend on internet in a week,activities that you have done in past 1 month from the list below', 'mandatory': False, 'label_type': '', 'applicable_labels': []},
    ],
    'brand': [
        {'name': 'Brand_awareness_funnel', 'description': 'What brands are you aware of. Funnel Questions - Aware → Considered → Purchased → Continue → Preferred', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': ['Consumer Health', 'Healthcare', 'MedTech', 'Patients']},
        {'name': 'Brand_Recall', 'description': 'Top of the mind brands', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Product_Usage', 'description': 'What products do you use in the category.', 'mandatory': True, 'label_type': 'Text', 'applicable_labels': []},
        {'name': 'Product_Usage_Frequency', 'description': 'Frequency of usage and purchase, Quantity', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Category_Usage_Frequency', 'description': 'How often you use', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Product_Usage_Financial', 'description': 'How much do you spend and if it is higher, type of purchase - subscription etc, channel info', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Brand_Product_Satisfaction', 'description': 'With the products used in the past and current', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': ['Consumer Health', 'Healthcare', 'MedTech', 'Patients']},
        {'name': 'Purchase_Decision', 'description': 'Who influences purchase decision', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Brand_Usage', 'description': 'Brands used for the product/category', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Brand_Choice', 'description': 'Brands used most often', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Brand_Usage_Context', 'description': 'Where, when and how brand is used', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Brand_Usage_Style', 'description': 'What is the brand used with', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': []},
    ],
    'concept': [
        {'name': 'Concept_eval_funnel', 'description': 'Likelihood to\n1. Follow up and learn\n2. New & Different\n3. Meets needs\n4. Recommend to others', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Concept_Feature_Highlight', 'description': 'Highlight most important & least important words/phrases from the concept descr. Additional text feedback', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Concept_impression', 'description': 'Overall Impression', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Concept_Intro', 'description': 'Concept Introduction for pricing and reaction with hyperlink', 'mandatory': True, 'label_type': 'Text', 'applicable_labels': []},
        {'name': 'Concept_Purchase_Likelihood', 'description': 'How likely are you to purchase, how soon will you purchase', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Message_reaction', 'description': 'Question to check preference for Product/Feature Name, Caption etc', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Survey_Invite', 'description': '', 'mandatory': False, 'label_type': '', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_visual_impression', 'description': 'P1.\tPlease tell me on an 11 point scale, how much you liked this', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_visual_like', 'description': '', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_visual_dislike', 'description': '', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_Visual_features', 'description': '', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_Aroma_Check', 'description': '', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_Aroma_impression', 'description': '', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_Aroma_like', 'description': '', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_Aroma_dislike', 'description': '', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_Aroma_features', 'description': '', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_Aroma_Strength', 'description': '', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_Aroma_OE', 'description': '', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_taste_impression', 'description': '', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_taste_like', 'description': '', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_taste_dislike', 'description': '', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_quality_impression', 'description': '', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_taste_featuers', 'description': '', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_trial_likelihood', 'description': 'how much would you want to try this', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
        {'name': 'Concept_choice', 'description': 'Which concept you rank best, worst', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
    ],
    'methodology': [
        {'name': 'VW_Likelihood', 'description': 'Additional likelihood on chosen price points for calibration', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Van Westendorp']},
        {'name': 'VW_pricing', 'description': 'Good value, expensive etc', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': ['Van Westendorp']},
        {'name': 'Concept_Intro', 'description': 'Concept Introduction for pricing and reaction with hyperlink', 'mandatory': True, 'label_type': 'Text', 'applicable_labels': ['Concept_Intro']},
        {'name': 'GG_Likelihood', 'description': 'Random price point and change basis response', 'mandatory': True, 'label_type': 'QNR', 'applicable_labels': ['Gabor Granger']},
        {'name': 'Blind_Taste_Test', 'description': 'Taste test for consumer retail. Cigarettes, beverages, etc', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': ['Taste Test']},
    ],
    'additional': [
        {'name': 'Adnl_demographics', 'description': 'Education, Employment, Salary, Ethnicity', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Media_cons', 'description': 'What platforms active on? Where do you consume information', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Adoption_behavior', 'description': 'Adoption to new products and tech', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': []},
        {'name': 'Adnl_awareness', 'description': 'Aware of features and potential new tech', 'mandatory': False, 'label_type': 'QNR', 'applicable_labels': []},
    ],
    'programmer_instructions': [
        {'name': 'Survey_Closing', 'description': 'Thank you message and survey closing text', 'mandatory': True, 'label_type': 'Text', 'applicable_labels': []},
        {'name': 'Routing_Logic', 'description': 'IF/THEN/ELSE routing logic instructions', 'mandatory': False, 'label_type': 'Rules', 'applicable_labels': []},
        {'name': 'Quota_Checks', 'description': 'Quota checks and controls for sample management', 'mandatory': False, 'label_type': 'Rules', 'applicable_labels': []},
        {'name': 'Termination_Rules', 'description': 'Termination rules and eligibility criteria', 'mandatory': False, 'label_type': 'Rules', 'applicable_labels': []},
        {'name': 'Skip_Logic', 'description': 'Skip logic requirements for question flow', 'mandatory': False, 'label_type': 'Rules', 'applicable_labels': []},
        {'name': 'SEC_Calculation', 'description': 'Socio-economic classification calculations', 'mandatory': False, 'label_type': 'Rules', 'applicable_labels': []},
        {'name': 'Validation_Rules', 'description': 'Validation rules and data quality checks', 'mandatory': False, 'label_type': 'Rules', 'applicable_labels': []},
        {'name': 'Randomization_Logic', 'description': 'Question or option randomization instructions', 'mandatory': False, 'label_type': 'Rules', 'applicable_labels': []},
    ]
}

# Category to section mapping
CATEGORY_TO_SECTION = {
    'sample_plan': 1,
    'screener': 2,
    'brand': 3,
    'concept': 4,
    'methodology': 5,
    'additional': 6,
    'programmer_instructions': 7
}


def seed_qnr_labels(db: Session) -> int:
    """
    Seed QNR labels from hardcoded data
    Returns: count of labels seeded
    """
    total_inserted = 0
    
    for category, labels in QNR_LABELS_DATA.items():
        section_id = CATEGORY_TO_SECTION[category]
        display_order = 1
        
        for label_data in labels:
            # Normalize label_type (empty string means Text by default)
            label_type = label_data['label_type'] if label_data['label_type'] else 'Text'
            
            db.execute(
                text("""
                    INSERT INTO qnr_labels 
                    (name, category, description, mandatory, label_type, 
                     applicable_labels, section_id, display_order)
                    VALUES (:name, :category, :description, :mandatory, :label_type,
                            :applicable_labels, :section_id, :display_order)
                    ON CONFLICT (name) DO UPDATE SET
                        description = EXCLUDED.description,
                        mandatory = EXCLUDED.mandatory,
                        label_type = EXCLUDED.label_type,
                        applicable_labels = EXCLUDED.applicable_labels,
                        category = EXCLUDED.category,
                        section_id = EXCLUDED.section_id,
                        display_order = EXCLUDED.display_order,
                        updated_at = NOW()
                """),
                {
                    'name': label_data['name'],
                    'category': category,
                    'description': label_data['description'],
                    'mandatory': label_data['mandatory'],
                    'label_type': label_type,
                    'applicable_labels': label_data['applicable_labels'],
                    'section_id': section_id,
                    'display_order': display_order
                }
            )
            
            total_inserted += 1
            display_order += 1
    
    db.commit()
    logger.info(f"✅ Seeded {total_inserted} QNR labels")
    return total_inserted


if __name__ == "__main__":
    from src.database.connection import SessionLocal
    
    db = SessionLocal()
    try:
        count = seed_qnr_labels(db)
        print(f"✅ Successfully seeded {count} QNR labels")
    except Exception as e:
        print(f"❌ Error seeding QNR labels: {e}")
        raise
    finally:
        db.close()

