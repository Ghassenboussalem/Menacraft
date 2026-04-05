# Reinforcement Learning System Architecture

## Overview

The RL Orchestrator is a self-improving system that learns from feedback to optimize bot detection accuracy. It dynamically adjusts the weights given to different detection agents based on their historical performance.

## System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Bot Detection Request                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Run 8 Detection Agents                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Image      │  │   Reverse    │  │     OCR      │          │
│  │  Forensics   │  │    Image     │  │    Claim     │  ...     │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Get Current Agent Weights (RL)                      │
│                                                                  │
│  Image Forensics:         0.20  ◄── Dynamically adjusted        │
│  Reverse Image Search:    0.18                                  │
│  OCR + Claim Checker:     0.15                                  │
│  Caption-Image Alignment: 0.12                                  │
│  Text Content Analyzer:   0.10                                  │
│  Bot Pattern Detector:    0.10                                  │
│  Source Credibility:      0.08                                  │
│  Link Scanner:            0.07                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Calculate Weighted Bot Score                        │
│                                                                  │
│  Score = Σ (agent_score × agent_weight)                         │
│                                                                  │
│  Example: (0.8 × 0.20) + (0.6 × 0.18) + ... = 0.65             │
│  Bot Score: 65/100                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Classification                                │
│                                                                  │
│  Bot Score >= 70  → BOT                                         │
│  Bot Score <= 30  → REAL                                        │
│  Otherwise        → INCONCLUSIVE                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Return Result to User                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              User Provides Ground Truth                          │
│                                                                  │
│  POST /api/rl-feedback                                          │
│  {                                                              │
│    "groundTruth": "bot",  ◄── Actual label                     │
│    "prediction": "bot",                                         │
│    "agents": [...],                                             │
│    "botScore": 65                                               │
│  }                                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  RL Orchestrator Evaluates                       │
│                                                                  │
│  Prediction: bot                                                │
│  Ground Truth: bot                                              │
│  Result: CORRECT ✓                                              │
│  Reward: +1.0                                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Update Agent Weights                                │
│                                                                  │
│  For each agent:                                                │
│    1. Did agent signal align with ground truth?                 │
│    2. Calculate contribution to correct/incorrect decision      │
│    3. Adjust weight: new = old + (learning_rate × contribution) │
│                                                                  │
│  Example:                                                       │
│    Bot Pattern Detector signaled BAD (bot) → Correct!          │
│    Weight: 0.100 → 0.105 (+0.005)                              │
│                                                                  │
│    Image Forensics signaled OK (real) → Incorrect              │
│    Weight: 0.200 → 0.198 (-0.002)                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Normalize Weights (sum to 1.0)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Save Weights to rl_weights.json                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Next Prediction Uses Updated Weights                │
└─────────────────────────────────────────────────────────────────┘
```

## Learning Algorithm

### Weight Update Formula

```
new_weight = old_weight + (learning_rate × agent_contribution)
```

### Agent Contribution Calculation

```javascript
if (prediction_correct) {
  if (ground_truth === 'bot' && agent_signal > 0.5) {
    // Agent correctly signaled bot
    contribution = agent_signal × reward
  } else if (ground_truth === 'real' && agent_signal < 0.5) {
    // Agent correctly signaled real
    contribution = (1 - agent_signal) × reward
  }
} else {
  if (ground_truth === 'bot' && agent_signal < 0.5) {
    // Agent incorrectly signaled real when it was bot
    contribution = -(1 - agent_signal) × |punishment|
  } else if (ground_truth === 'real' && agent_signal > 0.5) {
    // Agent incorrectly signaled bot when it was real
    contribution = -agent_signal × |punishment|
  }
}
```

### Agent Signal Mapping

- `OK` → 0.0 (signals real account)
- `WARN` → 0.5 (uncertain)
- `BAD` → 1.0 (signals bot account)

## Example Scenarios

### Scenario 1: Correct Bot Detection

**Initial State:**
- Bot Pattern Detector weight: 0.100
- Image Forensics weight: 0.200

**Detection:**
- Bot Pattern Detector: BAD (1.0)
- Image Forensics: OK (0.0)
- Prediction: bot (score 65/100)

**Ground Truth:** bot ✓

**Weight Updates:**
- Bot Pattern Detector: 0.100 → 0.105 (+0.005) ✓ Helped make correct decision
- Image Forensics: 0.200 → 0.198 (-0.002) ✗ Signaled wrong direction

### Scenario 2: False Positive

**Initial State:**
- Bot Pattern Detector weight: 0.105
- Source Credibility weight: 0.080

**Detection:**
- Bot Pattern Detector: BAD (1.0)
- Source Credibility: WARN (0.5)
- Prediction: bot (score 72/100)

**Ground Truth:** real ✗

**Weight Updates:**
- Bot Pattern Detector: 0.105 → 0.095 (-0.010) ✗ Led to false positive
- Source Credibility: 0.080 → 0.078 (-0.002) ✗ Also contributed to error

### Scenario 3: Correct Real Account Detection

**Initial State:**
- Bot Pattern Detector weight: 0.095
- Source Credibility weight: 0.078

**Detection:**
- Bot Pattern Detector: OK (0.0)
- Source Credibility: OK (0.0)
- Prediction: real (score 15/100)

**Ground Truth:** real ✓

**Weight Updates:**
- Bot Pattern Detector: 0.095 → 0.100 (+0.005) ✓ Correctly signaled real
- Source Credibility: 0.078 → 0.082 (+0.004) ✓ Also correct

## Performance Metrics

### Accuracy Over Time

```
Predictions: 100
Correct: 87
Incorrect: 13
Accuracy: 87%

