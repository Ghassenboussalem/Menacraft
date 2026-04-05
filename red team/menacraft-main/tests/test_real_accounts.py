"""
Test the bot detection pipeline on real Instagram accounts
"""

import json
import pandas as pd
from bot_detection_pipeline import InstagramBotDetectionPipeline
from feature_extraction import FeatureExtractor
from scoring_engine import BotScoringEngine

class RealAccountTester:
    """Test bot detection on real Instagram accounts"""
    
    def __init__(self, scoring_method='weighted_rules'):
        self.pipeline = InstagramBotDetectionPipeline(scoring_method=scoring_method)
        
        # Train the model on existing dataset
        print("Training model on InstaFake dataset...")
        self.pipeline.load_data("data", "automated-v1.0")
        self.pipeline.extract_features()
        
        if scoring_method != 'weighted_rules':
            self.pipeline.train_ml_model(test_size=0.2)
        else:
            self.pipeline.calculate_scores()
        
        print("Model ready!\n")
    
    def test_single_account(self, account_data):
        """
        Test a single account
        
        account_data format:
        {
            'username': 'example_user',
            'user_follower_count': 1000,
            'user_following_count': 500,
            'user_media_count': 50,
            'user_biography_length': 100,
            'user_has_profil_pic': 1,
            'user_is_private': 0,
            'username_length': 12,
            'username_digit_count': 2,
            # Optional fields for more accuracy:
            'media_like_numbers': [100, 150, 200, ...],
            'media_comment_numbers': [5, 10, 8, ...],
            'media_hashtag_numbers': [10, 15, 20, ...],
            'media_upload_times': [1234567890, 1234567900, ...],
            'media_has_location_info': [1, 0, 1, ...],
            'user_has_external_url': 1
        }
        """
        # Extract features
        features = self.pipeline.feature_extractor.extract_all_features(account_data)
        features_df = pd.DataFrame([features])
        
        # Calculate score
        score = self.pipeline.scoring_engine.score_accounts(features_df)
        if not isinstance(score, pd.Series):
            score = pd.Series(score)
        
        bot_score = score.iloc[0]
        
        # Classify
        classification = self.pipeline.scoring_engine.classify_account(bot_score)
        
        # Print results
        username = account_data.get('username', 'Unknown')
        print(f"\n{'='*60}")
        print(f"Account: @{username}")
        print(f"{'='*60}")
        print(f"Bot Score: {bot_score:.2f}/100")
        print(f"Classification: {classification.upper()}")
        
        if classification == 'bot':
            print("⚠️  HIGH RISK - Likely a bot/fake account")
        elif classification == 'inconclusive':
            print("⚠️  MEDIUM RISK - Needs human review")
        else:
            print("✅ LOW RISK - Likely a real account")
        
        # Show key indicators
        print(f"\nKey Indicators:")
        print(f"  Followers: {account_data.get('user_follower_count', 'N/A')}")
        print(f"  Following: {account_data.get('user_following_count', 'N/A')}")
        print(f"  Posts: {account_data.get('user_media_count', 'N/A')}")
        print(f"  Follower/Following Ratio: {features.get('follower_following_ratio', 0):.2f}")
        print(f"  Has Profile Pic: {'Yes' if account_data.get('user_has_profil_pic', 0) else 'No'}")
        print(f"  Bio Length: {account_data.get('user_biography_length', 0)} chars")
        print(f"  Engagement Rate: {features.get('engagement_rate', 0):.2f}%")
        
        return {
            'username': username,
            'bot_score': bot_score,
            'classification': classification,
            'features': features
        }
    
    def test_from_json(self, json_file):
        """Test accounts from a JSON file"""
        with open(json_file, 'r') as f:
            accounts = json.load(f)
        
        if not isinstance(accounts, list):
            accounts = [accounts]
        
        results = []
        for account in accounts:
            result = self.test_single_account(account)
            results.append(result)
        
        # Summary
        print(f"\n{'='*60}")
        print(f"SUMMARY: Tested {len(results)} accounts")
        print(f"{'='*60}")
        
        classifications = [r['classification'] for r in results]
        print(f"Real: {classifications.count('real')}")
        print(f"Inconclusive: {classifications.count('inconclusive')}")
        print(f"Bot: {classifications.count('bot')}")
        
        return results
    
    def test_batch(self, accounts_list):
        """Test multiple accounts from a list"""
        results = []
        for account in accounts_list:
            result = self.test_single_account(account)
            results.append(result)
        
        return results


