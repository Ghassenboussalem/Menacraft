/**
 * Standalone RL History Logging Demo
 * 
 * This demonstrates the RL system without needing the server running
 */

const { ReinforcementLearningOrchestrator } = require('../services/reinforcementLearning');
const fs = require('fs').promises;
const path = require('path');

async function demonstrateRLLogging() {
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║  RL History Logging - Standalone Demo                     ║');
  console.log('╚════════════════════════════════════════════════════════════╝\n');

  // Create RL orchestrator with demo paths
  const demoWeightsPath = './demo_rl_weights.json';
  const demoLogsPath = './demo_rl_logs';
  
  const rl = new ReinforcementLearningOrchestrator(demoWeightsPath, demoLogsPath);
  
  console.log('📊 Initial Agent Weights:');
  const initialWeights = rl.getWeights();
  for (const [agent, weight] of Object.entries(initialWeights)) {
    console.log(`  ${agent}: ${weight.toFixed(3)}`);
  }
  
  console.log('\n' + '='.repeat(70));
  console.log('SCENARIO 1: Correct Bot Detection');
  console.log('='.repeat(70) + '\n');
  
  // Simulate correct bot detection
  const agents1 = [
    { name: 'Bot Pattern Detector', score: 'BAD', finding: 'Bot score: 85/100 - High bot probability' },
    { name: 'Source Credibility', score: 'WARN', finding: 'Low credibility - Mixed signals' },
    { name: 'Image Forensics', score: 'OK', finding: 'No manipulation detected' },
    { name: 'Reverse Image Search', score: 'OK', finding: 'No prior reuse detected' },
  ];
  
  console.log('🤖 Detected Account: @suspicious_bot_123');
  console.log('📈 Bot Score: 85/100');
  console.log('🎯 Prediction: BOT');
  console.log('✅ Ground Truth: BOT (Correct!)');
  console.log('\nAgent Signals:');
  agents1.forEach(a => console.log(`  - ${a.name}: ${a.score}`));
  
  const result1 = await rl.recordPrediction({
    agents: agents1,
    prediction: 'bot',
    groundTruth: 'bot',
    username: 'suspicious_bot_123',
    botScore: 85,
  });
  
  console.log('\n📊 Result:');
  console.log(`  Correct: ${result1.isCorrect}`);
  console.log(`  Reward: ${result1.reward > 0 ? '+' : ''}${result1.reward}`);
  console.log('\n⚖️ Weight Adjustments:');
  for (const [agent, adj] of Object.entries(result1.weightAdjustments)) {
    console.log(`  ${agent}:`);
    console.log(`    ${adj.old} → ${adj.new} (${adj.change > 0 ? '+' : ''}${adj.change})`);
  }
  
  console.log('\n' + '='.repeat(70));
  console.log('SCENARIO 2: False Positive (Real Account Flagged as Bot)');
  console.log('='.repeat(70) + '\n');
  
  // Simulate false positive
  const agents2 = [
    { name: 'Bot Pattern Detector', score: 'BAD', finding: 'Bot score: 72/100 - Suspicious patterns' },
    { name: 'Source Credibility', score: 'WARN', finding: 'Low engagement metrics' },
    { name: 'Image Forensics', score: 'OK', finding: 'Authentic images' },
    { name: 'Caption–Image Alignment', score: 'OK', finding: 'Strong alignment' },
  ];
  
  console.log('👤 Detected Account: @real_user_456');
  console.log('📈 Bot Score: 72/100');
  console.log('🎯 Prediction: BOT');
  console.log('❌ Ground Truth: REAL (Incorrect - False Positive!)');
  console.log('\nAgent Signals:');
  agents2.forEach(a => console.log(`  - ${a.name}: ${a.score}`));
  
  const result2 = await rl.recordPrediction({
    agents: agents2,
    prediction: 'bot',
    groundTruth: 'real',
    username: 'real_user_456',
    botScore: 72,
  });
  
  console.log('\n📊 Result:');
  console.log(`  Correct: ${result2.isCorrect}`);
  console.log(`  Reward: ${result2.reward > 0 ? '+' : ''}${result2.reward}`);
  console.log('\n⚖️ Weight Adjustments (Punishment):');
  for (const [agent, adj] of Object.entries(result2.weightAdjustments)) {
    console.log(`  ${agent}:`);
    console.log(`    ${adj.old} → ${adj.new} (${adj.change > 0 ? '+' : ''}${adj.change})`);
  }
  
  console.log('\n' + '='.repeat(70));
  console.log('SCENARIO 3: Correct Real Account Detection');
  console.log('='.repeat(70) + '\n');
  
  // Simulate correct real account detection
  const agents3 = [
    { name: 'Bot Pattern Detector', score: 'OK', finding: 'Bot score: 25/100 - Organic behavior' },
    { name: 'Source Credibility', score: 'OK', finding: 'High credibility signals' },
    { name: 'Image Forensics', score: 'OK', finding: 'Authentic content' },
    { name: 'Reverse Image Search', score: 'OK', finding: 'Original images' },
  ];
  
  console.log('👤 Detected Account: @verified_user_789');
  console.log('📈 Bot Score: 25/100');
  console.log('🎯 Prediction: REAL');
  console.log('✅ Ground Truth: REAL (Correct!)');
  console.log('\nAgent Signals:');
  agents3.forEach(a => console.log(`  - ${a.name}: ${a.score}`));
  
  const result3 = await rl.recordPrediction({
    agents: agents3,
    prediction: 'real',
    groundTruth: 'real',
    username: 'verified_user_789',
    botScore: 25,
  });
  
  console.log('\n📊 Result:');
  console.log(`  Correct: ${result3.isCorrect}`);
  console.log(`  Reward: ${result3.reward > 0 ? '+' : ''}${result3.reward}`);
  console.log('\n⚖️ Weight Adjustments:');
  for (const [agent, adj] of Object.entries(result3.weightAdjustments)) {
    console.log(`  ${agent}:`);
    console.log(`    ${adj.old} → ${adj.new} (${adj.change > 0 ? '+' : ''}${adj.change})`);
  }
  
  // Add a few more predictions for better stats
  console.log('\n' + '='.repeat(70));
  console.log('Adding more predictions for statistics...');
  console.log('='.repeat(70) + '\n');
  
  const morePredictions = [
    { username: 'bot_account_1', prediction: 'bot', groundTruth: 'bot', botScore: 90 },
    { username: 'bot_account_2', prediction: 'bot', groundTruth: 'bot', botScore: 88 },
    { username: 'real_account_1', prediction: 'real', groundTruth: 'real', botScore: 20 },
    { username: 'real_account_2', prediction: 'real', groundTruth: 'real', botScore: 15 },
    { username: 'false_negative', prediction: 'real', groundTruth: 'bot', botScore: 45 },
  ];
  
  for (const pred of morePredictions) {
    const agents = [
      { name: 'Bot Pattern Detector', score: pred.botScore >= 70 ? 'BAD' : pred.botScore >= 30 ? 'WARN' : 'OK', finding: `Bot score: ${pred.botScore}/100` },
    ];
    
    await rl.recordPrediction({
      agents,
      prediction: pred.prediction,
      groundTruth: pred.groundTruth,
      username: pred.username,
      botScore: pred.botScore,
    });
    
    console.log(`✓ Processed @${pred.username}: ${pred.prediction === pred.groundTruth ? 'CORRECT' : 'INCORRECT'}`);
  }
  
  console.log('\n' + '='.repeat(70));
  console.log('OVERALL STATISTICS');
  console.log('='.repeat(70) + '\n');
  
  const stats = rl.getStats();
  console.log('📊 Performance Metrics:');
  console.log(`  Total Predictions: ${stats.totalPredictions}`);
  console.log(`  Accuracy: ${stats.accuracy}`);
  console.log(`  Correct: ${stats.correctPredictions}`);
  console.log(`  Incorrect: ${stats.incorrectPredictions}`);
  
  console.log('\n📈 Final Agent Weights:');
  const finalWeights = rl.getWeights();
  for (const [agent, weight] of Object.entries(finalWeights)) {
    const initial = initialWeights[agent];
    const change = weight - initial;
    const changePercent = ((change / initial) * 100).toFixed(1);
    const arrow = change > 0 ? '↑' : change < 0 ? '↓' : '→';
    
    console.log(`  ${agent}:`);
    console.log(`    ${initial.toFixed(3)} → ${weight.toFixed(3)} (${arrow} ${change > 0 ? '+' : ''}${changePercent}%)`);
  }
  
  console.log('\n' + '='.repeat(70));
  console.log('LOG FILES CREATED');
  console.log('='.repeat(70) + '\n');
  
  const today = new Date().toISOString().split('T')[0];
  const jsonLogPath = path.join(demoLogsPath, `rl_log_${today}.jsonl`);
  const summaryLogPath = path.join(demoLogsPath, `rl_summary_${today}.log`);
  
  console.log('📁 Log Files:');
  console.log(`  1. JSON Lines: ${jsonLogPath}`);
  console.log(`  2. Summary: ${summaryLogPath}`);
  
  // Show sample from JSON log
  try {
    const jsonContent = await fs.readFile(jsonLogPath, 'utf8');
    const lines = jsonContent.trim().split('\n');
    console.log(`\n📄 JSON Log Sample (first entry):`);
    const firstEntry = JSON.parse(lines[0]);
    console.log(JSON.stringify({
      timestamp: firstEntry.timestamp,
      username: firstEntry.username,
      prediction: firstEntry.prediction,
      groundTruth: firstEntry.groundTruth,
      isCorrect: firstEntry.isCorrect,
      reward: firstEntry.reward,
      botScore: firstEntry.botScore,
      agentCount: firstEntry.agentScores.length,
    }, null, 2));
  } catch (err) {
    console.log('  (Could not read JSON log)');
  }
  
  // Show sample from summary log
  try {
    const summaryContent = await fs.readFile(summaryLogPath, 'utf8');
    const lines = summaryContent.split('\n').slice(0, 20);
    console.log(`\n📄 Summary Log Sample (first entry):`);
    console.log(lines.join('\n'));
  } catch (err) {
    console.log('  (Could not read summary log)');
  }
  
  console.log('\n' + '='.repeat(70));
  console.log('ACCESSING LOGS PROGRAMMATICALLY');
  console.log('='.repeat(70) + '\n');
  
  // Demonstrate log retrieval
  const dates = await rl.getAvailableLogDates();
  console.log('📅 Available Log Dates:', dates);
  
  if (dates.length > 0) {
    const todayLogs = await rl.getLogsForDate(dates[0]);
    console.log(`\n📊 Logs for ${dates[0]}: ${todayLogs.length} predictions`);
    
    // Show date range stats
    const rangeStats = await rl.getStatsForDateRange(dates[0], dates[0]);
    console.log('\n📈 Date Range Statistics:');
    console.log(`  Total Predictions: ${rangeStats.totalPredictions}`);
    console.log(`  Accuracy: ${rangeStats.accuracy}`);
    
    if (rangeStats.agentStats) {
      console.log('\n🎯 Per-Agent Performance:');
      for (const [agentName, agentStat] of Object.entries(rangeStats.agentStats)) {
        console.log(`  ${agentName}:`);
        console.log(`    - Accuracy: ${agentStat.accuracy}`);
        console.log(`    - Avg Weight: ${agentStat.avgWeight}`);
      }
    }
    
    // Demonstrate CSV export
    console.log('\n📊 CSV Export Sample:');
    const csv = await rl.exportLogsAsCSV(dates[0], dates[0]);
    const csvLines = csv.split('\n').slice(0, 4);
    console.log(csvLines.join('\n'));
    console.log('...');
  }
  
  console.log('\n' + '='.repeat(70));
  console.log('✅ DEMO COMPLETE');
  console.log('='.repeat(70) + '\n');
  
  console.log('Key Takeaways:');
  console.log('1. ✅ System learns from feedback (correct predictions increase weights)');
  console.log('2. ❌ System adapts to mistakes (incorrect predictions decrease weights)');
  console.log('3. 📁 Complete history logged in two formats (JSON + Summary)');
  console.log('4. 📊 Statistics tracked and easily accessible');
  console.log('5. 📈 Weight evolution visible over time');
  console.log('6. 📄 CSV export available for external analysis');
  
  console.log('\n📂 Demo Files Created:');
  console.log(`  - ${demoWeightsPath}`);
  console.log(`  - ${demoLogsPath}/`);
  console.log('\nYou can inspect these files to see the RL system in action!');
  
  // Cleanup option
  console.log('\n🧹 To clean up demo files, run:');
  console.log(`  rm ${demoWeightsPath}`);
  console.log(`  rm -rf ${demoLogsPath}`);
}

// Run demo
if (require.main === module) {
  demonstrateRLLogging().catch(err => {
    console.error('❌ Demo failed:', err);
    process.exit(1);
  });
}

module.exports = { demonstrateRLLogging };
