"""Inference service for match predictions."""

import logging
from pathlib import Path
from ml.training import MatchModel, FEATURE_COLUMNS

logger = logging.getLogger(__name__)

# Global model instance
_model_instance = None


def get_model() -> MatchModel:
    """Get or load the match prediction model."""
    global _model_instance
    
    if _model_instance is None:
        _model_instance = MatchModel()
        try:
            _model_instance.load()
        except FileNotFoundError:
            logger.warning("Model not found. Running without ML predictions.")
            _model_instance = None
    
    return _model_instance


def predict_match_score(features: dict) -> float:
    """Predict match score using ML model."""
    model = get_model()
    
    if model is None:
        # Fallback: return rule-based score
        return (
            features.get('route_overlap_percent', 0) * 0.4 +
            features.get('time_compatibility', 0) * 0.3 +
            features.get('preference_compatibility', 0) * 0.2 +
            features.get('trust_product', 0) * 0.1
        )
    
    try:
        return model.predict(features)
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        # Fallback to rule-based score
        return (
            features.get('route_overlap_percent', 0) * 0.4 +
            features.get('time_compatibility', 0) * 0.3 +
            features.get('preference_compatibility', 0) * 0.2 +
            features.get('trust_product', 0) * 0.1
        )


def predict_batch_scores(features_list: list) -> list:
    """Predict match scores for multiple matches."""
    model = get_model()
    
    if model is None:
        # Fallback: return rule-based scores
        return [
            (
                f.get('route_overlap_percent', 0) * 0.4 +
                f.get('time_compatibility', 0) * 0.3 +
                f.get('preference_compatibility', 0) * 0.2 +
                f.get('trust_product', 0) * 0.1
            )
            for f in features_list
        ]
    
    try:
        return model.predict_batch(features_list)
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        # Fallback to rule-based scores
        return [
            (
                f.get('route_overlap_percent', 0) * 0.4 +
                f.get('time_compatibility', 0) * 0.3 +
                f.get('preference_compatibility', 0) * 0.2 +
                f.get('trust_product', 0) * 0.1
            )
            for f in features_list
        ]
