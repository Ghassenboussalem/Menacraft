/**
 * Example: Accessing RL History Logs
 * 
 * This script demonstrates how to access and analyze RL training logs
 */

const http = require('http');

const API_BASE = 'http://localhost:3001';

// Helper to make HTTP requests
function apiRequest(path, method = 'GET', body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, API_BASE);
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname,
      method,
      headers: method === 'POST' ? {
        'Content-Type': 'application/json',
      } : {},
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          resolve(data); // Return raw data for CSV
        }
      });
    });

    req.on('error', reject);
    
    if (body) {
      req.write(JSON.stringify(body));
    }
    
    req.end();
  });
}

// Example 1: Get available log dates
async function example1_GetLogDates() {
  console.log('\n=== Example 1: Get Available Log Dates ===\n');
  
  const result = await apiRequest('/api/rl-feedback/logs/dates', 'GET');
  console.log('Available log dates:', result.dates);
  
  if (result.dates.length > 0) {
    console.log(`\n✓ Found ${result.dates.length} days with logs`);
    console.log(`  Most recent: ${result.dates[0]}`);
  } else {
    console.log('\n⚠ No logs found yet. Run some predictions first!');
  }
  
  return result.dates;
}

// Example 2: Get logs for a specific date
async function example2_GetLogsForDate(date) {
  console.log(`\n=== Example 2: Get Logs for ${date} ===\n`);
  
  const result = await apiRequest(`/api/rl-feedback/logs/${date}`, 'GET');
  console.log(`Total predictions on ${date}: ${result.count}`);
  
  if (result.logs.length > 0) {
    console.log('\nSample log entry:');
    const sample = result.logs[0];
    console.log(JSON.stringify({
      timestamp: sample.timestamp,
      username: sample.username,
      prediction: sample.prediction,
      groundTruth: sample.groundTruth,
      isCorrect: sample.isCorrect,
      reward: sample.reward,
      botScore: sample.botScore,
    }, null, 2));
    
    // Show accuracy for this date
    const correct = result.logs.filter(l => l.isCorrect).length;
    const accuracy = (correct / result.logs.length * 100).toFixed(2);
    console.log(`\n📊 Accuracy on ${date}: ${accuracy}%`);
  }
}

// Example 3: Get stats for a date range
async function example3_GetDateRangeStats() {
  console.log('\n=== Example 3: Get Stats for Date Range ===\n');
  
  const today = new Date().toISOString().split('T')[0];
  const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  
  console.log(`Analyzing logs from ${weekAgo} to ${today}...\n`);
  
  const stats = await apiRequest(`/api/rl-feedback/logs/range/${weekAgo}/${today}`, 'GET');
  
  console.log('Overall Statistics:');
  console.log(`  Total Predictions: ${stats.totalPredictions}`);
  console.log(`  Accuracy: ${stats.accuracy}`);
  console.log(`  Correct: ${stats.correctPredictions}`);
  console.log(`  Incorrect: ${stats.incorrectPredictions}`);
  
  if (stats.agentStats) {
    console.log('\nPer-Agent Performance:');
    for (const [agentName, agentStat] of Object.entries(stats.agentStats)) {
      console.log(`  ${agentName}:`);
      console.log(`    - Accuracy: ${agentStat.accuracy}`);
      console.log(`    - Avg Weight: ${agentStat.avgWeight}`);
      console.log(`    - Total Signals: ${agentStat.total}`);
    }
  }
}

// Example 4: Export logs as CSV
async function example4_ExportCSV() {
  console.log('\n=== Example 4: Export Logs as CSV ===\n');
  
  const today = new Date().toISOString().split('T')[0];
  const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  
  console.log(`Exporting logs from ${weekAgo} to ${today}...\n`);
  
  const csv = await apiRequest(`/api/rl-feedback/logs/export/${weekAgo}/${today}`, 'GET');
  
  // Show first few lines
  const lines = csv.split('\n').slice(0, 5);
  console.log('CSV Preview (first 5 lines):');
  console.log(lines.join('\n'));
  console.log('...');
  
  console.log(`\n✓ CSV export complete. Total lines: ${csv.split('\n').length}`);
  console.log('  You can save this to a file for analysis in Excel/Google Sheets');
}

