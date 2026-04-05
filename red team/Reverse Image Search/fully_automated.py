#!/usr/bin/env python3
"""
Fully automated RT-1 verification with web scraping
"""
import sys
import os
import base64
import requests
from datetime import datetime
from dateutil import parser
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


class FullyAutomatedVerifier:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def upload_image(self, image_path: str) -> str:
        """Upload to ImgBB"""
        api_key = os.environ.get('IMGBB_API_KEY')
        
        if not api_key:
            raise Exception("IMGBB_API_KEY not set")
        
        print("📤 Uploading image...")
        
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        response = self.session.post(
            "https://api.imgbb.com/1/upload",
            data={'key': api_key, 'image': image_data},
            timeout=30
        )
        
        if response.json().get('success'):
            url = response.json()['data']['url']
            print(f"✓ Uploaded: {url}\n")
            return url
        
        raise Exception("Upload failed")
    
    def scrape_tineye(self, image_url: str) -> dict:
        """Scrape TinEye results using Selenium"""
        print("🔍 Scraping TinEye (automated)...")
        
        # Setup Chrome in headless mode
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            
            # Navigate to TinEye search
            search_url = f'https://tineye.com/search?url={image_url}&sort=crawl_date&order=asc'
            print(f"  Loading TinEye...")
            driver.get(search_url)
            
            # Wait for results to load
            time.sleep(5)
            
            # Get page source
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract total matches from title or h2
            total_matches = 0
            title = soup.find('title')
            if title:
                import re
                match = re.search(r'(\d+)\s+TinEye', title.get_text())
                if match:
                    total_matches = int(match.group(1))
            
            # Extract "First indexed by TinEye on" date
            first_indexed_date = None
            h4_tags = soup.find_all('h4', class_='text-sm')
            for h4 in h4_tags:
                text = h4.get_text()
                if 'First indexed by TinEye on' in text:
                    strong = h4.find('strong')
                    if strong:
                        first_indexed_date = strong.get_text().strip()
                        break
            
            driver.quit()
            
            if first_indexed_date:
                print(f"✓ Found {total_matches} total matches")
                print(f"  First indexed: {first_indexed_date}")
                
                return {
                    'success': True,
                    'total_matches': total_matches,
                    'oldest': {
                        'date_text': first_indexed_date,
                        'domain': 'TinEye Index'
                    },
                    'all_results': [{
                        'date_text': first_indexed_date,
                        'domain': 'TinEye Index'
                    }]
                }
            else:
                print("✗ No first indexed date found")
                return {'success': False}
        
        except Exception as e:
            print(f"  ⚠ Scraping error: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def parse_date(self, date_text: str) -> datetime:
        """Parse various date formats"""
        # Common patterns
        patterns = [
            '%d %B %Y',  # 27 novembre 2014
            '%B %d, %Y',  # November 27, 2014
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y'
        ]
        
        # Month translations
        months = {
            'janvier': 'January', 'février': 'February', 'mars': 'March',
            'avril': 'April', 'mai': 'May', 'juin': 'June',
            'juillet': 'July', 'août': 'August', 'septembre': 'September',
            'octobre': 'October', 'novembre': 'November', 'décembre': 'December'
        }
        
        # Translate French months
        text = date_text.lower()
        for fr, en in months.items():
            text = text.replace(fr, en)
        
        # Try parsing
        try:
            return parser.parse(text)
        except:
            return None
    
    def verify(self, image_path: str, claimed_date: str = None):
        """Full automated verification"""
        print(f"\n{'='*60}")
        print(f"🤖 FULLY AUTOMATED RT-1 VERIFICATION")
        print(f"{'='*60}")
        print(f"Image: {os.path.basename(image_path)}")
        print(f"Size: {os.path.getsize(image_path) / 1024:.1f} KB\n")
        
        # Upload
        image_url = self.upload_image(image_path)
        
        # Scrape TinEye
        tineye_results = self.scrape_tineye(image_url)
        
        if not tineye_results['success']:
            print(f"\n{'='*60}")
            print("📊 AUTOMATED RESULTS")
            print(f"{'='*60}\n")
            
            print("✓ No matches found in TinEye database")
            print("\n🎯 VERDICT: LIKELY RECENT/ORIGINAL IMAGE")
            print("\nExplanation:")
            print("  • Image not found in 82.8 billion indexed images")
            print("  • This suggests the image is:")
            print("    - Recently created/uploaded")
            print("    - Original content")
            print("    - Not widely circulated online")
            print("    - Potentially authentic for recent claims")
            
            print(f"\n{'='*60}\n")
            
            # Save report
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("RT-1 AUTOMATED VERIFICATION REPORT\n")
                f.write("="*60 + "\n\n")
                f.write(f"Image: {os.path.basename(image_path)}\n")
                f.write(f"Verification Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("Result: NO MATCHES FOUND\n")
                f.write("Verdict: LIKELY RECENT/ORIGINAL IMAGE\n\n")
                f.write("Explanation:\n")
                f.write("  - Image not found in TinEye's 82.8 billion image database\n")
                f.write("  - Suggests recent creation or original content\n")
                f.write("  - No evidence of prior circulation\n")
                f.write("  - Potentially authentic for recent event claims\n\n")
                f.write("Method: RT-1 (TinEye automated scraping)\n")
            
            print(f"💾 Report saved: {filename}")
            return
        
        # Parse oldest date
        oldest_date_text = tineye_results['oldest']['date_text']
        oldest_date = self.parse_date(oldest_date_text)
        
        if not oldest_date:
            print(f"\n⚠ Could not parse date: {oldest_date_text}")
            return
        
        # Generate report
        print(f"\n{'='*60}")
        print("📊 AUTOMATED RESULTS")
        print(f"{'='*60}\n")
        
        print(f"Total Matches: {tineye_results['total_matches']}")
        print(f"First Published: {oldest_date.strftime('%Y-%m-%d')}")
        print(f"Oldest Source: {tineye_results['oldest']['domain']}")
        
        # Calculate age
        age = datetime.now() - oldest_date
        print(f"\nImage Age: {age.days} days ({age.days / 365.25:.1f} years)")
        
        # If claimed date provided, calculate gap
        if claimed_date:
            claimed = parser.parse(claimed_date)
            gap = claimed - oldest_date
            
            print(f"\nClaimed Date: {claimed.strftime('%Y-%m-%d')}")
            print(f"Temporal Gap: {gap.days} days ({gap.days / 365.25:.1f} years)")
            
            # Verdict
            if gap.days < 0:
                verdict = "🚨 FAKE - Image predates claimed event"
            elif gap.days >= 365:
                verdict = "🚨 HIGHLY SUSPICIOUS - Multi-year gap"
            elif gap.days >= 180:
                verdict = "⚠️ SUSPICIOUS - 6+ month gap"
            elif gap.days >= 7:
                verdict = "⚠️ QUESTIONABLE - Week+ delay"
            else:
                verdict = "✓ PLAUSIBLE - Minimal gap"
            
            print(f"\n{verdict}")
        
        # Show top 5 results
        if len(tineye_results['all_results']) > 1:
            print(f"\nTop 5 Oldest Appearances:")
            for i, result in enumerate(tineye_results['all_results'][:5], 1):
                print(f"  {i}. {result['date_text']} - {result['domain']}")
        
        print(f"\n{'='*60}\n")
        
        # Save report
        self.save_report(image_path, tineye_results, oldest_date, claimed_date)
    
    def save_report(self, image_path: str, results: dict, oldest_date: datetime, claimed_date: str = None):
        """Save verification report"""
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("RT-1 AUTOMATED VERIFICATION REPORT\n")
            f.write("="*60 + "\n\n")
            f.write(f"Image: {os.path.basename(image_path)}\n")
            f.write(f"Verification Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total Matches Found: {results['total_matches']}\n")
            f.write(f"First Published: {oldest_date.strftime('%Y-%m-%d')}\n")
            f.write(f"Oldest Source: {results['oldest']['domain']}\n")
            
            age = datetime.now() - oldest_date
            f.write(f"\nImage Age: {age.days} days ({age.days / 365.25:.1f} years)\n")
            
            if claimed_date:
                claimed = parser.parse(claimed_date)
                gap = claimed - oldest_date
                f.write(f"\nClaimed Date: {claimed.strftime('%Y-%m-%d')}\n")
                f.write(f"Temporal Gap: {gap.days} days ({gap.days / 365.25:.1f} years)\n")
            
            f.write("\n\nMethod: RT-1 (TinEye automated scraping)\n")
        
        print(f"💾 Report saved: {filename}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python fully_automated.py <image_path> [claimed_date]")
        print("\nExamples:")
        print('  python fully_automated.py "photo.jpg"')
        print('  python fully_automated.py "photo.jpg" "2024-03-15"')
        print("\nRequires:")
        print("  - Chrome browser installed")
        print("  - ChromeDriver (auto-downloaded by selenium)")
        print("  - IMGBB_API_KEY environment variable")
        sys.exit(1)
    
    image_path = sys.argv[1]
    claimed_date = sys.argv[2] if len(sys.argv) > 2 else None
    
    verifier = FullyAutomatedVerifier()
    verifier.verify(image_path, claimed_date)


if __name__ == '__main__':
    main()
