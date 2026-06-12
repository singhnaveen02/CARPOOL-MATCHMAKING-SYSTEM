"""Synthetic data generation for ML training."""

import random
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict
import math


class SyntheticDataGenerator:
    """Generate synthetic ride and match data for training."""
    
    # Indian cities with coordinates
    CITIES = {
        'Delhi': (28.7041, 77.1025),
        'Bangalore': (12.9716, 77.5946),
        'Mumbai': (19.0760, 72.8777),
        'Hyderabad': (17.3850, 78.4867),
        'Chennai': (13.0827, 80.2707),
        'Pune': (18.5204, 73.8567),
        'Ahmedabad': (23.0225, 72.5714),
        'Kolkata': (22.5726, 88.3639),
        'Jaipur': (26.9124, 75.7873),
        'Lucknow': (26.8467, 80.9462),
        'IIT Roorkee': (29.8757, 77.8974),
        'Haridwar': (29.9457, 78.1642),
    }

    # Preferences distribution
    SMOKING_OPTIONS = ['yes', 'no', 'no_preference']
    GENDER_OPTIONS = ['male', 'female', 'any']
    MUSIC_OPTIONS = ['yes', 'no', 'quiet', 'no_preference']
    LUGGAGE_OPTIONS = ['small', 'medium', 'large', 'no_preference']
    AC_OPTIONS = ['yes', 'no', 'no_preference']

    @staticmethod
    def generate_synthetic_users(count: int = 100) -> List[Dict]:
        """Generate synthetic users with realistic attributes."""
        users = []
        
        names = ['Raj', 'Priya', 'Amit', 'Neha', 'Arjun', 'Anjali', 'Vikram', 'Isha',
                 'Rohit', 'Deepika', 'Nitin', 'Pooja', 'Samir', 'Kavya', 'Arun', 'Shreya']
        
        for i in range(count):
            user = {
                'id': i + 1,
                'name': random.choice(names) + str(i),
                'email': f'user{i}@example.com',
                'trust_score': random.uniform(30, 100),
                'total_rides': random.randint(0, 50),
                'smoking': random.choice(SyntheticDataGenerator.SMOKING_OPTIONS),
                'gender': random.choice(SyntheticDataGenerator.GENDER_OPTIONS),
                'music': random.choice(SyntheticDataGenerator.MUSIC_OPTIONS),
                'luggage': random.choice(SyntheticDataGenerator.LUGGAGE_OPTIONS),
                'ac_preference': random.choice(SyntheticDataGenerator.AC_OPTIONS),
                'cancellation_rate': random.uniform(0, 0.3),
            }
            users.append(user)
        
        return users

    @staticmethod
    def generate_synthetic_rides(users: List[Dict], count: int = 500) -> List[Dict]:
        """Generate synthetic ride postings."""
        rides = []
        cities_list = list(SyntheticDataGenerator.CITIES.items())
        
        base_date = datetime(2024, 6, 15)
        
        for i in range(count):
            # Pick random user as driver
            driver = random.choice(users)
            
            # Pick two random cities (source and destination)
            source_city, (source_lat, source_lng) = random.choice(cities_list)
            dest_city, (dest_lat, dest_lng) = random.choice(cities_list)
            
            # Skip if same city
            if source_city == dest_city:
                continue
            
            # Random departure time (next 30 days)
            days_ahead = random.randint(0, 30)
            hours = random.randint(6, 22)
            minutes = random.choice([0, 15, 30, 45])
            
            departure_time = base_date + timedelta(days=days_ahead, hours=hours, minutes=minutes)
            
            # Estimate distance (rough calculation)
            distance_km = SyntheticDataGenerator._haversine(
                source_lat, source_lng, dest_lat, dest_lng
            )
            duration_minutes = int(distance_km / 50 * 60)  # Assume 50 km/h average
            
            ride = {
                'id': i + 1,
                'driver_id': driver['id'],
                'source_address': source_city,
                'source_lat': source_lat + random.uniform(-0.05, 0.05),
                'source_lng': source_lng + random.uniform(-0.05, 0.05),
                'destination_address': dest_city,
                'destination_lat': dest_lat + random.uniform(-0.05, 0.05),
                'destination_lng': dest_lng + random.uniform(-0.05, 0.05),
                'departure_datetime': departure_time,
                'seats_available': random.randint(1, 4),
                'vehicle_type': random.choice(['car', 'auto', 'van']),
                'route_distance_km': distance_km,
                'route_duration_minutes': duration_minutes,
                'price_per_seat': random.randint(50, 300),
                'smoking': driver['smoking'],
                'gender': driver['gender'],
                'music': driver['music'],
                'luggage': driver['luggage'],
                'ac_preference': driver['ac_preference'],
                'status': 'active',
                'created_at': datetime.now() - timedelta(days=random.randint(0, 30))
            }
            rides.append(ride)
        
        return rides

    @staticmethod
    def generate_synthetic_matches(users: List[Dict], rides: List[Dict]) -> List[Dict]:
        """Generate synthetic matches based on route compatibility."""
        from services.match_service import MatchService
        
        matches = []
        
        # Create matches for rides with similar routes and times
        for i, ride1 in enumerate(rides):
            # Find compatible rides
            for ride2 in rides[i+1:]:
                if ride1['id'] == ride2['id']:
                    continue
                
                # Calculate route overlap (simple distance-based)
                source_dist = SyntheticDataGenerator._haversine(
                    ride1['source_lat'], ride1['source_lng'],
                    ride2['source_lat'], ride2['source_lng']
                )
                dest_dist = SyntheticDataGenerator._haversine(
                    ride1['destination_lat'], ride1['destination_lng'],
                    ride2['destination_lat'], ride2['destination_lng']
                )
                
                avg_dist = (source_dist + dest_dist) / 2
                
                # Routes too far apart
                if avg_dist > 5:
                    continue
                
                route_overlap = max(0, 100 - (avg_dist / 5) * 100)
                
                # Calculate time compatibility
                time_diff = abs((ride2['departure_datetime'] - ride1['departure_datetime']).total_seconds() / 60)
                time_compatibility = 100 / (1 + math.exp((time_diff - 30) / 20))
                
                # Calculate preference compatibility
                prefs1 = {k: ride1[k] for k in ['smoking', 'gender', 'music', 'luggage', 'ac_preference']}
                prefs2 = {k: ride2[k] for k in ['smoking', 'gender', 'music', 'luggage', 'ac_preference']}
                pref_compatibility = SyntheticDataGenerator._jaccard_similarity(prefs1, prefs2)
                
                # Get user trust scores
                user1 = next((u for u in users if u['id'] == ride1['driver_id']), None)
                user2 = next((u for u in users if u['id'] == ride2['driver_id']), None)
                
                if not user1 or not user2:
                    continue
                
                trust_product = (user1['trust_score'] * user2['trust_score']) / 100
                
                # Calculate overall score
                overall_score = (
                    route_overlap * 0.4 +
                    time_compatibility * 0.3 +
                    pref_compatibility * 0.2 +
                    trust_product * 0.1
                )
                
                # Only create matches with score > 60
                if overall_score > 60:
                    # Randomly assign label based on score and trust
                    if overall_score > 75 and user1['trust_score'] > 60 and user2['trust_score'] > 60:
                        is_good = random.choice([1, 1, 0])  # 66% chance good
                    else:
                        is_good = random.choice([1, 0])  # 50% chance
                    
                    match = {
                        'id': len(matches) + 1,
                        'driver_id': ride1['driver_id'],
                        'rider_id': ride2['driver_id'],
                        'ride_id': ride1['id'],
                        'route_overlap_percent': route_overlap,
                        'time_compatibility': time_compatibility,
                        'preference_compatibility': pref_compatibility,
                        'trust_product': trust_product,
                        'match_score': overall_score,
                        'is_good_match': is_good,
                    }
                    matches.append(match)
        
        return matches

    @staticmethod
    def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate haversine distance in km."""
        from math import radians, cos, sin, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return km

    @staticmethod
    def _jaccard_similarity(prefs1: Dict, prefs2: Dict) -> float:
        """Calculate Jaccard similarity between preference dicts."""
        set1 = {f"{k}:{v}" for k, v in prefs1.items() if v != 'no_preference'}
        set2 = {f"{k}:{v}" for k, v in prefs2.items() if v != 'no_preference'}
        
        if len(set1) + len(set2) == 0:
            return 75.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return (intersection / union * 100) if union > 0 else 75.0

    @staticmethod
    def generate_to_csv(output_path: str = 'backend/data/synthetic_matches.csv'):
        """Generate and save synthetic data to CSV."""
        print("Generating synthetic users...")
        users = SyntheticDataGenerator.generate_synthetic_users(100)
        
        print("Generating synthetic rides...")
        rides = SyntheticDataGenerator.generate_synthetic_rides(users, 500)
        
        print(f"Generating synthetic matches (from {len(rides)} rides)...")
        matches = SyntheticDataGenerator.generate_synthetic_matches(users, rides)
        
        # Convert to DataFrame and save
        df = pd.DataFrame(matches)
        df.to_csv(output_path, index=False)
        
        print(f"\nSynthetic data generated successfully!")
        print(f"- Users: {len(users)}")
        print(f"- Rides: {len(rides)}")
        print(f"- Matches: {len(matches)}")
        print(f"- Good matches: {df['is_good_match'].sum()}")
        print(f"- Saved to: {output_path}")
        
        return df


if __name__ == "__main__":
    # Generate synthetic data
    df = SyntheticDataGenerator.generate_to_csv()
    print("\nDataset preview:")
    print(df.head())
    print(f"\nDataset info:")
    print(df.info())
