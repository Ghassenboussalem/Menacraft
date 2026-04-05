# API Setup Guide

## ImgBB (Required) ✓
You already have this set up!
- API Key: 1d906e5ce7ff373716edcf7a79a8b306
- Status: Working

## Google Cloud Vision API (Recommended)

### Steps:
1. Go to: https://console.cloud.google.com/
2. Create a new project or select existing one
3. Enable "Cloud Vision API":
   - Search for "Vision API" in the search bar
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy the API key

### Set the key:
```bash
set GOOGLE_VISION_API_KEY=your_key_here
```

### What it does:
- Finds web pages with matching images
- Detects full and partial matches
- Shows where the image appears online
- More comprehensive than Wayback alone

## TinEye API (Optional - Paid)

### Steps:
1. Go to: https://services.tineye.com/
2. Sign up for API access (paid service)
3. Get your API keys (public + private)

### Set the keys:
```bash
set TINEYE_PUBLIC_KEY=your_public_key
set TINEYE_API_KEY=your_private_key
```

### What it does:
- Shows exact first crawl date
- Most accurate for temporal verification
- Sorts by oldest appearance
- Best for RT-1 methodology

## Free Alternative

If you don't want to set up APIs, the tool already opens:
- TinEye (manual upload)
- Yandex (manual upload)
- Google Images (manual upload)

Just use the browser tabs that open automatically!
