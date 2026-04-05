# Reinforcement Learning System - Quick Start

## Overview

The RL Orchestrator continuously improves bot detection by learning from feedback. When predictions are correct, agent weights are rewarded. When incorrect, they're adjusted to improve future performance.

## Quick Start

### 1. Run Bot Detection

```javascript
const result = await verifyPostReal(post);
const botAgent = result.agents.find(a => a.name === 'Bot Pattern Detector');
```

### 2. Provide Ground Truth

```bash
curl -X POST http://localhost:3001/api/rl-feedback \
  -H "Content-Type: application/json" \
  -d '{
    "username": "suspicious_account",
    "groundTruth": "bot",
    "agents": [...],
    "botScore": 85,
    "classification": "bot"
  }'
```

### 3. System Learns

```
[RL] Prediction for @suspicious_account: bot (actual: bot) - CORRECT ✓
[RL] Reward: +1
[RL] Weight adjustments: {
  'Bot Pattern Detector': { old: '0.100', new: '0.105', change: '+0.0050' }
}
```

### 4. Check Progress

```bash
curl http://localhost:3001/api/rl-feedback/stats
```

```json
{
  "stats": {
    "totalPredictions": 150,
    "accuracy": "87.33%"
  },
  "currentWeights": {
    "Bot Pattern Detector": 0.115
  }
}
```

### 5. View History Logs

```bash
# Get available log dates
curl http://localhost:3001/api/rl-feedback/logs/dates

# Get logs for specific date
curl http://localhost:3001/api/rl-feedback/logs/2026-04-05

# Get stats for date range
curl http://localhost:3001/api/rl-feedback/logs/range/2026-04-01/2026-04-05

# Export as CSV
curl http://localhost:3001/api/rl-feedback/logs/export/2026-04-01/2026-04-05 > logs.csv
```

## Log Files

The system creates logs in the `rl_logs/` directory:

1. **JSON Lines** (`rl_log_YYYY-MM-DD.jsonl`) - Machine-readable, complete data
2. **Summary** (`rl_summary_YYYY-MM-DD.log`) - Human-readable, easy to review

## API Endpoints

### Feedback
- `POST /api/rl-feedback` - Provide ground truth feedback

### Statistics
- `GET /api/rl-feedback/stats` - Current stats and weights

### Logs
- `GET /api/rl-feedback/logs/dates` - List available dates
- `GET /api/rl-feedback/logs/:date` - Logs for specific date
- `GET /api/rl-feedback/logs/range/:start/:end` - Aggregated stats
- `GET /api/rl-feedback/logs/export/:start/:end` - Export as CSV

## Test It

```bash
# Run unit tests
node server/services/reinforcementLearning.test.js

# Run feedback examples
node server/examples/rl-feedback-example.js

# Run log analysis examples
node server/examples/rl-logs-example.js
```

## Files Created

- `server/services/reinforcementLearning.js` - Core RL logic
- `server/routes/rl-feedback.js` - API endpoints
- `server/examples/rl-feedback-example.js` - Feedback examples
- `server/examples/rl-logs-example.js` - Log analysis examples
- `server/services/RL_README.md` - Detailed documentation
- `docs/RL_SYSTEM.md` - Architecture diagrams
- `rl_weights.json` - Saved weights (auto-generated)
- `rl_logs/` - Training history logs (auto-generated)

## Key Features

✅ **Self-Improving** - Accuracy increases with feedback  
✅ **Transparent** - All changes logged  
✅ **Persistent** - Weights and logs survive restarts  
✅ **Adaptive** - Learns which agents are reliable  
✅ **Analyzable** - Export logs for detailed analysis  

## Integration Example

```javascript
// After bot detection
const result = await verifyPostReal(post);

// User provides label
const groundTruth = getUserLabel(); // 'bot' or 'real'

// Train the system
await provideBotDetectionFeedback({
  username: post.username,
  groundTruth,
  agents: result.agents,
  botScore: result.botScore,
  classification: result.classification,
});
```

## Next Steps

1. ✅ System integrated and ready
2. 📊 Provide feedback to train
3. 📈 Monitor at `/api/rl-feedback/stats`
4. 📁 Review logs in `rl_logs/` directory
5. 📊 Export CSV for analysis
6. 🎯 Watch accuracy improve

For detailed documentation:
- `server/services/RL_README.md` - Complete API reference
- `docs/RL_SYSTEM.md` - Architecture and algorithms
