"""
Compare the three detection methods on sample data
"""
import pandas as pd
from feature_extraction import FeatureExtractor
from scoring_engine import BotScoringEngine

# Sample accounts for comparison
accounts = [
    {
        'name': '@FACTS (Real Creator)',
        'data': {
            'username': 'FACTS',
            'username_length': 5,
            'username_digit_count': 0,
            'user_has_profile_pic': 1,
            'user_biography_length': 106,
            'user_is_private': 0,
            'user_follower_count': 1000000,
            'user_following_count': 24,
            'user_media_count': 6012,
            'media_like_numbers': [22000],
            'media_comment_numbers': [160],
            'media_hashtag_numbers': [8],
            'user_has_external_url': 0,
            'media_upload_times': [],
            'mediaHasLocationInfo': []
        }
    },
    {
        'name': '@user847392 (Typical Bot)',
        'data': {
            'username': 'user847392',
            'username_length': 10,
            'username_digit_count': 6,
            'user_has_profile_pic': 0,
            'user_biography_length': 0,
            'user_is_private': 0,
            'user_follower_count': 150,
            'user_following_count': 5000,
            'user_media_count': 50,
            'media_like_numbers': [5, 3, 7, 4, 6],
            'media_comment_numbers': [0, 0, 1, 0, 0],
            'media_hashtag_numbers': [30, 30, 30, 30, 30],
            'user_has_external_url': 0,
            'media_upload_times': [],
            'mediaHasLocationInfo': []
        }
    },
    {
        'name': '@travel_sarah (Real User)',
        'data': {
            'username': 'travel_sarah',
            'username_length': 12,
            'username_digit_count': 0,
            'user_has_profile_pic': 1,
            'user_biography_length': 85,
            'user_is_private': 0,
            'user_follower_count': 2500,
            'user_following_count': 800,
            'user_media_count': 320,
            'media_like_numbers': [150, 200, 180, 220, 190],
            'media_comment_numbers': [12, 15, 10, 18, 14],
            'media_hashtag_numbers': [8, 10, 7, 9, 8],
            'user_has_external_url': 1,
            'media_upload_times': [],
            'mediaHasLocationInfo': [1, 1, 1, 1, 1]
        }
    },
    {
        'name': '@shop_deals99 (Spam Bot)',
        'data': {
            'username': 'shop_deals99',
            'username_length': 13,
            'username_digit_count': 2,
            'user_has_profile_pic': 1,
            'user_biography_length': 45,
            'user_is_private': 0,
            'user_follower_count': 500,
            'user_following_count': 4500,
            'user_media_count': 1200,
            'media_like_numbers': [10, 8, 12, 9, 11],
            'media_comment_numbers': [0, 1, 0, 0, 1],
            'media_hashtag_numbers': [28, 30, 29, 30, 27],
            'user_has_external_url': 1,
            'media_upload_times': [],
            'mediaHasLocationInfo': []
        }
    }
]

print("="*80)
print("BOT DETECTION MODEL COMPARISON")
print("="*80)

extractor = FeatureExtractor()
scorer = BotScoringEngine(method='weighted_rules')

results = []

