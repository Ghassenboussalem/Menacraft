import pandas as pd
import numpy as np
from feature_extraction import FeatureExtractor
from scoring_engine import BotScoringEngine
from network_analysis import NetworkAnalyzer
from utils import import_data

class InstagramBotDetectionPipeline:
    """
    Complete 5-stage Instagram bot detection pipeline
    
    Stage 1: Data collection (via Instagram Graph API or dataset)
    Stage 2: Feature extraction (profile, activity, engagement, content signals)
    Stage 3: Scoring engine (rule-based or ML classifier)
    Stage 4: Network analysis (bot farm detection)
    Stage 5: Final classification (real, inconclusive, bot)
    """
    
    def __init__(self, scoring_method='weighted_rules'):
        self.feature_extractor = FeatureExtractor()
        self.scoring_engine = BotScoringEngine(method=scoring_method)
        self.network_analyzer = NetworkAnalyzer()
        
        self.raw_data = None
        self.features = None
        self.scores = None
        self.classifications = None
    
    # ===== STAGE 1: DATA COLLECTION =====
    def load_data(self, dataset_path, dataset_version):
        """Load data from InstaFake dataset"""
        print(f"Stage 1: Loading data from {dataset_path}/{dataset_version}...")
        
        data = import_data(dataset_path, dataset_version)
        self.raw_data = data['dataframe']
        self.dataset_type = data['dataset_type']
        
        print(f"Loaded {len(self.raw_data)} accounts ({self.dataset_type} dataset)")
        return self.raw_data
    
    # ===== STAGE 2: FEATURE EXTRACTION =====
    def extract_features(self):
        """Extract features from raw data"""
        if self.raw_data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        print("\nStage 2: Extracting features...")
        print("  - Profile signals (username, bio, profile pic)")
        print("  - Activity signals (posting patterns, intervals)")
        print("  - Engagement signals (followers, likes, comments)")
        print("  - Content signals (hashtags, location, URLs)")
        
        self.features = self.feature_extractor.extract_features_from_dataframe(self.raw_data)
        
        print(f"Extracted {len(self.features.columns)} features")
        return self.features
    
    # ===== STAGE 3: SCORING ENGINE =====
    def calculate_scores(self):
        """Calculate bot probability scores"""
        if self.features is None:
            raise ValueError("No features extracted. Call extract_features() first.")
        
        print("\nStage 3: Calculating bot probability scores...")
        print(f"  Using method: {self.scoring_engine.method}")
        
        self.scores = self.scoring_engine.score_accounts(self.features)
        
        # Convert to Series if numpy array
        if not isinstance(self.scores, pd.Series):
            self.scores = pd.Series(self.scores)
        
        print(f"  Mean score: {self.scores.mean():.2f}")
        print(f"  Median score: {self.scores.median():.2f}")
        print(f"  Score range: {self.scores.min():.2f} - {self.scores.max():.2f}")
        
        return self.scores
    
    def train_ml_model(self, test_size=0.2):
        """Train ML model if using ML-based scoring"""
        if self.scoring_engine.method == 'weighted_rules':
            print("Skipping training - using rule-based scoring")
            return None
        
        if self.features is None:
            raise ValueError("No features extracted. Call extract_features() first.")
        
        # Get ground truth labels
        if self.dataset_type == 'fake':
            y = self.raw_data['is_fake']
        elif self.dataset_type == 'automated':
            y = self.raw_data['automated_behaviour']
        else:
            raise ValueError(f"Unknown dataset type: {self.dataset_type}")
        
        # Split data
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            self.features, y, test_size=test_size, random_state=42, stratify=y
        )
        
        print(f"\nTraining {self.scoring_engine.method} model...")
        print(f"  Training samples: {len(X_train)}")
        print(f"  Test samples: {len(X_test)}")
        
        self.scoring_engine.train_model(X_train, y_train)
        
        print("\nEvaluating model on test set:")
        results = self.scoring_engine.evaluate_model(X_test, y_test)
        
        return results
    
    # ===== STAGE 4: NETWORK ANALYSIS =====
    def analyze_network(self, follower_data=None, use_network_adjustment=False):
        """
        Perform network analysis for bot farm detection
        
        follower_data: list of (account_id, follower_id) tuples
        If None, skips network analysis
        """
        if follower_data is None:
            print("\nStage 4: Network analysis skipped (no follower data provided)")
            return None
        
        print("\nStage 4: Analyzing follower network...")
        
        # Build network
        self.network_analyzer.build_follower_network(follower_data)
        stats = self.network_analyzer.get_network_statistics()
        
        print(f"  Network nodes: {stats['num_nodes']}")
        print(f"  Network edges: {stats['num_edges']}")
        print(f"  Average degree: {stats['avg_degree']:.2f}")
        
        # Detect bot clusters
        bot_scores_dict = dict(enumerate(self.scores))
        clusters = self.network_analyzer.detect_bot_clusters(bot_scores_dict)
        
        print(f"  Detected {len(clusters)} suspicious clusters")
        
        # Adjust scores with network context if requested
        if use_network_adjustment:
            print("  Adjusting scores with network context...")
            adjusted_scores = []
            for idx, score in enumerate(self.scores):
                adjusted_score, _ = self.network_analyzer.adjust_score_with_network(
                    idx, score, bot_scores_dict
                )
                adjusted_scores.append(adjusted_score)
            
            self.scores = pd.Series(adjusted_scores)
            print(f"  New mean score: {self.scores.mean():.2f}")
        
        return clusters
    
    # ===== STAGE 5: FINAL CLASSIFICATION =====
    def classify_accounts(self, threshold_bot=70, threshold_real=30):
        """Final classification with inconclusive queue"""
        if self.scores is None:
            raise ValueError("No scores calculated. Call calculate_scores() first.")
        
        print("\nStage 5: Final classification...")
        print(f"  Bot threshold: >= {threshold_bot}")
        print(f"  Real threshold: <= {threshold_real}")
        
        self.classifications = self.scores.apply(
            lambda s: self.scoring_engine.classify_account(s, threshold_bot, threshold_real)
        )
        
        # Summary statistics
        class_counts = self.classifications.value_counts()
        print(f"\n  Classification results:")
        for label, count in class_counts.items():
            percentage = (count / len(self.classifications)) * 100
            print(f"    {label.capitalize()}: {count} ({percentage:.1f}%)")
        
        return self.classifications
    
    def get_results_dataframe(self):
        """Get complete results as dataframe"""
        if self.classifications is None:
            raise ValueError("No classifications. Run full pipeline first.")
        
        results = pd.DataFrame({
            'bot_score': self.scores,
            'classification': self.classifications
        })
        
        # Add ground truth if available
        if self.dataset_type == 'fake':
            results['ground_truth'] = self.raw_data['is_fake'].map({0: 'real', 1: 'bot'})
        elif self.dataset_type == 'automated':
            results['ground_truth'] = self.raw_data['automated_behaviour'].map({0: 'real', 1: 'bot'})
        
        return results
    
    def evaluate_performance(self):
        """Evaluate pipeline performance against ground truth"""
        results = self.get_results_dataframe()
        
        if 'ground_truth' not in results.columns:
            print("No ground truth available for evaluation")
            return None
        
        # Filter out inconclusive cases for evaluation
        decisive = results[results['classification'] != 'inconclusive']
        
        if len(decisive) == 0:
            print("No decisive classifications to evaluate")
            return None
        
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        y_true = (decisive['ground_truth'] == 'bot').astype(int)
        y_pred = (decisive['classification'] == 'bot').astype(int)
        
        print("\nPipeline Performance (excluding inconclusive):")
        print(f"  Accuracy:  {accuracy_score(y_true, y_pred):.4f}")
        print(f"  Precision: {precision_score(y_true, y_pred):.4f}")
        print(f"  Recall:    {recall_score(y_true, y_pred):.4f}")
        print(f"  F1-Score:  {f1_score(y_true, y_pred):.4f}")
        
        return {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred),
            'recall': recall_score(y_true, y_pred),
            'f1': f1_score(y_true, y_pred)
        }
    
    def run_full_pipeline(self, dataset_path, dataset_version, 
                         follower_data=None, use_network=False):
        """Run complete pipeline end-to-end"""
        print("="*60)
        print("INSTAGRAM BOT DETECTION PIPELINE")
        print("="*60)
        
        # Stage 1: Load data
        self.load_data(dataset_path, dataset_version)
        
        # Stage 2: Extract features
        self.extract_features()
        
        # Stage 3: Calculate scores
        if self.scoring_engine.method != 'weighted_rules':
            self.train_ml_model()
        
        self.calculate_scores()
        
        # Stage 4: Network analysis (optional)
        if follower_data:
            self.analyze_network(follower_data, use_network)
        
        # Stage 5: Classify
        self.classify_accounts()
        
        # Evaluate
        self.evaluate_performance()
        
        print("\n" + "="*60)
        print("PIPELINE COMPLETE")
        print("="*60)
        
        return self.get_results_dataframe()
