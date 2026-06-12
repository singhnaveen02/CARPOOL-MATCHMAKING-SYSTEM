"""Maps and geocoding service using OpenStreetMap and OSRM."""

import aiohttp
import asyncio
from typing import Optional, Dict, Tuple
from geopy.geocoders import Nominatim
from config import settings
from utils.exceptions import InvalidLocationException
import polyline
import logging

logger = logging.getLogger(__name__)


class MapsService:
    """Service for maps, geocoding, and routing."""
    
    def __init__(self):
        self.nominatim_url = settings.NOMINATIM_API_URL
        self.osrm_url = settings.OSRM_API_URL
        self.user_agent = settings.NOMINATIM_USER_AGENT

    async def geocode_address(self, address: str) -> Dict[str, float]:
        """Geocode address to coordinates using Nominatim."""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": address,
                    "format": "json",
                    "limit": 1
                }
                headers = {"User-Agent": self.user_agent}
                
                async with session.get(
                    f"{self.nominatim_url}/search",
                    params=params,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        raise InvalidLocationException(f"Failed to geocode address: {address}")
                    
                    results = await response.json()
                    
                    if not results:
                        raise InvalidLocationException(f"Address not found: {address}")
                    
                    result = results[0]
                    return {
                        "lat": float(result["lat"]),
                        "lng": float(result["lon"]),
                        "display_name": result.get("display_name", "")
                    }
        except Exception as e:
            logger.error(f"Geocoding error for {address}: {str(e)}")
            raise InvalidLocationException(f"Failed to geocode address: {address}")

    async def reverse_geocode(self, lat: float, lng: float) -> str:
        """Reverse geocode coordinates to address."""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "lat": lat,
                    "lon": lng,
                    "format": "json"
                }
                headers = {"User-Agent": self.user_agent}
                
                async with session.get(
                    f"{self.nominatim_url}/reverse",
                    params=params,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        return f"{lat}, {lng}"
                    
                    result = await response.json()
                    return result.get("address", {}).get("name", f"{lat}, {lng}")
        except Exception as e:
            logger.error(f"Reverse geocoding error: {str(e)}")
            return f"{lat}, {lng}"

    async def get_route(self, source_lat: float, source_lng: float, 
                       dest_lat: float, dest_lng: float) -> Dict:
        """Get route polyline and distance from OSRM."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.osrm_url}/route/v1/driving/{source_lng},{source_lat};{dest_lng},{dest_lat}"
                params = {
                    "overview": "full",
                    "steps": "false",
                    "geometries": "polyline"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"OSRM error: {response.status}")
                        return {
                            "polyline": None,
                            "distance_km": None,
                            "duration_minutes": None
                        }
                    
                    data = await response.json()
                    
                    if data.get("code") != "Ok" or not data.get("routes"):
                        logger.warning(f"OSRM returned no route: {data}")
                        return {
                            "polyline": None,
                            "distance_km": None,
                            "duration_minutes": None
                        }
                    
                    route = data["routes"][0]
                    
                    return {
                        "polyline": route.get("geometry"),
                        "distance_km": route.get("distance", 0) / 1000,
                        "duration_minutes": round(route.get("duration", 0) / 60),
                        "coordinates": self._decode_polyline(route.get("geometry", ""))
                    }
        except Exception as e:
            logger.error(f"Route calculation error: {str(e)}")
            return {
                "polyline": None,
                "distance_km": None,
                "duration_minutes": None,
                "coordinates": []
            }

    @staticmethod
    def _decode_polyline(polyline_str: str) -> list:
        """Decode polyline string to coordinates."""
        try:
            if not polyline_str:
                return []
            return polyline.decode(polyline_str)
        except Exception as e:
            logger.error(f"Polyline decode error: {str(e)}")
            return []

    @staticmethod
    def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate haversine distance between two points in kilometers."""
        from math import radians, cos, sin, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return km

    @staticmethod
    def polyline_distance(polyline_coords: list) -> float:
        """Calculate total distance of polyline in kilometers."""
        if len(polyline_coords) < 2:
            return 0
        
        total_distance = 0
        for i in range(len(polyline_coords) - 1):
            lat1, lng1 = polyline_coords[i]
            lat2, lng2 = polyline_coords[i + 1]
            total_distance += MapsService.haversine_distance(lat1, lng1, lat2, lng2)
        
        return total_distance

    @staticmethod
    def calculate_polyline_intersection(coords1: list, coords2: list, threshold_km: float = 0.5) -> float:
        """Calculate route overlap between two polylines using nearest point matching."""
        if not coords1 or not coords2:
            return 0
        
        # For each coordinate in coords1, find if there's a match in coords2 within threshold
        matched_distance = 0
        segment_distances = []
        
        # Calculate segment distances for coords1
        for i in range(len(coords1) - 1):
            lat1, lng1 = coords1[i]
            lat2, lng2 = coords1[i + 1]
            dist = MapsService.haversine_distance(lat1, lng1, lat2, lng2)
            segment_distances.append(dist)
        
        total_distance = sum(segment_distances)
        if total_distance == 0:
            return 0
        
        # For each segment in coords1, check if there's a matching segment in coords2
        for i, seg_dist in enumerate(segment_distances):
            lat1, lng1 = coords1[i]
            lat2, lng2 = coords1[i + 1]
            
            # Find closest point in coords2
            min_distance = float('inf')
            for j in range(len(coords2) - 1):
                lat3, lng3 = coords2[j]
                lat4, lng4 = coords2[j + 1]
                
                # Distance from segment 1 midpoint to segment 2 midpoint
                mid_lat1 = (lat1 + lat2) / 2
                mid_lng1 = (lng1 + lng2) / 2
                mid_lat2 = (lat3 + lat4) / 2
                mid_lng2 = (lng3 + lng4) / 2
                
                dist = MapsService.haversine_distance(mid_lat1, mid_lng1, mid_lat2, mid_lng2)
                min_distance = min(min_distance, dist)
            
            # If closest point is within threshold, count this segment as matched
            if min_distance <= threshold_km:
                matched_distance += seg_dist
        
        # Return overlap percentage using Sørensen-Dice coefficient
        overlap_percent = (matched_distance / total_distance * 100) if total_distance > 0 else 0
        return min(overlap_percent, 100)
