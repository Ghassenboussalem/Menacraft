#!/usr/bin/env python3
"""
Batch verification for multiple images
"""
import csv
import sys
from verifier import ImageVerifier
from datetime import datetime


def verify_batch(csv_file: str):
    """Verify multiple images from CSV file"""
    verifier = ImageVerifier()
    results = []
    
    print("\n📊 Batch Verification Starting...")
    print("="*60)
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader, 1):
            image_url = row.get('image_url', '').strip()
            claimed_date = row.get('claimed_date', '').strip()
            description = row.get('description', 'N/A').strip()
            
            if not image_url or not claimed_date:
                print(f"\n[{i}] Skipping - missing data")
                continue
            
            print(f"\n[{i}] {description[:50]}")
            print(f"    URL: {image_url[:60]}...")
            print(f"    Claimed: {claimed_date}")
            
            result = verifier.verify_image(image_url, claimed_date)
            
            if result.get('success'):
                analysis = result['analysis']
                verdict = analysis['verdict']
                gap_days = analysis['gap_days']
                
                results.append({
                    'description': description,
                    'url': image_url,
                    'claimed_date': claimed_date,
                    'verdict': verdict,
                    'gap_days': gap_days,
                    'oldest_found': analysis['oldest_date']
                })
                
                print(f"    ➜ {verdict} (gap: {gap_days} days)")
            else:
                print(f"    ➜ No data found")
                results.append({
                    'description': description,
                    'url': image_url,
                    'claimed_date': claimed_date,
                    'verdict': 'NO_DATA',
                    'gap_days': 'N/A',
                    'oldest_found': 'N/A'
                })
    
    # Save results
    output_file = f"verification_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    print(f"\n{'='*60}")
    print(f"✓ Results saved to: {output_file}")
    print(f"  Total processed: {len(results)}")
    print(f"  Suspicious/Fake: {sum(1 for r in results if 'FAKE' in r['verdict'] or 'SUSPICIOUS' in r['verdict'])}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python batch_verify.py <csv_file>")
        print("\nCSV format:")
        print("  image_url,claimed_date,description")
        print('  "https://example.com/img.jpg","2024-03-15","Event description"')
        sys.exit(1)
    
    verify_batch(sys.argv[1])


if __name__ == '__main__':
    main()
