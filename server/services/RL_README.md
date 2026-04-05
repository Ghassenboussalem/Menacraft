# Reinforcement Learning Orchestrator

## Overview

The RL Orchestrator implements a reinforcement learning system that continuously improves bot detection accuracy by learning from feedback. When the system correctly identifies whether an account is real or a bot, it receives a reward and adjusts the weights given to different detection agents. When it makes a mistake, it receives a punishment and adjusts accordingly.

## How It Works

### 1. Agent Weights

The orchestrator maintains dynamic weights for 8 detection agents:

- **Image Forensics** (initial: 0.20) - AI-generated image detection
- **Reverse Image Search** (initial: 0.18) - Temporal provenance checking
- **OCR + Claim Checker** (initial: 0.15) - Visual claim verification
- **Caption–Image Alignment** (initial: 0.12) - Semantic alignment
- **Text Content Analyzer** (initial: 0.10) - AI text detection
- **Bot Pattern Detector** (initial: 0.10) - Account behavior analysis
- **Source Credibility** (initial: 0.08) - Source reputation
- **Link Scanner** (initial: 0.07) - URL safety analysis

### 2. Learning Process

When ground truth is provided:

1. **Prediction**: System classifies account as 'bot' or 'real' based on weighted agent scores
2. **Comparison**: Prediction is compared to ground truth
3. **Reward/Punishment**:
   - Correct prediction: +1.0 reward
   - Incorrect prediction: -1.0 punishment
4. **Weight Update**: Agent weights are adjusted based on their contribution:
   - Agents that helped make correct decision → weight increased
   - Agents that led to wrong decision → weight decreased
5. **Normalization**: Weights are normalized to sum to 1.0
6. **Persistence**: Updated weights are saved to disk

### 3. Gradient-Based Updates

The system uses a gradient-based approach:

```
new_weight = old_weight + (learning_rate × agent_contribution)
```

Where:
- `learning_rate = 0.01` (how fast to adapt)
- `agent_contribution` depends on:
  - Whether prediction was correct
  - How strongly the agent signaled bot/real
  - Whether agent's signal aligned with ground truth

## API Usage

### Provide Feedback

After bot detection, provide ground truth to train the system:

```bash
POST /api/rl-feedback
Content-Type: application/json

{
  "username": "suspicious_account",
  "groundTruth": "bot",
  "agents": [...],  // Agent results from verification
  "botScore": 85.3,
  "classification": "bot"
}
```

Response:
```json
{
  "success": true,
  "message": "Feedback recorded for @suspicious_account",
  "isCorrect": true,
  "reward": 1.0,
  "updatedWeights": {
    "Image Forensics": 0.21,
    "Bot Pattern Detector": 0.12,
    ...
  }
}
```

### Get Statistics

View RL performance and current weights:

```bash
GET /api/rl-feedback/stats
```

Response:
```json
{
  "stats": {
    "totalPredictions": 150,
    "accuracy": "87.33%",
    "correctPredictions": 131,
    "incorrectPredictions": 19,
    "recentHistory": [...]
  },
  "currentWeights": {
    "Image Forensics": 0.21,
    "Reverse Image Search": 0.19,
    ...
  }
}
```

## Integration Example

### In Your Verification Flow

```javascript
// 1. Run bot detection
const result = await verifyPostReal(post);
const botAgent = result.agents.find(a => a.name === 'Bot Pattern Detector');
const botScore = botAgent?.raw?.bot_score || 50;
const classification = botAgent?.raw?.classification || 'inconclusive';

// 2. User provides ground truth (via UI or manual review)
const groundTruth = 'bot'; // or 'real'

// 3. Send feedback to RL system
await fetch('/api/rl-feedback', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: post.username,
    groundTruth,
    agents: result.agents,
    botScore,
    classification,
  }),
});
```

### Automated Feedback Loop

