"""
Test bot detection on pubity Instagram account
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feature_extraction import FeatureExtractor
from scoring_engine import BotScoringEngine

def test_pubity_account():
    """Test the pubity account from scraped post data"""
    
    # Scraped data from pubity post
    post_data = {
        "idx": 5,
        "id": "d14491d4-d043-4bf8-be91-dfe95ffac3b2",
        "post_url": "https://www.instagram.com/p/DWrti9ckVC8/",
        "username": "lovable.dev",
        "caption": "With @lovable.dev at 89 years old, this grandfather is doing what most people half his age still haven't, building apps from scratch.\n\nNo coding background. No tech career. No years spent learning how to program. Just an idea, some curiosity, and AI tools like Lovable. He's already vibe-coded two apps, showing how fast things are changing and how accessible building has become.\n\nThis is what the new era looks like. You don't need to \"learn to code\" the traditional way anymore, you just need to know what you want to create. The barrier isn't skill, it's mindset. And if an 89-year-old can start building, there's really no excuse left.\n\n#Pubity #Viralmoments #tech #Lovablepartner",
        "likes_count": "14K",
        "comments_count": ",109",
        "image_url": "https://scontent.cdninstagram.com/v/t51.82787-15/659795531_18593732317044850_6952351124444828230_n.jpg",
        "post_date": "2026-04-03 20:30:05+00",
        "hashtags": ["#Pubity", "#Viralmoments", "#tech", "#Lovablepartner"],
        "post_type": "image"
    }
    
    # Convert to account data format for analysis
    # Note: We need to estimate some values since we only have one post
    account_data = {
        'username': post_data['username'],
        'username_length': len(post_data['username']),
        'username_digit_count': sum(c.isdigit() for c in post_data['username']),
        
        # Estimated values (would need full profile scrape for accurate data)
        'user_follower_count': 50000,  # Estimated based on 14K likes
        'user_following_count': 500,   # Estimated reasonable following
        'user_media_count': 100,       # Estimated posts
        'user_biography_length': 150,  # Estimated bio length
        'user_has_profile_pic': 1,     # Assumed yes
        'user_is_private': 0,          # Public account
        
        # From post data
        'media_like_numbers': [14000],  # 14K likes
        'media_comment_numbers': [109], # 109 comments
        'media_hashtag_numbers': [4],   # 4 hashtags
        'media_upload_times': [post_data['post_date']],
        'mediaHasLocationInfo': [0],    # No location in this post
    }
    
    print("="*70)
    print("TESTING PUBITY ACCOUNT (@lovable.dev)")
    print("="*70)
    print(f"\nPost URL: {post_data['post_url']}")
    print(f"Username: {post_data['username']}")
    print(f"Likes: {post_data['likes_count']}")
    print(f"Comments: {post_data['comments_count']}")
    print(f"Hashtags: {', '.join(post_data['hashtags'])}")
    
    # Extract features
    print("\n" + "-"*70)
    print("FEATURE EXTRACTION")
    print("-"*70)
    
    extractor = FeatureExtractor()
    features = extractor.extract_all_features(account_data)
    
    print("\nExtracted Features:")
    for feature_name, value in features.items():
        print(f"  {feature_name}: {value:.4f}" if isinstance(value, float) else f"  {feature_name}: {value}")
    
    # Calculate bot score
    print("\n" + "-"*70)
    print("BOT DETECTION ANALYSIS")
    print("-"*70)
    
    scorer = BotScoringEngine(method='weighted_rules')
    score = scorer.calculate_rule_based_score(features)
    classification = scorer.classify_account(score)
    
    print(f"\nBot Score: {score:.2f}/100")
    print(f"Classification: {classification.upper()}")
    
    # Detailed breakdown
    print("\n" + "-"*70)
    print("SCORE BREAKDOWN")
    print("-"*70)
    
    breakdown = {
        'Username Analysis': {
            'Length': features['username_length'],
            'Digit Ratio': f"{features['username_digit_ratio']:.2f}",
            'High Digit Username': 'Yes' if features['high_digit_username'] else 'No'
        },
        'Profile Signals': {
            'Has Profile Pic': 'Yes' if features['has_profile_pic'] else 'No',
            'Bio Length': features['bio_length'],
            'Is Private': 'Yes' if features['is_private'] else 'No'
        },
        'Engagement Metrics': {
            'Follower/Following Ratio': f"{features['follower_following_ratio']:.2f}",
            'Following Count': account_data['user_following_count'],
            'Avg Likes': f"{features['avg_likes']:.0f}",
            'Avg Comments': f"{features['avg_comments']:.0f}",
            'Engagement Rate': f"{features['engagement_rate']:.4f}"
        },
        'Content Signals': {
            'Avg Hashtags': f"{features['avg_hashtags_per_post']:.1f}",
            'Location Usage Rate': f"{features['location_usage_rate']:.2f}",
            'Has External URL': 'Yes' if features['has_external_url'] else 'No'
        }
    }
    
    for category, metrics in breakdown.items():
        print(f"\n{category}:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value}")
    
    # Final verdict
    print("\n" + "="*70)
    print("FINAL VERDICT")
    print("="*70)
    
    if classification == 'real':
        print("✓ This account appears to be REAL/HUMAN")
        print("  The account shows normal human behavior patterns.")
    elif classification == 'bot':
        print("✗ This account appears to be a BOT/FAKE")
        print("  The account shows suspicious automated behavior.")
    else:
        print("? This account is INCONCLUSIVE")
        print("  Manual review recommended for final determination.")
    
    print(f"\nConfidence: {abs(score - 50) * 2:.1f}%")
    print("="*70)
    
    return {
        'username': post_data['username'],
        'score': score,
        'classification': classification,
        'features': features
    }

if __name__ == '__main__':
    result = test_pubity_account()
