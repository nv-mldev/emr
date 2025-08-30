# MediScribe - Medical Documentation Platform (POC)

## Project Structure (Monolithic Approach)

```
mediscribe/
├── app/                      # Single Flask application
│   ├── auth/                # Authentication module
│   ├── upload/              # File upload handling
│   ├── speech/              # Speech processing
│   ├── patients/            # Patient management
│   ├── dashboard/           # Main UI
│   ├── api/                 # REST API endpoints
│   ├── models/              # Database models
│   ├── utils/               # Shared utilities
│   └── templates/           # HTML templates
├── frontend/                # React web application
├── static/                  # CSS, JS, images
├── google-credentials/      # Google Cloud service keys
├── uploads/                 # Temporary file storage
└── config/                  # Configuration files
```

## POC Approach: Monolith First

### Why Monolithic for POC?
- ⚡ **Faster Development**: Single codebase, no service complexity
- 💰 **Lower Costs**: Single server vs multiple containers (~$25/month)
- 🐛 **Easier Debugging**: All code in one place
- 🚀 **Quick Deployment**: One container, simple CI/CD
- 📈 **Rapid Iteration**: Easy to modify based on user feedback

## User Workflow

### **During Patient Visit:**
1. **Doctor Login**: Secure authentication to access the platform
2. **Upload Audio Files**: Direct upload of dictation recordings to object storage
3. **Continue with Patients**: No waiting - files process in background

### **After Visit / End of Day:**
4. **Review Transcriptions**: All processed transcriptions ready for review
5. **Edit & Approve**: Correct any transcription errors, add notes
6. **Patient Management**: Organize transcriptions by patient, view trends
7. **Export/Download**: Download patient summaries for EMR integration

### **Background Processing:**
- Object storage automatically triggers speech-to-text pipeline
- Google Medical API processes audio files asynchronously  
- Completed transcriptions appear in doctor's dashboard
- No timeouts, no waiting, no interruptions to patient care

## Getting Started

### **Prerequisites**
1. Install Docker and Docker Compose
2. Create Google Cloud Project with billing enabled
3. Enable APIs: Cloud Storage, Speech-to-Text, Cloud Functions (for triggers)

### **Google Cloud Setup**
1. Create a service account with permissions:
   - Storage Admin
   - Speech Client
   - Cloud Functions Developer
2. Download service account key as JSON
3. Place the key file in `./google-credentials/service-account-key.json`
4. Create Google Cloud Storage bucket: `mediscribe-audio`

### **Local Development**
1. Copy environment files: `cp services/*/env.example services/*/.env`
2. Update `.env` files with your Google Cloud project details
3. Start services: `docker-compose up -d`
4. Access web portal: `http://localhost:3000`

### **Production Deployment**
- Use Google Cloud Run for microservices
- Google Cloud Storage for file storage
- Google Cloud Functions for event triggers
- Cloud SQL or MongoDB Atlas for database

## Technology Stack (Simplified for POC)

- **Backend**: Single Python Flask application
- **Frontend**: React.js with modern UI components
- **Database**: MongoDB (single database with collections)
- **Object Storage**: Google Cloud Storage for audio files
- **Speech-to-Text**: Google Cloud Medical Speech-to-Text API
- **Authentication**: Flask-Login + JWT for API
- **File Processing**: Background tasks with threading
- **Deployment**: Single Docker container

## Features

- 🔐 Secure doctor authentication
- 📱 Responsive web interface
- 🎤 Direct audio file upload
- 🏥 Medical-grade transcription with 95%+ accuracy
- ⚡ Event-driven background processing (no waiting during patient visits)
- ☁️ Google Cloud Storage with automatic pipeline triggers
- 💰 Cost-effective serverless processing
- 👥 Patient data management
- 📊 Historical transcription views
- 💾 Export functionality for EMR systems
- 🏥 HIPAA-compliant data handling (anonymized for MVP)

# 📋 POC Architecture Specification

## Monolithic Application Overview

### **Application Communication Pattern:**
```
Frontend (React) ↔ Flask Application (Single Process)
                        ↓
            Google Cloud Storage (File Upload)
                        ↓
           Background Threading (Speech Processing)
```

