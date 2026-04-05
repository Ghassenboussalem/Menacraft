# Complete Usage Guide - Instagram Bot Detection

## 🚀 Quick Start Options

### Option 1: Test with Sample Data (Fastest)
```bash
python quick_test.py
```
Tests 3 pre-configured accounts and lets you add your own.

### Option 2: Test from JSON File
```bash
python test_real_accounts.py sample_accounts.json
```
Test multiple accounts from a JSON file.

### Option 3: Scrape & Analyze (with Serper API)
```bash
python analyze_instagram_accounts.py username1 username2 username3
```
Automatically scrapes Instagram data and analyzes accounts.

### Option 4: Interactive Mode
```bash
python test_real_accounts.py
```
Then select option 2 to enter account data manually.

---

## 📊 Complete Workflow Examples

### Example 1: Analyze Specific Accounts

```bash
# Using Serper API to scrape data
python analyze_instagram_accounts.py cristiano therock instagram

# Or manually create JSON file
python test_real_accounts.py my_accounts.json
```

### Example 2: Batch Analysis

Create `accounts_to_check.json`:
```json
[
  {
    "username": "user1",
    "user_follower_count": 1000,
    "user_following_count": 500,
    "user_media_count": 100,
    "user_biography_length": 80,
    "user_has_profil_pic": 1,
    "user_is_private": 0,
    "username_length": 5,
    "username_digit_count": 1
  }
]
```

Then run:
```bash
python test_real_accounts.py accounts_to_check.json
```

### Example 3: Compare Different Models

```python
from test_real_accounts import RealAccountTester

account = {
    'username': 'test_user',
    'user_follower_count': 500,
    'user_following_count': 2000,
    'user_media_count': 10,
    'user_biography_length': 0,
    'user_has_profil_pic': 0,
    'user_is_private': 0,
    'username_length': 9,
    'username_digit_count': 0
}

# Test with rule-based
tester1 = RealAccountTester(scoring_method='weighted_rules')
result1 = tester1.test_single_account(account)

# Test with ML
tester2 = RealAccountTester(scoring_method='gradient_boosting')
result2 = tester2.test_single_account(account)

print(f"Rule-based score: {result1['bot_score']:.2f}")
print(f"ML score: {result2['bot_score']:.2f}")
```

---

## 🔧 Configuration Options

### Scoring Methods

1. **weighted_rules** (Default)
   - Fast, no training needed
   - Interpretable results
   - Good for quick checks
   ```python
   tester = RealAccountTester(scoring_method='weighted_rules')
   ```

2. **random_forest**
   - ML-based, requires training
   - 97% accuracy on test set
   - Feature importance analysis
   ```python
   tester = RealAccountTester(scoring_method='random_forest')
   ```

3. **gradient_boosting**
   - ML-based, highest accuracy
   - 95% accuracy, 0.99 ROC-AUC
   - Best for production use
   ```python
   tester = RealAccountTester(scoring_method='gradient_boosting')
   ```

### Classification Thresholds

Adjust in `scoring_engine.py`:
```python
def classify_account(self, score, threshold_bot=70, threshold_real=30):
    # Adjust these values:
    # threshold_bot: Score above this = bot
    # threshold_real: Score below this = real
```

---

## 📝 Data Collection Methods

### Method 1: Serper API (Automated)

Set your API key in `.env`:
```
SERPER_API_KEY=your_key_here
```

Then run:
```bash
python instagram_scraper.py username1 username2
```

**Limitations:**
- Google search snippets may not always include follower counts
- Rate limits apply
- Some accounts may not be found

### Method 2: Manual Collection

Visit Instagram profile and collect:
- Follower count
- Following count
- Number of posts
- Bio length (character count)
- Has profile picture? (yes/no)
- Is private? (yes/no)
- Username length
- Number of digits in username

### Method 3: Instagram API (Official)

