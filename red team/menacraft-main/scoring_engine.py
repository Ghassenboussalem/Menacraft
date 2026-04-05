import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

class BotScoringEngine:
    """Stage 3: Scoring engine with rule-based and ML classifiers"""
    
    def __init__(self, method='weighted_rules'):
        """
        Initialize scoring engine
        method: 'weighted_rules', 'random_forest', or 'gradient_boosting'
        """
        self.method = method
        self.model = None
        self.feature_weights = self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize feature weights for rule-based scoring"""
        return {
            # Profile signals (weight: importance)
            'no_profile_pic': 20,
            'no_bio': 15,
            'high_digit_username': 15,
            'username_digit_ratio': 10,
            
            # Activity signals
            'post_interval_regularity': 8,
            'burst_posts': 5,
            
            # Engagement signals (most important)
            # Note: low_engagement is less weighted because we often don't have this data
            'low_engagement': 5,  # Reduced from 20
            'suspicious_follower_ratio': 25,  # Most important indicator
            'high_following': 20,
            
            # Content signals
            'excessive_hashtags': 12,
            'location_usage_rate': -5,  # Negative weight (real accounts use locations)
            'has_external_url': -5  # Real accounts often have URLs
        }
    
    def calculate_rule_based_score(self, features):
        """Calculate 0-100 bot probability score using weighted rules"""
        score = 0
        max_score = sum([abs(w) for w in self.feature_weights.values()])
        
        for feature, weight in self.feature_weights.items():
            if feature in features:
                feature_value = features[feature]
                
                # Special handling for engagement rate
                # If engagement_rate is 0 but we have high followers and posts, 
                # it likely means we don't have engagement data, not that it's a bot
                if feature == 'low_engagement' and feature_value == 1:
                    follower_count = features.get('follower_count', 0)
                    media_count = features.get('media_count', 0)
                    
                    # If it's a large account with many posts, don't penalize missing engagement
                    if follower_count > 10000 and media_count > 100:
                        continue  # Skip this feature
                
                score += feature_value * weight
        
        # Normalize to 0-100
        normalized_score = (score / max_score) * 100
        return max(0, min(100, normalized_score))
    
    def score_accounts(self, feature_df):
        """Score all accounts in feature dataframe"""
        if self.method == 'weighted_rules':
            scores = feature_df.apply(
                lambda row: self.calculate_rule_based_score(row.to_dict()), 
                axis=1
            )
            return scores
        
        elif self.method in ['random_forest', 'gradient_boosting']:
            if self.model is None:
                raise ValueError("Model not trained. Call train_model() first.")
            
            # Predict probabilities
            probs = self.model.predict_proba(feature_df)
            # Return probability of bot class (assuming class 1 is bot)
            return probs[:, 1] * 100
        
        else:
            raise ValueError(f"Unknown method: {self.method}")
    
    def train_model(self, X_train, y_train):
        """Train ML classifier"""
        if self.method == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
        elif self.method == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        else:
            raise ValueError("train_model() only works with ML methods")
        
        # Handle missing values
        X_train_clean = X_train.fillna(0)
        
        self.model.fit(X_train_clean, y_train)
        return self.model
    
    def evaluate_model(self, X_test, y_test):
        """Evaluate trained model"""
        if self.model is None:
            raise ValueError("Model not trained")
        
        X_test_clean = X_test.fillna(0)
        
        y_pred = self.model.predict(X_test_clean)
        y_pred_proba = self.model.predict_proba(X_test_clean)[:, 1]
        
        print("Classification Report:")
        print(classification_report(y_test, y_pred, target_names=['Real', 'Bot']))
        
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        print(f"\nROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")
        
        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            feature_importance = pd.DataFrame({
                'feature': X_test.columns,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print("\nTop 10 Most Important Features:")
            print(feature_importance.head(10))
        
        return {
            'predictions': y_pred,
            'probabilities': y_pred_proba,
            'roc_auc': roc_auc_score(y_test, y_pred_proba)
        }
    
    def classify_account(self, score, threshold_bot=70, threshold_real=30):
        """
        Classify account based on score
        Returns: 'bot', 'real', or 'inconclusive'
        """
        if score >= threshold_bot:
            return 'bot'
        elif score <= threshold_real:
            return 'real'
        else:
            return 'inconclusive'
