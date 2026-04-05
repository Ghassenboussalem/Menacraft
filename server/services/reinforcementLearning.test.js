/**
 * Simple tests for the Reinforcement Learning Orchestrator
 * 
 * Run with: node server/services/reinforcementLearning.test.js
 */

const { ReinforcementLearningOrchestrator } = require('./reinforcementLearning');
const fs = require('fs').promises;

// Test weights file path
const TEST_WEIGHTS_PATH = './test_rl_weights.json';

async function cleanup() {
  try {
    await fs.unlink(TEST_WEIGHTS_PATH);
  } catch (err) {
    // File doesn't exist, that's fine
  }
}

async function test1_InitialWeights() {
  console.log('\n=== Test 1: Initial Weights ===');
  
  await cleanup();
  const rl = new ReinforcementLearningOrchestrator(TEST_WEIGHTS_PATH);
  
  const weights = rl.getWeights();
  console.log('Initial weights:', weights);
  
  // Check that weights sum to approximately 1.0
  const sum = Object.values(weights).reduce((a, b) => a + b, 0);
  console.log('Sum of weights:', sum.toFixed(3));
  
  if (Math.abs(sum - 1.0) < 0.01) {
    console.log('✓ Weights sum to 1.0');
  } else {
    console.log('✗ Weights do not sum to 1.0');
  }
  
  await cleanup();
}

async function test2_CorrectPrediction() {
  console.log('\n=== Test 2: Correct Bot Prediction ===');
  
  await cleanup();
  const rl = new ReinforcementLearningOrchestrator(TEST_WEIGHTS_PATH);
  
  const initialWeights = { ...rl.getWeights() };
  
  // Simulate agents correctly identifying a bot
  const agents = [
    { name: 'Bot Pattern Detector', score: 'BAD', finding: 'High bot score' },
    { name: 'Source Credibility', score: 'WARN', finding: 'Low credibility' },
    { name: 'Image Forensics', score: 'OK', finding: 'No manipulation' },
  ];
  
  const result = await rl.recordPrediction({
    agents,
    prediction: 'bot',
    groundTruth: 'bot',
    username: 'test_bot',
    botScore: 85,
  });
  
  console.log('Result:', result);
  console.log('Is correct:', result.isCorrect);
  console.log('Reward:', result.reward);
  
  const updatedWeights = rl.getWeights();
  
  // Bot Pattern Detector should have increased weight
  const botDetectorChange = updatedWeights['Bot Pattern Detector'] - initialWeights['Bot Pattern Detector'];
  console.log('Bot Pattern Detector weight change:', botDetectorChange.toFixed(4));
  
  if (botDetectorChange > 0) {
    console.log('✓ Bot Pattern Detector weight increased (correct signal)');
  } else {
    console.log('✗ Bot Pattern Detector weight did not increase');
  }
  
  await cleanup();
}

async function test3_IncorrectPrediction() {
  console.log('\n=== Test 3: Incorrect Prediction (False Positive) ===');
  
  await cleanup();
  const rl = new ReinforcementLearningOrchestrator(TEST_WEIGHTS_PATH);
  
  const initialWeights = { ...rl.getWeights() };
  
  // Simulate agents incorrectly flagging a real account as bot
  const agents = [
    { name: 'Bot Pattern Detector', score: 'BAD', finding: 'High bot score' },
    { name: 'Source Credibility', score: 'WARN', finding: 'Low credibility' },
  ];
  
  const result = await rl.recordPrediction({
    agents,
    prediction: 'bot',
    groundTruth: 'real', // Actually real!
    username: 'real_user',
    botScore: 75,
  });
  
  console.log('Result:', result);
  console.log('Is correct:', result.isCorrect);
  console.log('Reward:', result.reward);
  
  const updatedWeights = rl.getWeights();
  
  // Bot Pattern Detector should have decreased weight
  const botDetectorChange = updatedWeights['Bot Pattern Detector'] - initialWeights['Bot Pattern Detector'];
  console.log('Bot Pattern Detector weight change:', botDetectorChange.toFixed(4));
  
  if (botDetectorChange < 0) {
    console.log('✓ Bot Pattern Detector weight decreased (incorrect signal)');
  } else {
    console.log('✗ Bot Pattern Detector weight did not decrease');
  }
  
  await cleanup();
}

