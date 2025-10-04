# Lead Management System

Lead management system for law firms with automated emailing, file handling, and role-based access control.  

Note: A lead is a form **PUBLICLY** available for prospects to fill in, the required fields include:

- First name
- Last name
- Email
- Resume / CV
---
## Requirements

### Functional Requirements
- Support creation/ retrieval/ update leads (including file-based)
- Support auto-emailing to attorney and the lead when a new lead is submitted
- Support attorney to manually update the status of a lead (from PENDING to REACHED_OUT)
- Support retrieval for a list of leads (guarded by authorization)

### Technical Requirements
- Must leverage FastAPI and related libraries
- Storage for data persistence
---
## Entity Modeling

- **Lead**: Represents a prospect who submits information through the public lead form. Stores personal details, resume path, and lead status.  
- **User**: Represents system users (e.g., attorneys, clients, admins) with role-based access control for managing leads and system operations.  

<p align="center">
  <img width="2090" height="776" alt="image" src="https://github.com/user-attachments/assets/d3b1e5ea-bf11-4344-b068-2a6087008e7c" />
  <br/>
  <em>Figure: Entity Relationship Diagram (ERD) for Lead and User entities</em>
</p>

---  

## Architecture and Technologies

- **Technologies**

  - **Backend**: FastAPI, Apache Kafka, SQLAlchemy, Pydantic, Alembic, JWT  
  - **Storage**: PostgreSQL, MinIO Bucket
  - **Containerization**: Docker
 
### Considerations
- **Lead notifications**: When a new lead is created, emails must be sent to the attorney and the lead. Two design approaches:  
  1. **Synchronous service-to-service call**  
     - Directly call the Notification Service during lead creation.  
     - **Pros**: Simple to implement.  
     - **Cons**: Tightly coupled; high traffic can slow API responses or cause failures; scaling email delivery requires scaling the Lead Service.  

  2. **Publish/Subscribe (Pub/Sub) system**  
     - Lead Service publishes a `lead.created` event to a broker (e.g., Kafka); Notification Service consumes events asynchronously.  
     - **Pros**: Decouples lead creation and email delivery, handles high traffic, supports retries, and can be extended for other workflows.  
     - **Cons**: Slightly more complex to implement and monitor.  

  - Since the lead form is **public**, traffic can spike unpredictably (e.g., 10–50 leads/sec during campaigns or news events).  
  - **Decision**: Pub/Sub is preferred for better scalability, reliability, and maintainability.

 <p align="center">
  <img width="5588" height="1331" alt="image" src="https://github.com/user-attachments/assets/c545aed7-e3b0-4648-9429-83d514ae0d9b" />
  <br/>
  <em>Figure: System architecture/ workflow for sending emails upon new lead creation</em>
</p>

- **Storage**:  
  - **SQL**: PostgreSQL for structured data and time-series support.  
  - **Object storage**: MinIO bucket (lightweight, S3-compatible) for resumes and files.
 
 <p align="center">
  <img width="1300" height="700" alt="image" src="https://github.com/user-attachments/assets/a120fffb-d7f4-439e-a932-0d9a24774142" />
  <br/>
  <em>Figure: Storage architecture supporting file-based</em>
</p>

---

## Repository Structure & Local Setup

The following outline the current structure of our monorepo:
```text
alma/
├── alma-infra/                    # Infrastructure & orchestration
├── leads-service/                 # Core lead management microservice
└── notifications-service/         # Email notification microservice
```

### Pre-requisites  
Before setting up  locally, ensure the following are installed and available :

