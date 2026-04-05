"""
Analyze Instagram post with account information and bot detection

Usage:
    python analyze_post_with_account.py <json_file>
    
Example:
    python analyze_post_with_account.py lovable_dev_post.json
"""

import json
import sys
import os
from instagram_scraper import InstagramScraper
from bot_detection_pipeline import InstagramBotDetectionPipeline
from feature_extraction import FeatureExtractor
from scoring_engine import BotScoringEngine
import pandas as pd


class PostAccountAnalyzer:
    """Analyze Instagram post with account data and bot detection"""
    
    def __init__(self):
        self.scraper = InstagramScraper()
        self.feature_extractor = FeatureExtractor()
        self.scoring_engine = BotScoringEngine(method='weighted_rules')
    
    def load_post_data(self, json_file):
        """Load post data from JSON file"""
        print(f"Loading post data from: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            post_data = json.load(f)
        
        print(f"✅ Loaded post data")
        print(f"   Username: @{post_data.get('username', 'N/A')}")
        print(f"   Post URL: {post_data.get('post_url', 'N/A')}")
        
        return post_data
    
    def scrape_account_info(self, username):
        """Scrape account information using Serper API"""
        print(f"\n{'='*60}")
        print(f"SCRAPING ACCOUNT: @{username}")
        print(f"{'='*60}")
        
        account_data = self.scraper.scrape_account(username)
        
        if not account_data:
            print(f"❌ Failed to scrape account data for @{username}")
            return None
        
        print(f"✅ Successfully scraped account data")
        return account_data
    
    def merge_data(self, post_data, account_data):
        """Merge post data with account data"""
        print(f"\nMerging post and account data...")
        
        # Create combined data structure
        combined_data = {
            # Post information
            'post': {
                'idx': post_data.get('idx'),
                'id': post_data.get('id'),
                'post_url': post_data.get('post_url'),
                'caption': post_data.get('caption'),
                'likes_count': post_data.get('likes_count'),
                'comments_count': post_data.get('comments_count'),
                'image_url': post_data.get('image_url'),
                'post_date': post_data.get('post_date'),
                'post_date_raw': post_data.get('post_date_raw'),
                'hashtags': post_data.get('hashtags', []),
                'scraped_at': post_data.get('scraped_at'),
                'media_urls': post_data.get('media_urls', []),
                'video_url': post_data.get('video_url'),
                'post_type': post_data.get('post_type')
            },
            
            # Account information (from scraper)
            'account': account_data,
            
            # Combined for bot detection
            'bot_detection_input': account_data
        }
        
        print(f"✅ Data merged successfully")
        return combined_data
    
    def detect_bot(self, account_data):
        """Run bot detection on account"""
        print(f"\n{'='*60}")
        print(f"BOT DETECTION ANALYSIS")
        print(f"{'='*60}")
        
        # Extract features
        print("\nExtracting features...")
        features = self.feature_extractor.extract_all_features(account_data)
        features_df = pd.DataFrame([features])
        
        # Calculate bot score
        print("Calculating bot score...")
        score = self.scoring_engine.score_accounts(features_df)
        if not isinstance(score, pd.Series):
            score = pd.Series(score)
        
        bot_score = score.iloc[0]
        
        # Classify
        classification = self.scoring_engine.classify_account(bot_score)
        
        # Print results
        username = account_data.get('username', 'Unknown')
        print(f"\n{'='*60}")
        print(f"RESULTS FOR: @{username}")
        print(f"{'='*60}")
        print(f"Bot Score: {bot_score:.2f}/100")
        print(f"Classification: {classification.upper()}")
        
        if classification == 'bot':
            print("⚠️  HIGH RISK - Likely a bot/fake account")
            risk_level = "HIGH"
        elif classification == 'inconclusive':
            print("⚠️  MEDIUM RISK - Needs human review")
            risk_level = "MEDIUM"
        else:
            print("✅ LOW RISK - Likely a real account")
            risk_level = "LOW"
        
        # Show key indicators
        print(f"\nKey Indicators:")
        print(f"  Followers: {account_data.get('user_follower_count', 'N/A'):,}")
        print(f"  Following: {account_data.get('user_following_count', 'N/A'):,}")
        print(f"  Posts: {account_data.get('user_media_count', 'N/A'):,}")
        print(f"  Follower/Following Ratio: {features.get('follower_following_ratio', 0):.2f}")
        print(f"  Has Profile Pic: {'Yes' if account_data.get('user_has_profil_pic', 0) else 'No'}")
        print(f"  Bio Length: {account_data.get('user_biography_length', 0)} chars")
        print(f"  Username Digits: {account_data.get('username_digit_count', 0)}")
        
        # Show suspicious indicators
        print(f"\nSuspicious Indicators:")
        suspicious_flags = []
        
        if features.get('no_profile_pic', 0) == 1:
            suspicious_flags.append("❌ No profile picture")
        if features.get('no_bio', 0) == 1:
            suspicious_flags.append("❌ No biography")
        if features.get('high_digit_username', 0) == 1:
            suspicious_flags.append("❌ Username has many digits")
        if features.get('suspicious_follower_ratio', 0) == 1:
            suspicious_flags.append("❌ Suspicious follower/following ratio")
        if features.get('high_following', 0) == 1:
            suspicious_flags.append("❌ Following too many accounts")
        
        if suspicious_flags:
            for flag in suspicious_flags:
                print(f"  {flag}")
        else:
            print("  ✅ No major red flags detected")
        
        return {
            'bot_score': float(bot_score),
            'classification': classification,
            'risk_level': risk_level,
            'features': features,
            'suspicious_flags': suspicious_flags
        }
    
    def save_results(self, combined_data, output_file):
        """Save combined results to JSON file"""
        print(f"\nSaving results to: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Results saved successfully")
    
    def analyze(self, json_file):
        """Complete analysis workflow"""
        print(f"\n{'#'*60}")
        print(f"# INSTAGRAM POST & ACCOUNT ANALYZER")
        print(f"{'#'*60}\n")
        
        # Step 1: Load post data
        post_data = self.load_post_data(json_file)
        username = post_data.get('username')
        
        if not username:
            print("❌ Error: No username found in post data")
            return None
        
        # Step 2: Scrape account info
        account_data = self.scrape_account_info(username)
        
        if not account_data:
            print("❌ Analysis failed - could not scrape account data")
            return None
        
        # Step 3: Merge data
        combined_data = self.merge_data(post_data, account_data)
        
        # Step 4: Bot detection
        bot_analysis = self.detect_bot(account_data)
        
        # Add bot analysis to combined data
        combined_data['bot_analysis'] = bot_analysis
        
        # Step 5: Save results
        base_name = os.path.splitext(json_file)[0]
        output_file = f"{base_name}_analyzed.json"
        self.save_results(combined_data, output_file)
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"ANALYSIS COMPLETE")
        print(f"{'='*60}")
        print(f"Account: @{username}")
        print(f"Bot Score: {bot_analysis['bot_score']:.2f}/100")
        print(f"Risk Level: {bot_analysis['risk_level']}")
        print(f"Classification: {bot_analysis['classification'].upper()}")
        print(f"\n📁 Full results saved to: {output_file}")
        
        return combined_data


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python analyze_post_with_account.py <json_file>")
        print("\nExample:")
        print("  python analyze_post_with_account.py lovable_dev_post.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"❌ Error: File not found: {json_file}")
        sys.exit(1)
    
    # Run analysis
    analyzer = PostAccountAnalyzer()
    analyzer.analyze(json_file)


if __name__ == "__main__":
    main()