async function test4_Persistence() {
  console.log('\n=== Test 4: Weight Persistence ===');
  
  await cleanup();
  
  // Create RL instance and record a prediction
  const rl1 = new ReinforcementLearningOrchestrator(TEST_WEIGHTS_PATH);
  
  const agents = [
    { name: 'Bot Pattern Detector', score: 'BAD', finding: 'Bot detected' },
  ];
  
  await rl1.recordPrediction({
    agents,
    prediction: 'bot',
    groundTruth: 'bot',
    username: 'test_bot',
    botScore: 90,
  });
  
  const weights1 = rl1.getWeights();
  console.log('Weights after first prediction:', weights1['Bot Pattern Detector'].toFixed(4));
  
  // Create new instance (simulating server restart)
  const rl2 = new ReinforcementLearningOrchestrator(TEST_WEIGHTS_PATH);
  await rl2.loadWeights();
  
  const weights2 = rl2.getWeights();
  console.log('Weights after reload:', weights2['Bot Pattern Detector'].toFixed(4));
  
  if (Math.abs(weights1['Bot Pattern Detector'] - weights2['Bot Pattern Detector']) < 0.0001) {
    console.log('✓ Weights persisted correctly');
  } else {
    console.log('✗ Weights did not persist');
  }
  
  await cleanup();
}

async function test5_Statistics() {
  console.log('\n=== Test 5: Statistics Tracking ===');
  
  await cleanup();
  const rl = new ReinforcementLearningOrchestrator(TEST_WEIGHTS_PATH);
  
  // Record multiple predictions
  const predictions = [
    { prediction: 'bot', groundTruth: 'bot', botScore: 85 },
    { prediction: 'real', groundTruth: 'real', botScore: 20 },
    { prediction: 'bot', groundTruth: 'real', botScore: 70 }, // Incorrect
    { prediction: 'bot', groundTruth: 'bot', botScore: 90 },
  ];
  
  for (let i = 0; i < predictions.length; i++) {
    const p = predictions[i];
    await rl.recordPrediction({
      agents: [{ name: 'Bot Pattern Detector', score: 'BAD', finding: 'Test' }],
      prediction: p.prediction,
      groundTruth: p.groundTruth,
      username: `user_${i}`,
      botScore: p.botScore,
    });
  }
  
  const stats = rl.getStats();
  console.log('Statistics:', stats);
  
  if (stats.totalPredictions === 4) {
    console.log('✓ Total predictions tracked correctly');
  }
  
  if (stats.correctPredictions === 3 && stats.incorrectPredictions === 1) {
    console.log('✓ Correct/incorrect counts are accurate');
  }
  
  const expectedAccuracy = (3 / 4 * 100).toFixed(2);
  if (stats.accuracy === expectedAccuracy + '%') {
    console.log('✓ Accuracy calculated correctly:', stats.accuracy);
  }
  
  await cleanup();
}

async function runAllTests() {
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║  Reinforcement Learning Orchestrator - Tests              ║');
  console.log('╚════════════════════════════════════════════════════════════╝');
  
  try {
    await test1_InitialWeights();
    await test2_CorrectPrediction();
    await test3_IncorrectPrediction();
    await test4_Persistence();
    await test5_Statistics();
    
    console.log('\n✅ All tests completed!');
  } catch (err) {
    console.error('\n❌ Test failed:', err);
  } finally {
    await cleanup();
  }
}

// Run tests if called directly
if (require.main === module) {
  runAllTests();
}

module.exports = { runAllTests };
