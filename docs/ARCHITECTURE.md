# Carpool Matchmaking System - Architecture

## System Overview

GenAI-Powered Smart Carpool Matchmaking System is a full-stack application that matches drivers and passengers traveling on similar routes at similar times using ML and GenAI technologies.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Layer                                 │
│  ┌────────────────────┐  ┌────────────────────┐  ┌──────────────┐  │
│  │   React Frontend   │  │   Mobile App       │  │   Web UI     │  │
│  │  (Tailwind CSS)    │  │   (Future)         │  │              │  │
│  └────────────────────┘  └────────────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                                    ↓ REST API
┌──────────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                               │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │              FastAPI + Uvicorn                                 │  │
│  │  - JWT Authentication  - CORS  - Rate Limiting                │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    Application Layer                                 │
│  ┌──────────────────┐ ┌──────────────────┐ ┌────────────────────┐   │
│  │ Auth Service     │ │ User Service     │ │ Ride Service       │   │
│  │ - Signup         │ │ - Profile Mgmt   │ │ - CRUD Operations  │   │
│  │ - JWT tokens     │ │ - Trust Scoring  │ │ - Validation       │   │
│  │ - Email verify   │ │ - Preferences    │ │ - Geocoding        │   │
│  └──────────────────┘ └──────────────────┘ └────────────────────┘   │
│  ┌──────────────────┐ ┌──────────────────┐ ┌────────────────────┐   │
│  │ Match Service    │ │ ML Service       │ │ GenAI Service      │   │
│  │ - Route overlap  │ │ - XGBoost model  │ │ - Gemini API       │   │
│  │ - Time compat    │ │ - Feature eng.   │ │ - NLU extraction   │   │
│  │ - Preference     │ │ - Inference      │ │ - Explanations     │   │
│  └──────────────────┘ └──────────────────┘ └────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Maps Service (OpenStreetMap + OSRM)                          │   │
│  │ - Geocoding (Nominatim)  - Route polylines  - Distance calc  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│                      Data Layer                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL (PostGIS) + Alembic Migrations                     │  │
│  │  - Users, Rides, Matches, Ratings, Notifications              │  │
│  │  - Spatial indexing for route queries                          │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
User Registration/Login
  │
  ├─→ Email verification
  ├─→ JWT token generation
  └─→ User preferences stored

Ride Creation
  │
  ├─→ Address input
  ├─→ Geocoding (Nominatim)
  ├─→ Route fetching (OSRM)
  ├─→ Polyline storage
  └─→ Ride details saved in DB

Ride Search
  │
  ├─→ Source/destination coordinates
  ├─→ Search rides on date
  ├─→ Filter by seats available
  └─→ Return matching rides

Match Generation (Phase 2+)
  │
  ├─→ Get all candidate rides
  ├─→ Calculate route overlap
  ├─→ Calculate time compatibility
  ├─→ Extract ML features
  ├─→ XGBoost prediction
  ├─→ Score normalization
  ├─→ Generate explanation (GenAI)
  └─→ Return ranked matches

Rating & Trust Update
  │
  ├─→ User rates ride/partner
  ├─→ Calculate average rating
  ├─→ Recalculate trust score
  ├─→ Update user profile
  └─→ Notify participants
