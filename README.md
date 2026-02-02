# Deal Brief Pipeline

LLM-powered deal text extraction pipeline with real-time status updates.

## Features

- **Text Extraction**: Submit unstructured deal text (pitch emails, memos) and extract structured data using GPT-4o
- **Real-time Updates**: WebSocket-based status updates as extraction progresses
- **Deduplication**: SHA-256 hash-based duplicate detection (returns 409 Conflict)
- **Validation & Retry**: Pydantic validation with LLM repair prompt fallback
- **Modern UI**: React frontend with list/detail views

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python / FastAPI |
| Frontend | React / Vite / TypeScript |
| Database | SQLite |
| LLM | OpenAI GPT-4o |
| Real-time | WebSocket |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key

### Running Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/Ziadabdelsalam/deal-brief.git
   cd deal-brief
   ```

2. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your-api-key-here
   ```

3. Start all services:
   ```bash
   docker compose up
   ```

4. Open the UI at http://localhost:3000

### Running Without Docker

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/deals` | Submit new deal text |
| GET | `/api/deals` | List latest 10 deals |
| GET | `/api/deals/{id}` | Get deal detail |
| WS | `/ws/deals/{id}` | Subscribe to status updates |

## Status Flow

```
pending → extracting → validating → completed
              ↓            ↓
            failed       failed
```

## Extracted Fields

| Field | Description |
|-------|-------------|
| company_name | Company name |
| founders | List of founder names |
| sector | Industry sector |
| geography | Geographic focus |
| stage | Funding stage (Seed, Series A, etc.) |
| round_size | Funding amount |
| metrics | Key metrics (ARR, growth, users, etc.) |
| investment_brief | 5-10 bullet point summary |
| tags | Categorization tags |

## Running Tests

```bash
cd backend
pytest tests/ -v
```

## Design Decisions

- **Hash-based Dedupe**: SHA-256 of normalized text returns 409 Conflict for duplicates
- **Input Limit**: 10KB (~2,500 words) to manage LLM costs
- **Retry Logic**: Max 2 attempts with repair prompt on validation failure
- **Async Processing**: Background task with WebSocket updates for UX

---

## AWS Deployment

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│     ALB     │────▶│ ECS Fargate │────▶│     RDS     │
│ (WebSocket) │     │  (Backend)  │     │ (PostgreSQL)│
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Secrets   │
                    │   Manager   │
                    └─────────────┘
```

### Components

| Component | AWS Service | Justification |
|-----------|-------------|---------------|
| API Hosting | ECS Fargate | Containerized, auto-scaling, pay-per-use |
| Database | RDS PostgreSQL | Managed backups, replicas, easy SQLite migration |
| Load Balancer | ALB | Native WebSocket support, SSL termination |
| Secrets | Secrets Manager | API key rotation, IAM integration, audit trail |
| Observability | CloudWatch + X-Ray | Logs, metrics, distributed tracing |

### Estimated Costs (small scale)

- ECS Fargate: ~$30/month (0.5 vCPU, 1GB)
- RDS PostgreSQL: ~$15/month (db.t3.micro)
- ALB: ~$20/month
- **Total: ~$65/month**
