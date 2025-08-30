#!/usr/bin/env python3
"""
Test script to demonstrate the new pediatric oncology JSON schema
"""

import requests
import json

def test_schema_with_sample_data():
    """Test the API with sample medical dictation"""
    
    # Sample medical dictation from work.md
    sample_transcription = """
    Patient is a 7-year-old female with B-ALL high risk induction day 30. 
    She is now admitted with fever associated with cough and rhinitis. 
    Temperature 100.3 Fahrenheit. General condition is fair, febrile.
    Heart rate 120 per minute, blood pressure 104/60 mmHg.
    Respiratory system shows no retractions, crepitations present.
    Laboratory results show Hemoglobin 9, WBC count 1000, platelet count 147000.
    She was started on Cefoperazone sulbactam for 3 days, 
    Oseltamivir for 3 days, and Clarithromycin for 3 days.
    Attending physician Dr. Prasanth V.R.
    """
    
    print("🧪 Testing Pediatric Oncology Schema Integration")
    print("=" * 60)
    
    try:
        # Test report generation with sample data
        response = requests.post('http://127.0.0.1:5000/api/generate-report', 
                               json={'transcription': sample_transcription})
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Report generation successful!")
            print("\n📋 Structured Data Preview:")
            print("-" * 40)
            
            # Display key sections
            structured = data.get('structured_data', {})
            
            print(f"🏥 Department: {structured.get('department')}")
            print(f"👨‍⚕️ Division Head: {structured.get('division_head')}")
            
            patient = structured.get('patient_details', {})
            print(f"\n👤 Patient Details:")
            print(f"   Age: {patient.get('age')} years")
            print(f"   Sex: {patient.get('sex')}")
            print(f"   Attending: {patient.get('attending_oncologist')}")
            
            admission = structured.get('admission_details', {})
            print(f"\n🏥 Admission:")
            print(f"   Diagnosis: {admission.get('diagnosis')}")
            
            vitals = structured.get('clinical_examination', {}).get('vitals', {})
            print(f"\n📊 Vitals:")
            print(f"   Temperature: {vitals.get('temp')}")
            print(f"   Heart Rate: {vitals.get('hr')}")
            print(f"   Blood Pressure: {vitals.get('bp')}")
            
            labs = structured.get('investigations', {}).get('lab_results', [])
            if labs:
                print(f"\n🧪 Lab Results:")
                for lab in labs:
                    print(f"   Date: {lab.get('date')}")
                    if lab.get('hb'): print(f"   Hb: {lab['hb']}")
                    if lab.get('wbc'): print(f"   WBC: {lab['wbc']}")
                    if lab.get('platelet'): print(f"   Platelet: {lab['platelet']}")
            
            meds = structured.get('treatment', {}).get('medications', [])
            if meds:
                print(f"\n💊 Medications:")
                for med in meds:
                    print(f"   • {med.get('name')}")
            
            metadata = structured.get('metadata', {})
            print(f"\n📈 Processing Metadata:")
            print(f"   Model: {metadata.get('processing_model')}")
            print(f"   Confidence: {metadata.get('confidence_score', 0):.1%}")
            
            print(f"\n📄 Discharge Summary Preview:")
            print("-" * 40)
            summary = data.get('report', {}).get('discharge_summary', '')
            print(summary[:500] + "..." if len(summary) > 500 else summary)
            
            # Save full JSON for inspection
            with open('test_report.json', 'w') as f:
                json.dump(structured, f, indent=2)
            print(f"\n💾 Full JSON saved to: test_report.json")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("Make sure the server is running: python app.py")
    print("Then run this test script\n")
    test_schema_with_sample_data()