// Example 5: Analyze weight evolution
async function example5_AnalyzeWeightEvolution(dates) {
  console.log('\n=== Example 5: Analyze Weight Evolution ===\n');
  
  if (dates.length === 0) {
    console.log('⚠ No logs available for weight evolution analysis');
    return;
  }
  
  // Get logs for the first and last available dates
  const firstDate = dates[dates.length - 1];
  const lastDate = dates[0];
  
  console.log(`Comparing weights from ${firstDate} to ${lastDate}...\n`);
  
  const firstLogs = await apiRequest(`/api/rl-feedback/logs/${firstDate}`, 'GET');
  const lastLogs = await apiRequest(`/api/rl-feedback/logs/${lastDate}`, 'GET');
  
  if (firstLogs.logs.length === 0 || lastLogs.logs.length === 0) {
    console.log('⚠ Insufficient data for comparison');
    return;
  }
  
  // Get weights from first and last logs
  const firstWeights = {};
  const lastWeights = {};
  
  for (const agent of firstLogs.logs[0].agentScores) {
    firstWeights[agent.name] = agent.weight;
  }
  
  for (const agent of lastLogs.logs[lastLogs.logs.length - 1].agentScores) {
    lastWeights[agent.name] = agent.weight;
  }
  
  console.log('Weight Evolution:');
  for (const agentName in firstWeights) {
    const initial = firstWeights[agentName];
    const current = lastWeights[agentName] || initial;
    const change = current - initial;
    const changePercent = ((change / initial) * 100).toFixed(1);
    
    const arrow = change > 0 ? '↑' : change < 0 ? '↓' : '→';
    const color = change > 0 ? '+' : '';
    
    console.log(`  ${agentName}:`);
    console.log(`    ${initial.toFixed(3)} → ${current.toFixed(3)} (${arrow} ${color}${changePercent}%)`);
  }
}

// Example 6: Find problematic predictions
async function example6_FindProblematicPredictions(date) {
  console.log(`\n=== Example 6: Find Problematic Predictions on ${date} ===\n`);
  
  const result = await apiRequest(`/api/rl-feedback/logs/${date}`, 'GET');
  
  if (result.logs.length === 0) {
    console.log('⚠ No logs found for this date');
    return;
  }
  
  // Find incorrect predictions
  const incorrect = result.logs.filter(l => !l.isCorrect);
  
  console.log(`Found ${incorrect.length} incorrect predictions out of ${result.logs.length} total\n`);
  
  if (incorrect.length > 0) {
    console.log('Incorrect Predictions:');
    incorrect.forEach((log, idx) => {
      console.log(`\n${idx + 1}. @${log.username}`);
      console.log(`   Predicted: ${log.prediction} | Actual: ${log.groundTruth}`);
      console.log(`   Bot Score: ${log.botScore}/100`);
      console.log(`   Agent Signals:`);
      log.agentScores.forEach(a => {
        console.log(`     - ${a.name}: ${a.score}`);
      });
    });
  }
}

// Run all examples
async function runExamples() {
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║  RL History Logs - Examples                                ║');
  console.log('╚════════════════════════════════════════════════════════════╝');
  
  try {
    // Get available dates
    const dates = await example1_GetLogDates();
    
    if (dates.length === 0) {
      console.log('\n⚠ No logs found. Please run some predictions with feedback first.');
      console.log('   Try: node server/examples/rl-feedback-example.js');
      return;
    }
    
    await new Promise(r => setTimeout(r, 1000));
    
    // Get logs for most recent date
    await example2_GetLogsForDate(dates[0]);
    await new Promise(r => setTimeout(r, 1000));
    
    // Get date range stats
    await example3_GetDateRangeStats();
    await new Promise(r => setTimeout(r, 1000));
    
    // Export CSV
    await example4_ExportCSV();
    await new Promise(r => setTimeout(r, 1000));
    
    // Analyze weight evolution
    await example5_AnalyzeWeightEvolution(dates);
    await new Promise(r => setTimeout(r, 1000));
    
    // Find problematic predictions
    await example6_FindProblematicPredictions(dates[0]);
    
    console.log('\n✅ All examples completed successfully!');
    console.log('\nNext steps:');
    console.log('1. Access logs via API endpoints');
    console.log('2. Export CSV for analysis in Excel/Google Sheets');
    console.log('3. Monitor weight evolution over time');
    console.log('4. Identify and fix problematic predictions');
    
  } catch (err) {
    console.error('\n❌ Error:', err.message);
    console.log('\nMake sure the server is running: npm run dev');
  }
}

// Run if called directly
if (require.main === module) {
  runExamples();
}

module.exports = { runExamples };
