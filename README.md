# Carpool Matchmaking System - Quick Start Guide

## Backend Setup

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 15 (or Docker)
- Git

### 2. Clone & Setup Backend

```bash
cd carpool-backend
cp .env.example .env
```

Edit `.env`:
```
DATABASE_URL=postgresql://carpool_user:carpool_password@localhost:5432/carpool_db
SECRET_KEY=generate-a-long-random-string-here
```

### 3. Install & Run

**With venv:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**With Docker:**
```bash
docker-compose up
```

Backend runs at: **http://localhost:8000**

### 4. Test Endpoints

```bash
# Health check
curl http://localhost:8000/api/health

# API docs (interactive)
open http://localhost:8000/docs
```

## Frontend Setup

### 1. Install Dependencies

```bash
cd carpool-frontend
npm install
```

### 2. Configure

Create `.env.local`:
```
REACT_APP_API_URL=http://localhost:8000/api
```

### 3. Run Development Server

```bash
npm start
```

Frontend runs at: **http://localhost:3000**

## Database Setup

### Option A: Docker (Recommended)

```bash
docker-compose up postgres
```

### Option B: Manual PostgreSQL

```bash
# Create database
createdb carpool_db

# Apply schema
psql carpool_db < carpool-backend/database/schema.sql

# Enable PostGIS
psql carpool_db -c "CREATE EXTENSION postgis;"
```

## Test the System

### 1. Signup

```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "password": "SecurePass123"
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "email": "user@example.com",
    "message": "Check your email for verification link"
  }
}
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

Save the `access_token` from response.

### 3. Get User Profile

```bash
curl -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Create a Ride

```bash
curl -X POST http://localhost:8000/api/rides \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_address": "IIT Roorkee, Roorkee",
    "destination_address": "Haridwar, India",
    "departure_datetime": "2024-06-15T08:00:00",
    "seats_available": 3,
    "vehicle_type": "car",
    "ride_details": {
      "smoking": "no",
      "music": "quiet",
      "price_per_seat": 100
    }
  }'
```

### 5. Search Rides

```bash
curl -X POST http://localhost:8000/api/rides/search \
  -H "Content-Type: application/json" \
  -d '{
    "source_lat": 29.9,
    "source_lng": 77.9,
    "destination_lat": 29.9,
    "destination_lng": 78.2,
    "departure_date": "2024-06-15",
    "time_window_minutes": 120
  }'
```

## Project Structure

```
c:\Users\singh\Codes\HOSTEL COUNCIL PROJECT\2\
├── carpool-backend/          ← FastAPI backend
│   ├── main.py
│   ├── requirements.txt
│   ├── config.py
│   ├── database/
│   ├── api/
│   ├── services/
│   └── ...
├── carpool-frontend/         ← React frontend
│   ├── package.json
│   ├── src/
│   └── ...
├── docs/                     ← Documentation
├── docker-compose.yml        ← Local dev setup
└── README.md
```

## Common Commands

### Database Migrations (Future)

```bash
# Create migration
alembic revision --autogenerate -m "Add column"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Run Tests

```bash
cd carpool-backend
pytest tests/ -v
```

### Format Code

```bash
# Backend
black carpool-backend/
isort carpool-backend/

# Frontend
npm run format
```

## Troubleshooting

### "Connection refused" to database
- Ensure PostgreSQL is running: `docker-compose up postgres`
- Check DATABASE_URL in .env

### "Module not found" errors
- Install dependencies: `pip install -r requirements.txt`
- Activate venv: `source venv/bin/activate`

### CORS errors in browser
- Check FRONTEND_URL in backend .env
- Ensure backend CORS middleware is configured

### Port already in use
- Backend port 8000: `lsof -i :8000` (kill process)
- Frontend port 3000: `lsof -i :3000`

## Next Steps

1. ✅ **Phase 1 Complete** - Auth, user profiles, ride CRUD
2. 📌 **Phase 2** - Route matching, ML model, recommendations
3. 🔜 **Phase 3** - GenAI integration, NLU ride creation
4. 🚀 **Phase 4** - Trust system, recurring rides, deployment

See [ARCHITECTURE.md](ARCHITECTURE.md) for system design details.

---

**Need help?** Check the documentation in `/docs` or create an issue on GitHub.
