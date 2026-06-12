"""Match service for calculating ride compatibility and scoring."""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database.models import Ride, User, Match
from services.maps_service import MapsService
from utils.constants import MATCH_WEIGHT_ROUTE, MATCH_WEIGHT_TIME, MATCH_WEIGHT_PREFERENCES, MATCH_WEIGHT_TRUST
import logging
import math

logger = logging.getLogger(__name__)


class MatchService:
    """Service for calculating ride matches and recommendations."""
    
    def __init__(self):
        self.maps_service = MapsService()

    @staticmethod
    def calculate_route_overlap(polyline1: Optional[str], polyline2: Optional[str], 
                               source_lat1: float, source_lng1: float,
                               dest_lat1: float, dest_lng1: float,
                               source_lat2: float, source_lng2: float,
                               dest_lat2: float, dest_lng2: float) -> float:
        """Calculate route overlap percentage using Sørensen-Dice coefficient."""
        if not polyline1 or not polyline2:
            # Fallback: use simple distance-based calculation
            return MatchService._calculate_route_overlap_simple(
                source_lat1, source_lng1, dest_lat1, dest_lng1,
                source_lat2, source_lng2, dest_lat2, dest_lng2
            )
        
        try:
            coords1 = MapsService._decode_polyline(polyline1)
            coords2 = MapsService._decode_polyline(polyline2)
            
            if not coords1 or not coords2:
                return 0
            
            # Calculate distance traveled on both routes
            dist1 = MapsService.polyline_distance(coords1)
            dist2 = MapsService.polyline_distance(coords2)
            
            if dist1 == 0 or dist2 == 0:
                return 0
            
            # Calculate intersection distance using segment matching
            intersection_dist = MatchService._calculate_polyline_intersection(coords1, coords2, threshold_km=1.0)
            
            # Sørensen-Dice coefficient: 2 * intersection / (sum of distances)
            overlap_percent = (2 * intersection_dist) / (dist1 + dist2) * 100
            
            return min(overlap_percent, 100)
        except Exception as e:
            logger.error(f"Route overlap calculation error: {str(e)}")
            return 0

    @staticmethod
    def _calculate_route_overlap_simple(source_lat1: float, source_lng1: float,
                                        dest_lat1: float, dest_lng1: float,
                                        source_lat2: float, source_lng2: float,
                                        dest_lat2: float, dest_lng2: float) -> float:
        """Simple route overlap based on start/end distances."""
        source_dist = MapsService.haversine_distance(source_lat1, source_lng1, source_lat2, source_lng2)
        dest_dist = MapsService.haversine_distance(dest_lat1, dest_lng1, dest_lat2, dest_lng2)
        
        # Average distance between routes (in km)
        avg_dist = (source_dist + dest_dist) / 2
        
        # If average distance > 5km, routes are too far apart
        if avg_dist > 5:
            return 0
        
        # Scale: 0km = 100%, 5km = 0%
        overlap_percent = max(0, 100 - (avg_dist / 5) * 100)
        
        return overlap_percent

    @staticmethod
    def _calculate_polyline_intersection(coords1: List[tuple], coords2: List[tuple], 
                                         threshold_km: float = 1.0) -> float:
        """Calculate intersection distance of two polylines."""
        if len(coords1) < 2 or len(coords2) < 2:
            return 0
        
        matched_distance = 0
        segment_distances = []
        
        # Calculate segment distances for route 1
        for i in range(len(coords1) - 1):
            lat1, lng1 = coords1[i]
            lat2, lng2 = coords1[i + 1]
            dist = MapsService.haversine_distance(lat1, lng1, lat2, lng2)
            segment_distances.append((i, dist))
        
        total_distance = sum(d for _, d in segment_distances)
        if total_distance == 0:
            return 0
        
        # For each segment in route 1, check if it's close to any segment in route 2
        for idx, seg_dist in segment_distances:
            lat1, lng1 = coords1[idx]
            lat2, lng2 = coords1[idx + 1]
            mid_lat1 = (lat1 + lat2) / 2
            mid_lng1 = (lng1 + lng2) / 2
            
            # Find closest segment in route 2
            min_distance = float('inf')
            for j in range(len(coords2) - 1):
                lat3, lng3 = coords2[j]
                lat4, lng4 = coords2[j + 1]
                mid_lat2 = (lat3 + lat4) / 2
                mid_lng2 = (lng3 + lng4) / 2
                
                dist = MapsService.haversine_distance(mid_lat1, mid_lng1, mid_lat2, mid_lng2)
                min_distance = min(min_distance, dist)
            
            # If closest distance is within threshold, count as matched
            if min_distance <= threshold_km:
                matched_distance += seg_dist
        
        return matched_distance

    @staticmethod
    def calculate_time_compatibility(time1: datetime, time2: datetime) -> float:
        """Calculate time compatibility score (0-100)."""
        diff_minutes = abs((time2 - time1).total_seconds() / 60)
        
        # Sigmoid function: centered at 30 minutes, scale to 0-100
        # At diff=0: score≈100, at diff=30: score=50, at diff=60: score≈0
        if diff_minutes == 0:
            return 100.0
        
        # Sigmoid: 1 / (1 + exp((x - 30) / 20))
        score = 100 / (1 + math.exp((diff_minutes - 30) / 20))
        
        return score

    @staticmethod
    def calculate_preference_compatibility(prefs1: Dict, prefs2: Dict) -> float:
        """Calculate preference similarity using Jaccard coefficient (0-100)."""
        # Convert preferences to sets
        pref_keys = ['smoking', 'gender', 'music', 'luggage', 'ac_preference']
        
        set1 = set()
        set2 = set()
        
        for key in pref_keys:
            val1 = prefs1.get(key, 'no_preference')
            val2 = prefs2.get(key, 'no_preference')
            
            if val1 != 'no_preference':
                set1.add(f"{key}:{val1}")
            if val2 != 'no_preference':
                set2.add(f"{key}:{val2}")
        
        # Jaccard similarity: |intersection| / |union|
        if len(set1) + len(set2) == 0:
            return 75.0  # Neutral when both have no preferences
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        jaccard = intersection / union if union > 0 else 0
        
        return jaccard * 100

    @staticmethod
    def calculate_trust_product(driver_trust: float, rider_trust: float) -> float:
        """Calculate trust score product (0-100)."""
        # Product of trust scores, normalized to 0-100 scale
        product = (driver_trust * rider_trust) / 100
        return min(product, 100)

    @staticmethod
    def calculate_overall_match_score(route_overlap: float,
                                     time_compatibility: float,
                                     preference_compatibility: float,
                                     trust_product: float) -> float:
        """Calculate weighted overall match score (0-100)."""
        score = (
            route_overlap * MATCH_WEIGHT_ROUTE +
            time_compatibility * MATCH_WEIGHT_TIME +
            preference_compatibility * MATCH_WEIGHT_PREFERENCES +
            trust_product * MATCH_WEIGHT_TRUST
        )
        
        return min(max(score, 0), 100)

    @staticmethod
    def generate_explanation(route_overlap: float,
                           time_compatibility: float,
                           preference_compatibility: float,
                           trust_product: float,
                           driver_name: str,
                           driver_rides: int) -> str:
        """Generate human-readable explanation for match score."""
        explanations = []
        
        # Route explanation
        if route_overlap > 90:
            explanations.append(f"{route_overlap:.0f}% of your route overlaps")
        elif route_overlap > 70:
            explanations.append(f"{route_overlap:.0f}% of your route overlaps")
        elif route_overlap > 50:
            explanations.append(f"{route_overlap:.0f}% route overlap")
        
        # Time explanation
        diff_minutes = abs(30 - (time_compatibility / 100 * 60))  # Approximate
        if time_compatibility > 90:
            explanations.append("timings align perfectly")
        elif time_compatibility > 70:
            explanations.append("your times differ by 15-30 minutes")
        elif time_compatibility > 50:
            explanations.append("timing is compatible")
        
        # Preferences explanation
        if preference_compatibility > 80:
            explanations.append("you share most preferences")
        elif preference_compatibility > 50:
            explanations.append("you have compatible preferences")
        
        # Trust explanation
        if trust_product > 70:
            explanations.append(f"{driver_name} has excellent trust score")
        if driver_rides > 20:
            explanations.append(f"with {driver_rides}+ completed rides")
        
        return "This ride is recommended because " + ", ".join(explanations) + "."

    @staticmethod
    def find_matches_for_ride(db: Session, ride_id: int, user_id: int,
                             source_lat: float, source_lng: float,
                             dest_lat: float, dest_lng: float,
                             departure_time: datetime,
                             min_score: float = 50.0) -> List[Dict]:
        """Find matching rides for a given ride posting."""
        
        # Get user's preferences
        from services.user_service import UserService
        user_prefs = UserService.get_user_preferences(db, user_id)
        user_trust = UserService.get_trust_score(db, user_id)
        
        # Get current user's ride
        current_ride = db.query(Ride).filter(Ride.id == ride_id).first()
        if not current_ride:
            return []
        
        # Search for potential matches (different user, similar date, active status)
        search_window = timedelta(hours=2)
        candidate_rides = db.query(Ride).filter(
            and_(
                Ride.user_id != user_id,
                Ride.status == "active",
                Ride.seats_available > 0,
                Ride.departure_datetime >= departure_time - search_window,
                Ride.departure_datetime <= departure_time + search_window,
            )
        ).all()
        
        matches = []
        
        for candidate in candidate_rides:
            candidate_user = candidate.user
            candidate_trust = UserService.get_trust_score(db, candidate.user_id)
            candidate_prefs = UserService.get_user_preferences(db, candidate.user_id)
            
            # Calculate match components
            route_overlap = MatchService.calculate_route_overlap(
                current_ride.polyline, candidate.polyline,
                current_ride.source_lat, current_ride.source_lng,
                current_ride.destination_lat, current_ride.destination_lng,
                candidate.source_lat, candidate.source_lng,
                candidate.destination_lat, candidate.destination_lng
            )
            
            time_compat = MatchService.calculate_time_compatibility(
                current_ride.departure_datetime,
                candidate.departure_datetime
            )
            
            # Get preferences as dicts
            user_prefs_dict = {
                'smoking': user_prefs.smoking,
                'gender': user_prefs.gender,
                'music': user_prefs.music,
                'luggage': user_prefs.luggage,
                'ac_preference': user_prefs.ac_preference,
            }
            
            candidate_prefs_dict = {
                'smoking': candidate_prefs.smoking,
                'gender': candidate_prefs.gender,
                'music': candidate_prefs.music,
                'luggage': candidate_prefs.luggage,
                'ac_preference': candidate_prefs.ac_preference,
            }
            
            pref_compat = MatchService.calculate_preference_compatibility(
                user_prefs_dict, candidate_prefs_dict
            )
            
            trust_prod = MatchService.calculate_trust_product(
                candidate_trust['trust_score'],
                user_trust['trust_score']
            )
            
            overall_score = MatchService.calculate_overall_match_score(
                route_overlap, time_compat, pref_compat, trust_prod
            )
            
            # Only include matches above threshold
            if overall_score >= min_score:
                explanation = MatchService.generate_explanation(
                    route_overlap, time_compat, pref_compat, trust_prod,
                    candidate_user.name, len(candidate_user.rides)
                )
                
                matches.append({
                    'ride_id': candidate.id,
                    'driver_id': candidate.user_id,
                    'driver_name': candidate_user.name,
                    'driver_trust_score': candidate_trust['trust_score'],
                    'source_address': candidate.source_address,
                    'destination_address': candidate.destination_address,
                    'departure_datetime': candidate.departure_datetime,
                    'seats_available': candidate.seats_available,
                    'vehicle_type': candidate.vehicle_type,
                    'match_score': overall_score,
                    'route_overlap': route_overlap,
                    'time_compatibility': time_compat,
                    'preference_compatibility': pref_compat,
                    'explanation': explanation,
                })
        
        # Sort by score descending
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matches[:10]  # Return top 10 matches
