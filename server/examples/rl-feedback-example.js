/**
 * Example: Using the RL Feedback System
 * 
 * This script demonstrates how to provide feedback to the RL orchestrator
 * to improve bot detection accuracy over time.
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
          reject(new Error('Invalid JSON response'));
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

// Example 1: Provide feedback for a correctly identified bot
async function example1_CorrectBotDetection() {
  console.log('\n=== Example 1: Correct Bot Detection ===\n');
  
  // Simulated agent results (normally from verifyPostReal)
  const agents = [
    { name: 'Bot Pattern Detector', score: 'BAD', finding: 'Bot score: 85/100' },
    { name: 'Source Credibility', score: 'WARN', finding: 'Low credibility' },
    { name: 'Image Forensics', score: 'OK', finding: 'No manipulation detected' },
  ];
  
  const feedback = {
    username: 'fake_bot_123',
    groundTruth: 'bot',
    agents,
    botScore: 85,
    classification: 'bot',
  };
  
  const result = await apiRequest('/api/rl-feedback', 'POST', feedback);
  console.log('Result:', JSON.stringify(result, null, 2));
  console.log('\n✓ System correctly identified bot - weights adjusted positively');
}

// Example 2: Provide feedback for a false positive (real account flagged as bot)
async function example2_FalsePositive() {
  console.log('\n=== Example 2: False Positive (Real Account Flagged as Bot) ===\n');
  
  const agents = [
    { name: 'Bot Pattern Detector', score: 'BAD', finding: 'Bot score: 72/100' },
    { name: 'Source Credibility', score: 'WARN', finding: 'Mixed signals' },
    { name: 'Image Forensics', score: 'OK', finding: 'Authentic' },
  ];
  
  const feedback = {
    username: 'real_user_456',
    groundTruth: 'real',  // Actually real, but system said bot
    agents,
    botScore: 72,
    classification: 'bot',
  };
  
  const result = await apiRequest('/api/rl-feedback', 'POST', feedback);
  console.log('Result:', JSON.stringify(result, null, 2));
  console.log('\n✗ System incorrectly flagged real account - weights adjusted negatively');
}

// Example 3: View RL statistics
async function example3_ViewStats() {
  console.log('\n=== Example 3: View RL Statistics ===\n');
  
  const stats = await apiRequest('/api/rl-feedback/stats', 'GET');
  console.log('Statistics:', JSON.stringify(stats, null, 2));
  console.log('\n📊 Current accuracy and agent weights displayed');
}

// Example 4: Batch feedback from labeled dataset
async function example4_BatchFeedback() {
  console.log('\n=== Example 4: Batch Feedback from Labeled Dataset ===\n');
  
  // Simulated labeled dataset
  const labeledAccounts = [
    { username: 'bot_1', groundTruth: 'bot', botScore: 88, classification: 'bot' },
    { username: 'real_1', groundTruth: 'real', botScore: 25, classification: 'real' },
    { username: 'bot_2', groundTruth: 'bot', botScore: 75, classification: 'bot' },
    { username: 'real_2', groundTruth: 'real', botScore: 35, classification: 'real' },
  ];
  
  for (const account of labeledAccounts) {
    const agents = [
      { 
        name: 'Bot Pattern Detector', 
        score: account.botScore >= 70 ? 'BAD' : account.botScore >= 30 ? 'WARN' : 'OK',
        finding: `Bot score: ${account.botScore}/100`,
      },
    ];
    
    const feedback = {
      username: account.username,
      groundTruth: account.groundTruth,
      agents,
      botScore: account.botScore,
      classification: account.classification,
    };
    
    const result = await apiRequest('/api/rl-feedback', 'POST', feedback);
    console.log(`✓ Processed @${account.username}: ${result.isCorrect ? 'CORRECT' : 'INCORRECT'}`);
  }
  
  console.log('\n📈 Batch training complete - system learned from multiple examples');
}

// Run all examples
async function runExamples() {
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║  Reinforcement Learning Feedback System - Examples        ║');
  console.log('╚════════════════════════════════════════════════════════════╝');
  
  try {
    await example1_CorrectBotDetection();
    await new Promise(r => setTimeout(r, 1000));
    
    await example2_FalsePositive();
    await new Promise(r => setTimeout(r, 1000));
    
    await example3_ViewStats();
    await new Promise(r => setTimeout(r, 1000));
    
    await example4_BatchFeedback();
    await new Promise(r => setTimeout(r, 1000));
    
    await example3_ViewStats(); // View stats again after batch training
    
    console.log('\n✅ All examples completed successfully!');
    console.log('\nNext steps:');
    console.log('1. Integrate feedback into your verification workflow');
    console.log('2. Monitor accuracy at /api/rl-feedback/stats');
    console.log('3. Provide feedback for real predictions to improve the system');
    
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