- **Docker & Docker Compose**  
  - [Install Docker](https://docs.docker.com/get-docker/)  
- **Python 3.10+**  
  - [Install Python](https://www.python.org/downloads/)  
- **Virtual Environment Tools**  
  - `venv` module (comes with Python) to create isolated Python environments.  
- **Git**  
  - [Install Git](https://git-scm.com/downloads)  
- **Optional: Docker Desktop**  
  - Provides a GUI to monitor running containers and volumes.  
> Ensure Docker daemon is running before executing the setup steps below.

### Local Setup

#### CRUCIAL: Create .env files for each directory
#### 1. Sample .env for alma-infra
```
# PostgreSQL
POSTGRES_PASSWORD=alma_password
POSTGRES_DB=alma
POSTGRES_USER=postgres

# MinIO
MINIO_ROOT_USER=alma_access_key
MINIO_ROOT_PASSWORD=alma_secret_key

# Kafka
KAFKA_VERSION=7.5.0
KAFKA_BROKER_ID=1
KAFKA_EXTERNAL_PORT=9092
KAFKA_INTERNAL_PORT=29092
KAFKA_REPLICATION_FACTOR=1
KAFKA_AUTO_CREATE_TOPICS=true
KAFKA_CLUSTER_NAME=alma-local

# Zookeeper
ZOOKEEPER_CLIENT_PORT=2181
ZOOKEEPER_TICK_TIME=2000

# Kafka UI
KAFKA_UI_VERSION=latest
KAFKA_UI_PORT=8080

```

#### 2. Sample .env for leads-service  
**Note**: need to generate secret key first (for password encryption)
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

```
# Database - use Docker service names
POSTGRES_SERVER=alma-postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=alma_password
POSTGRES_DB=alma
POSTGRES_PORT=5432

# MinIO/S3 - use Docker service names
MINIO_URL=http://localhost:9001
MINIO_ENDPOINT=alma-minio:9000
MINIO_ACCESS_KEY=alma_access_key
MINIO_SECRET_KEY=alma_secret_key
MINIO_BUCKET_NAME=leads

# Kafka
KAFKA_BOOTSTRAP_SERVERS=alma-kafka:29092
KAFKA_NEW_LEADS_TOPIC=new_leads

# JWT Security
SECRET_KEY=your-secret-key

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

#### 3. Sample .env for notifications-service  
**Note**: Need to generate app mail password for the configured SMTP user (see this guide: [YouTube - How to Generate App Password for Gmail SMTP](https://www.youtube.com/watch?v=GsXyF5Zb5UY)) 
```
# PostgreSQL
POSTGRES_SERVER=alma-postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=alma_password
POSTGRES_DB=alma
POSTGRES_PORT=5432

#Kafka
KAFKA_BOOTSTRAP_SERVERS=alma-kafka:29092
KAFKA_NEW_LEADS_TOPIC=new_leads
KAFKA_CONSUMER_GROUP=notification-workers

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alma-sender-email-here@gmail.com
SMTP_PASSWORD=alma-sender-mail-app-password
FROM_EMAIL=notifications@alma.com
ATTORNEY_EMAIL=alma-attorney-email-here@gmail.com
```


#### 1. Create infrastructure resources
```bash
cd alma-infra
docker compose up -d
```

#### 2. Run DDL Migrations and Start Leads Service
```bash
cd leads-service

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
alembic upgrade head

# Start leads service
docker compose up --build
```

#### 3. Start Notifications Service
```bash
cd notifications-service
docker compose up --build
```
Once successfully set up, all containerized resources should be running as below:

 <p align="center">
  <img width="1443" height="570" alt="Screenshot 2025-10-04 at 3 51 19 PM" src="https://github.com/user-attachments/assets/12038400-17cd-44ef-9a21-7d9026984d45" />
  <br/>
  <em>Figure: Local Setup (Docker Desktop)</em>
</p>

---

## API Documentation

- Once system is up and running -- all APIs are available on Swagger: http://localhost:8000/docs
- **Postman Collection Available For Download**: https://drive.google.com/file/d/1swOgKQSOmpV7ysMlKbLo5BnsQo_DYvev/view?usp=sharing


<p align="center">
  <img width="1167" height="477" alt="Screenshot 2025-10-04 at 4 36 00 PM" src="https://github.com/user-attachments/assets/5e2ff8ee-4ff0-4058-8c01-1ecb6ae4216a" />
  <br/>
  <em>Figure: Collection of APIs available</em>
</p>

---

## Testing
```bash
cd leads-service

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
```

---

## Demo

Video: https://us06web.zoom.us/rec/share/cg91zBDI_VBBmwY5ROiLRs4QWoXONcLm1-26y-QITtHHkYxg6LDkJsC_EC5OZq_h.GeWa7T8Uq94TxbSF  
Passcode: 2X3VIMF*

---

## Future work
Due to limited time, below topics were considered but not yet implemented :(
- Retry logic for Pub/Sub
- System-wide observability
- More unit tests/ integration tests

