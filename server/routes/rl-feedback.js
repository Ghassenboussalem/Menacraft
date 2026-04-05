const router = require('express').Router();
const { provideBotDetectionFeedback, getRLStats } = require('../services/verifyService');

/**
 * POST /api/rl-feedback
 * 
 * Provide ground truth feedback for bot detection to train the RL system
 * 
 * Body:
 * {
 *   username: string,
 *   groundTruth: 'bot' | 'real',
 *   agents: Array,
 *   botScore: number,
 *   classification: 'bot' | 'real' | 'inconclusive'
 * }
 */
router.post('/', async (req, res) => {
  try {
    const { username, groundTruth, agents, botScore, classification } = req.body;
    
    // Validate input
    if (!username) {
      return res.status(400).json({ error: 'username is required' });
    }
    
    if (!groundTruth || !['bot', 'real'].includes(groundTruth)) {
      return res.status(400).json({ error: 'groundTruth must be "bot" or "real"' });
    }
    
    if (!agents || !Array.isArray(agents)) {
      return res.status(400).json({ error: 'agents array is required' });
    }
    
    if (typeof botScore !== 'number') {
      return res.status(400).json({ error: 'botScore must be a number' });
    }
    
    if (!classification) {
      return res.status(400).json({ error: 'classification is required' });
    }
    
    // Record feedback
    const result = await provideBotDetectionFeedback({
      username,
      groundTruth,
      agents,
      botScore,
      classification,
    });
    
    res.json({
      success: true,
      message: `Feedback recorded for @${username}`,
      ...result,
    });
  } catch (err) {
    console.error('[rl-feedback] error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

/**
 * GET /api/rl-feedback/stats
 * 
 * Get RL performance statistics and current agent weights
 */
router.get('/stats', async (req, res) => {
  try {
    const stats = getRLStats();
    res.json(stats);
  } catch (err) {
    console.error('[rl-feedback/stats] error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

/**
 * GET /api/rl-feedback/logs/dates
 * 
 * Get list of available log dates
 */
router.get('/logs/dates', async (req, res) => {
  try {
    const { getRLOrchestrator } = require('../services/reinforcementLearning');
    const rlOrchestrator = getRLOrchestrator();
    
    const dates = await rlOrchestrator.getAvailableLogDates();
    res.json({ dates });
  } catch (err) {
    console.error('[rl-feedback/logs/dates] error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

/**
 * GET /api/rl-feedback/logs/:date
 * 
 * Get logs for a specific date (YYYY-MM-DD)
 */
router.get('/logs/:date', async (req, res) => {
  try {
    const { date } = req.params;
    
    // Validate date format
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
      return res.status(400).json({ error: 'Invalid date format. Use YYYY-MM-DD' });
    }
    
    const { getRLOrchestrator } = require('../services/reinforcementLearning');
    const rlOrchestrator = getRLOrchestrator();
    
    const logs = await rlOrchestrator.getLogsForDate(date);
    res.json({ date, count: logs.length, logs });
  } catch (err) {
    console.error('[rl-feedback/logs/:date] error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

/**
 * GET /api/rl-feedback/logs/range/:startDate/:endDate
 * 
 * Get aggregated statistics for a date range
 */
router.get('/logs/range/:startDate/:endDate', async (req, res) => {
  try {
    const { startDate, endDate } = req.params;
    
    // Validate date formats
    if (!/^\d{4}-\d{2}-\d{2}$/.test(startDate) || !/^\d{4}-\d{2}-\d{2}$/.test(endDate)) {
      return res.status(400).json({ error: 'Invalid date format. Use YYYY-MM-DD' });
    }
    
    const { getRLOrchestrator } = require('../services/reinforcementLearning');
    const rlOrchestrator = getRLOrchestrator();
    
    const stats = await rlOrchestrator.getStatsForDateRange(startDate, endDate);
    res.json(stats);
  } catch (err) {
    console.error('[rl-feedback/logs/range] error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

/**
 * GET /api/rl-feedback/logs/export/:startDate/:endDate
 * 
 * Export logs as CSV for a date range
 */
router.get('/logs/export/:startDate/:endDate', async (req, res) => {
  try {
    const { startDate, endDate } = req.params;
    
    // Validate date formats
    if (!/^\d{4}-\d{2}-\d{2}$/.test(startDate) || !/^\d{4}-\d{2}-\d{2}$/.test(endDate)) {
      return res.status(400).json({ error: 'Invalid date format. Use YYYY-MM-DD' });
    }
    
    const { getRLOrchestrator } = require('../services/reinforcementLearning');
    const rlOrchestrator = getRLOrchestrator();
    
    const csv = await rlOrchestrator.exportLogsAsCSV(startDate, endDate);
    
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', `attachment; filename="rl_logs_${startDate}_to_${endDate}.csv"`);
    res.send(csv);
  } catch (err) {
    console.error('[rl-feedback/logs/export] error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
