# Sara7a (MenaCraft Verification Pipeline)

An intelligent, multi-agent misinformation detection pipeline designed specifically for verifying Instagram content in real-time. Sara7a acts as a robust fact-checking overlay, utilizing an innovative "Red Team vs. Blue Team" architecture orchestrated by a central LLM-driven Synthesis Agent.

## Overview

Sara7a reads Instagram posts (via a bespoke Chrome Extension DOM bridge) and automatically streams the content to a Supabase cache. From there, the data is pulled into an 8-agent AI pipeline that checks for image manipulation, claim accuracy, bot-like engagement, and historical reuse. 

By avoiding standard API scraping, it bypasses Instagram's aggressive anti-scraping protections while delivering a seamless, in-browser fact-checking experience.

## Features

- **Red Team / Blue Team Methodology**: Independent agents verify different axes of truth (content authenticity, contextual consistency, source credibility).
- **LLM-Powered Synthesis**: A meta-reasoning agent (powered by Groq Llama 4 Scout) weights the findings from all agents and resolves contradictions to provide a final synthesized verdict.
- **Deepfake & Image Forensics**: Utilizes MobileViT combined with Groq Vision for granular artifact detection.
- **Bot Detection**: Extracts engagement metrics and employs Serper API + rule-based scoring to assign bot probabilities.
- **Temporal Provenance**: Automates reverse image searching via TinEye to detect if an image is being reused out of context.
- **Real-Time Streaming**: Agents stream their individual verdicts progressively directly to the Vite frontend via Server-Sent Events (SSE).

## Tech Stack

- **Frontend**: React, Vite, Zustand
- **Backend**: Node.js, Express (REST/SSE)
- **AI Microservice**: Python, Flask, Groq Llama 4 Scout, MobileViT
- **Storage**: Supabase (PostgreSQL)

## Getting Started

### Prerequisites
- Node.js (v18+)
- Python 3.10+
- A Supabase project
- API Keys for Groq, Serper, and ImgBB.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Ghassenboussalem/Menacraft.git
   cd Menacraft
   ```

2. **Backend / Frontend Setup:**
   ```bash
   # Install JS dependencies at the root (concurrently, express, etc.)
   npm install

   # Install Client dependencies
   cd client
   npm install
   cd ..

   # Install Server dependencies
   cd server
   npm install
   cd ..
   ```

3. **Environment Variables:**
   You must set up `.env` files in multiple directories based on the provided `.env.example` templates.
   
   - **Main Server** (`server/.env`):
     ```bash
     cp server/.env.example server/.env
     # Fill in SUPABASE_URL and SUPABASE_ANON_KEY
     ```
   
   - **Python AI Microservice** (`server/python/.env`):
     ```bash
     cp server/python/.env.example server/python/.env
     # Fill in GROQ_API_KEY, SERPER_API_KEY, IMGBB_API_KEY
     ```

4. **Python Dependencies:**
   ```bash
   cd server/python
   pip install -r requirements.txt
   ```

### Running the Project

From the project root directory, run the primary development script:

```bash
npm run dev
```

This will concurrently launch:
1. The Vite React Frontend (`localhost:5173`)
2. The Express Backend (`localhost:3001`)
3. The Python AI Microservice (`localhost:5001`)

Open your browser to `http://localhost:5173` to see the Agent dashboard.

## Contributing

Please refer to `ARCHITECTURE.md` for a detailed breakdown of the interaction between the scraping mechanism, the agent weighting, and the synthesis pipeline.
