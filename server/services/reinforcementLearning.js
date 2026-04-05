const fs = require('fs').promises;
const path = require('path');

/**
 * Reinforcement Learning Module for Agent Weight Optimization
 * 
 * This module implements a simple RL system that:
 * - Tracks bot detection predictions vs ground truth
 * - Rewards/punishes the orchestrator based on accuracy
 * - Adjusts agent weights dynamically to improve performance
 */

class ReinforcementLearningOrchestrator {
  constructor(weightsPath = './rl_weights.json', logsPath = './rl_logs') {
    this.weightsPath = weightsPath;
    this.logsPath = logsPath;
    
    // Initial agent weights (same as AGENT_WEIGHTS in verifyService.js)
    this.agentWeights = {
      'Image Forensics':         0.20,
      'Reverse Image Search':    0.18,
      'OCR + Claim Checker':     0.15,
      'Caption–Image Alignment': 0.12,
      'Text Content Analyzer':   0.10,
      'Bot Pattern Detector':    0.10,
      'Source Credibility':      0.08,
      'Link Scanner':            0.07,
    };
    
    // RL hyperparameters
    this.learningRate = 0.01;        // How fast to adjust weights
    this.rewardCorrect = 1.0;        // Reward for correct prediction
    this.punishmentIncorrect = -1.0; // Punishment for incorrect prediction
    
    // History tracking
    this.history = [];
    this.maxHistorySize = 1000;
    
    // Session tracking
    this.sessionId = Date.now();
    this.sessionStartTime = new Date().toISOString();
    
    // Load saved weights if they exist
    this.loadWeights();
    
    // Initialize logs directory
    this.initializeLogsDirectory();
  }
  
  /**
   * Initialize logs directory
   */
  async initializeLogsDirectory() {
    try {
      await fs.mkdir(this.logsPath, { recursive: true });
      console.log(`[RL] Logs directory initialized: ${this.logsPath}`);
    } catch (err) {
      console.error('[RL] Failed to create logs directory:', err.message);
    }
  }
  
  /**
   * Load saved weights from disk
   */
  async loadWeights() {
    try {
      const data = await fs.readFile(this.weightsPath, 'utf8');
      const saved = JSON.parse(data);
      
      if (saved.agentWeights) {
        this.agentWeights = saved.agentWeights;
        console.log('[RL] Loaded saved agent weights');
      }
      
      if (saved.history) {
        this.history = saved.history.slice(-this.maxHistorySize);
        console.log(`[RL] Loaded ${this.history.length} historical records`);
      }
    } catch (err) {
      console.log('[RL] No saved weights found, using defaults');
    }
  }
  
  /**
   * Save current weights to disk
   */
  async saveWeights() {
    try {
      const data = {
        agentWeights: this.agentWeights,
        history: this.history.slice(-this.maxHistorySize),
        lastUpdated: new Date().toISOString(),
      };
      
      await fs.writeFile(this.weightsPath, JSON.stringify(data, null, 2));
      console.log('[RL] Saved agent weights');
    } catch (err) {
      console.error('[RL] Failed to save weights:', err.message);
    }
  }
  
  /**
   * Get current agent weights
   */
  getWeights() {
    return { ...this.agentWeights };
  }
  
  /**
   * Calculate bot score from agent results using current weights
   */
  calculateWeightedBotScore(agents) {
    let weightedSum = 0;
    let totalWeight = 0;
    
    for (const agent of agents) {
      if (!agent || !agent.name) continue;
      
      const weight = this.agentWeights[agent.name] || 0.10;
      
      // Convert agent score to numeric value
      let score = 0;
      if (agent.score === 'OK') score = 0;      // Low bot probability
      else if (agent.score === 'WARN') score = 0.5;  // Medium
      else if (agent.score === 'BAD') score = 1.0;   // High bot probability
      
      // Skip neutral/skipped agents
      const isNeutral = agent.finding && (
        agent.finding.includes('skipped') ||
        agent.finding.includes('No external URLs') ||
        agent.finding.includes('No significant text')
      );
      
      if (isNeutral) continue;
      
      weightedSum += score * weight;
      totalWeight += weight;
    }
    
    if (totalWeight === 0) return 50; // Neutral
    
    // Return 0-100 bot score
    return Math.round((weightedSum / totalWeight) * 100);
  }
  
