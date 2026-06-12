"""Feature engineering for ML models."""

from typing import List, Dict, Tuple
from datetime import datetime
from database.models import Ride, User, Match, Rating
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import numpy as np


class FeatureEngineering:
    """Feature extraction and engineering for ML models."""

    @staticmethod
    def extract_features_from_match(db: Session, ride1_id: int, ride2_id: int) -> Dict:
        """Extract ML features from two rides for matching prediction."""
        from services.match_service import MatchService
        from services.maps_service import MapsService
        from services.user_service import UserService
        
        # Get rides
        ride1 = db.query(Ride).filter(Ride.id == ride1_id).first()
        ride2 = db.query(Ride).filter(Ride.id == ride2_id).first()
        
        if not ride1 or not ride2:
            return {}
        
        # Get users and their trust scores
        user1 = db.query(User).filter(User.id == ride1.user_id).first()
        user2 = db.query(User).filter(User.id == ride2.user_id).first()
        
        trust1 = UserService.get_trust_score(db, ride1.user_id)
        trust2 = UserService.get_trust_score(db, ride2.user_id)
        
        prefs1 = UserService.get_user_preferences(db, ride1.user_id)
        prefs2 = UserService.get_user_preferences(db, ride2.user_id)
        
        # Feature 1: Route overlap
        route_overlap = MatchService.calculate_route_overlap(
            ride1.polyline, ride2.polyline,
            ride1.source_lat, ride1.source_lng,
            ride1.destination_lat, ride1.destination_lng,
            ride2.source_lat, ride2.source_lng,
            ride2.destination_lat, ride2.destination_lng
        )
        
        # Feature 2: Time difference
        time_diff_minutes = abs((ride2.departure_datetime - ride1.departure_datetime).total_seconds() / 60)
        
        # Feature 3: Time compatibility
        time_compatibility = MatchService.calculate_time_compatibility(
            ride1.departure_datetime, ride2.departure_datetime
        )
        
        # Feature 4: Preference compatibility
        prefs1_dict = {
            'smoking': prefs1.smoking,
            'gender': prefs1.gender,
            'music': prefs1.music,
            'luggage': prefs1.luggage,
            'ac_preference': prefs1.ac_preference,
        }
        prefs2_dict = {
            'smoking': prefs2.smoking,
            'gender': prefs2.gender,
            'music': prefs2.music,
            'luggage': prefs2.luggage,
            'ac_preference': prefs2.ac_preference,
        }
        
        pref_compatibility = MatchService.calculate_preference_compatibility(
            prefs1_dict, prefs2_dict
        )
        
        # Feature 5: Trust scores
        driver_trust = trust1['trust_score']
        rider_trust = trust2['trust_score']
        trust_product = (driver_trust * rider_trust) / 100
        
        # Feature 6: Experience (ride counts)
        experience1 = trust1['total_rides_as_driver'] + trust1['total_rides_as_passenger']
        experience2 = trust2['total_rides_as_driver'] + trust2['total_rides_as_passenger']
        
        # Feature 7: Distance between pickup points
        pickup_distance = MapsService.haversine_distance(
            ride1.source_lat, ride1.source_lng,
            ride2.source_lat, ride2.source_lng
        )
        
        # Feature 8: Seats availability
        seats_available = ride1.seats_available
        
        # Feature 9: Ride duration
        ride_duration = ride1.route_duration_minutes or 0
        
        # Feature 10-14: Individual preference compatibility (binary)
        gender_compatible = 1 if (prefs1.gender == 'any' or prefs2.gender == 'any' or 
                                  prefs1.gender == prefs2.gender) else 0
        smoking_compatible = 1 if (prefs1.smoking == 'no_preference' or prefs2.smoking == 'no_preference' or
                                   prefs1.smoking == prefs2.smoking) else 0
        music_compatible = 1 if (prefs1.music == 'no_preference' or prefs2.music == 'no_preference' or
                                 prefs1.music == prefs2.music) else 0
        luggage_compatible = 1 if (prefs1.luggage == 'no_preference' or prefs2.luggage == 'no_preference' or
                                   prefs1.luggage == prefs2.luggage) else 0
        ac_compatible = 1 if (prefs1.ac_preference == 'no_preference' or prefs2.ac_preference == 'no_preference' or
                              prefs1.ac_preference == prefs2.ac_preference) else 0
        
        # Feature 15: Cancellation history
        user1_cancellations = trust1['cancellation_count']
        user2_cancellations = trust2['cancellation_count']
        
        # Feature 16: Average rating
        user1_rating = trust1['average_rating']
        user2_rating = trust2['average_rating']
        
        return {
            'route_overlap_percent': route_overlap,
            'time_diff_minutes': time_diff_minutes,
            'time_compatibility': time_compatibility,
            'preference_compatibility': pref_compatibility,
            'driver_trust_score': driver_trust,
            'rider_trust_score': rider_trust,
            'trust_product': trust_product,
            'driver_experience': experience1,
            'rider_experience': experience2,
            'pickup_distance_km': pickup_distance,
            'seats_available': seats_available,
            'ride_duration_minutes': ride_duration,
            'gender_compatible': gender_compatible,
            'smoking_compatible': smoking_compatible,
            'music_compatible': music_compatible,
            'luggage_compatible': luggage_compatible,
            'ac_compatible': ac_compatible,
            'driver_cancellations': user1_cancellations,
            'rider_cancellations': user2_cancellations,
            'driver_avg_rating': user1_rating,
            'rider_avg_rating': user2_rating,
        }

    @staticmethod
    def create_training_dataframe(db: Session) -> pd.DataFrame:
        """Create training dataframe from historical matches."""
        from services.match_service import MatchService
        
        # Get all completed matches with ratings
        matches = db.query(Match).filter(Match.status == "completed").all()
        
        data = []
        feature_cols = [
            'route_overlap_percent', 'time_diff_minutes', 'time_compatibility',
            'preference_compatibility', 'driver_trust_score', 'rider_trust_score',
            'trust_product', 'driver_experience', 'rider_experience',
            'pickup_distance_km', 'seats_available', 'ride_duration_minutes',
            'gender_compatible', 'smoking_compatible', 'music_compatible',
            'luggage_compatible', 'ac_compatible', 'driver_cancellations',
            'rider_cancellations', 'driver_avg_rating', 'rider_avg_rating'
        ]
        
        for match in matches:
            try:
                # Extract features
                features = FeatureEngineering.extract_features_from_match(
                    db, match.ride_id, match.ride_id
                )
                
                if not features:
                    continue
                
                # Determine label: "good match" if both users have average rating >= 4
                driver_ratings = db.query(Rating).filter(
                    Rating.to_user_id == match.driver_id
                ).all()
                rider_ratings = db.query(Rating).filter(
                    Rating.to_user_id == match.rider_id
                ).all()
                
                driver_avg = np.mean([r.score for r in driver_ratings]) if driver_ratings else 3.0
                rider_avg = np.mean([r.score for r in rider_ratings]) if rider_ratings else 3.0
                
                is_good_match = 1 if (driver_avg >= 4.0 and rider_avg >= 4.0) else 0
                
                # Add features and label to data
                row = {**features, 'is_good_match': is_good_match}
                data.append(row)
            except Exception as e:
                print(f"Error processing match {match.id}: {str(e)}")
                continue
        
        return pd.DataFrame(data)
