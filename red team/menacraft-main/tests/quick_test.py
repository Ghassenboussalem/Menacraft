"""
Quick test script - Test real Instagram accounts easily
"""

from test_real_accounts import RealAccountTester

print("\n" + "="*70)
print("QUICK TEST - Instagram Bot Detection")
print("="*70)

# Initialize with rule-based scoring (faster, no training needed)
print("\nInitializing bot detector (rule-based method)...")
tester = RealAccountTester(scoring_method='weighted_rules')

print("\n" + "="*70)
print("Testing Sample Accounts")
print("="*70)

# Test 1: Suspicious bot-like account
print("\n--- Test 1: Suspicious Account (bot-like) ---")
bot_account = {
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
    'media_comment_numbers': [0, 0],
    'media_hashtag_numbers': [30, 30]
}
tester.test_single_account(bot_account)

# Test 2: Normal user account
print("\n--- Test 2: Normal User Account ---")
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
    'media_comment_numbers': [5, 8, 3, 6, 4],
    'media_hashtag_numbers': [5, 7, 6, 8, 5]
}
tester.test_single_account(normal_account)

# Test 3: Influencer account
print("\n--- Test 3: Influencer Account ---")
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
    'media_comment_numbers': [50, 60, 45, 55, 52],
    'media_hashtag_numbers': [10, 12, 11, 13, 10]
}
tester.test_single_account(influencer_account)

# Test 4: Your custom account
print("\n" + "="*70)
print("Test Your Own Account")
print("="*70)
print("\nEnter account details (or press Enter to skip):")

username = input("Username: ").strip()
if username:
    try:
        follower_count = int(input("Follower count: "))
        following_count = int(input("Following count: "))
        media_count = int(input("Number of posts: "))
        bio_length = int(input("Bio length (characters): "))
        has_profile_pic = int(input("Has profile picture? (1=Yes, 0=No): "))
        is_private = int(input("Is private account? (1=Yes, 0=No): "))
        
        custom_account = {
            'username': username,
            'user_follower_count': follower_count,
            'user_following_count': following_count,
            'user_media_count': media_count,
            'user_biography_length': bio_length,
            'user_has_profil_pic': has_profile_pic,
            'user_is_private': is_private,
            'username_length': len(username),
            'username_digit_count': sum(c.isdigit() for c in username)
        }
        
        print("\n--- Your Account Test ---")
        tester.test_single_account(custom_account)
        
    except ValueError:
        print("Invalid input, skipping custom test")

print("\n" + "="*70)
print("Testing Complete!")
print("="*70)
print("\nTo test from JSON file, run:")
print("  python test_real_accounts.py sample_accounts.json")
print("\nTo test interactively, run:")
print("  python test_real_accounts.py")
print("  Then select option 2")