  /**
   * Record a prediction and update weights based on ground truth
   * 
   * @param {Object} params
   * @param {Array} params.agents - Agent results
   * @param {string} params.prediction - 'bot' or 'real'
   * @param {string} params.groundTruth - 'bot' or 'real' (actual label)
   * @param {string} params.username - Account username
   * @param {number} params.botScore - Calculated bot score (0-100)
   */
  async recordPrediction({ agents, prediction, groundTruth, username, botScore }) {
    const isCorrect = prediction === groundTruth;
    const reward = isCorrect ? this.rewardCorrect : this.punishmentIncorrect;
    
    console.log(`[RL] Prediction for @${username}: ${prediction} (actual: ${groundTruth}) - ${isCorrect ? 'CORRECT ✓' : 'INCORRECT ✗'}`);
    console.log(`[RL] Reward: ${reward > 0 ? '+' : ''}${reward}`);
    
    // Capture weights before update
    const weightsBefore = { ...this.agentWeights };
    
    // Record in history
    const record = {
      timestamp: new Date().toISOString(),
      sessionId: this.sessionId,
      username,
      prediction,
      groundTruth,
      isCorrect,
      reward,
      botScore,
      agentScores: agents.map(a => ({
        name: a.name,
        score: a.score,
        weight: this.agentWeights[a.name] || 0.10,
        finding: a.finding,
      })),
      weightsBefore,
    };
    
    this.history.push(record);
    if (this.history.length > this.maxHistorySize) {
      this.history.shift();
    }
    
    // Update weights based on agent contributions
    const weightAdjustments = await this.updateWeights(agents, reward, prediction, groundTruth);
    
    // Add weight changes to record
    record.weightsAfter = { ...this.agentWeights };
    record.weightAdjustments = weightAdjustments;
    
    // Log to file
    await this.logPrediction(record);
    
    // Save updated weights
    await this.saveWeights();
    
    return {
      isCorrect,
      reward,
      updatedWeights: this.getWeights(),
      weightAdjustments,
    };
  }
  
  /**
   * Update agent weights using gradient-based RL
   * 
   * Strategy:
   * - If prediction was correct, increase weights of agents that contributed to correct decision
   * - If prediction was incorrect, decrease weights of agents that led to wrong decision
   */
  async updateWeights(agents, reward, prediction, groundTruth) {
    const adjustments = {};
    
    for (const agent of agents) {
      if (!agent || !agent.name) continue;
      
      const agentName = agent.name;
      const currentWeight = this.agentWeights[agentName] || 0.10;
      
      // Skip neutral agents
      const isNeutral = agent.finding && (
        agent.finding.includes('skipped') ||
        agent.finding.includes('No external URLs') ||
        agent.finding.includes('No significant text')
      );
      if (isNeutral) continue;
      
      // Determine if this agent's signal aligned with the prediction
      let agentSignal = 0;
      if (agent.score === 'BAD') agentSignal = 1;      // Signaled bot
      else if (agent.score === 'WARN') agentSignal = 0.5;
      else if (agent.score === 'OK') agentSignal = 0;  // Signaled real
      
      // Determine if agent was helpful or harmful
      let agentContribution = 0;
      
      if (reward > 0) {
        // Correct prediction
        if (groundTruth === 'bot' && agentSignal > 0.5) {
          // Agent correctly signaled bot
          agentContribution = agentSignal * reward;
        } else if (groundTruth === 'real' && agentSignal < 0.5) {
          // Agent correctly signaled real
          agentContribution = (1 - agentSignal) * reward;
        }
      } else {
        // Incorrect prediction
        if (groundTruth === 'bot' && agentSignal < 0.5) {
          // Agent incorrectly signaled real when it was bot
          agentContribution = -(1 - agentSignal) * Math.abs(reward);
        } else if (groundTruth === 'real' && agentSignal > 0.5) {
          // Agent incorrectly signaled bot when it was real
          agentContribution = -agentSignal * Math.abs(reward);
        }
      }
      
      // Update weight with gradient
      const weightAdjustment = this.learningRate * agentContribution;
      const newWeight = Math.max(0.01, Math.min(0.50, currentWeight + weightAdjustment));
      
      adjustments[agentName] = {
        old: currentWeight.toFixed(3),
        new: newWeight.toFixed(3),
        change: weightAdjustment.toFixed(4),
        agentSignal: agentSignal.toFixed(2),
        contribution: agentContribution.toFixed(4),
      };
      
      this.agentWeights[agentName] = newWeight;
    }
    
    // Normalize weights to sum to 1.0
    this.normalizeWeights();
    
    console.log('[RL] Weight adjustments:', adjustments);
    
    return adjustments;
  }
  
