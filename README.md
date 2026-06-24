# Kaaj — Lender Matching Platform

Evaluates business loan applications against multiple equipment finance lenders' credit policies and ranks matches by fit score with per-criterion pass/fail reasoning.

## Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (for PostgreSQL)

### 1. Start PostgreSQL

```bash
docker-compose up -d
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env

python seed_data.py

uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173`.

## Architecture Overview

```
backend/
  app/
    main.py          FastAPI app, CORS, table creation
    database.py      SQLAlchemy engine and session
    models.py        ORM: Lender, LenderProgram, LenderCriterion, LoanApplication, MatchResult
    schemas.py       Pydantic request/response shapes
    routers/
      applications.py  CRUD for loan applications
      lenders.py       CRUD for lenders, programs, and criteria
      underwriting.py  POST /run and GET /results
    services/
      matching.py    Core eligibility engine and fit score calculation

frontend/
  src/
    types/           TypeScript interfaces and shared constants
    api/client.ts    Axios wrappers for all API calls
    pages/           One file per screen
    components/      CriterionRow, ScoreBadge
```

### Data Model

**Lender** owns **LenderPrograms**, each of which owns **LenderCriteria**.

A **LoanApplication** captures all borrower and request details. Running underwriting produces one **MatchResult** per lender, storing eligibility, fit score, matched program, and a JSON snapshot of per-criterion evaluations.

### Matching Engine

For each lender the engine:
1. Filters programs to those applicable for the application (based on PayNet presence, corp-only, industry, etc.)
2. Sorts by priority ascending (priority 1 = best tier, tried first)
3. Evaluates every criterion in the program; stops at the first program where all hard-reject criteria pass
4. If no program passes, records the failure reasons from the best program attempted
5. For eligible matches, computes a fit score (0–100) as a weighted average of per-criterion scores

### Extending the System

**Add a new lender:** Insert rows into the database via the UI or the `/lenders` API. No code change required.

**Add a new criterion type:** Add an `elif` branch in `matching.py`'s `evaluate_criterion()` function and create rows using the new type.

**Add a new applicability type:** Add an `elif` branch in `get_applicable_programs()` in `matching.py`.

## API Documentation

Interactive Swagger UI: `http://localhost:8000/docs`

Key endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | /applications/ | List all applications |
| POST | /applications/ | Create application |
| GET | /applications/{id} | Get application |
| PUT | /applications/{id} | Update application |
| DELETE | /applications/{id} | Delete application |
| GET | /lenders/ | List all lenders |
| POST | /lenders/ | Create lender |
| GET | /lenders/{id} | Get lender with programs and criteria |
| POST | /lenders/{id}/programs | Add program to lender |
| POST | /lenders/{id}/programs/{pid}/criteria | Add criterion to program |
| PUT | /lenders/{id}/programs/{pid}/criteria/{cid} | Update criterion |
| DELETE | /lenders/{id}/programs/{pid}/criteria/{cid} | Delete criterion |
| POST | /underwriting/{id}/run | Run underwriting for an application |
| GET | /underwriting/{id}/results | Retrieve saved results |
