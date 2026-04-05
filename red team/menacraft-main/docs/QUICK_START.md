# Quick Start - Test Any Instagram Account

## ✅ Easiest Method: Direct Testing

### Step 1: Visit the Instagram Profile
Go to: `https://www.instagram.com/USERNAME`

Example: https://www.instagram.com/ghassenbousselem

### Step 2: Collect This Information
Look at the profile and note down:
- **Followers**: The number shown (e.g., 1.2K = 1200, 5M = 5000000)
- **Following**: The number shown
- **Posts**: The number shown
- **Bio length**: Count characters in the bio (or estimate)
- **Has profile picture**: Yes (1) or No (0)
- **Is private**: Yes (1) or No (0)

### Step 3: Run the Test

**Option A: Interactive (Recommended)**
```bash
python test_account_direct.py
```
Then enter the data when prompted.

**Option B: Edit & Run**
1. Open `test_ghassenbousselem.py`
2. Fill in the values
3. Run: `python test_ghassenbousselem.py`

**Option C: Create JSON File**
Create `my_account.json`:
```json
[
  {
    "username": "ghassenbousselem",
    "user_follower_count": 1500,
    "user_following_count": 800,
    "user_media_count": 200,
    "user_biography_length": 80,
    "user_has_profil_pic": 1,
    "user_is_private": 0,
    "username_length": 16,
    "username_digit_count": 0
  }
]
```

Then run:
```bash
python test_real_accounts.py my_account.json
```

## 📊 Example: Testing @ghassenbousselem

Let's say you visit the profile and see:
- Followers: 1,234
- Following: 567
- Posts: 89
- Bio: "Photographer | Tunisia 🇹🇳" (25 characters)
- Has profile picture: Yes
- Is private: No

### Method 1: Interactive
```bash
python test_account_direct.py
```

Enter:
```
Username: ghassenbousselem
Follower count: 1234
Following count: 567
Number of posts: 89
Bio length: 25
Has profile picture: 1
Is private: 0
```

### Method 2: JSON File
Create `ghassenbousselem.json`:
```json
[
  {
    "username": "ghassenbousselem",
    "user_follower_count": 1234,
    "user_following_count": 567,
    "user_media_count": 89,
    "user_biography_length": 25,
    "user_has_profil_pic": 1,
    "user_is_private": 0,
    "username_length": 16,
    "username_digit_count": 0
  }
]
```

Run:
```bash
python test_real_accounts.py ghassenbousselem.json
```

## 🎯 Understanding Results

You'll get output like:
```
============================================================
Account: @ghassenbousselem
============================================================
Bot Score: 15.23/100
Classification: REAL
✅ LOW RISK - Likely a real account

Key Indicators:
  Followers: 1,234
  Following: 567
  Posts: 89
  Follower/Following Ratio: 2.18
  Has Profile Pic: Yes
  Bio Length: 25 chars
  Engagement Rate: 0.00%
```

### Score Interpretation:
- **0-30**: ✅ REAL - Low risk, likely legitimate
- **30-70**: ⚠️ INCONCLUSIVE - Needs manual review
- **70-100**: 🚫 BOT - High risk, likely fake/automated

## 🚀 Quick Commands

```bash
# Test with examples
python quick_test.py

# Test interactively
python test_account_direct.py

# Test from JSON
python test_real_accounts.py sample_accounts.json

# Try to scrape & analyze (may not work for all accounts)
python analyze_instagram_accounts.py username1 username2
```

## 💡 Tips

1. **For better accuracy**, also provide:
   - Average likes per post
   - Average comments per post
   - Average hashtags per post

2. **If scraping fails**, use manual input methods

3. **For batch testing**, create a JSON file with multiple accounts

4. **Save results** for later analysis

## ❓ Need Help?

- Can't find the profile? Check spelling
- Scraping not working? Use manual input
- Want more accuracy? Add engagement data
- Need to test many accounts? Use JSON batch method

## 📝 Example Workflow

1. Visit Instagram profile
2. Note down the numbers
3. Run `python test_account_direct.py`
4. Enter the data
5. Get instant bot detection results
6. Save results if needed

That's it! No API scraping needed, just manual data entry and instant analysis.
