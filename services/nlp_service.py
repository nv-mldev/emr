from google.cloud import language_v1
import re
import json
import logging
import traceback

class NLPService:
    def __init__(self):
        self.client = language_v1.LanguageServiceClient()
        self.logger = logging.getLogger('services.nlp_service')
        self.logger.info("NLPService initialized")
        
    def extract_entities(self, text):
        self.logger.info(f"Starting entity extraction for text: {len(text)} characters")
        
        try:
            if not text or text.strip() == "":
                self.logger.warning("Empty text provided for entity extraction")
                return []
                
            document = language_v1.Document(
                content=text,
                type_=language_v1.Document.Type.PLAIN_TEXT,
            )
            
            self.logger.debug("Calling Google Cloud Natural Language API")
            response = self.client.analyze_entities(
                request={'document': document, 'encoding_type': language_v1.EncodingType.UTF8}
            )
            
            entities = []
            for entity in response.entities:
                entity_data = {
                    'name': entity.name,
                    'type': entity.type_.name,
                    'salience': entity.salience,
                    'mentions': [mention.text.content for mention in entity.mentions]
                }
                entities.append(entity_data)
                self.logger.debug(f"Extracted entity: {entity.name} (type: {entity.type_.name}, salience: {entity.salience:.3f})")
            
            self.logger.info(f"Successfully extracted {len(entities)} entities")
            return entities
            
        except Exception as e:
            self.logger.error(f"Entity extraction failed: {str(e)}")
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def structure_data(self, entities, original_text):
        from datetime import datetime
        from utils.json_schema import PEDIATRIC_ONCOLOGY_SCHEMA
        
        # Initialize with default department information
        structured_data = {
            'department': 'Department of Paediatric Oncology',
            'division_head': 'Dr. Priyakumari T (Professor)',
            'service_head': 'Dr. Priyakumari T (Professor)',
            'doctors': [
                'Dr. Manjusha Nair (Assoc. Professor)',
                'Dr. Prasanth VR (Asst. Professor)', 
                'Dr. Binitha R (Assoc. Professor)',
                'Dr. Guruprasad CS (Assoc. Professor)',
                'Dr. Kalasekhar VS (Asst. Professor)'
            ],
            'patient_details': {
                'cr_no': '',
                'name': '',
                'age': '',
                'sex': '',
                'unit': '',
                'attending_oncologist': ''
            },
            'admission_details': {
                'diagnosis': '',
                'histology': 'NIL',
                'stage': '',
                'doa': '',
                'dod': '',
                'reason_for_admission': ''
            },
            'history': {
                'chief_complaints': '',
                'presenting_history': ''
            },
            'clinical_examination': {
                'general_condition': '',
                'vitals': {
                    'hr': '',
                    'bp': '',
                    'temp': '',
                    'rr': ''
                },
                'systems': {
                    'respiratory_system': '',
                    'cardiovascular_system': 'WNL',
                    'gastrointestinal_system': 'WNL',
                    'neurological_system': 'WNL',
                    'other_systems': 'WNL'
                }
            },
            'investigations': {
                'lab_results': [],
                'other_investigations': {
                    'blood_culture': '',
                    'procalcitonin': '',
                    'cxr': '',
                    'urine_culture': '',
                    'other': ''
                }
            },
            'treatment': {
                'drugs_regime_and_dose': {},
                'medications': []
            },
            'course_in_hospital': '',
            'emergency_contacts': {
                'casualty': '04712522458 (24 Hrs)',
                'a_clinic': '04712522317/2522392/2522391',
                'b_clinic': '04712522379/2522398',
                'c_clinic': '04712522202/2522371',
                'd_clinic': '04712522372/2522374',
                'e_clinic': '04712522334/2522397',
                'f_clinic': '04712522368/8289897454'
            },
            'original_transcript': original_text,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'processing_model': 'google_cloud_nlp',
                'confidence_score': 0.0
            }
        }
        
        self.logger.info("Parsing medical entities from transcription")
        
        # Extract patient demographics
        age_pattern = r'(?:age|aged?)\s*:?\s*(\d+)'
        age_match = re.search(age_pattern, original_text, re.IGNORECASE)
        if age_match:
            structured_data['patient_details']['age'] = age_match.group(1)
            
        sex_pattern = r'(?:sex|gender)\s*:?\s*(male|female|m|f)'
        sex_match = re.search(sex_pattern, original_text, re.IGNORECASE)
        if sex_match:
            structured_data['patient_details']['sex'] = sex_match.group(1).upper()
        
        # Extract diagnosis information
        diagnosis_patterns = [
            r'(B[\s-]?ALL[^\.]*)',
            r'(leukemia[^\.]*)',
            r'(diagnosed with ([^\.]+))',
            r'(condition[:\s]+([^\.]+))'
        ]
        for pattern in diagnosis_patterns:
            matches = re.findall(pattern, original_text, re.IGNORECASE)
            for match in matches:
                diagnosis = match[0] if isinstance(match, tuple) else match
                if diagnosis and diagnosis not in structured_data['admission_details']['diagnosis']:
                    structured_data['admission_details']['diagnosis'] = diagnosis.strip()
                    break
        
        # Extract vitals and clinical findings
        temp_pattern = r'(?:temperature|temp|fever)[:\s]*(\d+\.?\d*)\s*(F|C|fahrenheit|celsius)?'
        temp_match = re.search(temp_pattern, original_text, re.IGNORECASE)
        if temp_match:
            temp_unit = temp_match.group(2) if temp_match.group(2) else 'F'
            structured_data['clinical_examination']['vitals']['temp'] = f"{temp_match.group(1)}°{temp_unit.upper()}"
            structured_data['clinical_examination']['general_condition'] = f"Febrile ({temp_match.group(1)}°{temp_unit.upper()})"
        
        hr_pattern = r'(?:heart rate|HR|pulse)[:\s]*(\d+)(?:/min)?'
        hr_match = re.search(hr_pattern, original_text, re.IGNORECASE)
        if hr_match:
            structured_data['clinical_examination']['vitals']['hr'] = f"{hr_match.group(1)}/min"
        
        bp_pattern = r'(?:blood pressure|BP)[:\s]*(\d+/\d+)'
        bp_match = re.search(bp_pattern, original_text, re.IGNORECASE)
        if bp_match:
            structured_data['clinical_examination']['vitals']['bp'] = f"{bp_match.group(1)}mmhg"
        
        # Extract respiratory system findings
        resp_findings = []
        if re.search(r'crepitations?', original_text, re.IGNORECASE):
            resp_findings.append('Crepitations present')
        if re.search(r'no retractions?', original_text, re.IGNORECASE):
            resp_findings.append('No retractions')
        if resp_findings:
            structured_data['clinical_examination']['systems']['respiratory_system'] = '. '.join(resp_findings)
        
        # Extract lab results
        lab_result = {}
        lab_patterns = {
            'hb': r'(?:Hb|hemoglobin)[:\s]*(\d+\.?\d*)',
            'wbc': r'(?:WBC|white blood cell count?)[:\s]*(\d+\.?\d*)',
            'platelet': r'(?:platelet count?)[:\s]*(\d+\.?\d*)'
        }
        
        for lab_name, pattern in lab_patterns.items():
            match = re.search(pattern, original_text, re.IGNORECASE)
            if match:
                lab_result[lab_name] = match.group(1)
        
        if lab_result:
            lab_result['date'] = datetime.now().strftime('%d/%m/%Y')
            structured_data['investigations']['lab_results'].append(lab_result)
        
        # Extract medications
        medication_patterns = [
            r'((?:Inj\.?\s+|Syp\.?\s+|Tab\.?\s+)?(?:Cefoperazone[^,\.]*|Oseltamivir[^,\.]*|Clarithromycin[^,\.]*|Paracetamol[^,\.]*|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)[^,\.]*)',
        ]
        
        medications_found = set()
        for pattern in medication_patterns:
            matches = re.findall(pattern, original_text, re.IGNORECASE)
            for match in matches:
                med_name = match.strip()
                if len(med_name) > 3 and med_name not in medications_found:
                    medications_found.add(med_name)
                    structured_data['treatment']['medications'].append({
                        'name': med_name,
                        'dose': '',
                        'frequency': '',
                        'duration': ''
                    })
        
        # Extract attending oncologist
        dr_pattern = r'(?:Dr\.?\s+|Doctor\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]*\.?)*)'
        dr_matches = re.findall(dr_pattern, original_text, re.IGNORECASE)
        for dr_name in dr_matches:
            full_name = f"Dr. {dr_name.strip()}"
            if not structured_data['patient_details']['attending_oncologist']:
                structured_data['patient_details']['attending_oncologist'] = full_name
            break
        
        # Extract chief complaints and history
        complaint_patterns = [
            r'(?:chief complaint|complaints?|CC)[:\s]+([^\.]+)',
            r'(?:presenting with|presents with|admitted with)[:\s]+([^\.]+)',
            r'(?:fever[^\.]*cough[^\.]*|cough[^\.]*fever[^\.]*)'
        ]
        
        for pattern in complaint_patterns:
            match = re.search(pattern, original_text, re.IGNORECASE)
            if match:
                complaint = match.group(1) if len(match.groups()) > 0 else match.group(0)
                structured_data['history']['chief_complaints'] = complaint.strip()
                break
        
        # Use original text for presenting history if specific history not found
        if not structured_data['history']['presenting_history']:
            structured_data['history']['presenting_history'] = original_text[:200] + "..." if len(original_text) > 200 else original_text
        
        # Calculate confidence score based on extracted information
        confidence_factors = 0
        total_factors = 6
        
        if structured_data['patient_details']['age']: confidence_factors += 1
        if structured_data['patient_details']['sex']: confidence_factors += 1
        if structured_data['admission_details']['diagnosis']: confidence_factors += 1
        if structured_data['clinical_examination']['vitals']['temp']: confidence_factors += 1
        if structured_data['investigations']['lab_results']: confidence_factors += 1
        if structured_data['treatment']['medications']: confidence_factors += 1
        
        structured_data['metadata']['confidence_score'] = confidence_factors / total_factors
        
        self.logger.info(f"Structured data extraction completed with confidence: {structured_data['metadata']['confidence_score']:.2f}")
        
        return structured_data