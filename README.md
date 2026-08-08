# 🏥 PACS DICOM Router Gateway (Cloud Edition)

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)
![AWS S3](https://img.shields.io/badge/AWS-S3-FF9900)
![License](https://img.shields.io/badge/license-MIT-green)

An enterprise-grade, lightweight DICOM routing gateway built with FastAPI. Designed for modern HealthTech architectures, this microservice intercepts DICOM files, strictly enforces GDPR-compliant PHI (Protected Health Information) redaction in-memory, and securely streams the sanitized data directly to AWS S3 based on imaging modalities.

## ✨ Enterprise-Grade Features

* **🛡️ GDPR-Compliant Pseudonymization**: 
  Implements strict PHI redaction before data leaves the memory buffer. `PatientName` and `DOB` are erased, while `PatientID` is pseudonymized using one-way SHA-256 hashing to maintain longitudinal data traceability without compromising patient identity.
* **☁️ Cloud-Native S3 Integration**: 
  Stateless architecture utilizing `io.BytesIO` for in-memory stream processing. DICOM payloads are piped directly to AWS S3 (`boto3`) without temporary local disk storage, maximizing I/O throughput and security.
* **📊 Observability & Audit Trails**: 
  Comprehensive structured JSON logging via `loguru`. Every upload, redaction event, and S3 transfer is meticulously logged with contextual metadata (IP, Modality, File Size, Hashed ID) for seamless integration with Datadog or AWS CloudWatch.
* **🤖 Automated CI/CD Pipeline**: 
  Fully tested using `pytest`. The CI pipeline runs on GitHub Actions, utilizing `unittest.mock` to simulate AWS S3 interactions, ensuring code reliability and preventing regression before deployment.

## 🛠️ Tech Stack

* **Core**: Python 3.10+, FastAPI, Uvicorn
* **Medical Imaging**: `pydicom`
* **Cloud Infrastructure**: AWS SDK (`boto3`)
* **DevOps & Testing**: `pytest`, GitHub Actions, `loguru`

## 🚀 Getting Started

### 1. Prerequisites
Create an IAM User in AWS with `AmazonS3FullAccess` (or a restricted custom policy) and generate Access Keys. 
Create a `.env` file in the root directory (this file is git-ignored for security):

```ini
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=eu-north-1
S3_BUCKET_NAME=your-s3-bucket-name
```

### 2. Installation
Clone the repository and install the dependencies in a virtual environment:
```Bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the Gateway
Start the Uvicorn server:
```Bash
uvicorn main:app --reload --port 8000
```
Access the interactive Swagger API documentation at: http://127.0.0.1:8000/docs

### 📡 API Usage
POST /api/router/upload
Uploads a .dcm file, performs in-memory PHI redaction, and routes it to the corresponding Modality folder in AWS S3.
Request:
Content-Type: multipart/form-data
file: The DICOM file payload.
Success Response (200 OK):
```JSON
{
  "message": "DICOM file sanitized and securely routed to Cloud",
  "modality": "CT",
  "sanitized_patient_id": "8d969eef6ecad3c2",
  "cloud_location": "s3://your-s3-bucket-name/CT/scan_001.dcm",
  "filename": "scan_001.dcm"
}
```

### 🧪 Testing
The project uses pytest with extensive mocking for cloud services to ensure tests run fast and isolated from actual network I/O.
```Bash
pytest -v
```


# 🏥 DICOM Router Gateway

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)
![Healthcare IT](https://img.shields.io/badge/Domain-Healthcare_IT-e34c26.svg)

## 📌 Overview
**DICOM Router** is a lightweight, production-ready backend microservice designed for automated medical imaging data ingestion and distribution. 

In a clinical environment, hospitals generate massive volumes of DICOM files across various modalities (CT, MRI, X-Ray). This gateway acts as a smart ingress node: it securely receives raw DICOM files via a RESTful API, parses the internal metadata using `pydicom`, and dynamically routes the files into categorized storage based on their imaging `Modality`. 

This project bridges the gap between raw clinical data and downstream AI pipelines, demonstrating a strong focus on **Healthcare IT standards**, **API design**, and **Cloud-native architecture**.

## 🚀 Key Features
*   **Automated Modality Routing**: Extracts DICOM tags (e.g., `(0008, 0060) Modality`) and automatically archives scans into isolated directories (e.g., `/data/CT/`, `/data/MR/`).
*   **High-Performance REST API**: Built with **FastAPI** for asynchronous handling, robust data validation, and self-documenting endpoints (OpenAPI/Swagger).
*   **Data Integrity & Validation**: Rejects invalid file formats and ensures only structurally sound DICOM files enter the storage pipeline.
*   **Containerized Environment**: Fully containerized using **Docker**, ensuring isolated and reproducible deployments across any cloud or local environment.
*   **Quality Mindset**: Test coverage implemented via `pytest` to guarantee routing reliability and error handling.

## 🏗️ Architecture & Workflow

```mermaid
graph LR
    %% 客户端层
    subgraph Hospital Network
        CT[📸 CT Scanner] -->|POST .dcm| Gateway
        MRI[🩻 MRI Scanner] -->|POST .dcm| Gateway
    end

    %% 核心网关层 (Stateless & In-Memory)
    subgraph DICOM Router Gateway (Stateless)
        Gateway{⚙️ FastAPI Router}
        MemoryBuf[🧠 In-Memory Buffer]
        DeID[🛡️ GDPR Redaction & Hash]
        Logger[📝 Structured Audit Log]
        
        Gateway -->|Load Bytes| MemoryBuf
        MemoryBuf -->|Sanitize PHI| DeID
        DeID -.->|Record Event| Logger
    end

    %% 云端存储层
    subgraph Cloud Infrastructure
        DeID -->|boto3 Stream| AWS[(☁️ AWS S3 Vault)]
    end

    %% 自定义样式
    classDef core fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef cloud fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    class Gateway,MemoryBuf,DeID core;
    class AWS cloud;
```

1.  **Ingress**: A client (e.g., a simulated PACS node) POSTs a .dcm file to /api/router/upload.
2.  **In-Memory Processing**: To ensure maximum I/O throughput and security, the FastAPI router reads the file directly into a memory buffer (io.BytesIO). No sensitive data is ever written to the local disk.
3.  **GDPR Sanitization**: The de-identification pipeline intercepts the dataset, strips direct identifiers (e.g., PatientName, DOB), and pseudonymizes the PatientID using a cryptographic SHA-256 hash.
4.  **Cloud Routing & Audit**: The sanitized dataset is streamed directly to an AWS S3 bucket, organized automatically by its Modality tag (e.g., /CT/...), while a structured JSON audit log is generated via loguru for observability.

## 💻 Getting Started

### Prerequisites
*   Docker & Docker Compose (Recommended)
*   *Or* Python 3.10+ (for local development)

### Option A: Run with Docker (Production-like)
```bash
# 1. Build the Docker image
docker build -t dicom-router-gateway .

# 2. Run the container (maps local port 8000 and data volume)
docker run -p 8000:8000 -v $(pwd)/data:/app/data dicom-router-gateway
```

### Option B: Local Development Setup
```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the FastAPI server
uvicorn main:app --reload
```
## 📖 API Documentation
Once the server is running, the interactive Swagger UI is automatically available at:
👉 http://localhost:8000/docs
<img src="./docs/swagger.png" width="400" alt="DICOM Router UI">
<img src="./docs/swagger2.png" width="400" alt="DICOM Router UI">

## Example API Request (cURL)
```bash
curl -X 'POST' \
  'http://localhost:8000/api/router/upload' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@dummy_scan.dcm;type=application/dicom'
```

## 🛣️ Future Roadmap (Next Steps)
To further align with enterprise HealthTech standards, the following features are planned:
- [ ] **AWS S3 Integration:** Replace local disk storage with AWS S3 buckets utilizing `boto3` for scalable cloud archiving.
- [x] **De-identification Pipeline:** Implement automated PHI (Protected Health Information) stripping to ensure strict GDPR compliance before routing. *(Completed)*
- [x] **CI/CD Pipeline & Containerization:** Set up GitHub Actions for automated testing, pytest execution, and Docker image management. *(Completed)*
- [x] **Observability:** Integrate structured logging and basic metrics tracking.
---
**Designed and engineered by Weijia Li**