If you have Instagram API access:
```python
# Pseudo-code
from instagram_api import InstagramAPI

api = InstagramAPI(access_token='your_token')
profile = api.get_user('username')

account_data = {
    'username': profile.username,
    'user_follower_count': profile.follower_count,
    'user_following_count': profile.following_count,
    'user_media_count': profile.media_count,
    'user_biography_length': len(profile.biography),
    'user_has_profil_pic': 1 if profile.profile_pic_url else 0,
    'user_is_private': 1 if profile.is_private else 0,
    'username_length': len(profile.username),
    'username_digit_count': sum(c.isdigit() for c in profile.username)
}
```

### Method 4: Web Scraping (Advanced)

Using `instaloader`:
```bash
pip install instaloader
```

```python
import instaloader

L = instaloader.Instaloader()
profile = instaloader.Profile.from_username(L.context, 'username')

account_data = {
    'username': profile.username,
    'user_follower_count': profile.followers,
    'user_following_count': profile.followees,
    'user_media_count': profile.mediacount,
    'user_biography_length': len(profile.biography),
    'user_has_profil_pic': 1,
    'user_is_private': 1 if profile.is_private else 0,
    'username_length': len(profile.username),
    'username_digit_count': sum(c.isdigit() for c in profile.username)
}
```

**⚠️ Warning:** Check Instagram's Terms of Service before scraping.

---

## 📈 Understanding Results

### Bot Score Interpretation

| Score Range | Risk Level | Meaning |
|------------|-----------|---------|
| 0-30 | ✅ Low | Likely a real account |
| 30-70 | ⚠️ Medium | Inconclusive, needs review |
| 70-100 | 🚫 High | Likely a bot/fake account |

### Key Indicators

**High Bot Risk Signals:**
- Very low follower/following ratio (< 0.1)
- High following count (> 2000)
- No profile picture
- Empty bio
- Many digits in username
- Low engagement rate (< 1%)
- Excessive hashtags (> 20 per post)

**Low Bot Risk Signals:**
- Balanced follower/following ratio (0.5-5.0)
- Complete profile (pic + bio)
- Moderate engagement rate (2-10%)
- Reasonable hashtag usage (5-15 per post)
- External URL in bio
- Location tags on posts

### Classification Labels

- **real**: Low risk, appears to be a legitimate account
- **inconclusive**: Medium risk, manual review recommended
- **bot**: High risk, likely fake or automated account

---

## 🔍 Troubleshooting

### Issue: "Serper API key not provided"
**Solution:** Create `.env` file with:
```
SERPER_API_KEY=your_key_here
```

### Issue: "No accounts could be scraped"
**Solution:** 
- Check username spelling
- Try manual data entry instead
- Verify Serper API key is valid

### Issue: "All accounts classified as bot"
**Solution:**
- Use `weighted_rules` method instead of ML
- Provide more data fields (engagement metrics)
- Adjust classification thresholds

### Issue: "Model training takes too long"
**Solution:**
- Use `weighted_rules` method (no training)
- Reduce dataset size in `bot_detection_pipeline.py`

### Issue: "Low accuracy on specific account types"
**Solution:**
- Add engagement data (likes, comments)
- Include posting timestamps
- Provide hashtag counts

---

## 💡 Best Practices

1. **Always provide engagement data** when available (likes, comments)
2. **Use ML models** for production, rule-based for quick checks
3. **Review inconclusive cases** manually
4. **Batch process** multiple accounts for efficiency
5. **Save results** to JSON for later analysis
6. **Respect rate limits** when using APIs
7. **Follow Instagram ToS** when collecting data

---

## 📚 Additional Resources

- **Dataset Paper**: [Instagram Fake and Automated Account Detection](https://arxiv.org/pdf/1910.03090.pdf)
- **Dataset GitHub**: [fcakyon/instafake-dataset](https://github.com/fcakyon/instafake-dataset)
- **Serper API**: [serper.dev](https://serper.dev)

---

## 🆘 Getting Help

If you encounter issues:

1. Check this guide first
2. Review `TESTING_GUIDE.md` for data collection help
3. Check `README_PIPELINE.md` for pipeline details
4. Verify all dependencies are installed: `pip install -r requirements.txt`

---

## 📄 License & Ethics

- This tool is for research and educational purposes
- Always respect Instagram's Terms of Service
- Bot detection is probabilistic, not definitive
- Allow for human review of flagged accounts
- Consider privacy implications
- Don't use for harassment or discrimination
