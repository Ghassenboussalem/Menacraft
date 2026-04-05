"""
Test the FACTS Instagram account with our bot detection model
"""
from feature_extraction import FeatureExtractor
from scoring_engine import BotScoringEngine

# Account data from the provided input
account_data = {
    # Profile data
    'username': 'FACTS',
    'username_length': 5,
    'username_digit_count': 0,
    'user_has_profile_pic': 1,  # Assuming yes (not explicitly stated)
    'user_biography_length': 106,
    'user_is_private': 0,  # No
    
    # Follower/Following data
    'user_follower_count': 1000000,  # 1M followers
    'user_following_count': 24,
    'user_media_count': 6012,  # Posts
    
    # Post data from the sample
    'media_like_numbers': [22000],  # 22K likes on the sample post
    'media_comment_numbers': [160],  # 160 comments
    'media_hashtag_numbers': [8],  # 8 hashtags in the sample
    
    # Additional fields (not provided, using defaults)
    'user_has_external_url': 0,
    'media_upload_times': [],  # No timestamp data
    'mediaHasLocationInfo': []
}

# Initialize feature extractor and scoring engine
extractor = FeatureExtractor()
scorer = BotScoringEngine(method='weighted_rules')

# Extract features
print("="*60)
print("BOT DETECTION ANALYSIS: @FACTS")
print("="*60)
print("\nAccount Overview:")
print(f"  Username: FACTS")
print(f"  Followers: 1,000,000")
print(f"  Following: 24")
print(f"  Posts: 6,012")
print(f"  Bio length: 106 chars")
print(f"  Private: No")

print("\n" + "-"*60)
print("FEATURE EXTRACTION")
print("-"*60)

# Extract all features
features = extractor.extract_all_features(account_data)

# Display features by category
print("\n1. PROFILE SIGNALS:")
profile_features = {
    'username_length': features['username_length'],
    'username_digit_ratio': features['username_digit_ratio'],
    'has_profile_pic': features['has_profile_pic'],
    'bio_length': features['bio_length'],
    'is_private': features['is_private'],
    'no_bio': features['no_bio'],
    'no_profile_pic': features['no_profile_pic'],
    'high_digit_username': features['high_digit_username']
}
for key, value in profile_features.items():
    print(f"  {key}: {value}")

print("\n2. ACTIVITY SIGNALS:")
activity_features = {
    'media_count': features['media_count'],
    'avg_post_interval': features['avg_post_interval'],
    'std_post_interval': features['std_post_interval'],
    'post_interval_regularity': features['post_interval_regularity'],
    'burst_posts': features['burst_posts']
}
for key, value in activity_features.items():
    print(f"  {key}: {value}")

print("\n3. ENGAGEMENT SIGNALS:")
engagement_features = {
    'follower_count': features['follower_count'],
    'following_count': features['following_count'],
    'follower_following_ratio': features['follower_following_ratio'],
    'avg_likes_per_post': features['avg_likes_per_post'],
    'engagement_rate': features['engagement_rate'],
    'avg_comments_per_post': features['avg_comments_per_post'],
    'low_engagement': features['low_engagement'],
    'suspicious_follower_ratio': features['suspicious_follower_ratio'],
    'high_following': features['high_following']
}
for key, value in engagement_features.items():
    print(f"  {key}: {value}")

print("\n4. CONTENT SIGNALS:")
content_features = {
    'avg_hashtags_per_post': features['avg_hashtags_per_post'],
    'max_hashtags': features['max_hashtags'],
    'excessive_hashtags': features['excessive_hashtags'],
    'location_usage_rate': features['location_usage_rate'],
    'has_external_url': features['has_external_url']
}
for key, value in content_features.items():
    print(f"  {key}: {value}")

print("\n" + "-"*60)
print("SCORING & CLASSIFICATION")
print("-"*60)

# Calculate bot score
bot_score = scorer.calculate_rule_based_score(features)
classification = scorer.classify_account(bot_score, threshold_bot=70, threshold_real=30)

print(f"\nBot Probability Score: {bot_score:.2f}/100")
print(f"Classification: {classification.upper()}")

# Detailed analysis
print("\n" + "-"*60)
print("DETAILED ANALYSIS")
print("-"*60)

print("\nPositive Indicators (Real Account):")
positive_indicators = []

if features['follower_following_ratio'] > 10:
    positive_indicators.append(f"  ✓ Excellent follower/following ratio: {features['follower_following_ratio']:.1f}:1")
    
if features['has_profile_pic'] == 1:
    positive_indicators.append("  ✓ Has profile picture")
    
if features['bio_length'] > 50:
    positive_indicators.append(f"  ✓ Substantial bio ({features['bio_length']} chars)")
    
if features['engagement_rate'] > 1:
    positive_indicators.append(f"  ✓ Good engagement rate: {features['engagement_rate']:.2f}%")
    
if features['media_count'] > 1000:
    positive_indicators.append(f"  ✓ Extensive posting history: {features['media_count']} posts")
    
if features['username_digit_ratio'] == 0:
    positive_indicators.append("  ✓ Clean username (no random digits)")

if positive_indicators:
    for indicator in positive_indicators:
        print(indicator)
else:
    print("  None detected")

print("\nNegative Indicators (Bot-like Behavior):")
negative_indicators = []

if features['no_profile_pic'] == 1:
    negative_indicators.append("  ✗ No profile picture")
    
if features['no_bio'] == 1:
    negative_indicators.append("  ✗ No bio")
    
if features['high_digit_username'] == 1:
    negative_indicators.append("  ✗ Username has many digits")
    
if features['suspicious_follower_ratio'] == 1:
    negative_indicators.append("  ✗ Suspicious follower/following ratio")
    
if features['high_following'] == 1:
    negative_indicators.append("  ✗ Following too many accounts")
    
if features['low_engagement'] == 1:
    negative_indicators.append(f"  ✗ Low engagement rate: {features['engagement_rate']:.2f}%")
    
if features['excessive_hashtags'] == 1:
    negative_indicators.append(f"  ✗ Excessive hashtag usage: {features['avg_hashtags_per_post']:.1f} per post")

if negative_indicators:
    for indicator in negative_indicators:
        print(indicator)
else:
    print("  None detected")

print("\n" + "="*60)
print("CONCLUSION")
print("="*60)

if classification == 'real':
    print("\n✓ This account appears to be LEGITIMATE")
    print("  The account shows strong indicators of authentic human behavior.")
elif classification == 'bot':
    print("\n✗ This account appears to be a BOT")
    print("  The account shows multiple red flags consistent with automated behavior.")
else:
    print("\n? This account is INCONCLUSIVE")
    print("  The account shows mixed signals. Manual review recommended.")

print("\n")