### **Simplified Flow:**
1. **Web Interface**: React frontend communicates with Flask backend
2. **File Upload**: Direct upload to Google Cloud Storage
3. **Background Processing**: Threading for speech-to-text processing
4. **Database**: Single MongoDB with all collections

---

## 🔧 Flask Application Structure

### **1. Authentication Module** (`app/auth/`)
**Responsibility**: Doctor login, session management

**Routes:**
```python
/auth/register          # Doctor registration
/auth/login             # Doctor login
/auth/logout            # Doctor logout
/auth/profile           # Doctor profile management
```

**Features:**
- Flask-Login for session management
- Password hashing with bcrypt
- Simple form-based authentication
- Session persistence

---

### **2. Upload Module** (`app/upload/`)
**Responsibility**: Audio file upload to Google Cloud Storage

**Routes:**
```python
/upload                 # File upload page
/api/upload             # AJAX file upload endpoint
/api/upload-status/:id  # Check upload progress
```

**Workflow:**
1. Validate file format (wav, mp3, m4a)
2. Upload directly to Google Cloud Storage
3. Store file metadata in MongoDB
4. Trigger background speech processing
5. Return upload confirmation

---

### **3. Speech Processing Module** (`app/speech/`)
**Responsibility**: Background speech-to-text processing

**Functions:**
```python
process_audio_file()    # Background thread function
get_transcription()     # Retrieve transcription status
retry_failed()          # Retry failed processing
```

**Processing Pipeline:**
1. Background thread monitors new uploads
2. Download audio from Google Cloud Storage
3. Send to Google Medical Speech-to-Text API
4. Post-process medical terminology
5. Save transcription to MongoDB
6. Update processing status

---

### **4. Patient Management Module** (`app/patients/`)
**Responsibility**: Patient data and transcription organization

**Routes:**
```python
/patients               # Patient list page
/patients/:id           # Patient detail page
/api/patients           # Patient CRUD API
/api/patients/:id/transcriptions  # Patient transcriptions
/api/export/:id         # Export patient data
```

**Features:**
- Simple patient record management
- Link transcriptions to patients
- Basic search and filtering
- Export to PDF/JSON

---

### **5. Dashboard Module** (`app/dashboard/`)
**Responsibility**: Main application interface

**Routes:**
```python
/                       # Main dashboard
/dashboard              # Doctor overview
/transcriptions         # Recent transcriptions
/transcriptions/:id     # Edit transcription
```

**Features:**
- Overview of recent activity
- Quick access to pending transcriptions
- Basic statistics and metrics

---

## 📊 Database Schema Design

### **MongoDB Collections:**

#### **doctors**
```json
{
  "_id": ObjectId,
  "email": "doctor@clinic.com",
  "name": "Dr. Smith", 
  "phone_number": "+1234567890",
  "hashed_password": "bcrypt_hash",
  "is_active": true,
  "created_at": ISODate,
  "last_login": ISODate,
  "settings": {
    "default_patient_type": "outpatient",
    "auto_approve_high_confidence": true
  }
}
```

#### **patients**
```json
{
  "_id": ObjectId,
  "patient_id": "ANON_20241201_143022", 
  "doctor_id": ObjectId,
  "name": "Anonymous Patient",
  "age": 45,
  "gender": "F",
  "created_at": ISODate,
  "last_transcription": ISODate,
  "notes": "Additional patient context",
  "is_active": true
}
```

#### **audio_files**
```json
{
  "_id": ObjectId,
  "doctor_id": ObjectId,
  "original_filename": "dictation_001.wav",
  "gcs_bucket": "mediscribe-audio",
  "gcs_object_name": "doctor123/20241201/audio_abc123.wav",
  "file_size": 2048576,
  "duration_seconds": 120,
  "format": "wav",
  "uploaded_at": ISODate,
  "processing_status": "uploaded|processing|completed|failed"
}
```

