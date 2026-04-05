"""
Direct account testing - Enter data and get instant results
No scraping needed, just manual input
"""

from test_real_accounts import RealAccountTester
import sys

def test_account_direct():
    """Test account with direct data entry"""
    
    print("\n" + "="*70)
    print("DIRECT ACCOUNT TESTING")
    print("="*70)
    print("\nEnter Instagram account details:")
    print("-"*70)
    
    # Get username
    username = input("\nUsername (without @): ").strip()
    if not username:
        print("❌ Username required")
        return
    
    print(f"\nEnter data for @{username}:")
    print("(Visit instagram.com/{} to get this info)\n".format(username))
    
    try:
        # Get account data
        follower_count = int(input("Follower count: "))
        following_count = int(input("Following count: "))
        media_count = int(input("Number of posts: "))
        bio_length = int(input("Bio length (character count): "))
        has_profile_pic = int(input("Has profile picture? (1=Yes, 0=No): "))
        is_private = int(input("Is private account? (1=Yes, 0=No): "))
        
        # Optional engagement data
        print("\n--- Optional (press Enter to skip) ---")
        avg_likes_input = input("Average likes per post (optional): ").strip()
        avg_comments_input = input("Average comments per post (optional): ").strip()
        avg_hashtags_input = input("Average hashtags per post (optional): ").strip()
        
        # Build account data
        account_data = {
            'username': username,
            'user_follower_count': follower_count,
            'user_following_count': following_count,
            'user_media_count': media_count,
            'user_biography_length': bio_length,
            'user_has_profil_pic': has_profile_pic,
            'user_is_private': is_private,
            'username_length': len(username),
            'username_digit_count': sum(c.isdigit() for c in username),
            'user_has_external_url': 0
        }
        
        # Add optional engagement data
        if avg_likes_input:
            avg_likes = int(avg_likes_input)
            account_data['media_like_numbers'] = [avg_likes] * min(media_count, 10)
        
        if avg_comments_input:
            avg_comments = int(avg_comments_input)
            account_data['media_comment_numbers'] = [avg_comments] * min(media_count, 10)
        
        if avg_hashtags_input:
            avg_hashtags = int(avg_hashtags_input)
            account_data['media_hashtag_numbers'] = [avg_hashtags] * min(media_count, 10)
        
        # Choose scoring method
        print("\n" + "-"*70)
        print("Scoring method:")
        print("  1. Rule-based (fast)")
        print("  2. Gradient Boosting (ML, more accurate)")
        
        method_choice = input("\nSelect (1 or 2, default=1): ").strip()
        scoring_method = 'gradient_boosting' if method_choice == '2' else 'weighted_rules'
        
        # Initialize tester
        print("\n" + "="*70)
        print("ANALYZING ACCOUNT")
        print("="*70)
        
        tester = RealAccountTester(scoring_method=scoring_method)
        
        # Test account
        result = tester.test_single_account(account_data)
        
        # Additional recommendations
        print("\n" + "="*70)
        print("RECOMMENDATIONS")
        print("="*70)
        
        score = result['bot_score']
        classification = result['classification']
        
        if classification == 'bot':
            print("\n🚫 HIGH RISK - This account shows strong bot indicators:")
            features = result['features']
            
            if features.get('suspicious_follower_ratio', 0) == 1:
                print("  • Very low follower/following ratio")
            if features.get('no_profile_pic', 0) == 1:
                print("  • No profile picture")
            if features.get('no_bio', 0) == 1:
                print("  • Empty biography")
            if features.get('high_digit_username', 0) == 1:
                print("  • Username contains many digits")
            if features.get('low_engagement', 0) == 1:
                print("  • Very low engagement rate")
            if features.get('high_following', 0) == 1:
                print("  • Following too many accounts")
            
            print("\n  Recommendation: Likely a bot or fake account")
            
        elif classification == 'inconclusive':
            print("\n⚠️  MEDIUM RISK - Manual review recommended:")
            print(f"  • Bot score: {score:.2f}/100 (borderline)")
            print("  • Some bot indicators present")
            print("  • Could be a new account or inactive user")
            print("\n  Recommendation: Review account activity manually")
            
        else:
            print("\n✅ LOW RISK - This account appears legitimate:")
            features = result['features']
            
            if features.get('has_profile_pic', 0) == 1:
                print("  • Has profile picture")
            if features.get('bio_length', 0) > 20:
                print("  • Has biography")
            if features.get('follower_following_ratio', 0) > 0.5:
                print("  • Healthy follower/following ratio")
            if features.get('engagement_rate', 0) > 2:
                print("  • Good engagement rate")
            
            print("\n  Recommendation: Likely a real account")
        
        # Save option
        print("\n" + "-"*70)
        save = input("Save results to JSON? (y/n): ").strip().lower()
        
        if save == 'y':
            import json
            output = {
                'username': username,
                'bot_score': float(score),
                'classification': classification,
                'account_data': account_data
            }
            
            filename = f"{username}_analysis.json"
            with open(filename, 'w') as f:
                json.dump(output, f, indent=2)
            
            print(f"✅ Saved to: {filename}")
        
        print("\n" + "="*70)
        print("ANALYSIS COMPLETE")
        print("="*70)
        
    except ValueError as e:
        print(f"\n❌ Error: Invalid input - {e}")
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print("""
Direct Account Testing Tool

Usage:
  python test_account_direct.py

This script will prompt you to enter Instagram account details manually.
No API or scraping required - just visit the Instagram profile and 
enter the information you see.

Required Information:
  - Username
  - Follower count
  - Following count
  - Number of posts
  - Bio length (character count)
  - Has profile picture (yes/no)
  - Is private account (yes/no)

Optional Information (for better accuracy):
  - Average likes per post
  - Average comments per post
  - Average hashtags per post

Example:
  Username: cristiano
  Follower count: 500000000
  Following count: 500
  Number of posts: 3500
  Bio length: 120
  Has profile picture: 1
  Is private: 0
        """)
    else:
        test_account_direct()
