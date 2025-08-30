PEDIATRIC_ONCOLOGY_SCHEMA = {
    "type": "object",
    "properties": {
        "department": {"type": "string", "default": "Department of Paediatric Oncology"},
        "division_head": {"type": "string", "default": "Dr. Priyakumari T (Professor)"},
        "service_head": {"type": "string", "default": "Dr. Priyakumari T (Professor)"},
        "doctors": {
            "type": "array",
            "items": {"type": "string"},
            "default": [
                "Dr. Manjusha Nair (Assoc. Professor)",
                "Dr. Prasanth VR (Asst. Professor)", 
                "Dr. Binitha R (Assoc. Professor)",
                "Dr. Guruprasad CS (Assoc. Professor)",
                "Dr. Kalasekhar VS (Asst. Professor)"
            ]
        },
        "patient_details": {
            "type": "object",
            "properties": {
                "cr_no": {"type": "string"},
                "name": {"type": "string"},
                "age": {"type": ["string", "integer"]},
                "sex": {"type": "string"},
                "unit": {"type": "string"},
                "attending_oncologist": {"type": "string"}
            }
        },
        "admission_details": {
            "type": "object",
            "properties": {
                "diagnosis": {"type": "string"},
                "histology": {"type": "string"},
                "stage": {"type": "string"},
                "doa": {"type": "string"},
                "dod": {"type": "string"},
                "reason_for_admission": {"type": "string"}
            }
        },
        "history": {
            "type": "object",
            "properties": {
                "chief_complaints": {"type": "string"},
                "presenting_history": {"type": "string"}
            }
        },
        "clinical_examination": {
            "type": "object",
            "properties": {
                "general_condition": {"type": "string"},
                "vitals": {
                    "type": "object",
                    "properties": {
                        "hr": {"type": "string"},
                        "bp": {"type": "string"},
                        "temp": {"type": "string"},
                        "rr": {"type": "string"}
                    }
                },
                "systems": {
                    "type": "object",
                    "properties": {
                        "respiratory_system": {"type": "string"},
                        "cardiovascular_system": {"type": "string"},
                        "gastrointestinal_system": {"type": "string"},
                        "neurological_system": {"type": "string"},
                        "other_systems": {"type": "string"}
                    }
                }
            }
        },
        "investigations": {
            "type": "object",
            "properties": {
                "lab_results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string"},
                            "hb": {"type": "string"},
                            "wbc": {"type": "string"},
                            "platelet": {"type": "string"},
                            "dc_neutrophils": {"type": "string"},
                            "lymphocytes": {"type": "string"},
                            "eosinophils": {"type": "string"},
                            "monocytes": {"type": "string"},
                            "basophils": {"type": "string"},
                            "total_protein": {"type": "string"},
                            "sodium": {"type": "string"},
                            "potassium": {"type": "string"},
                            "urea": {"type": "string"},
                            "creatinine": {"type": "string"},
                            "sgpt": {"type": "string"},
                            "sgot": {"type": "string"},
                            "c_reactive_protein": {"type": "string"},
                            "phosphorus": {"type": "string"},
                            "calcium": {"type": "string"},
                            "bilirubin_total": {"type": "string"},
                            "alkaline_phosphatase": {"type": "string"},
                            "albumin": {"type": "string"},
                            "random_sugar": {"type": "string"},
                            "magnesium": {"type": "string"}
                        }
                    }
                },
                "other_investigations": {
                    "type": "object",
                    "properties": {
                        "blood_culture": {"type": "string"},
                        "procalcitonin": {"type": "string"},
                        "cxr": {"type": "string"},
                        "urine_culture": {"type": "string"},
                        "other": {"type": "string"}
                    }
                }
            }
        },
        "treatment": {
            "type": "object",
            "properties": {
                "drugs_regime_and_dose": {"type": "object"},
                "medications": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "dose": {"type": "string"},
                            "frequency": {"type": "string"},
                            "duration": {"type": "string"}
                        }
                    }
                }
            }
        },
        "course_in_hospital": {"type": "string"},
        "emergency_contacts": {
            "type": "object",
            "properties": {
                "casualty": {"type": "string", "default": "04712522458 (24 Hrs)"},
                "a_clinic": {"type": "string", "default": "04712522317/2522392/2522391"},
                "b_clinic": {"type": "string", "default": "04712522379/2522398"},
                "c_clinic": {"type": "string", "default": "04712522202/2522371"},
                "d_clinic": {"type": "string", "default": "04712522372/2522374"},
                "e_clinic": {"type": "string", "default": "04712522334/2522397"},
                "f_clinic": {"type": "string", "default": "04712522368/8289897454"}
            }
        },
        "original_transcript": {"type": "string"},
        "metadata": {
            "type": "object",
            "properties": {
                "generated_at": {"type": "string"},
                "processing_model": {"type": "string"},
                "confidence_score": {"type": "number"}
            }
        }
    }
}

DISCHARGE_SUMMARY_TEMPLATE = """
PEDIATRIC ONCOLOGY DISCHARGE SUMMARY

PATIENT INFORMATION:
Name: {patient_name}
Age: {patient_age}
Sex: {patient_sex}
MRN: {patient_mrn}
Date of Report: {report_date}

DIAGNOSIS:
{diagnoses_section}

CLINICAL EXAMINATION:
{clinical_findings_section}

INVESTIGATIONS:
{lab_results_section}

TREATMENT:
{medications_section}

MEDICAL TEAM:
{medical_professionals_section}

ORIGINAL TRANSCRIPT:
{original_transcript}
"""