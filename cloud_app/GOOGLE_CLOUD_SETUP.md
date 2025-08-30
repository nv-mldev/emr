# Google Cloud Platform Setup Guide

This guide will help you set up Google Cloud Platform services for MediScribe - Medical Documentation Platform.

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `mediscribe-platform` (recommended new name)
4. Enable billing for the project

## Step 2: Enable Required APIs

Enable the following APIs in your project:

```bash
# Using gcloud CLI (recommended)
gcloud services enable storage.googleapis.com
gcloud services enable speech.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable pubsub.googleapis.com
```

Or enable via Console:
- [Cloud Storage API](https://console.cloud.google.com/apis/library/storage.googleapis.com)
- [Cloud Speech-to-Text API](https://console.cloud.google.com/apis/library/speech.googleapis.com)
- [Cloud Functions API](https://console.cloud.google.com/apis/library/cloudfunctions.googleapis.com)

## Step 3: Create Service Account

1. Go to [IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click "Create Service Account"
3. Name: `mediscribe-service`
4. Description: `Service account for MediScribe medical documentation platform`

### Assign Roles:
- **Storage Admin**: Full access to Google Cloud Storage
- **Speech Client**: Access to Speech-to-Text API
- **Cloud Functions Developer**: Deploy event triggers
- **Pub/Sub Admin**: For event messaging

## Step 4: Generate Service Account Key

1. Click on your service account
2. Go to "Keys" tab
3. Click "Add Key" → "Create New Key"
4. Select "JSON" format
5. Download the key file
6. Save as `./google-credentials/service-account-key.json` in your project

## Step 5: Create Cloud Storage Bucket

```bash
# Using gcloud CLI
gsutil mb gs://mediscribe-audio

# Set uniform bucket-level access
gsutil uniformbucketlevelaccess set on gs://mediscribe-audio
```

Or via Console:
1. Go to [Cloud Storage](https://console.cloud.google.com/storage)
2. Click "Create Bucket"
3. Name: `mediscribe-audio`
4. Location: Choose region closest to your users
5. Storage class: Standard
6. Access control: Uniform

## Step 6: Set Up Event Triggers (Optional for MVP)

For production, set up Cloud Functions to trigger speech processing:

```bash
# This will be implemented in the speech service
gcloud functions deploy mediscribe-process-audio \
    --runtime python311 \
    --trigger-bucket mediscribe-audio \
    --entry-point process_audio \
    --memory 1024MB \
    --timeout 540s
```

## Step 7: Configure Environment Variables

Update your `.env` files:

```env
# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json
GCS_BUCKET_NAME=mediscribe-audio
GOOGLE_CLOUD_PROJECT=mediscribe-platform
```

## Cost Estimates (US pricing)

### Speech-to-Text API:
- **Medical Model**: $0.024 per minute
- Example: 100 hours/month = $144/month

### Cloud Storage:
- **Storage**: $0.020 per GB/month
- **Operations**: $0.004 per 1000 operations
- Example: 100GB + 10K operations = $2.04/month

### Cloud Functions (for triggers):
- **Invocations**: First 2M free, then $0.40 per 1M
- **Compute**: $0.0000025 per GB-second
- Minimal cost for event triggers

### Total Estimated Cost:
- **Small practice** (50 hours/month): ~$75/month
- **Medium practice** (200 hours/month): ~$300/month
- **Large practice** (500 hours/month): ~$750/month

## Security Best Practices

1. **Service Account**: Use minimal required permissions
2. **Bucket Access**: Enable uniform bucket-level access
3. **Network**: Use VPC for production deployments
4. **Encryption**: Enable customer-managed encryption keys (CMEK) for PHI
5. **Audit Logging**: Enable Cloud Audit Logs
6. **Data Retention**: Set up lifecycle policies for old audio files

## HIPAA Compliance

For production medical deployments:

1. **Sign BAA**: Sign Business Associate Agreement with Google Cloud
2. **Enable Audit Logs**: For all API calls
3. **Data Location**: Ensure data stays in appropriate regions
4. **Access Controls**: Implement IAM policies
5. **Encryption**: Use CMEK for sensitive data
6. **Network Security**: Use Private Google Access

## Troubleshooting

### Common Issues:

1. **Authentication Error**:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
   ```

2. **Permission Denied**:
   - Check service account has required roles
   - Verify API is enabled

3. **Bucket Not Found**:
   - Ensure bucket name is globally unique
   - Check bucket exists in correct project

### Test Setup:

```bash
# Test authentication
gcloud auth activate-service-account --key-file=service-account-key.json

# Test storage access
gsutil ls gs://mediscribe-audio

# Test speech API
curl -X POST \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "Content-Type: application/json" \
     "https://speech.googleapis.com/v1/speech:recognize"
```

This setup provides a scalable, HIPAA-compliant foundation for the MediScribe medical documentation platform.