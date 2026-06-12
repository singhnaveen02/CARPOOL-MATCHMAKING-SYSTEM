"""XGBoost model training for ride matching."""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import xgboost as xgb
import joblib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Feature columns
FEATURE_COLUMNS = [
    'route_overlap_percent', 'time_diff_minutes', 'time_compatibility',
    'preference_compatibility', 'driver_trust_score', 'rider_trust_score',
    'trust_product', 'driver_experience', 'rider_experience',
    'pickup_distance_km', 'seats_available', 'ride_duration_minutes',
    'gender_compatible', 'smoking_compatible', 'music_compatible',
    'luggage_compatible', 'ac_compatible', 'driver_cancellations',
    'rider_cancellations', 'driver_avg_rating', 'rider_avg_rating'
]


class MatchModel:
    """XGBoost model for ride matching predictions."""
    
    def __init__(self, model_path: str = 'backend/ml/models/match_model.joblib'):
        self.model_path = Path(model_path)
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = FEATURE_COLUMNS
    
    def train(self, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42):
        """Train XGBoost model on synthetic or real data."""
        logger.info(f"Training on {len(df)} samples")
        
        # Prepare features and target
        X = df[self.feature_columns]
        y = df['is_good_match']
        
        # Handle missing values
        X = X.fillna(X.mean())
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # Normalize features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train XGBoost model
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            verbosity=1
        )
        
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            early_stopping_rounds=10,
            verbose=True
        )
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'roc_auc': roc_auc,
        }
        
        logger.info(f"Model metrics:\n{pd.Series(metrics)}")
        
        # Get feature importance
        importances = self.model.feature_importances_
        feature_importance_df = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        logger.info(f"Feature importance:\n{feature_importance_df}")
        
        return metrics, feature_importance_df

    def predict(self, features: dict) -> float:
        """Predict match score for a single match."""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Create feature array
        X = np.array([[features.get(col, 0) for col in self.feature_columns]])
        
        # Normalize
        X_scaled = self.scaler.transform(X)
        
        # Predict probability
        prob = self.model.predict_proba(X_scaled)[0][1]
        
        # Scale to 0-100
        return prob * 100

    def predict_batch(self, features_list: list) -> list:
        """Predict match scores for multiple matches."""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Create feature matrix
        X = np.array([[f.get(col, 0) for col in self.feature_columns] for f in features_list])
        
        # Handle missing values
        X = np.nan_to_num(X)
        
        # Normalize
        X_scaled = self.scaler.transform(X)
        
        # Predict probabilities
        probs = self.model.predict_proba(X_scaled)[:, 1]
        
        # Scale to 0-100
        return (probs * 100).tolist()

    def save(self):
        """Save model to disk."""
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'features': self.feature_columns
        }, self.model_path)
        logger.info(f"Model saved to {self.model_path}")

    def load(self):
        """Load model from disk."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        
        data = joblib.load(self.model_path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_columns = data['features']
        logger.info(f"Model loaded from {self.model_path}")


def train_model_from_csv(csv_path: str = 'backend/data/synthetic_matches.csv'):
    """Train model from CSV file."""
    # Load data
    df = pd.read_csv(csv_path)
    
    # Train model
    model = MatchModel()
    metrics, feature_importance = model.train(df)
    
    # Save model
    model.save()
    
    return model, metrics, feature_importance


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    csv_path = sys.argv[1] if len(sys.argv) > 1 else 'backend/data/synthetic_matches.csv'
    
    print(f"Training model from {csv_path}...")
    model, metrics, features = train_model_from_csv(csv_path)
    
    print("\nTraining complete!")
    print(f"Metrics: {metrics}")
    print(f"Model saved to: {model.model_path}")
