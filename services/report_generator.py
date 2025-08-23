from datetime import datetime
import json
import logging
import traceback

class ReportGenerator:
    def __init__(self):
        self.logger = logging.getLogger('services.report_generator')
        self.logger.info("ReportGenerator initialized")
    
    def generate_report(self, structured_data):
        self.logger.info("Starting report generation")
        
        try:
            if not structured_data:
                raise Exception("No structured data provided for report generation")
                
            self.logger.debug(f"Generating report from structured data: {json.dumps(structured_data, indent=2)}")
            
            discharge_summary = self._generate_discharge_summary(structured_data)
            
            report = {
                'discharge_summary': discharge_summary,
                'json_data': structured_data,
                'generated_at': datetime.now().isoformat()
            }
            
            self.logger.info("Report generation completed successfully")
            self.logger.info(f"Discharge summary length: {len(discharge_summary)} characters")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}")
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def _generate_discharge_summary(self, data):
        """Generate a comprehensive discharge summary following pediatric oncology format"""
        
        patient = data.get('patient_details', {})
        admission = data.get('admission_details', {})
        history = data.get('history', {})
        clinical = data.get('clinical_examination', {})
        investigations = data.get('investigations', {})
        treatment = data.get('treatment', {})
        
        summary = f"""
==============================================================================
                    DEPARTMENT OF PAEDIATRIC ONCOLOGY
==============================================================================

Division Head: {data.get('division_head', 'Dr. Priyakumari T (Professor)')}
Service Head: {data.get('service_head', 'Dr. Priyakumari T (Professor)')}

DISCHARGE SUMMARY

PATIENT DETAILS:
• CR No: {patient.get('cr_no', 'Not available')}
• Name: {patient.get('name', 'Not specified')}
• Age: {patient.get('age', 'Not specified')} years
• Sex: {patient.get('sex', 'Not specified')}
• Unit: {patient.get('unit', 'FC')}
• Attending Oncologist: {patient.get('attending_oncologist', 'Not specified')}

ADMISSION DETAILS:
• Diagnosis: {admission.get('diagnosis', 'Not specified')}
• Histology: {admission.get('histology', 'NIL')}
• Stage: {admission.get('stage', 'Not specified')}
• Date of Admission: {admission.get('doa', 'Not specified')}
• Date of Discharge: {admission.get('dod', 'Not specified')}
• Reason for Admission: {admission.get('reason_for_admission', 'Not specified')}

HISTORY:
• Chief Complaints: {history.get('chief_complaints', 'Not specified')}
• Presenting History: {history.get('presenting_history', 'Not specified')}

CLINICAL EXAMINATION:
• General Condition: {clinical.get('general_condition', 'Not documented')}

Vitals:
  - Heart Rate: {clinical.get('vitals', {}).get('hr', 'Not recorded')}
  - Blood Pressure: {clinical.get('vitals', {}).get('bp', 'Not recorded')}
  - Temperature: {clinical.get('vitals', {}).get('temp', 'Not recorded')}
  - Respiratory Rate: {clinical.get('vitals', {}).get('rr', 'Not recorded')}

Systems Examination:
  - Respiratory System: {clinical.get('systems', {}).get('respiratory_system', 'WNL')}
  - Cardiovascular System: {clinical.get('systems', {}).get('cardiovascular_system', 'WNL')}
  - Gastrointestinal System: {clinical.get('systems', {}).get('gastrointestinal_system', 'WNL')}
  - Neurological System: {clinical.get('systems', {}).get('neurological_system', 'WNL')}
  - Other Systems: {clinical.get('systems', {}).get('other_systems', 'WNL')}

INVESTIGATIONS:
"""
        
        # Lab Results
        if investigations.get('lab_results'):
            summary += "Laboratory Results:\n"
            for i, lab in enumerate(investigations['lab_results'], 1):
                summary += f"  {lab.get('date', 'Date not specified')}:\n"
                if lab.get('hb'): summary += f"    - Hb: {lab['hb']}\n"
                if lab.get('wbc'): summary += f"    - WBC: {lab['wbc']}\n"
                if lab.get('platelet'): summary += f"    - Platelet: {lab['platelet']}\n"
                if lab.get('dc_neutrophils'): summary += f"    - Neutrophils: {lab['dc_neutrophils']}%\n"
                if lab.get('lymphocytes'): summary += f"    - Lymphocytes: {lab['lymphocytes']}%\n"
        else:
            summary += "Laboratory Results: No specific lab values documented\n"
        
        # Other Investigations
        other_inv = investigations.get('other_investigations', {})
        if any(other_inv.values()):
            summary += "\nOther Investigations:\n"
            if other_inv.get('blood_culture'): summary += f"  - Blood Culture: {other_inv['blood_culture']}\n"
            if other_inv.get('procalcitonin'): summary += f"  - Procalcitonin: {other_inv['procalcitonin']}\n"
            if other_inv.get('cxr'): summary += f"  - CXR: {other_inv['cxr']}\n"
        
        summary += "\nTREATMENT:\n"
        
        # Medications
        if treatment.get('medications'):
            summary += "Medications:\n"
            for med in treatment['medications']:
                summary += f"  • {med.get('name', 'Unknown medication')}"
                if med.get('dose'): summary += f" - {med['dose']}"
                if med.get('frequency'): summary += f" ({med['frequency']})"
                if med.get('duration'): summary += f" for {med['duration']}"
                summary += "\n"
        else:
            summary += "Medications: Not specified\n"
        
        # Course in Hospital
        if data.get('course_in_hospital'):
            summary += f"\nCOURSE IN HOSPITAL:\n{data['course_in_hospital']}\n"
        
        # Medical Team
        if data.get('doctors'):
            summary += "\nMEDICAL TEAM:\n"
            for doctor in data['doctors']:
                summary += f"• {doctor}\n"
        
        # Emergency Contacts
        emergency = data.get('emergency_contacts', {})
        if emergency:
            summary += "\nEMERGENCY CONTACTS:\n"
            summary += f"• Casualty: {emergency.get('casualty', 'Not available')} (24 Hours)\n"
            summary += f"• A Clinic: {emergency.get('a_clinic', 'Not available')}\n"
            summary += f"• B Clinic: {emergency.get('b_clinic', 'Not available')}\n"
            summary += f"• C Clinic: {emergency.get('c_clinic', 'Not available')}\n"
            summary += f"• D Clinic: {emergency.get('d_clinic', 'Not available')}\n"
            summary += f"• E Clinic: {emergency.get('e_clinic', 'Not available')}\n"
            summary += f"• F Clinic: {emergency.get('f_clinic', 'Not available')}\n"
        
        # Metadata
        metadata = data.get('metadata', {})
        summary += f"\n" + "="*78 + "\n"
        summary += f"Report generated: {metadata.get('generated_at', 'Unknown')}\n"
        summary += f"Processing model: {metadata.get('processing_model', 'Unknown')}\n"
        summary += f"Confidence score: {metadata.get('confidence_score', 0):.1%}\n"
        summary += "="*78 + "\n"
        
        return summary.strip()
    
    def export_to_json(self, structured_data, filename):
        with open(filename, 'w') as f:
            json.dump(structured_data, f, indent=2)
            
    def export_to_text(self, report, filename):
        with open(filename, 'w') as f:
            f.write(report['discharge_summary'])