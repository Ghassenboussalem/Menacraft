"""
Test specific account: ghassenbousselem
Enter the data manually here
"""

from test_real_accounts import RealAccountTester

# Account data for @ghassenbousselem
# Visit https://www.instagram.com/ghassenbousselem/ and fill in these values:

account_data = {
    'username': 'ghassenbousselem',
    
    # REQUIRED: Fill these in by visiting the Instagram profile
    'user_follower_count': 0,      # Enter follower count here
    'user_following_count': 0,     # Enter following count here
    'user_media_count': 0,         # Enter number of posts here
    'user_biography_length': 0,    # Count characters in bio
    'user_has_profil_pic': 1,      # 1 if has profile pic, 0 if not
    'user_is_private': 0,          # 1 if private, 0 if public
    
    # Auto-calculated
    'username_length': len('ghassenbousselem'),
    'username_digit_count': sum(c.isdigit() for c in 'ghassenbousselem'),
    'user_has_external_url': 0     # 1 if has URL in bio, 0 if not
}

# INSTRUCTIONS:
# 1. Visit https://www.instagram.com/ghassenbousselem/
# 2. Fill in the values above
# 3. Run: python test_ghassenbousselem.py

print("\n" + "="*70)
print("Testing @ghassenbousselem")
print("="*70)

# Check if data is filled in
if account_data['user_follower_count'] == 0 and account_data['user_media_count'] == 0:
    print("\n⚠️  Please fill in the account data first!")
    print("\nSteps:")
    print("1. Visit: https://www.instagram.com/ghassenbousselem/")
    print("2. Edit this file (test_ghassenbousselem.py)")
    print("3. Fill in the values:")
    print("   - user_follower_count")
    print("   - user_following_count")
    print("   - user_media_count")
    print("   - user_biography_length")
    print("   - user_has_profil_pic (1 or 0)")
    print("   - user_is_private (1 or 0)")
    print("4. Run again: python test_ghassenbousselem.py")
    print("\n" + "="*70)
else:
    # Test the account
    print("\nInitializing bot detector...")
    tester = RealAccountTester(scoring_method='weighted_rules')
    
    print("\nAnalyzing account...")
    result = tester.test_single_account(account_data)
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