  /**
   * Normalize weights so they sum to 1.0
   */
  normalizeWeights() {
    const sum = Object.values(this.agentWeights).reduce((a, b) => a + b, 0);
    
    if (sum > 0) {
      for (const key in this.agentWeights) {
        this.agentWeights[key] = this.agentWeights[key] / sum;
      }
    }
  }
  
  /**
   * Get performance statistics
   */
  getStats() {
    if (this.history.length === 0) {
      return {
        totalPredictions: 0,
        accuracy: 0,
        correctPredictions: 0,
        incorrectPredictions: 0,
      };
    }
    
    const correct = this.history.filter(r => r.isCorrect).length;
    const total = this.history.length;
    
    return {
      totalPredictions: total,
      accuracy: (correct / total * 100).toFixed(2) + '%',
      correctPredictions: correct,
      incorrectPredictions: total - correct,
      recentHistory: this.history.slice(-10),
    };
  }
  
  /**
   * Log prediction to file
   */
  async logPrediction(record) {
    try {
      const date = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
      const logFile = path.join(this.logsPath, `rl_log_${date}.jsonl`);
      
      // Append as JSON Lines format (one JSON object per line)
      const logLine = JSON.stringify(record) + '\n';
      await fs.appendFile(logFile, logLine);
      
      // Also create a human-readable summary log
      await this.logSummary(record, date);
    } catch (err) {
      console.error('[RL] Failed to write log:', err.message);
    }
  }
  
  /**
   * Log human-readable summary
   */
  async logSummary(record, date) {
    try {
      const summaryFile = path.join(this.logsPath, `rl_summary_${date}.log`);
      
      const summary = [
        `\n${'='.repeat(80)}`,
        `Timestamp: ${record.timestamp}`,
        `Username: @${record.username}`,
        `Prediction: ${record.prediction.toUpperCase()} | Ground Truth: ${record.groundTruth.toUpperCase()}`,
        `Result: ${record.isCorrect ? '✓ CORRECT' : '✗ INCORRECT'} | Reward: ${record.reward > 0 ? '+' : ''}${record.reward}`,
        `Bot Score: ${record.botScore}/100`,
        ``,
        `Agent Scores:`,
        ...record.agentScores.map(a => 
          `  - ${a.name}: ${a.score} (weight: ${a.weight.toFixed(3)}) - ${a.finding}`
        ),
        ``,
        `Weight Adjustments:`,
        ...Object.entries(record.weightAdjustments || {}).map(([name, adj]) =>
          `  - ${name}: ${adj.old} → ${adj.new} (${adj.change > 0 ? '+' : ''}${adj.change})`
        ),
        `${'='.repeat(80)}\n`,
      ].join('\n');
      
      await fs.appendFile(summaryFile, summary);
    } catch (err) {
      console.error('[RL] Failed to write summary log:', err.message);
    }
  }
  
  /**
   * Get logs for a specific date
   */
  async getLogsForDate(date) {
    try {
      const logFile = path.join(this.logsPath, `rl_log_${date}.jsonl`);
      const content = await fs.readFile(logFile, 'utf8');
      
      // Parse JSON Lines format
      const logs = content
        .trim()
        .split('\n')
        .filter(line => line.trim())
        .map(line => JSON.parse(line));
      
      return logs;
    } catch (err) {
      if (err.code === 'ENOENT') {
        return []; // No logs for this date
      }
      throw err;
    }
  }
  
  /**
   * Get all available log dates
   */
  async getAvailableLogDates() {
    try {
      const files = await fs.readdir(this.logsPath);
      const logFiles = files.filter(f => f.startsWith('rl_log_') && f.endsWith('.jsonl'));
      
      const dates = logFiles.map(f => {
        const match = f.match(/rl_log_(\d{4}-\d{2}-\d{2})\.jsonl/);
        return match ? match[1] : null;
      }).filter(Boolean);
      
      return dates.sort().reverse(); // Most recent first
    } catch (err) {
      console.error('[RL] Failed to read log directory:', err.message);
      return [];
    }
  }
  
