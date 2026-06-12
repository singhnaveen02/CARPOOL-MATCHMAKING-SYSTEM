-- Enable PostGIS extension for spatial queries
CREATE EXTENSION IF NOT EXISTS postgis;

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    institute_email VARCHAR(255),
    profile_picture_url TEXT,
    bio TEXT,
    verification_token VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    email_verified_at TIMESTAMP,
    phone_verified BOOLEAN DEFAULT FALSE,
    phone_verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_institute_email ON users(institute_email);

-- User Preferences table
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    smoking VARCHAR(50) DEFAULT 'no_preference',  -- yes, no, no_preference
    gender VARCHAR(50) DEFAULT 'any',  -- male, female, any
    music VARCHAR(50) DEFAULT 'no_preference',  -- yes, no, quiet, no_preference
    luggage VARCHAR(50) DEFAULT 'no_preference',  -- small, medium, large, no_preference
    ac_preference VARCHAR(50) DEFAULT 'no_preference',  -- yes, no, no_preference
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Trust Scores table
CREATE TABLE user_trust_scores (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    average_rating DECIMAL(3, 2) DEFAULT 0,
    total_rides_completed INTEGER DEFAULT 0,
    total_rides_as_driver INTEGER DEFAULT 0,
    total_rides_as_passenger INTEGER DEFAULT 0,
    cancellation_count INTEGER DEFAULT 0,
    email_verified_at TIMESTAMP,
    phone_verified_at TIMESTAMP,
    trust_score DECIMAL(5, 2) DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trust_scores_user_id ON user_trust_scores(user_id);
CREATE INDEX idx_trust_scores_trust_score ON user_trust_scores(trust_score);

-- Rides table
CREATE TABLE rides (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_lat DECIMAL(10, 8) NOT NULL,
    source_lng DECIMAL(11, 8) NOT NULL,
    destination_lat DECIMAL(10, 8) NOT NULL,
    destination_lng DECIMAL(11, 8) NOT NULL,
    source_address VARCHAR(500),
    destination_address VARCHAR(500),
    departure_datetime TIMESTAMP NOT NULL,
    seats_available INTEGER NOT NULL DEFAULT 1,
    vehicle_type VARCHAR(50),  -- car, auto, van, bike
    vehicle_name VARCHAR(255),
    vehicle_plate VARCHAR(50),
    polyline TEXT,  -- Encoded polyline from OSRM
    route_distance_km DECIMAL(10, 2),
    route_duration_minutes INTEGER,
    status VARCHAR(50) DEFAULT 'active',  -- active, completed, cancelled
    is_recurring_series BOOLEAN DEFAULT FALSE,
    recurrence_pattern JSONB,  -- {"frequency": "daily", "days": ["Mon", "Tue"], "end_date": "2024-12-31"}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_rides_user_id ON rides(user_id);
CREATE INDEX idx_rides_departure_datetime ON rides(departure_datetime);
CREATE INDEX idx_rides_status ON rides(status);
CREATE INDEX idx_rides_source ON rides USING GIST (
    ST_GeographyFromText('SRID=4326;POINT(' || source_lng || ' ' || source_lat || ')')
);

-- Ride Details (Preferences) table
CREATE TABLE ride_details (
    id SERIAL PRIMARY KEY,
    ride_id INTEGER NOT NULL UNIQUE REFERENCES rides(id) ON DELETE CASCADE,
    smoking VARCHAR(50) DEFAULT 'no_preference',
    gender VARCHAR(50) DEFAULT 'any',
    music VARCHAR(50) DEFAULT 'no_preference',
    luggage VARCHAR(50) DEFAULT 'no_preference',
    ac_preference VARCHAR(50) DEFAULT 'no_preference',
    price_per_seat DECIMAL(10, 2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ride Occurrences (for recurring rides)
CREATE TABLE ride_occurrences (
    id SERIAL PRIMARY KEY,
    ride_id INTEGER NOT NULL REFERENCES rides(id) ON DELETE CASCADE,
    occurrence_date DATE NOT NULL,
    is_cancelled BOOLEAN DEFAULT FALSE,
    cancellation_reason VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ride_occurrences_ride_id ON ride_occurrences(ride_id);
CREATE INDEX idx_ride_occurrences_date ON ride_occurrences(occurrence_date);

-- Matches table
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    driver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rider_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ride_id INTEGER NOT NULL REFERENCES rides(id) ON DELETE CASCADE,
    match_score DECIMAL(5, 2) DEFAULT 0,
    route_overlap_percent DECIMAL(5, 2),
    time_compatibility DECIMAL(5, 2),
    preference_compatibility DECIMAL(5, 2),
    explanation TEXT,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, accepted, rejected, completed, cancelled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP,
    completed_at TIMESTAMP,
    rating_from_driver_id INTEGER REFERENCES users(id),
    rating_from_rider_id INTEGER REFERENCES users(id)
);

CREATE INDEX idx_matches_driver_id ON matches(driver_id);
CREATE INDEX idx_matches_rider_id ON matches(rider_id);
CREATE INDEX idx_matches_ride_id ON matches(ride_id);
CREATE INDEX idx_matches_status ON matches(status);
CREATE UNIQUE INDEX idx_matches_unique ON matches(rider_id, ride_id) WHERE status IN ('pending', 'accepted');

-- Ratings table
CREATE TABLE ratings (
    id SERIAL PRIMARY KEY,
    from_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    to_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ride_id INTEGER NOT NULL REFERENCES rides(id) ON DELETE CASCADE,
    match_id INTEGER REFERENCES matches(id) ON DELETE SET NULL,
    score INTEGER NOT NULL CHECK (score >= 1 AND score <= 5),
    punctuality_rating INTEGER CHECK (punctuality_rating >= 1 AND punctuality_rating <= 5),
    cleanliness_rating INTEGER CHECK (cleanliness_rating >= 1 AND cleanliness_rating <= 5),
    behavior_rating INTEGER CHECK (behavior_rating >= 1 AND behavior_rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ratings_from_user ON ratings(from_user_id);
CREATE INDEX idx_ratings_to_user ON ratings(to_user_id);
CREATE INDEX idx_ratings_ride_id ON ratings(ride_id);
CREATE UNIQUE INDEX idx_ratings_unique ON ratings(from_user_id, to_user_id, ride_id);

-- Notifications table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,  -- match_found, match_accepted, ride_completed, etc.
    title VARCHAR(255),
    message TEXT NOT NULL,
    data JSONB,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(read);
CREATE INDEX idx_notifications_created ON notifications(created_at);
