import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

class GeminiNLPService:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
        
    def extract_entities(self, text):
        prompt = f"""
        Extract medical entities from this pediatric oncology clinical text. 
        Return ONLY a JSON object with these fields:
        
        {{
            "patient_details": {{
                "age": null,
                "sex": null,
                "name": null
            }},
            "diagnoses": [],
            "clinical_findings": [],
            "lab_results": [],
            "medications": [],
            "medical_professionals": []
        }}
        
        Clinical text: "{text}"
        
        Instructions:
        - Extract age as number only
        - Extract sex as M/F
        - Put diagnoses like "B-ALL", "leukemia" in diagnoses array
        - Put vital signs, symptoms in clinical_findings
        - Put lab values like "Hb 9", "WBC 1000" in lab_results
        - Put drug names in medications array
        - Put doctor names in medical_professionals
        - Return valid JSON only, no explanation
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            json_text = response.text.strip()
            if json_text.startswith('```json'):
                json_text = json_text.replace('```json', '').replace('```', '').strip()
            
            entities = json.loads(json_text)
            return entities
            
        except Exception as e:
            print(f"Gemini extraction error: {e}")
            return self._fallback_extraction(text)
    
    def _fallback_extraction(self, text):
        structured_data = {
            'patient_details': {'age': None, 'sex': None, 'name': None},
            'diagnoses': [],
            'clinical_findings': [],
            'lab_results': [],
            'medications': [],
            'medical_professionals': []
        }
        
        age_match = re.search(r'(?:age|aged?)\s*:?\s*(\d+)', text, re.IGNORECASE)
        if age_match:
            structured_data['patient_details']['age'] = age_match.group(1)
            
        sex_match = re.search(r'(?:sex|gender)\s*:?\s*(male|female|m|f)', text, re.IGNORECASE)
        if sex_match:
            structured_data['patient_details']['sex'] = sex_match.group(1).upper()
            
        if 'dr.' in text.lower() or 'doctor' in text.lower():
            dr_matches = re.findall(r'dr\.?\s*([a-z\s\.]+)', text, re.IGNORECASE)
            structured_data['medical_professionals'].extend(dr_matches)
            
        return structured_data
    
    def structure_data(self, entities, original_text):
        entities['original_transcript'] = original_text
        return entities