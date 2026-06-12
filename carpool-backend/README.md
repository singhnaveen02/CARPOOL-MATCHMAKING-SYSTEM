# Carpool Matchmaking System - Backend

GenAI-Powered Smart Carpool Matchmaking System Backend API

## Quick Start

### 1. Setup Environment

```bash
cd carpool-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
cp .env.example .env
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup Database

```bash
# Create PostgreSQL database with PostGIS
createdb carpool_db
psql carpool_db < database/schema.sql
```

Or using Docker:

```bash
docker-compose up postgres
```

### 4. Run Development Server

```bash
python main.py
```

Server will start at `http://localhost:8000`

### 5. API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
carpool-backend/
├── main.py                    # FastAPI application entry point
├── config.py                  # Configuration and settings
├── requirements.txt           # Python dependencies
├── database/
│   ├── connection.py         # SQLAlchemy connection setup
│   ├── models.py             # ORM models (User, Ride, Match, etc.)
│   └── schema.sql            # Raw SQL schema (reference)
├── api/
│   ├── schemas.py            # Pydantic request/response models
│   ├── dependencies.py       # JWT auth and DB dependencies
│   └── routes/
│       ├── auth.py           # Auth endpoints (signup, login, verify)
│       ├── users.py          # User profile and preferences
│       ├── rides.py          # Ride CRUD operations
│       ├── matches.py        # Match recommendations
│       └── ratings.py        # Rating system
├── services/
│   ├── auth_service.py       # Authentication logic
│   ├── user_service.py       # User management and trust scoring
│   ├── ride_service.py       # Ride creation and search
│   ├── match_service.py      # Match scoring (Phase 2)
│   ├── maps_service.py       # OpenStreetMap/OSRM integration
│   └── genai_service.py      # Gemini API integration (Phase 3)
├── ml/
│   ├── feature_engineering.py # Feature extraction for ML
│   ├── training.py           # XGBoost model training
│   ├── inference.py          # Model prediction
│   └── models/               # Trained model storage
├── prompts/
│   ├── ride_extraction.py    # LLM extraction prompts
│   └── explanation_generation.py
├── utils/
│   ├── logger.py             # Logging configuration
│   ├── validators.py         # Input validation
│   ├── constants.py          # Constants and enums
│   └── exceptions.py         # Custom exceptions
└── tests/
    ├── test_auth.py
    ├── test_rides.py
    └── test_matches.py
```

## API Endpoints (Phase 1)

### Authentication
- `POST /api/auth/signup` — Register new user
- `POST /api/auth/verify-email` — Verify email
- `POST /api/auth/login` — Authenticate user
- `POST /api/auth/refresh` — Refresh access token

### Users
- `GET /api/users/me` — Get current user profile
- `GET /api/users/{user_id}` — Get user profile
- `PUT /api/users/me` — Update current user
- `GET /api/users/{user_id}/preferences` — Get user preferences
- `PUT /api/users/{user_id}/preferences` — Update preferences
- `GET /api/users/{user_id}/trust-score` — Get trust score

### Rides
- `POST /api/rides` — Create ride
- `GET /api/rides/{ride_id}` — Get ride details
- `GET /api/rides/my-rides` — Get user's rides
- `POST /api/rides/search` — Search rides
- `PUT /api/rides/{ride_id}` — Update ride
- `DELETE /api/rides/{ride_id}` — Cancel ride
- `POST /api/rides/{ride_id}/complete` — Mark as completed

### Matches (Phase 2+)
- `GET /api/matches?ride_id={id}` — Get ride matches
- `POST /api/matches/{match_id}/accept` — Accept match
- `POST /api/matches/{match_id}/reject` — Reject match

### Ratings
- `POST /api/ratings` — Create rating
- `GET /api/ratings/{user_id}/received` — Get ratings received

## Environment Variables

See `.env.example` for all variables:

```
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-api-key
OSRM_API_URL=https://router.project-osrm.org
```

## Development

### Run with Docker

```bash
docker-compose up
```

### Run Tests

```bash
pytest tests/ -v
```

### Format Code

```bash
black .
isort .
```

## Database Migrations (Alembic)

```bash
# Create migration
alembic revision --autogenerate -m "Add user table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Phase 1 Deliverables ✅

- [x] Database schema (PostgreSQL + PostGIS)
- [x] SQLAlchemy ORM models
- [x] Authentication system (JWT)
- [x] User management endpoints
- [x] Ride CRUD endpoints
- [x] Basic ride search
- [x] Rating system
- [x] Trust score calculation
- [x] Logging configuration
- [x] Error handling
- [x] Docker setup

## Phase 2 (Coming Soon)

- [ ] Route matching algorithm
- [ ] Synthetic data generation
- [ ] XGBoost model training
- [ ] Match scoring and recommendation engine
- [ ] Template-based explanation generation

## Phase 3 (Coming Soon)

- [ ] Gemini API integration
- [ ] Natural language ride creation (NLU)
- [ ] GenAI-powered explanations
- [ ] Advanced NLU with clarification

## Contributing

1. Create feature branch: `git checkout -b feature/feature-name`
2. Make changes and test
3. Commit: `git commit -m "Add feature"`
4. Push and create PR

## License

MIT