#### **transcriptions**
```json
{
  "_id": ObjectId,
  "audio_file_id": ObjectId,
  "doctor_id": ObjectId,
  "patient_id": ObjectId,
  "raw_text": "Patient presents with chest pain...",
  "processed_text": "Patient presents with chest pain. History of present illness: 45-year-old female...",
  "confidence_score": 0.94,
  "word_details": [
    {"word": "Patient", "confidence": 0.99, "start_time": 0.5, "end_time": 0.8}
  ],
  "processing_status": "pending|processing|completed|failed",
  "model_used": "google_medical_dictation",
  "created_at": ISODate,
  "processed_at": ISODate,
  "doctor_approved": false,
  "doctor_notes": "Corrected medication dosage"
}
```

---

## 🔄 Data Flow & Event Architecture

### **Upload & Processing Flow:**
```
1. Doctor uploads audio file
   ↓
2. Upload Service validates file
   ↓
3. File stored in Google Cloud Storage
   ↓
4. Upload Service triggers Speech Service webhook
   ↓
5. Speech Service processes audio asynchronously
   ↓
6. Transcription saved to MongoDB
   ↓
7. Patient Service links transcription to patient
   ↓
8. Frontend polls for completed transcriptions
```

### **Review & Management Flow:**
```
1. Doctor accesses patient dashboard
   ↓
2. Frontend fetches transcriptions from Patient Service
   ↓
3. Doctor reviews/edits transcriptions
   ↓
4. Updates saved to MongoDB
   ↓
5. Doctor generates patient summary
   ↓
6. Summary exported for EMR integration
```

---

## 🚀 POC Deployment Strategy

### **Local Development:**
- Single Flask application
- Local MongoDB or MongoDB Atlas free tier
- Google Cloud Storage for audio files
- Flask development server with hot reload

### **POC Production (Simple & Cost-Effective):**
- **Compute**: Single Google Cloud Run container
- **Database**: MongoDB Atlas free tier (512MB)
- **Storage**: Google Cloud Storage (5GB free tier)
- **Total Cost**: ~$0-25/month for small usage

### **Future Migration to Microservices:**
- **When to migrate**: Multiple practices, >1000 transcriptions/month
- **How**: Extract services gradually (Auth → Upload → Speech → Patient)
- **Benefits**: Independent scaling, team separation, fault isolation

---

## 💰 POC Cost Analysis

### **POC Phase (10-50 hours transcription/month):**
- **Speech API**: $14-72 (10-50 hours × $0.024/min × 60)
- **Cloud Storage**: $0-2 (5GB free tier covers most POC usage)
- **Cloud Run**: $0-10 (free tier covers minimal compute)
- **Database**: $0 (MongoDB Atlas free tier - 512MB)
- **POC Total**: $14-84/month

### **Post-POC Growth:**
#### **Small Practice (100+ hours/month):**
- Speech API: $144/month
- Infrastructure: $25-50/month
- **Total: ~$169-194/month**

### **Cost Comparison:**
- **Traditional Solution**: $500-2000/month (transcription service)
- **Our POC**: $14-84/month (90%+ cost savings)

---

## 🔒 Security & Compliance

### **Security Measures:**
- JWT-based authentication
- HTTPS/TLS encryption
- Rate limiting and DDoS protection
- Input validation and sanitization
- Secure file upload validation
- Audit logging

### **HIPAA Compliance Roadmap:**
- Sign Google Cloud BAA
- Implement audit logging
- Add customer-managed encryption keys
- Data retention policies
- Access control reviews
- Security monitoring

---

## 🧪 Testing Strategy

### **Unit Tests:**
- Individual service logic testing
- Database operations testing
- Google Cloud API integration testing

### **Integration Tests:**
- Service-to-service communication
- End-to-end workflow testing
- Error handling scenarios

### **Load Tests:**
- Concurrent file uploads
- Speech processing throughput
- Database performance

---

---

## 🎯 POC Feature Priorities

### **Phase 1: Core POC (2-3 weeks)**
#### **Must-Have Features:**
1. **Doctor Registration/Login** (simple form-based)
2. **File Upload Interface** (drag & drop, basic validation)
3. **Google Cloud Storage Integration** (direct upload)
4. **Speech-to-Text Processing** (Google Medical API)
5. **Transcription Review** (display, basic editing)
6. **Simple Patient Linking** (dropdown selection)