```

## Database Schema

### Core Tables

**Users**
- id (PK), email, name, phone, password_hash
- institute_email, email_verified, profile_picture_url
- created_at, updated_at, last_login, is_active

**Rides**
- id (PK), user_id (FK), source_lat, source_lng
- destination_lat, destination_lng, departure_datetime
- seats_available, vehicle_type, polyline
- route_distance_km, route_duration_minutes
- status (active/completed/cancelled)
- is_recurring_series, recurrence_pattern

**Matches**
- id (PK), driver_id (FK), rider_id (FK), ride_id (FK)
- match_score, route_overlap_percent, time_compatibility
- preference_compatibility, explanation
- status (pending/accepted/rejected/completed)
- accepted_at, completed_at

**Ratings**
- id (PK), from_user_id (FK), to_user_id (FK), ride_id (FK)
- score (1-5), punctuality_rating, cleanliness_rating
- behavior_rating, comment, created_at

**Supporting Tables**
- UserPreferences (smoking, gender, music, luggage, AC)
- UserTrustScores (trust_score, average_rating, total_rides)
- RideDetails (preferences for specific rides)
- RideOccurrences (for recurring rides)
- Notifications (match found, accepted, completed, etc.)

## API Design

### REST Convention

**Resource**: Rides
- `POST /api/rides` - Create
- `GET /api/rides/{id}` - Read
- `PUT /api/rides/{id}` - Update
- `DELETE /api/rides/{id}` - Delete (cancel)
- `GET /api/rides/search` - Search

**Response Format**
```json
{
  "success": true,
  "data": { /* resource data */ },
  "error": null
}
```

### Authentication

- **Type**: JWT (Bearer token)
- **Payload**: `{"sub": user_id, "exp": expiry_time}`
- **Headers**: `Authorization: Bearer <token>`

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Local Development                                      │
│  docker-compose up (backend, frontend, postgres)       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Production (AWS/Render)                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Frontend (S3 + CloudFront / Vercel)            │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Backend (EC2 / ECS / Render)                   │   │
│  │  - Nginx reverse proxy                          │   │
│  │  - Uvicorn ASGI servers (multiple)              │   │
│  │  - Auto-scaling groups                          │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Database (RDS PostgreSQL + PostGIS)            │   │
│  │  - Automated backups                            │   │
│  │  - Read replicas for scaling                    │   │
│  │  - Multi-AZ deployment                          │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Services                                       │   │
│  │  - OpenStreetMap / OSRM API                     │   │
│  │  - Gemini API (GenAI)                           │   │
│  │  - SendGrid (Email notifications)               │   │
│  │  - Redis (Caching, rate limiting)               │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 18 + Tailwind CSS | User interface |
| Backend | FastAPI + Uvicorn | REST API |
| Database | PostgreSQL + PostGIS | Data storage & spatial queries |
| Authentication | JWT (python-jose) | Session management |
| Password Hashing | bcrypt (passlib) | Secure password storage |
| ORM | SQLAlchemy | Database abstraction |
| ML | XGBoost + scikit-learn | Match prediction |
| GenAI | Gemini API + LangChain | NLU & explanations |
| Maps | OpenStreetMap + OSRM | Geocoding & routing |
| Containerization | Docker + Docker Compose | Deployment |
| Testing | pytest | Unit & integration tests |

## Key Design Decisions

1. **SQLAlchemy ORM** - Type safety, migrations, relationships
2. **Async FastAPI** - Performance, concurrent requests
3. **XGBoost over NN** - Interpretability, small datasets, fast training
4. **OpenStreetMap/OSRM** - Free, open-source, no API key needed (initially)
5. **JWT vs OAuth** - Simpler MVP, OAuth can be added later
6. **PostgreSQL PostGIS** - Spatial indexing for route queries
7. **Docker** - Reproducible environments, easy deployment

## Scalability Considerations

1. **Database**: Use read replicas for match queries, Redis cache for frequently accessed data
2. **API**: Horizontal scaling with load balancer (nginx)
3. **ML**: Batch prediction job, cache scores for 5 minutes
4. **File Storage**: S3 for profile pictures
5. **Notifications**: Queue system (Celery/RabbitMQ) for async jobs

## Security Considerations

1. **Input Validation**: Pydantic schemas with validators
2. **SQL Injection**: Parameterized queries via SQLAlchemy
3. **CORS**: Whitelist frontend origin in production
4. **Rate Limiting**: Implement per-user/IP limits
5. **HTTPS**: Use SSL certificates in production
6. **Secrets**: Environment variables, never commit API keys
7. **Email Verification**: Token-based verification links
8. **Password Security**: Bcrypt hashing + min length requirements

## Monitoring & Logging

1. **Structured Logging**: JSON logs with request IDs for tracing
2. **Error Tracking**: Sentry integration
3. **Performance Monitoring**: New Relic or DataDog
4. **Database Monitoring**: CloudWatch (AWS) metrics
5. **Uptime Monitoring**: Status page service

---

**Status**: Phase 1 Core Architecture (2024)  
**Next**: Phase 2 - ML Engine & Matching (2024)