  /**
   * Get aggregated statistics for a date range
   */
  async getStatsForDateRange(startDate, endDate) {
    try {
      const dates = await this.getAvailableLogDates();
      const relevantDates = dates.filter(d => d >= startDate && d <= endDate);
      
      let allLogs = [];
      for (const date of relevantDates) {
        const logs = await this.getLogsForDate(date);
        allLogs = allLogs.concat(logs);
      }
      
      if (allLogs.length === 0) {
        return {
          dateRange: { start: startDate, end: endDate },
          totalPredictions: 0,
          accuracy: '0%',
          correctPredictions: 0,
          incorrectPredictions: 0,
        };
      }
      
      const correct = allLogs.filter(r => r.isCorrect).length;
      const total = allLogs.length;
      
      // Calculate per-agent accuracy
      const agentStats = {};
      for (const log of allLogs) {
        for (const agent of log.agentScores) {
          if (!agentStats[agent.name]) {
            agentStats[agent.name] = {
              total: 0,
              correctSignals: 0,
              weights: [],
            };
          }
          
          agentStats[agent.name].total++;
          agentStats[agent.name].weights.push(agent.weight);
          
          // Check if agent's signal was correct
          const signalBot = agent.score === 'BAD' || agent.score === 'WARN';
          const actualBot = log.groundTruth === 'bot';
          if (signalBot === actualBot) {
            agentStats[agent.name].correctSignals++;
          }
        }
      }
      
      // Calculate average weights and accuracy per agent
      for (const agentName in agentStats) {
        const stats = agentStats[agentName];
        stats.accuracy = ((stats.correctSignals / stats.total) * 100).toFixed(2) + '%';
        stats.avgWeight = (stats.weights.reduce((a, b) => a + b, 0) / stats.weights.length).toFixed(3);
        delete stats.weights; // Remove raw weights array
      }
      
      return {
        dateRange: { start: startDate, end: endDate },
        totalPredictions: total,
        accuracy: (correct / total * 100).toFixed(2) + '%',
        correctPredictions: correct,
        incorrectPredictions: total - correct,
        agentStats,
        logs: allLogs,
      };
    } catch (err) {
      console.error('[RL] Failed to get stats for date range:', err.message);
      throw err;
    }
  }
  
  /**
   * Export logs as CSV
   */
  async exportLogsAsCSV(startDate, endDate) {
    try {
      const stats = await this.getStatsForDateRange(startDate, endDate);
      
      if (stats.logs.length === 0) {
        return 'No logs found for the specified date range';
      }
      
      // CSV header
      const header = [
        'Timestamp',
        'Username',
        'Prediction',
        'Ground Truth',
        'Is Correct',
        'Reward',
        'Bot Score',
        'Session ID',
      ].join(',');
      
      // CSV rows
      const rows = stats.logs.map(log => [
        log.timestamp,
        log.username,
        log.prediction,
        log.groundTruth,
        log.isCorrect,
        log.reward,
        log.botScore,
        log.sessionId || 'N/A',
      ].join(','));
      
      return [header, ...rows].join('\n');
    } catch (err) {
      console.error('[RL] Failed to export CSV:', err.message);
      throw err;
    }
  }
  
  /**
   * Get performance statistics
   */
  getStats() {
    if (this.history.length === 0) {
      return {
        totalPredictions: 0,
        accuracy: 0,
        correctPredictions: 0,
        incorrectPredictions: 0,
      };
    }
    
    const correct = this.history.filter(r => r.isCorrect).length;
    const total = this.history.length;
    
    return {
      totalPredictions: total,
      accuracy: (correct / total * 100).toFixed(2) + '%',
      correctPredictions: correct,
      incorrectPredictions: total - correct,
      recentHistory: this.history.slice(-10),
    };
  }
}

// Singleton instance
let rlOrchestrator = null;

function getRLOrchestrator() {
  if (!rlOrchestrator) {
    rlOrchestrator = new ReinforcementLearningOrchestrator();
  }
  return rlOrchestrator;
}

module.exports = {
  ReinforcementLearningOrchestrator,
  getRLOrchestrator,
};