def interactive_test():
    """Interactive mode - enter account data manually"""
    print("\n" + "="*60)
    print("INTERACTIVE ACCOUNT TESTING")
    print("="*60)
    
    # Initialize tester
    tester = RealAccountTester(scoring_method='gradient_boosting')
    
    while True:
        print("\n" + "-"*60)
        print("Enter account details (or 'quit' to exit):")
        print("-"*60)
        
        username = input("Username: ").strip()
        if username.lower() == 'quit':
            break
        
        try:
            follower_count = int(input("Follower count: "))
            following_count = int(input("Following count: "))
            media_count = int(input("Number of posts: "))
            bio_length = int(input("Bio length (characters): "))
            has_profile_pic = int(input("Has profile picture? (1=Yes, 0=No): "))
            is_private = int(input("Is private account? (1=Yes, 0=No): "))
            username_digits = sum(c.isdigit() for c in username)
            
            account_data = {
                'username': username,
                'user_follower_count': follower_count,
                'user_following_count': following_count,
                'user_media_count': media_count,
                'user_biography_length': bio_length,
                'user_has_profil_pic': has_profile_pic,
                'user_is_private': is_private,
                'username_length': len(username),
                'username_digit_count': username_digits
            }
            
            # Optional: Add engagement data
            add_engagement = input("\nAdd engagement data? (y/n): ").lower()
            if add_engagement == 'y':
                avg_likes = int(input("Average likes per post: "))
                avg_comments = int(input("Average comments per post: "))
                
                # Simulate engagement data
                account_data['media_like_numbers'] = [avg_likes] * min(media_count, 10)
                account_data['media_comment_numbers'] = [avg_comments] * min(media_count, 10)
            
            tester.test_single_account(account_data)
            
        except ValueError as e:
            print(f"Error: Invalid input - {e}")
        except KeyboardInterrupt:
            print("\nExiting...")
            break


def example_tests():
    """Run example tests with sample accounts"""
    print("\n" + "="*60)
    print("EXAMPLE TESTS")
    print("="*60)
    
    # Initialize tester
    tester = RealAccountTester(scoring_method='gradient_boosting')
    
    # Example 1: Suspicious account (bot-like)
    suspicious_account = {
        'username': 'user12345678',
        'user_follower_count': 50,
        'user_following_count': 5000,
        'user_media_count': 2,
        'user_biography_length': 0,
        'user_has_profil_pic': 0,
        'user_is_private': 0,
        'username_length': 12,
        'username_digit_count': 8,
        'media_like_numbers': [5, 3],
        'media_comment_numbers': [0, 0]
    }
    
    # Example 2: Normal account
    normal_account = {
        'username': 'john_doe',
        'user_follower_count': 500,
        'user_following_count': 400,
        'user_media_count': 150,
        'user_biography_length': 80,
        'user_has_profil_pic': 1,
        'user_is_private': 0,
        'username_length': 8,
        'username_digit_count': 0,
        'media_like_numbers': [100, 120, 95, 110, 105],
        'media_comment_numbers': [5, 8, 3, 6, 4]
    }
    
    # Example 3: Influencer account
    influencer_account = {
        'username': 'travel_blogger',
        'user_follower_count': 50000,
        'user_following_count': 1000,
        'user_media_count': 500,
        'user_biography_length': 150,
        'user_has_profil_pic': 1,
        'user_is_private': 0,
        'username_length': 14,
        'username_digit_count': 0,
        'media_like_numbers': [2000, 2500, 1800, 2200, 2100],
        'media_comment_numbers': [50, 60, 45, 55, 52]
    }
    
    print("\n--- Test 1: Suspicious Account ---")
    tester.test_single_account(suspicious_account)
    
    print("\n--- Test 2: Normal Account ---")
    tester.test_single_account(normal_account)
    
    print("\n--- Test 3: Influencer Account ---")
    tester.test_single_account(influencer_account)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test from JSON file
        json_file = sys.argv[1]
        print(f"Testing accounts from: {json_file}")
        tester = RealAccountTester(scoring_method='gradient_boosting')
        tester.test_from_json(json_file)
    else:
        # Show menu
        print("\n" + "#"*60)
        print("# INSTAGRAM BOT DETECTION - REAL ACCOUNT TESTER")
        print("#"*60)
        print("\nOptions:")
        print("1. Run example tests")
        print("2. Interactive mode (enter account data manually)")
        print("3. Test from JSON file")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == '1':
            example_tests()
        elif choice == '2':
            interactive_test()
        elif choice == '3':
            json_file = input("Enter JSON file path: ").strip()
            tester = RealAccountTester(scoring_method='gradient_boosting')
            tester.test_from_json(json_file)
        else:
            print("Invalid option")
