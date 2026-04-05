# Instagram Bot Detection Pipeline

A complete 5-stage pipeline for detecting fake and automated Instagram accounts using the InstaFake dataset.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    STAGE 1: DATA COLLECTION                     │
│  Instagram Graph API / Public Scraping / InstaFake Dataset     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  STAGE 2: FEATURE EXTRACTION                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Profile    │  │   Activity   │  │  Engagement  │         │
│  │   Signals    │  │   Signals    │  │   Signals    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐                                               │
│  │   Content    │                                               │
│  │   Signals    │                                               │
│  └──────────────┘                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   STAGE 3: SCORING ENGINE                       │
│  Rule-Based Weights  OR  ML Classifier (RF/GBM)                │
│  → Bot Probability Score (0-100)                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  STAGE 4: NETWORK ANALYSIS                      │
│  Community Detection → Bot Farm Identification                  │
│  Network Context → Score Adjustment                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                STAGE 5: FINAL CLASSIFICATION                    │
│  Real (0-30) | Inconclusive (30-70) | Bot (70-100)            │
│  → Inconclusive cases queued for human review                  │
└─────────────────────────────────────────────────────────────────┘
```

## Features Extracted

### Profile Signals
- Username entropy (randomness)
- Username digit ratio
- Profile picture presence
- Biography length
- Account privacy status

### Activity Signals
- Posting frequency patterns
- Post interval regularity (bot detection)
- Burst posting behavior
- Account age

### Engagement Signals
- Follower/following ratio
- Engagement rate (likes per follower)
- Average likes and comments per post
- Suspicious follower patterns

### Content Signals
- Hashtag usage patterns
- Location tagging frequency
- External URL presence
- Content repetition indicators

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from bot_detection_pipeline import InstagramBotDetectionPipeline

# Initialize pipeline
pipeline = InstagramBotDetectionPipeline(scoring_method='weighted_rules')

# Run complete pipeline
results = pipeline.run_full_pipeline(
    dataset_path="data",
    dataset_version="fake-v1.0"
)

# View results
print(results.head())
```

### Run Demo

```bash
python demo.py
```

## Scoring Methods

### 1. Rule-Based Scoring (Default)
Weighted combination of features with expert-defined weights:

```python
pipeline = InstagramBotDetectionPipeline(scoring_method='weighted_rules')
```

**Advantages:**
- No training required
- Interpretable
- Fast
- Works with small datasets

### 2. Random Forest Classifier

```python
pipeline = InstagramBotDetectionPipeline(scoring_method='random_forest')
```

**Advantages:**
- Handles non-linear relationships
- Feature importance analysis
- Robust to outliers

### 3. Gradient Boosting Classifier

```python
pipeline = InstagramBotDetectionPipeline(scoring_method='gradient_boosting')
```

**Advantages:**
- High accuracy
- Handles complex patterns
- Good generalization

## Advanced Usage

### Step-by-Step Pipeline Execution

```python
from bot_detection_pipeline import InstagramBotDetectionPipeline

pipeline = InstagramBotDetectionPipeline(scoring_method='random_forest')

# Stage 1: Load data
pipeline.load_data("data", "fake-v1.0")

# Stage 2: Extract features
features = pipeline.extract_features()
print(f"Extracted {len(features.columns)} features")

# Stage 3: Train and score
pipeline.train_ml_model(test_size=0.2)
scores = pipeline.calculate_scores()

# Stage 4: Network analysis (optional)
# follower_data = [(account_id, follower_id), ...]
# pipeline.analyze_network(follower_data, use_network_adjustment=True)

# Stage 5: Classify
classifications = pipeline.classify_accounts(
    threshold_bot=70,
    threshold_real=30
)

# Evaluate
pipeline.evaluate_performance()

# Get results
results = pipeline.get_results_dataframe()
```

### Custom Feature Extraction

```python
from feature_extraction import FeatureExtractor

extractor = FeatureExtractor()

# Extract features for single account
account_data = {
    'username_length': 15,
    'username_digit_count': 5,
    'user_follower_count': 100,
    'user_following_count': 5000,
    # ... more fields
}

features = extractor.extract_all_features(account_data)
print(features)
```

### Network Analysis

```python
from network_analysis import NetworkAnalyzer

analyzer = NetworkAnalyzer()

# Build follower network
follower_relationships = [
    (1, 2), (1, 3), (2, 3), (4, 5), (4, 6)
]
analyzer.build_follower_network(follower_relationships)

# Detect bot clusters
bot_scores = {1: 85, 2: 90, 3: 88, 4: 25, 5: 30, 6: 28}
clusters = analyzer.detect_bot_clusters(bot_scores, threshold=55)

print(f"Found {len(clusters)} suspicious clusters")
```

## Dataset Structure

### Fake Account Dataset
- `user_media_count`: Total posts
- `user_follower_count`: Total followers
- `user_following_count`: Total following
- `user_has_profil_pic`: Has profile picture (0/1)
- `user_is_private`: Private account (0/1)
- `user_biography_length`: Bio character count
- `username_length`: Username character count
- `username_digit_count`: Digits in username
- `is_fake`: Ground truth label (0=real, 1=fake)

### Automated Account Dataset
All fake dataset features plus:
- `media_like_numbers`: List of likes per post
- `media_comment_numbers`: List of comments per post
- `media_hashtag_numbers`: List of hashtags per post
- `media_upload_times`: List of post timestamps
- `media_has_location_info`: Location tags per post
- `automated_behaviour`: Ground truth label (0=real, 1=bot)

## Performance Metrics

The pipeline evaluates performance using:
- **Accuracy**: Overall correctness
- **Precision**: Bot predictions that are correct
- **Recall**: Actual bots that are detected
- **F1-Score**: Harmonic mean of precision and recall
- **ROC-AUC**: Area under ROC curve (ML models)

## Classification Thresholds

Adjust thresholds based on your use case:

```python
# Conservative (fewer false positives)
pipeline.classify_accounts(threshold_bot=80, threshold_real=20)

# Aggressive (catch more bots, more false positives)
pipeline.classify_accounts(threshold_bot=60, threshold_real=40)

# Balanced (default)
pipeline.classify_accounts(threshold_bot=70, threshold_real=30)
```

## Inconclusive Cases

Accounts scoring between thresholds are marked "inconclusive" and should be:
1. Queued for human review
2. Used to generate labeled training data
3. Fed back into model retraining

```python
results = pipeline.get_results_dataframe()
inconclusive = results[results['classification'] == 'inconclusive']
print(f"{len(inconclusive)} accounts need human review")
```

## Citation

If you use this pipeline or the InstaFake dataset, please cite:

```
@article{akyon2019instagram,
  title={Instagram Fake and Automated Account Detection},
  author={Akyon, Fatih Cagatay and Kalfaoglu, Esat},
  journal={arXiv preprint arXiv:1910.03090},
  year={2019}
}
```

## License

This implementation is provided for research and educational purposes.
The InstaFake dataset is licensed under CC BY-NC 4.0.

## References

- [InstaFake Dataset Paper](https://arxiv.org/pdf/1910.03090.pdf)
- [InstaFake GitHub Repository](https://github.com/fcakyon/instafake-dataset)
