#!/usr/bin/env python3
"""
Test script to verify character array handling fix in document parser
"""

import ast
import json

def test_character_array_handling():
    """Test the character array handling logic from document parser"""
    
    # This is the actual character array response from the failed document
    # Based on the LLM audit output we saw earlier
    character_array_response = """['\\n\\n', 'Here is', ' the extracted RF', 'Q information in', ' JSON format:\\n\\n', '```\\n{\\n', '  "confidence', '\": 0', '.85,\\n', '  "', 'identified_sections', '\": {\\n', '    "object', 'ives\": {\\n', '      "confidence', '\": 0', '.9,\\n', '      "', 'source', '_text\": \"', 'Determine', ' optimal', ' price', ' points for AIR', ' OPTIX plus', ' HydraGly', 'de across different', ' market segments\",\\n', '      "', 'source', '_section\": \"', 'Research Objectives', '\",\\n', '      "', 'extracted', '_data', '\": [\"Price', ' Acceptance Analysis', '\", \"Purchase', ' Intent Measurement\", \"', 'Value', ' Perception Assessment\"]\\n', '    },\\n', '    "business', '_context', '\": {\\n', '      "confidence', '\": 0', '.8,\\n', '      "', 'source', '_text', '\": \"', 'Al', 'con', ' is the', ' global', ' leader in', ' eye care', ' with over', ' 75', ' years of', ' heritage', ', operating as', ' the largest eye', ' care device company', ' worldwide.\",\\n', '      "', 'source', '_section\":', ' \"Company', ' Background\",\\n', '      "', 'extracted', '_data', '\": [\"', 'Al', 'con\", \"', 'eye', ' care\",', ' \"global leader\"]\\n', '    },\\n', '    "target', '_audience', '\": {\\n', '      "', 'confidence\": ', '0.', '9,\\n', '      "', 'source_text', '\": \"', 'Current', ' Contact Lens Wear', 'ers (', '70', '% of', ' sample', ') and New', ' Contact Lens Adopt', 'ers (', '30', '% of', ' sample', ')\",\\n', '      "', 'source', '_section\":', ' \"Primary Consumers', ' and Target Audience', '\",\\n', '      "', 'extracted', '_data', '\": [\"', 'Current', ' Contact Lens', ' Wearers\",', ' \"New', ' Contact Lens Adopters', '\"]\\n', '    },\\n', '    "constraints', '\": {\\n', '      "confidence', '\": 0', '.8,\\n', '      "', 'source', '_text\":', ' \"', 'Total', ' Sample', ' Size: ', '800-', '1', ',200 respondents', '\",\\n', '      "', 'source_section', '\": \"Sample', ' Considerations\",\\n', '      "extract', 'ed_data\":', ' [\"', 'Total Sample', ' Size\", \"', '800', '-', '1', ',200', ' respondents', '\"]\\n', '    },\\n', '    "', 'method', 'ologies', '\": {\\n', '      "confidence', '\": 0', '.7,\\n', '      "', 'source_text\":', ' \"', 'Quantitative', ' pricing study\",\\n', '      "', 'source', '_section\": \"', 'Research', ' Objectives\",\\n', '     ', ' \"', 'extract', 'ed_data', '\":', ' [\"Quant', 'itative pricing', ' study\"]\\n', '    }\\n', '  },\\n', '  "extract', 'ed', '_entities', '\": {\\n', '    "', 'stakeholders', '\":', ' [\"Al', 'con', '\", \"', 'Contact Lens', ' Wearers', '\"],\\n', '    "', 'indust', 'ries', '\": [\"', 'Eye Care\",', ' \"Health', 'care\"],\\n', '    "', 'research', '_types\":', ' [\"', 'Quantitative', ' Pricing Study\",', ' \"', 'Market Research', '\"],\\n', '    "', 'method', 'ologies', '\": [\"', 'Quantitative', '\"]\\n', '  },\\n', '  "field', '_mappings', '\": [\\n', '    {\\n', '     ', ' \"field\":', ' \"', 'title\",\\n', '      "value', '\": \"', 'Quant', 'itative Market Research', ' for Contact Lens', ' Pricing: AIR', ' OPTIX plus', ' HydraGly', 'de Pricing Study', '\",\\n', '      "', 'confidence\": ', '0.95', ',\\n', '      "', 'source\": \"', 'Title', ': Quant', 'itative Market Research', ' for Contact Lens', ' Pricing: AIR', ' OPTIX plus', ' HydraGly', 'de Pricing Study', '\",\\n', '     ', ' \"reasoning', '\": \"', 'Clear', ' title', ' in document', ' header', '\",\\n', '     ', ' \"priority\":', ' \"', 'critical\"\\n', '    },\\n', '    {\\n', '      "field', '\": \"description', '\",\\n', '      "', 'value\": \"', 'Conduct', ' a comprehensive', ' quantitative pricing', ' study for the', ' recently launched AIR', ' OPTIX plus', ' HydraGly', 'de contact lens', ' product.\",\\n', '     ', ' \"confidence\":', ' 0.', '85,\\n', '     ', ' \"source\":', ' \"', 'The company', ' is seeking proposals', ' from qualified market', ' research agencies to', ' conduct a comprehensive', ' quantitative pricing study', '...\",\\n', '      "', 'reasoning\":', ' \"', 'Main research', ' description', ' in introduction', '\",\\n', '      "', 'priority\": \"', 'critical\"\\n', '    },\\n', '    {\\n', '      "field', '\": \"company', '_product_background\",\\n', '      "value', '\": \"', 'Al', 'con', ' is the', ' global leader in', ' eye care with', ' over 75', ' years of heritage', ', operating as', ' the largest eye', ' care device company', ' worldwide.\",\\n', '      "', 'confidence\": ', '0.80', ',\\n', '      "', 'source\": \"', 'About Alcon', ': We are', ' the global leader', ' in eye care', ' with over ', '75 years of', ' heritage...\",\\n', '     ', ' \"reasoning', '\": \"Company', ' background section with', ' clear business context', '\",\\n', '      "', 'priority\": \"', 'critical\"\\n', '    },\\n', '    {\\n', '      "field', '\": \"business', '_problem\",\\n', '     ', ' \"value\":', ' \"', 'Determine', ' optimal price points', ' for AIR OPT', 'IX plus Hydra', 'Glyde', ' across different market', ' segments\",\\n', '     ', ' \"confidence\":', ' 0.', '85,\\n', '     ', ' \"source\":', ' \"The', ' challenge we face', ' is determining which', ' features to prioritize', ' for the next', ' product release...\",\\n', '      "', 'reason', 'ing\": \"', 'Clear problem statement', ' in business context', '\",\\n', '      "', 'priority\": \"', 'high\"\\n', '    },\\n', '    {\\n', '      "field', '\": \"primary', '_method\",\\n', '     ', ' \"value\":', ' \"', 'Quantitative', '\",\\n', '      "', 'confidence\": ', '0.90', ',\\n', '      "', 'source\": \"', 'Quantitative pricing', ' study\",\\n', '     ', ' \"reasoning', '\": \"Explicit', ' mention of quantitative', ' methodology\",\\n', '     ', ' \"priority', '\": \"', 'high\"\\n', '    },\\n', '    {\\n', '      "', 'field\": \"', 'research', '_aud', 'ience\",\\n', '     ', ' \"value\":', ' \"', 'Current Contact', ' Lens', ' Wearers', ' (', '70', '% of', ' sample)', ' and New Contact', ' Lens Adopters', ' (', '30', '% of', ' sample', ')\",\\n', '      "confidence', '\": 0', '.9,\\n', '      "source', '\": \"Target', ' participants: Current', ' Contact', ' Lens Wear', 'ers (', '70', '% of sample', ') and New', ' Contact Lens Adopt', 'ers (', '30', '% of sample', ')\",\\n', '      "', 'reasoning', '\": \"', 'Clear demographic', ' and behavioral', ' criteria\",\\n', '      "', 'priority\": \"', 'medium\"\\n', '    },\\n', '    {\\n', '      "field', '\": \"', 'q', 'nr_sections', '_detected', '\",\\n', '      "', 'value\": [\"', 'sample_plan\",', ' \"s', 'cre', 'ener\",', ' \"', 'concept_ex', 'posure', '\", \"', 'method', 'ology_section\",', ' \"additional', '_questions', '\", \"', 'program', 'mer_instructions', '\"],\\n', '      "', 'confidence\": ', '0.', '80,\\n', '      "', 'source\": \"', 'Quant', 'itative pricing study', ' methodology', ' detected\",\\n', '     ', ' \"reason', 'ing\": \"', 'Based on quantitative', ' methodology, these', ' Q', 'NR sections', ' are required\",\\n', '     ', ' \"priority', '\": \"medium', '\"\\n', '    },\\n', '    {\\n', '     ', ' \"field\":', ' \"', 'text', '_requirements_detected', '\",\\n', '      "', 'value\": [\"', 'Study_Intro', '\",', ' \"Conf', 'identiality_A', 'greement\"],\\n', '      "confidence', '\": 0', '.9,\\n', '      "', 'source\": \"', 'Quant', 'itative', ' study with', ' sensitive data', ' collection', '\",\\n', '      "', 'reasoning\":', ' \"', 'Quantitative', ' studies require study', ' intro and confidentiality', ' agreement\",\\n', '     ', ' \"priority\": \"', 'medium\"\\n', '    },\\n', '    {\\n', '     ', ' \"field\": \"', 'requires_piping', '_logic\",\\n', '     ', ' \"value\":', ' true,\\n', '     ', ' \"confidence\":', ' 0.', '9,\\n', '     ', ' \"source\":', ' \"Complex conj', 'oint design with', ' feature', ' dependencies\",\\n', '      "', 'reasoning\": \"', 'Quantitative analysis', ' typically requires piping', ' logic for dynamic', ' choice tasks\",\\n', '      "', 'priority\": \"', 'medium\"\\n', '    },\\n', '    {\\n', '     ', ' \"field\":', ' \"requires_sampling', '_logic\",\\n', '      "', 'value\": false', ',\\n', '      "', 'confidence\": ', '0.65', ',\\n', '      "', 'source\": \"', 'No specific', ' quota', ' or random', 'ization', ' requirements mentioned\",\\n', '      "', 'reasoning\": \"', 'Standard sampling', ' approach implied\",\\n', '      "', 'priority\": \"', 'medium\"\\n', '    },\\n', '    {\\n', '     ', ' \"field\": \"', 'brand_recall', '_required\",\\n', '      "', 'value\":', ' false,\\n', '      "', 'confidence\": ', '0.80', ',\\n', '      "', 'source', '\":', ' \"Focus on', ' product', ' features,', ' not', ' brand awareness\",\\n', '      "', 'reasoning\": \"', 'Feature research', \" doesn't require\", ' brand recall questions\",\\n', '      "', 'priority', '\": \"medium', '\"\\n', '    }\\n', '  ]\\n', '}\\n', '```']"""
    
    print("🧪 Testing character array handling logic...")
    print(f"📊 Input length: {len(character_array_response)} characters")
    print(f"📊 Input starts with: {character_array_response[:50]}")
    print(f"📊 Input ends with: {character_array_response[-50:]}")
    
    # Test the character array detection and conversion logic
    json_content = character_array_response.strip()
    
    print(f"\n🔍 Checking for character array format...")
    print(f"🔍 Content starts with: {json_content[:50]}")
    print(f"🔍 Content ends with: {json_content[-50:]}")
    
    if json_content.startswith('[') and json_content.endswith(']'):
        print(f"🔧 Detected potential character array format")
        try:
            # Try to parse as a character array and join it
            char_array = ast.literal_eval(json_content)
            if isinstance(char_array, list) and all(isinstance(c, str) for c in char_array):
                original_length = len(json_content)
                json_content = ''.join(char_array).strip()
                print(f"🔧 Successfully converted character array to string")
                print(f"🔧 Original length: {original_length}, New length: {len(json_content)}")
                print(f"🔧 First 200 chars: {json_content[:200]}")
                
                # Now try to parse as JSON - need to extract JSON from the text
                print(f"\n🔍 Attempting to parse as JSON...")
                
                # Look for JSON content between ``` markers or extract JSON object
                import re
                
                # Try to find JSON between ``` markers
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', json_content, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
                    print(f"🔧 Found JSON between ``` markers")
                else:
                    # Try to find JSON object starting with {
                    json_match = re.search(r'(\{.*\})', json_content, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(1)
                        print(f"🔧 Found JSON object in text")
                    else:
                        print(f"❌ No JSON object found in converted text")
                        return False
                
                try:
                    parsed_json = json.loads(json_text)
                    print(f"✅ JSON parsing successful!")
                    print(f"📊 Parsed JSON keys: {list(parsed_json.keys()) if isinstance(parsed_json, dict) else 'Not a dict'}")
                    print(f"📊 Confidence score: {parsed_json.get('confidence', 'N/A')}")
                    return True
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing failed: {e}")
                    print(f"🔍 JSON error at position {e.pos}: {json_text[max(0, e.pos-50):e.pos+50]}")
                    return False
            else:
                print(f"⚠️ Character array contains non-string elements")
                print(f"⚠️ Array type: {type(char_array)}, First few elements: {char_array[:5] if char_array else 'empty'}")
                return False
        except Exception as e:
            print(f"⚠️ Failed to parse character array: {e}")
            print(f"⚠️ Raw content: {json_content[:100]}")
            return False
    else:
        print(f"🔍 Content does not appear to be a character array")
        return False

if __name__ == "__main__":
    success = test_character_array_handling()
    if success:
        print("\n🎉 Character array handling test PASSED!")
    else:
        print("\n❌ Character array handling test FAILED!")