for account in accounts:
    print(f"\n{'='*80}")
    print(f"Account: {account['name']}")
    print('='*80)
    
    # Extract features
    features = extractor.extract_all_features(account['data'])
    
    # Calculate score
    score = scorer.calculate_rule_based_score(features)
    classification = scorer.classify_account(score)
    
    # Display key metrics
    print(f"\nKey Metrics:")
    print(f"  Followers: {features['follower_count']:,}")
    print(f"  Following: {features['following_count']:,}")
    print(f"  Follower/Following Ratio: {features['follower_following_ratio']:.2f}:1")
    print(f"  Posts: {features['media_count']}")
    print(f"  Engagement Rate: {features['engagement_rate']:.2f}%")
    print(f"  Avg Hashtags: {features['avg_hashtags_per_post']:.1f}")
    
    print(f"\nRed Flags Detected:")
    red_flags = []
    if features['no_profile_pic'] == 1:
        red_flags.append("  ✗ No profile picture")
    if features['no_bio'] == 1:
        red_flags.append("  ✗ No bio")
    if features['high_digit_username'] == 1:
        red_flags.append("  ✗ High digit username")
    if features['suspicious_follower_ratio'] == 1:
        red_flags.append("  ✗ Suspicious follower ratio")
    if features['high_following'] == 1:
        red_flags.append("  ✗ Following too many accounts")
    if features['low_engagement'] == 1:
        red_flags.append("  ✗ Low engagement rate")
    if features['excessive_hashtags'] == 1:
        red_flags.append("  ✗ Excessive hashtag usage")
    
    if red_flags:
        for flag in red_flags:
            print(flag)
    else:
        print("  None")
    
    print(f"\n{'─'*80}")
    print(f"BOT SCORE: {score:.2f}/100")
    print(f"CLASSIFICATION: {classification.upper()}")
    print('─'*80)
    
    results.append({
        'Account': account['name'],
        'Score': score,
        'Classification': classification,
        'Followers': features['follower_count'],
        'Following': features['following_count'],
        'Ratio': features['follower_following_ratio'],
        'Engagement': features['engagement_rate']
    })

# Summary table
print(f"\n\n{'='*80}")
print("SUMMARY TABLE")
print('='*80)

df = pd.DataFrame(results)
print(df.to_string(index=False))

print("\n\nModel Explanation:")
print("-" * 80)
print("RULE-BASED WEIGHTED SCORING (Currently Used)")
print("-" * 80)
print("""
How it works:
1. Extract 24+ features from account data
2. Apply weighted scoring based on feature importance
3. Normalize to 0-100 scale
4. Classify: ≥70 = Bot, ≤30 = Real, else Inconclusive

Key Feature Weights:
  - Suspicious follower ratio: 25 (highest)
  - High following count: 20
  - No profile picture: 20
  - No bio: 15
  - High digit username: 15
  - Excessive hashtags: 12
  - Low engagement: 5

Advantages:
  ✓ Fast (milliseconds per account)
  ✓ Interpretable (can explain every decision)
  ✓ No training required
  ✓ Works immediately on new data

Disadvantages:
  ✗ Fixed rules may miss sophisticated bots
  ✗ Requires manual weight tuning
  ✗ May not adapt to new bot patterns
""")

print("\n" + "-" * 80)
print("MACHINE LEARNING ALTERNATIVES (Optional)")
print("-" * 80)
print("""
1. RANDOM FOREST CLASSIFIER
   - Ensemble of 100 decision trees
   - Each tree votes on classification
   - Handles non-linear relationships
   - Accuracy: ~92-95% with training data
   - Requires labeled dataset for training

2. GRADIENT BOOSTING CLASSIFIER
   - Sequential tree building
   - Each tree corrects previous errors
   - Often highest accuracy
   - Accuracy: ~93-96% with training data
   - Requires labeled dataset for training

To use ML methods:
  1. Load labeled dataset (fake vs real)
  2. Train model: pipeline.train_ml_model()
  3. Model learns optimal feature combinations
  4. Outputs probability scores (0-100%)

Advantages:
  ✓ Higher accuracy potential
  ✓ Learns from data automatically
  ✓ Adapts to new patterns
  ✓ Handles complex feature interactions

Disadvantages:
  ✗ Requires training data
  ✗ Less interpretable
  ✗ May overfit to training data
  ✗ Needs retraining for new bot types
""")

print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)
print("""
Current Setup: Rule-based scoring is EXCELLENT for your use case because:
  ✓ Works immediately without training
  ✓ Transparent and explainable decisions
  ✓ Fast enough for real-time detection
  ✓ Easy to adjust weights based on feedback

Consider ML methods if:
  • You have large labeled dataset (1000+ accounts)
  • You need highest possible accuracy
  • Bot patterns are evolving rapidly
  • You can retrain models regularly
""")

print("\n")