For accounts with verified labels (e.g., from Instagram's verified badge or known bot databases):

```javascript
async function verifyWithAutoFeedback(post, knownLabel) {
  const result = await verifyPostReal(post);
  
  // Extract bot detection info
  const botAgent = result.agents.find(a => a.name === 'Bot Pattern Detector');
  
  if (knownLabel && botAgent) {
    // Automatically provide feedback
    await provideBotDetectionFeedback({
      username: post.username,
      groundTruth: knownLabel, // 'bot' or 'real'
      agents: result.agents,
      botScore: botAgent.raw?.bot_score || 50,
      classification: botAgent.raw?.classification || 'inconclusive',
    });
  }
  
  return result;
}
```

## Configuration

Edit `server/services/reinforcementLearning.js` to adjust:

- `learningRate`: How fast weights adapt (default: 0.01)
- `rewardCorrect`: Reward for correct predictions (default: 1.0)
- `punishmentIncorrect`: Punishment for errors (default: -1.0)
- `maxHistorySize`: Number of records to keep (default: 1000)
- `weightsPath`: Where to save weights (default: './rl_weights.json')

## Monitoring

### View Current Weights

```bash
curl http://localhost:3001/api/rl-feedback/stats
```

### Access History Logs

**Get available log dates:**
```bash
curl http://localhost:3001/api/rl-feedback/logs/dates
```

**Get logs for a specific date:**
```bash
curl http://localhost:3001/api/rl-feedback/logs/2026-04-05
```

**Get stats for a date range:**
```bash
curl http://localhost:3001/api/rl-feedback/logs/range/2026-04-01/2026-04-05
```

**Export logs as CSV:**
```bash
curl http://localhost:3001/api/rl-feedback/logs/export/2026-04-01/2026-04-05 > rl_logs.csv
```

### Log Files

The system creates two types of log files in the `rl_logs/` directory:

1. **JSON Lines Format** (`rl_log_YYYY-MM-DD.jsonl`):
   - Machine-readable format
   - One JSON object per line
   - Contains complete prediction details

2. **Human-Readable Summary** (`rl_summary_YYYY-MM-DD.log`):
   - Easy to read format
   - Shows predictions, rewards, and weight changes
   - Great for quick review

### Check Learning Progress

The system logs all weight updates:

```
[RL] Prediction for @bot_account: bot (actual: bot) - CORRECT ✓
[RL] Reward: +1
[RL] Weight adjustments: {
  'Bot Pattern Detector': { old: '0.100', new: '0.105', change: '+0.0050' },
  'Image Forensics': { old: '0.200', new: '0.198', change: '-0.0020' }
}
```

## Best Practices

1. **Provide Diverse Feedback**: Train on both bots and real accounts
2. **Quality Over Quantity**: Accurate ground truth is more important than volume
3. **Monitor Accuracy**: Check `/api/rl-feedback/stats` regularly
4. **Review Logs**: Analyze `/api/rl-feedback/logs/dates` to track progress
5. **Export Data**: Use CSV export for detailed analysis in Excel/Google Sheets
6. **Gradual Learning**: The system learns slowly (0.01 rate) to avoid overfitting
7. **Backup Weights**: The `rl_weights.json` file contains learned knowledge
8. **Backup Logs**: The `rl_logs/` directory contains complete training history

## Persistence

Weights and logs are automatically saved:

- **Weights**: `rl_weights.json` - Updated after each feedback
- **Logs**: `rl_logs/` directory - Daily log files in JSON Lines and summary formats

To reset:

```bash
# Reset weights only
rm rl_weights.json

# Reset everything (weights + logs)
rm rl_weights.json
rm -rf rl_logs/

# Restart server - will use default weights
```

## API Endpoints

### Feedback
- `POST /api/rl-feedback` - Provide ground truth feedback

### Statistics
- `GET /api/rl-feedback/stats` - Get current stats and weights

### Logs
- `GET /api/rl-feedback/logs/dates` - List available log dates
- `GET /api/rl-feedback/logs/:date` - Get logs for specific date
- `GET /api/rl-feedback/logs/range/:start/:end` - Get aggregated stats for date range
- `GET /api/rl-feedback/logs/export/:start/:end` - Export logs as CSV

## Future Enhancements

Potential improvements:

- **Adaptive Learning Rate**: Decrease learning rate as accuracy improves
- **Confidence-Weighted Updates**: Stronger updates for high-confidence predictions
- **Multi-Armed Bandit**: Explore/exploit tradeoff for agent selection
- **Deep RL**: Replace gradient updates with neural network policy
- **A/B Testing**: Compare RL weights vs. static weights