After 500 predictions:
Accuracy: 92% ↑ (improved through learning)
```

### Weight Evolution

```
Initial → After 100 → After 500 predictions

Bot Pattern Detector:
0.100 → 0.115 → 0.135 (increased - reliable for bot detection)

Image Forensics:
0.200 → 0.195 → 0.185 (decreased - less reliable for bot detection)

Source Credibility:
0.080 → 0.085 → 0.095 (increased - more reliable than expected)
```

## Configuration

### Hyperparameters

```javascript
learningRate: 0.01          // How fast to adapt (0.01 = 1% per update)
rewardCorrect: 1.0          // Reward for correct predictions
punishmentIncorrect: -1.0   // Punishment for errors
maxHistorySize: 1000        // Number of predictions to remember
```

### Tuning Guidelines

- **High Learning Rate (0.05+)**: Fast adaptation, but may be unstable
- **Low Learning Rate (0.001)**: Slow but stable learning
- **Recommended**: 0.01 for balanced learning

## API Reference

### Provide Feedback

```http
POST /api/rl-feedback
Content-Type: application/json

{
  "username": "account_name",
  "groundTruth": "bot",
  "agents": [...],
  "botScore": 85,
  "classification": "bot"
}
```

### Get Statistics

```http
GET /api/rl-feedback/stats
```

Response:
```json
{
  "stats": {
    "totalPredictions": 150,
    "accuracy": "87.33%",
    "correctPredictions": 131,
    "incorrectPredictions": 19
  },
  "currentWeights": {
    "Bot Pattern Detector": 0.115,
    "Image Forensics": 0.195,
    ...
  }
}
```

## Best Practices

1. **Diverse Training Data**: Provide feedback for both bots and real accounts
2. **Quality Labels**: Ensure ground truth is accurate
3. **Regular Monitoring**: Check `/api/rl-feedback/stats` to track improvement
4. **Backup Weights**: Save `rl_weights.json` before major changes
5. **Gradual Rollout**: Test RL weights on a subset before full deployment

## Troubleshooting

### Accuracy Not Improving

- Check if ground truth labels are accurate
- Ensure diverse training examples (not all bots or all real)
- Consider increasing learning rate slightly

### Weights Becoming Extreme

- Decrease learning rate
- Check for biased training data
- Reset weights and retrain with balanced dataset

### System Too Sensitive

- Decrease learning rate
- Increase punishment magnitude (more conservative updates)
- Add more training examples to stabilize weights
