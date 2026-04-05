# Testing Real Instagram Accounts

This guide shows you how to test the bot detection pipeline on real Instagram accounts.

## Method 1: Quick Example Tests

Run pre-configured example tests:

```bash
python test_real_accounts.py
```

Then select option `1` to see tests on:
- A suspicious bot-like account
- A normal user account  
- An influencer account

## Method 2: Interactive Mode

Enter account data manually:

```bash
python test_real_accounts.py
```

Select option `2`, then enter:
- Username
- Follower count
- Following count
- Number of posts
- Bio length
- Profile picture (1=Yes, 0=No)
- Private account (1=Yes, 0=No)
- Optional: Average likes and comments

## Method 3: Test from JSON File

### Step 1: Create a JSON file with account data

Example `my_accounts.json`:

```json
[
  {
    "username": "test_user",
    "user_follower_count": 500,
    "user_following_count": 300,
    "user_media_count": 100,
    "user_biography_length": 80,
    "user_has_profil_pic": 1,
    "user_is_private": 0,
    "username_length": 9,
    "username_digit_count": 0
  }
]
```

### Step 2: Run the test

```bash
python test_real_accounts.py my_accounts.json
```

Or use the provided sample:

```bash
python test_real_accounts.py sample_accounts.json
```

## Required Fields

### Minimum Required:
- `username`: Account username
- `user_follower_count`: Number of followers
- `user_following_count`: Number of following
- `user_media_count`: Number of posts
- `user_biography_length`: Bio character count
- `user_has_profil_pic`: Has profile picture (1 or 0)
- `user_is_private`: Is private account (1 or 0)
- `username_length`: Length of username
- `username_digit_count`: Number of digits in username

### Optional (for better accuracy):
- `media_like_numbers`: Array of likes per post (e.g., [100, 150, 120])
- `media_comment_numbers`: Array of comments per post
- `media_hashtag_numbers`: Array of hashtags per post
- `media_upload_times`: Array of Unix timestamps
- `media_has_location_info`: Array of location tags (1 or 0)
- `user_has_external_url`: Has URL in bio (1 or 0)

## How to Get Instagram Data

### Manual Collection:
1. Visit the Instagram profile
2. Count followers, following, posts
3. Check bio length (character count)
4. Note if they have profile picture
5. Check if account is private

### Using Instagram API:
If you have API access, you can fetch this data programmatically:

```python
# Pseudo-code example
account_data = {
    'username': profile.username,
    'user_follower_count': profile.followers_count,
    'user_following_count': profile.following_count,
    'user_media_count': profile.media_count,
    'user_biography_length': len(profile.biography),
    'user_has_profil_pic': 1 if profile.profile_pic_url else 0,
    'user_is_private': 1 if profile.is_private else 0,
    'username_length': len(profile.username),
    'username_digit_count': sum(c.isdigit() for c in profile.username)
}
```

### Using Web Scraping:
You can scrape public Instagram profiles (check Instagram's terms of service):

```python
# Example with instaloader (install: pip install instaloader)
import instaloader

L = instaloader.Instaloader()
profile = instaloader.Profile.from_username(L.context, 'username')

account_data = {
    'username': profile.username,
    'user_follower_count': profile.followers,
    'user_following_count': profile.followees,
    'user_media_count': profile.mediacount,
    'user_biography_length': len(profile.biography),
    'user_has_profil_pic': 1 if profile.profile_pic_url else 0,
    'user_is_private': 1 if profile.is_private else 0,
    'username_length': len(profile.username),
    'username_digit_count': sum(c.isdigit() for c in profile.username)
}
```

## Understanding Results

### Bot Score (0-100):
- **0-30**: Likely REAL account
- **30-70**: INCONCLUSIVE (needs review)
- **70-100**: Likely BOT/FAKE account

### Classification:
- **real**: Low risk, appears legitimate
- **inconclusive**: Medium risk, manual review recommended
- **bot**: High risk, likely fake/automated

### Key Indicators:
The system shows important metrics:
- Follower/Following ratio (bots often follow many, have few followers)
- Engagement rate (bots have low engagement)
- Profile completeness (bots often lack bio/profile pic)
- Username patterns (bots often have random digits)

## Example Output

```
============================================================
Account: @suspicious_bot123
============================================================
Bot Score: 85.23/100
Classification: BOT

⚠️  HIGH RISK - Likely a bot/fake account

Key Indicators:
  Followers: 25
  Following: 3500
  Posts: 1
  Follower/Following Ratio: 0.01
  Has Profile Pic: No
  Bio Length: 0 chars
  Engagement Rate: 0.08%
```

## Tips for Accurate Testing

1. **Include engagement data** (likes/comments) for better accuracy
2. **Test multiple accounts** to see patterns
3. **Use the ML models** (gradient_boosting) for best results
4. **Consider context**: New accounts may score higher even if legitimate
5. **Manual review**: Always review "inconclusive" cases

## Batch Testing

To test many accounts at once:

```python
from test_real_accounts import RealAccountTester

tester = RealAccountTester(scoring_method='gradient_boosting')

accounts = [
    {'username': 'user1', 'user_follower_count': 100, ...},
    {'username': 'user2', 'user_follower_count': 200, ...},
    # ... more accounts
]

results = tester.test_batch(accounts)

# Export results
import pandas as pd
df = pd.DataFrame(results)
df.to_csv('bot_detection_results.csv', index=False)
```

## Troubleshooting

**Issue**: Model takes long to load
- **Solution**: First run trains the model, subsequent runs are faster

**Issue**: Low accuracy on specific account types
- **Solution**: Provide more optional fields (engagement data)

**Issue**: All accounts classified as "inconclusive"
- **Solution**: Adjust thresholds in the code or provide more data

## Legal & Ethical Considerations

⚠️ **Important**: 
- Respect Instagram's Terms of Service
- Don't use for harassment or discrimination
- Bot detection is probabilistic, not definitive
- Always allow for human review
- Consider privacy implications