#### **Success Criteria:**
- Doctor can upload audio file
- Receives accurate medical transcription
- Can review and edit result
- Can associate with patient
- Takes <5 minutes end-to-end

### **Phase 2: POC Enhancement (1-2 weeks)**
#### **Nice-to-Have Features:**
1. **Patient Management** (add/edit patients)
2. **Transcription History** (list view with search)
3. **Export Functionality** (PDF, text download)
4. **Basic Dashboard** (recent activity, stats)
5. **Error Handling** (failed uploads, retry logic)

### **Phase 3: User Feedback & Iteration (ongoing)**
- Deploy to staging environment
- Get doctor feedback
- Iterate on UI/UX
- Performance optimization
- Prepare for scaling

---

## 🏗️ Development Timeline

### **Week 1: Foundation**
- Flask app structure setup
- MongoDB models and schemas
- Google Cloud Storage integration
- Basic authentication (login/register)

### **Week 2: Core Features**
- File upload functionality
- Speech-to-text processing (background threading)
- Transcription display and editing
- Basic patient management

### **Week 3: Polish & Deploy**
- Error handling and user feedback
- UI/UX improvements
- Testing and bug fixes
- Deploy to staging environment

### **Week 4+: Feedback & Scale**
- Doctor user testing
- Performance optimization
- Feature enhancements based on feedback
- Prepare microservices migration plan

---

## ✅ POC Success Metrics

### **Technical Metrics:**
- 95%+ speech recognition accuracy
- <30 seconds processing time per minute of audio
- <2 seconds page load times
- 99%+ uptime during testing

### **User Experience Metrics:**
- Doctor can complete workflow in <5 minutes
- Requires minimal training (<30 minutes)
- Positive feedback on transcription quality
- Willingness to pay for the service

### **Business Validation:**
- At least 3 doctors complete full workflow
- Demonstrate 90%+ cost savings vs traditional services
- Identify clear value proposition
- Validate medical workflow assumptions

This POC approach provides a clear path to validate MediScribe's medical documentation platform quickly and cost-effectively before committing to a full microservices architecture.

## 🏥 About MediScribe

**MediScribe** is an intelligent medical documentation platform that transforms voice dictations into accurate, structured medical records using advanced AI speech recognition.

### **Mission**: 
Reduce administrative burden on healthcare providers by enabling fast, accurate voice-to-text medical documentation.

### **Vision**: 
Make medical documentation as simple as having a conversation, so doctors can focus on patient care.

### **Target Users**:
- Pediatric practices (initial focus)
- Family medicine doctors  
- Medical specialists
- Healthcare clinics and hospitals

## Google Medical Speech-to-Text API Features

Our speech service leverages Google's specialized medical transcription model for superior accuracy in healthcare environments:

### **Medical-Specific Capabilities:**
- 🎯 **Medical Dictation Model**: Trained specifically on healthcare terminology
- 📚 **Medical Vocabulary**: Pre-loaded with drug names, procedures, anatomical terms
- 🔍 **Enhanced Recognition**: 20x boost for medical terminology vs generic models
- 👥 **Speaker Diarization**: Distinguishes between doctor and patient voices
- ⚡ **Real-time Processing**: Fast transcription for immediate clinical use

### **Clinical Accuracy Features:**
- 📝 **Automatic Punctuation**: Proper formatting for medical reports
- 🩺 **Medical Abbreviations**: Intelligent expansion (e.g., "bp" → "blood pressure")
- 💊 **Dosage Recognition**: Accurate transcription of medication dosages
- 📋 **Report Sections**: Recognizes standard medical report structure
- 🔢 **Word-level Confidence**: Detailed accuracy scores for quality assurance

### **Compliance & Security:**
- ✅ **HIPAA Compliant**: Google Cloud Healthcare APIs meet healthcare standards
- 🔒 **Secure Processing**: End-to-end encryption for PHI protection
- 📊 **Audit Logging**: Complete transcription audit trails
- 🏥 **Healthcare Optimized**: Configured for physician office environments