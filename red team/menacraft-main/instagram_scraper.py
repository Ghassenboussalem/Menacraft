"""
Instagram account scraper using Serper API and web scraping
"""

import requests
import json
import re
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

class InstagramScraper:
    """Scrape Instagram account data for bot detection"""
    
    def __init__(self, serper_api_key=None):
        self.serper_api_key = serper_api_key or os.getenv('SERPER_API_KEY')
        if not self.serper_api_key:
            raise ValueError("Serper API key not provided")
    
    def search_instagram_profile(self, username):
        """Search for Instagram profile using Serper API"""
        url = "https://google.serper.dev/search"
        
        payload = json.dumps({
            "q": f"instagram.com/{username}",
            "num": 5
        })
        
        headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            results = response.json()
            
            # Find Instagram profile link
            for result in results.get('organic', []):
                link = result.get('link', '')
                if f'instagram.com/{username}' in link.lower():
                    return {
                        'url': link,
                        'title': result.get('title', ''),
                        'snippet': result.get('snippet', '')
                    }
            
            return None
            
        except Exception as e:
            print(f"Error searching for profile: {e}")
            return None
    
    def extract_from_snippet(self, snippet, title):
        """Extract basic info from search snippet"""
        data = {
            'username': None,
            'follower_count': 0,
            'following_count': 0,
            'media_count': 0,
            'biography_length': 0,
            'has_profile_pic': 1,  # Assume yes
            'is_private': 0,
            'has_external_url': 0
        }
        
        # Extract follower count
        follower_match = re.search(r'([\d,\.]+[KMB]?)\s*[Ff]ollowers?', snippet)
        if follower_match:
            data['follower_count'] = self._parse_count(follower_match.group(1))
        
        # Extract following count
        following_match = re.search(r'([\d,\.]+[KMB]?)\s*[Ff]ollowing', snippet)
        if following_match:
            data['following_count'] = self._parse_count(following_match.group(1))
        
        # Extract post count
        post_match = re.search(r'([\d,\.]+[KMB]?)\s*[Pp]osts?', snippet)
        if post_match:
            data['media_count'] = self._parse_count(post_match.group(1))
        
        # Extract bio length (approximate from snippet)
        if snippet:
            # Remove follower/following/post info
            bio_text = re.sub(r'\d+[KMB]?\s*[Ff]ollowers?', '', snippet)
            bio_text = re.sub(r'\d+[KMB]?\s*[Ff]ollowing', '', bio_text)
            bio_text = re.sub(r'\d+[KMB]?\s*[Pp]osts?', '', bio_text)
            data['biography_length'] = len(bio_text.strip())
        
        # Check for URL in bio
        if 'http' in snippet or 'www.' in snippet:
            data['has_external_url'] = 1
        
        # Check if private
        if 'private' in snippet.lower() or 'private account' in title.lower():
            data['is_private'] = 1
        
        return data
    
    def _parse_count(self, count_str):
        """Parse count string like '1.5K' or '2M' to integer"""
        count_str = count_str.replace(',', '').strip()
        
        multipliers = {
            'K': 1000,
            'M': 1000000,
            'B': 1000000000
        }
        
        for suffix, multiplier in multipliers.items():
            if suffix in count_str.upper():
                number = float(count_str.upper().replace(suffix, ''))
                return int(number * multiplier)
        
        try:
            return int(float(count_str))
        except:
            return 0
    
    def scrape_account(self, username):
        """
        Scrape Instagram account data
        Returns account data dict suitable for bot detection
        """
        print(f"\nSearching for @{username}...")
        
        # Search for profile
        profile_info = self.search_instagram_profile(username)
        
        if not profile_info:
            print(f"Could not find Instagram profile for @{username}")
            return None
        
        print(f"Found profile: {profile_info['url']}")
        
        # Extract data from snippet
        data = self.extract_from_snippet(
            profile_info.get('snippet', ''),
            profile_info.get('title', '')
        )
        
        # Add username info
        data['username'] = username
        data['username_length'] = len(username)
        data['username_digit_count'] = sum(c.isdigit() for c in username)
        
        # Rename fields to match bot detection format
        account_data = {
            'username': data['username'],
            'user_follower_count': data['follower_count'],
            'user_following_count': data['following_count'],
            'user_media_count': data['media_count'],
            'user_biography_length': data['biography_length'],
            'user_has_profil_pic': data['has_profile_pic'],
            'user_is_private': data['is_private'],
            'username_length': data['username_length'],
            'username_digit_count': data['username_digit_count'],
            'user_has_external_url': data['has_external_url']
        }
        
        print(f"\nExtracted data:")
        print(f"  Followers: {account_data['user_follower_count']:,}")
        print(f"  Following: {account_data['user_following_count']:,}")
        print(f"  Posts: {account_data['user_media_count']:,}")
        print(f"  Bio length: {account_data['user_biography_length']} chars")
        print(f"  Private: {'Yes' if account_data['user_is_private'] else 'No'}")
        
        return account_data
    
    def scrape_multiple(self, usernames):
        """Scrape multiple accounts"""
        results = []
        
        for username in usernames:
            account_data = self.scrape_account(username)
            if account_data:
                results.append(account_data)
        
        return results


def main():
    """Demo usage"""
    import sys
    
    # Initialize scraper
    scraper = InstagramScraper()
    
    if len(sys.argv) > 1:
        # Scrape accounts from command line
        usernames = sys.argv[1:]
    else:
        # Demo accounts
        print("Demo mode - testing with example usernames")
        print("Usage: python instagram_scraper.py username1 username2 ...")
        
        usernames = input("\nEnter Instagram usernames (space-separated): ").strip().split()
        
        if not usernames:
            print("No usernames provided, exiting")
            return
    
    # Scrape accounts
    accounts = scraper.scrape_multiple(usernames)
    
    if accounts:
        # Save to JSON
        output_file = 'scraped_accounts.json'
        with open(output_file, 'w') as f:
            json.dump(accounts, f, indent=2)
        
        print(f"\n✅ Scraped {len(accounts)} accounts")
        print(f"📁 Saved to: {output_file}")
        print(f"\nTo analyze these accounts, run:")
        print(f"  python test_real_accounts.py {output_file}")
    else:
        print("\n❌ No accounts scraped")


if __name__ == "__main__":
    main()
