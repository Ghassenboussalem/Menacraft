const http = require('http');
const { getRLOrchestrator } = require('./reinforcementLearning');

const PYTHON_BASE = process.env.PYTHON_SERVICE_URL || 'http://localhost:5001';

// ── HTTP helper ──────────────────────────────────────────────────────────
function callPython(path, body) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify(body);
    const url = new URL(path, PYTHON_BASE);
    const options = {
      hostname: url.hostname,
      port: url.port || 80,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload),
      },
    };
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (c) => { data += c; });
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { reject(new Error('Invalid JSON from Python service')); }
      });
    });
    req.on('error', reject);
    req.setTimeout(300000, () => { req.destroy(new Error('Python service timeout')); });
    req.write(payload);
    req.end();
  });
}

// ── Score mappers ────────────────────────────────────────────────────────
function ocrVerdictToScore(verdict) {
  if (verdict === 'CONSISTENT') return 'OK';
  if (verdict === 'PARTIAL')    return 'WARN';
  return 'BAD';
}

function reverseVerdictToScore(verdict) {
  if (verdict === 'ORIGINAL' || verdict === 'PLAUSIBLE') return 'OK';
  if (verdict === 'QUESTIONABLE')                        return 'WARN';
  return 'BAD';
}

function aiDetectVerdictToScore(verdict) {
  if (verdict === 'likely_authentic')       return 'OK';
  if (verdict === 'uncertain')              return 'WARN';
  if (verdict === 'possibly_ai_generated')  return 'WARN';
  return 'BAD'; // likely_ai_generated
}

// ── Real agent: Image Forensics (AI Detection) ───────────────────────────
async function runImageForensicsAgent(post) {
  if (!post.image_url) {
    return {
      team: 'blue', name: 'Image Forensics', model: 'Groq Llama4 + MobileViT', icon: '🔬', axis: 'auth',
      score: 'WARN',
      finding: 'No image attached — AI detection skipped.',
      reasoning: 'Without an image URL, the forensics pipeline cannot run.',
      real: false,
    };
  }
  try {
    const result = await callPython('/ai-detect', { image_url: post.image_url });
    if (result.error || result.skipped) return buildImageForensicsMock(post, result.error || 'service unavailable');

    const score = aiDetectVerdictToScore(result.verdict);
    const verdictLabels = {
      likely_ai_generated:   'Likely AI-Generated',
      possibly_ai_generated: 'Possibly AI-Generated',
      uncertain:             'Uncertain',
      likely_authentic:      'Likely Authentic',
    };
    const findings = (result.key_findings || []).slice(0, 3).join(' · ');

    return {
      team: 'blue', name: 'Image Forensics', model: result.method === 'combined' ? 'Groq Llama4 + MobileViT' : 'Groq Llama4 Scout', icon: '🔬', axis: 'auth',
      score,
      finding: `${verdictLabels[result.verdict] || result.verdict} — ${Math.round((result.confidence || 0) * 100)}% AI probability.`,
      reasoning: result.overall_reasoning || result.summary || 'Multi-stage Groq vision pipeline analysis complete.',
      real: true,
      raw: {
        verdict: result.verdict,
        confidence: result.confidence,
        method: result.method,
        scores: result.scores,
        key_findings: result.key_findings || [],
        stages: result.stages || {},
        annotated_image_b64: result.annotated_image_b64 || null,
      },
    };
  } catch (err) {
    return buildImageForensicsMock(post, err.message);
  }
}

function buildImageForensicsMock(post, reason) {
  const cap = (post.caption || '').toLowerCase();
  const flags = ['breaking', 'conspiracy', 'expose'];
  const ok = flags.some(f => cap.includes(f)) ? 'BAD' : 'OK';
  return {
    team: 'blue', name: 'Image Forensics', model: 'Groq Llama4 + MobileViT (mock)', icon: '🔬', axis: 'auth',
    score: ok,
    finding: ok === 'BAD' ? 'Suspicious image characteristics detected (mock).' : 'No manipulation signatures detected (mock).',
    reasoning: `Real agent unavailable (${reason}). Falling back to heuristic analysis.`,
    real: false,
  };
}

// ── Real agent: OCR + Claim Checker ──────────────────────────────────────
async function runOcrClaimAgent(post) {
  if (!post.image_url) {
    return {
      team: 'blue', name: 'OCR + Claim Checker', model: 'Groq Llama 4 Scout', icon: '📝', axis: 'auth',
      score: 'WARN', finding: 'No image attached — visual claim verification skipped.',
      reasoning: 'Without an image, OCR and visual consistency check cannot run.', real: false,
    };
  }
  try {
    const result = await callPython('/ocr-claim', { image_url: post.image_url, caption: post.caption || '' });
    if (result.error || result.skipped) return buildOcrMock(post, result.error || 'service unavailable');

    const score = ocrVerdictToScore(result.verdict);
    return {
      team: 'blue', name: 'OCR + Claim Checker', model: 'Groq Llama 4 Scout', icon: '📝', axis: 'auth',
      score,
      finding: `${result.verdict} — match score ${result.match_score}%.`,
      reasoning: result.explanation || '',
      real: true,
      raw: {
        verdict: result.verdict,
        match_score: result.match_score,
        manipulation_type: result.manipulation_type,
        ocr_detected: result.ocr_detected || [],
        visual_signals: result.visual_signals || '',
        core_claims_status: result.core_claims_status || '',
        metadata_status: result.metadata_status || '',
        red_flags: result.red_flags || [],
        claims: result.claims || [],
        content_type: result.content_type || 'other',
        commercial_signals: result.commercial_signals || [],
      },
    };
  } catch (err) {
    return buildOcrMock(post, err.message);
  }
}

function buildOcrMock(post, reason) {
  const cap = (post.caption || '').toLowerCase();
  const flags = ['breaking', 'urgent', 'share before', 'wake up', 'conspiracy', 'expose'];
  const fc = flags.filter(f => cap.includes(f)).length;
  const score = fc > 1 ? 'BAD' : fc === 1 ? 'WARN' : 'OK';
  return {
    team: 'blue', name: 'OCR + Claim Checker', model: 'Gemini 2.5 Flash (mock)', icon: '📝', axis: 'auth',
    score, finding: fc > 1 ? 'Multiple unverifiable claims (mock).' : fc === 1 ? 'One flagged claim (mock).' : 'Caption appears factual (mock).',
    reasoning: `Real agent unavailable (${reason}). Heuristic fallback.`, real: false,
  };
}

// ── Real agent: Reverse Image Search ─────────────────────────────────────
async function runReverseImageAgent(post) {
  if (!post.image_url) {
    return {
      team: 'red', name: 'Reverse Image Search', model: 'TinEye via Selenium', icon: '🔄', axis: 'context',
      score: 'WARN', finding: 'No image attached — reverse image search skipped.',
      reasoning: 'Without an image URL, TinEye search cannot be performed.', real: false,
    };
  }
  try {
    const result = await callPython('/reverse-image', { image_url: post.image_url, claimed_date: post.post_date || null });
    if (result.error || result.skipped) return buildReverseImageMock(post, result.error || 'service unavailable');

    const score = reverseVerdictToScore(result.verdict);
    return {
      team: 'red', name: 'Reverse Image Search', model: 'TinEye via Selenium + ImgBB', icon: '🔄', axis: 'context',
      score,
      finding: result.verdict === 'ORIGINAL'
        ? 'Not found in TinEye — image appears original.'
        : `${result.total_matches} matches. Oldest: ${result.oldest_date}.`,
      reasoning: result.explanation || '',
      real: true,
      raw: {
        verdict: result.verdict,
        total_matches: result.total_matches,
        oldest_date: result.oldest_date,
        gap_days: result.gap_days,
      },
    };
  } catch (err) {
    return buildReverseImageMock(post, err.message);
  }
}

function buildReverseImageMock(post, reason) {
  const cap = (post.caption || '').toLowerCase();
  const suspicious = ['breaking', 'urgent', 'conspiracy', 'expose'].some(f => cap.includes(f));
  return {
    team: 'red', name: 'Reverse Image Search', model: 'TinEye (mock)', icon: '🔄', axis: 'context',
    score: suspicious ? 'WARN' : 'OK',
    finding: suspicious ? 'Possible context reuse detected (mock).' : 'No prior contextual reuse (mock).',
    reasoning: `Real agent unavailable (${reason}). Heuristic fallback.`, real: false,
  };
}

// ── Real agent: Bot Pattern Detector (Serper + Feature Extraction + Scoring) ─
function botScoreToAgentScore(botScore) {
  if (botScore >= 70) return 'BAD';
  if (botScore > 30)  return 'WARN';
  return 'OK';
}

async function runBotDetectionAgent(post) {
  const username = post.username;
  if (!username) {
    return {
      team: 'red', name: 'Bot Pattern Detector', model: 'Serper + Scoring Engine', icon: '🤖', axis: 'source',
      score: 'WARN',
      finding: 'No username available — bot detection skipped.',
      reasoning: 'Without a username, the account scraping pipeline cannot run.',
      real: false,
    };
  }
  try {
    // Send the full Supabase post JSON (same structure as lovable_dev_post.json)
    // so the Python pipeline can merge post data + scraped account data
    const result = await callPython('/bot-detect', { post });
    if (result.error || result.skipped) return buildBotDetectionMock(post, result.error || 'service unavailable');

    const score = botScoreToAgentScore(result.bot_score);
    const classLabels = { bot: 'Bot', inconclusive: 'Inconclusive', real: 'Real' };
    const riskEmoji = { HIGH: '🚨', MEDIUM: '⚠️', LOW: '✅' };

    return {
      team: 'red', name: 'Bot Pattern Detector', model: 'Serper API + Rule-based Scoring', icon: '🤖', axis: 'source',
      score,
      finding: `${riskEmoji[result.risk_level] || ''} ${classLabels[result.classification] || result.classification} — Bot score: ${result.bot_score.toFixed(1)}/100.`,
      reasoning: result.risk_level === 'HIGH'
        ? `Account @${username} scored ${result.bot_score.toFixed(1)}/100 on the bot detection pipeline. Multiple suspicious indicators detected across profile, activity, and engagement signals.`
        : result.risk_level === 'MEDIUM'
          ? `Account @${username} scored ${result.bot_score.toFixed(1)}/100. Some indicators are inconclusive — human review recommended.`
          : `Account @${username} scored ${result.bot_score.toFixed(1)}/100. No major bot indicators detected. Profile, engagement, and activity signals are consistent with organic behaviour.`,
      real: true,
      raw: {
        bot_score: result.bot_score,
        classification: result.classification,
        risk_level: result.risk_level,
        features: result.features || {},
        suspicious_flags: result.suspicious_flags || [],
        account_data: result.account_data || {},
      },
    };
  } catch (err) {
    return buildBotDetectionMock(post, err.message);
  }
}

function buildBotDetectionMock(post, reason) {
  const likes    = parseInt(post.likes_count) || 0;
  const comments = parseInt(post.comments_count) || 0;
  const botty    = comments / (likes + 1) > 0.5;
  return {
    team: 'red', name: 'Bot Pattern Detector', model: 'Serper + Scoring Engine (mock)', icon: '🤖', axis: 'source',
    score: botty ? 'BAD' : 'OK',
    finding: botty ? 'Coordinated inauthentic behaviour (CIB) detected (mock).' : 'Organic engagement pattern (mock).',
    reasoning: `Real agent unavailable (${reason}). Falling back to heuristic analysis.`,
    real: false,
  };
}

// ── Real agent: Caption–Image Alignment (Groq Vision) ─────────────────────
async function runCaptionAlignmentAgent(post) {
  if (!post.image_url) {
    return {
      team: 'red', name: 'Caption–Image Alignment', model: 'Groq Llama 4 Scout Vision', icon: '🎯', axis: 'context',
      score: 'WARN',
      finding: 'No image attached — alignment check skipped.',
      reasoning: 'Without an image, caption-image alignment cannot be evaluated.',
      real: false,
    };
  }
  try {
    const result = await callPython('/caption-alignment', {
      image_url: post.image_url,
      caption: post.caption || '',
    });
    if (result.error || result.skipped) return buildCaptionAlignmentMock(post, result.error || 'unavailable');

    const alignScore = result.alignment_score || 0.5;
    const score = alignScore >= 0.7 ? 'OK' : alignScore >= 0.4 ? 'WARN' : 'BAD';
    const verdictLabels = {
      strong_match: 'Strong Match', partial_match: 'Partial Match',
      weak_match: 'Weak Match', mismatch: 'Mismatch', uncertain: 'Uncertain',
    };

    return {
      team: 'red', name: 'Caption–Image Alignment', model: 'Groq Llama 4 Scout Vision', icon: '🎯', axis: 'context',
      score,
      finding: `${verdictLabels[result.verdict] || result.verdict} — alignment score: ${(alignScore * 100).toFixed(0)}%.`,
      reasoning: result.reasoning || 'Visual-semantic alignment analysis completed.',
      real: true,
      raw: {
        alignment_score: alignScore,
        verdict: result.verdict,
        reasoning: result.reasoning,
        key_observations: result.key_observations || [],
      },
    };
  } catch (err) {
    return buildCaptionAlignmentMock(post, err.message);
  }
}

function buildCaptionAlignmentMock(post, reason) {
  return {
    team: 'red', name: 'Caption–Image Alignment', model: 'Groq Vision (mock)', icon: '🎯', axis: 'context',
    score: 'OK',
    finding: 'Alignment check unavailable (mock).',
    reasoning: `Agent unavailable (${reason}). Returning neutral score.`,
    real: false,
  };
}

// ── Real agent: Source Credibility (Gemini) ────────────────────────────────
async function runSourceCredibilityAgent(post) {
  try {
    const result = await callPython('/source-credibility', {
      username: post.username || '',
      caption: post.caption || '',
      likes_count: post.likes_count || '0',
      comments_count: post.comments_count || '0',
      hashtags: post.hashtags || [],
      post_type: post.post_type || 'unknown',
    });
    if (result.error || result.skipped) return buildSourceCredibilityMock(post, result.error || 'unavailable');

    const credScore = result.credibility_score || 0.5;
    const score = credScore >= 0.7 ? 'OK' : credScore >= 0.4 ? 'WARN' : 'BAD';
    const verdictLabels = {
      highly_credible: 'Highly Credible', credible: 'Credible',
      mixed: 'Mixed Signals', low_credibility: 'Low Credibility', not_credible: 'Not Credible',
    };

    return {
      team: 'red', name: 'Source Credibility', model: 'Groq Llama 4 Scout', icon: '🏅', axis: 'source',
      score,
      finding: `${verdictLabels[result.verdict] || result.verdict} — credibility: ${(credScore * 100).toFixed(0)}%.`,
      reasoning: result.reasoning || 'Source credibility analysis completed.',
      real: true,
      raw: {
        credibility_score: credScore,
        verdict: result.verdict,
        risk_factors: result.risk_factors || [],
        positive_signals: result.positive_signals || [],
        reasoning: result.reasoning,
      },
    };
  } catch (err) {
    return buildSourceCredibilityMock(post, err.message);
  }
}

function buildSourceCredibilityMock(post, reason) {
  const likes = parseInt(post.likes_count) || 0;
  return {
    team: 'red', name: 'Source Credibility', model: 'Gemini Flash (mock)', icon: '🏅', axis: 'source',
    score: likes > 1000 ? 'OK' : 'WARN',
    finding: likes > 1000 ? 'Credible engagement (mock).' : 'Low engagement (mock).',
    reasoning: `Agent unavailable (${reason}). Falling back to heuristic.`,
    real: false,
  };
}

// ── Real agent: Link Scanner (Gemini URL analysis) ────────────────────────
async function runLinkScannerAgent(post) {
  try {
    const result = await callPython('/link-scan', {
      caption: post.caption || '',
      post_url: post.post_url || '',
      username: post.username || '',
    });
    if (result.error || result.skipped) return buildLinkScannerMock(post, result.error || 'unavailable');

    const riskScore = result.risk_score || 0;
    const score = riskScore <= 0.2 ? 'OK' : riskScore <= 0.5 ? 'WARN' : 'BAD';
    const verdictLabels = {
      clean: 'Clean', safe: 'Safe', caution: 'Caution',
      suspicious: 'Suspicious', dangerous: 'Dangerous',
    };
    const urlCount = (result.urls_found || []).length + (result.domains_found || []).length;

    return {
      team: 'blue', name: 'Link Scanner', model: 'Groq Llama 4 Scout', icon: '🔗', axis: 'auth',
      score,
      finding: urlCount === 0
        ? 'No external URLs or domains detected in caption.'
        : `${verdictLabels[result.verdict] || result.verdict} — ${urlCount} link(s) analyzed, risk: ${(riskScore * 100).toFixed(0)}%.`,
      reasoning: result.reasoning || 'Link safety analysis completed.',
      real: true,
      raw: {
        risk_score: riskScore,
        verdict: result.verdict,
        urls_found: result.urls_found || [],
        domains_found: result.domains_found || [],
        flags: result.flags || [],
        url_analysis: result.url_analysis || [],
        reasoning: result.reasoning,
      },
    };
  } catch (err) {
    return buildLinkScannerMock(post, err.message);
  }
}

function buildLinkScannerMock(post, reason) {
  return {
    team: 'blue', name: 'Link Scanner', model: 'Gemini Flash (mock)', icon: '🔗', axis: 'auth',
    score: 'OK',
    finding: 'Link scan unavailable (mock).',
    reasoning: `Agent unavailable (${reason}). Returning neutral score.`,
    real: false,
  };
}

// ── Real agent: Text Content Analyzer (OCR.space + LLaVA + Llama) ────────
async function runTextContentAgent(post) {
  if (!post.image_url) {
    return {
      team: 'blue', name: 'Text Content Analyzer', model: 'OCR.space + Ollama LLaVA', icon: '📄', axis: 'auth',
      score: 'WARN', finding: 'No image attached — text analysis skipped.',
      reasoning: 'Without an image, OCR and text-AI detection cannot run.', real: false,
    };
  }
  try {
    const result = await callPython('/text-content', { image_url: post.image_url, caption: post.caption || '' });
    if (result.error) return buildTextContentMock(post, result.error);
    if (result.skipped) return {
      team: 'blue', name: 'Text Content Analyzer', model: 'OCR.space', icon: '📄', axis: 'auth',
      score: 'OK', finding: 'No significant text detected — image is photo/visual content.',
      reasoning: 'OCR scan found no text. Text-AI analysis only applies to text-heavy images (quotes, screenshots, memes).',
      real: true, raw: null,
    };

    const aiProb = result.ai_text_probability || 0;
    const score = aiProb >= 0.6 ? 'BAD' : aiProb >= 0.35 ? 'WARN' : 'OK';
    const verdictLabels = {
      likely_ai_generated: 'Likely AI-Generated Text',
      possibly_ai_generated: 'Possibly AI-Generated Text',
      likely_authentic: 'Likely Authentic Text',
      uncertain: 'Uncertain',
    };

    return {
      team: 'blue', name: 'Text Content Analyzer', model: 'OCR.space + Groq Llama 4 Scout', icon: '📄', axis: 'auth',
      score,
      finding: `${verdictLabels[result.verdict] || result.verdict} — ${Math.round(aiProb * 100)}% AI text probability.`,
      reasoning: result.reasoning || 'OCR + LLaVA text extraction with AI generation analysis.',
      real: true,
      raw: {
        ocr_text: result.ocr_text || '',
        llava_text: result.llava_text || '',
        best_text: result.best_text || '',
        is_text_only: result.is_text_only,
        content_type: result.content_type,
        language: result.language,
        is_coherent: result.is_coherent,
        message: result.message || '',
        ai_text_probability: aiProb,
        ai_tells: result.ai_tells || [],
        verdict: result.verdict,
      },
    };
  } catch (err) {
    return buildTextContentMock(post, err.message);
  }
}

function buildTextContentMock(post, reason) {
  return {
    team: 'blue', name: 'Text Content Analyzer', model: 'OCR.space + LLaVA (mock)', icon: '📄', axis: 'auth',
    score: 'WARN', finding: 'Text analysis unavailable (mock).',
    reasoning: `Agent unavailable (${reason}). Returning neutral score.`, real: false,
  };
}

// ── Base score helper ─────────────────────────────────────────────────────
function computeBaseScore(post) {
  const cap = (post.caption || '').toLowerCase();
  const likes = parseInt(post.likes_count) || 0;
  const comments = parseInt(post.comments_count) || 0;
  const flags = ['breaking', 'urgent', 'share before', 'they dont', 'wake up', 'secret', 'conspiracy', 'expose'];
  let score = 72 - flags.filter(f => cap.includes(f)).length * 13;
  if (comments / (likes + 1) > 0.5) score -= 16;
  if (likes > 5000 && comments < 50) score -= 9;
  if (!post.image_url) score -= 4;
  return Math.max(5, Math.min(95, score + Math.round(Math.random() * 8 - 4)));
}

function scoreToOk(score) {
  return score > 65 ? 'OK' : score > 42 ? 'WARN' : 'BAD';
}

function agentToNum(s) {
  return s === 'OK' ? 1 : s === 'WARN' ? 0.5 : 0;
}

// ── Agent weights — reflects signal strength and reliability ─────────────
// Weights sum to 1.0. Agents analyzing actual media (forensics, reverse image)
// count more than context-only agents (bot detection, credibility).
// NOTE: These are now dynamically adjusted by the RL orchestrator
function getAgentWeights() {
  const rlOrchestrator = getRLOrchestrator();
  return rlOrchestrator.getWeights();
}

const AGENT_WEIGHTS = getAgentWeights();

function computeWeightedScore(agents) {
  const AGENT_WEIGHTS = getAgentWeights(); // Get current RL-adjusted weights
  let weightedSum = 0;
  let totalWeight = 0;

  for (const agent of agents) {
    if (!agent) continue;
    const w = AGENT_WEIGHTS[agent.name] || 0.10;
    const score = agentToNum(agent.score);

    // Neutral results (skipped, no data) shouldn't count for or against
    const isNeutral = agent.finding && (
      agent.finding.includes('skipped') ||
      agent.finding.includes('No external URLs') ||
      agent.finding.includes('No significant text')
    );

    if (isNeutral) continue; // Don't include neutral agents in the weighted average

    weightedSum += score * w;
    totalWeight += w;
  }

  if (totalWeight === 0) return 50; // No meaningful data
  return Math.round((weightedSum / totalWeight) * 100);
}

function weightedVerdict(score) {
  return score >= 75 ? 'verified' : score >= 35 ? 'suspicious' : 'fake';
}

// ── Call the LLM-powered Synthesis Agent (Python /synthesis endpoint) ─────
async function callSynthesisAgent(agents, post) {
  try {
    // Strip annotated_image_b64 to keep the payload small
    const cleanAgents = agents.map(a => {
      if (!a) return a;
      if (!a.raw?.annotated_image_b64) return a;
      const { annotated_image_b64: _drop, ...rawClean } = a.raw;
      return { ...a, raw: rawClean };
    });

    const result = await callPython('/synthesis', {
      agents: cleanAgents,
      post: {
        username: post.username || '',
        caption: post.caption || '',
        likes_count: post.likes_count || '0',
        comments_count: post.comments_count || '0',
        hashtags: post.hashtags || [],
        image_url: post.image_url || null,
        post_type: post.post_type || 'unknown',
      },
      weights: getAgentWeights(), // Use current RL-adjusted weights
    });

    if (result.error) throw new Error(result.error);
    return result;
  } catch (err) {
    console.error('[synthesis] LLM synthesis failed:', err.message);
    return null; // fallback to weighted scoring
  }
}

// ── Public: verifyPostReal ────────────────────────────────────────────────
async function verifyPostReal(post) {
  // All agents now use Groq (cloud), so no GPU conflicts with MobileViT.
  // LLaVA agents still run sequentially with delays to respect Groq API rate limits.
  // ai-detect uses Groq + MobileViT combined pipeline.
  const delay = (ms) => new Promise((r) => setTimeout(r, ms));

  const [linkAgent, reverseAgent, botAgent, credibilityAgent] = await Promise.all([
    runLinkScannerAgent(post),
    runReverseImageAgent(post),
    runBotDetectionAgent(post),
    runSourceCredibilityAgent(post),
  ]);

  // LLaVA agents — strictly sequential with longer gaps so Ollama fully unloads between calls
  const forensicsAgent = await runImageForensicsAgent(post);
  await delay(3000);
  const ocrAgent       = await runOcrClaimAgent(post);
  await delay(3000);
  const captionAgent   = await runCaptionAlignmentAgent(post);
  await delay(3000);
  const textAgent      = await runTextContentAgent(post);

  const agents = [
    forensicsAgent,           // Image Forensics      ← REAL (Groq + MobileViT)
    ocrAgent,                 // OCR + Claim          ← REAL (Groq Llama 4 Scout)
    linkAgent,                // Link Scanner         ← REAL (Groq Llama 4 Scout)
    reverseAgent,             // Reverse Image        ← REAL (TinEye)
    captionAgent,             // Caption Alignment    ← REAL (Groq Llama 4 Scout Vision)
    botAgent,                 // Bot Pattern          ← REAL (Serper + Scoring)
    credibilityAgent,         // Source Credibility   ← REAL (Groq Llama 4 Scout)
    textAgent,                // Text Content         ← REAL (OCR.space + Groq)
  ];

  // ── Weighted scoring (replaces the old simple average) ──
  const weightedScore = computeWeightedScore(agents);

  // ── LLM-powered Synthesis Agent (replaces the old hardcoded strings) ──
  console.log('[synthesis] Calling LLM synthesis agent...');
  const synthResult = await callSynthesisAgent(agents, post);

  if (synthResult) {
    // LLM synthesis succeeded — use its verdict and reasoning
    return {
      verdict: synthResult.verdict,
      confidence: synthResult.confidence,
      synthesis: synthResult.synthesis,
      key_evidence: synthResult.key_evidence || [],
      contradictions: synthResult.contradictions || [],
      decisive_factors: synthResult.decisive_factors || '',
      weighted_score: weightedScore,
      agents,
    };
  }

  // Fallback: LLM synthesis failed — use weighted score with a generic message
  console.warn('[synthesis] Falling back to weighted scoring (no LLM reasoning)');
  const fallbackVerdict = weightedVerdict(weightedScore);
  const fallbackTexts = {
    verified: `Weighted analysis across ${agents.length} agents (score: ${weightedScore}/100). All major signals — forensics, reverse image, OCR, and caption alignment — returned clean. No credible misinformation indicators detected.`,
    suspicious: `Weighted analysis across ${agents.length} agents (score: ${weightedScore}/100). Mixed signals detected — one or more high-weight agents flagged concerns. Manual review recommended.`,
    fake: `Weighted analysis across ${agents.length} agents (score: ${weightedScore}/100). Multiple high-weight agents returned critical failures. Strong indicators of manipulation or misinformation.`,
  };

  return {
    verdict: fallbackVerdict,
    confidence: weightedScore,
    synthesis: fallbackTexts[fallbackVerdict],
    weighted_score: weightedScore,
    agents,
  };
}

// ── Legacy mock (used for demo data preview only) ─────────────────────────
function verifyPost(post) {
  const score = computeBaseScore(post);
  const verdict = score >= 80 ? 'verified' : score >= 40 ? 'suspicious' : 'fake';
  const agents = [
    buildImageForensicsMock(post, 'demo mode'),
    buildOcrMock(post, 'demo mode'),
    buildLinkScannerMock(post, 'demo mode'),
    buildReverseImageMock(post, 'demo mode'),
    buildCaptionAlignmentMock(post, 'demo mode'),
    buildBotDetectionMock(post, 'demo mode'),
    buildSourceCredibilityMock(post, 'demo mode'),
    buildTextContentMock(post, 'demo mode'),
  ];
  const synthTexts = {
    verified: 'Both teams returned clean signals — VERIFIED (mock run, real agents not called).',
    suspicious: 'Mixed signals — exercise caution (mock run).',
    fake: 'Near-unanimous failures — DISINFORMATION (mock run).',
  };
  return { verdict, confidence: score, synthesis: synthTexts[verdict], agents };
}

// ── Streaming verification: each agent result is sent as it finishes ──────
async function runAgentsSse(post, emit) {
  // ai-detect (idx 0) is slow (MobileViT model load + inference ~30-45s).
  // Run it separately so the other 6 fast agents can emit a verdict without waiting.
  // Non-LLaVA agents: run in parallel immediately
  const fastSlots = [
    { idx: 2, name: 'Link Scanner',         fn: () => runLinkScannerAgent(post) },
    { idx: 3, name: 'Reverse Image Search', fn: () => runReverseImageAgent(post) },
    { idx: 5, name: 'Bot Pattern Detector', fn: () => runBotDetectionAgent(post) },
    { idx: 6, name: 'Source Credibility',   fn: () => runSourceCredibilityAgent(post) },
  ];
  // All agents now use Groq (cloud) instead of Ollama, so no GPU conflicts.
  // Sequential execution with delays still helps respect Groq API rate limits.
  const llavaSlots = [
    { idx: 0, name: 'Image Forensics',         fn: () => runImageForensicsAgent(post),   delay: 0    },
    { idx: 1, name: 'OCR + Claim Checker',     fn: () => runOcrClaimAgent(post),          delay: 3000 },
    { idx: 4, name: 'Caption–Image Alignment', fn: () => runCaptionAlignmentAgent(post),  delay: 3000 },
    { idx: 7, name: 'Text Content Analyzer',   fn: () => runTextContentAgent(post),       delay: 3000 },
  ];

  const agents = new Array(8).fill(null);

  // Emit placeholders for all LLaVA agents immediately
  llavaSlots.forEach(slot => {
    const placeholder = {
      team: slot.idx <= 1 ? 'blue' : slot.idx === 4 ? 'red' : 'blue',
      name: slot.name, model: '…', icon: ['🔬','📝','','','🎯','','','📄'][slot.idx] || '⏳',
      axis: slot.idx <= 2 || slot.idx === 7 ? 'auth' : 'context',
      score: 'WARN', finding: 'Analyzing…', reasoning: '', real: false, pending: true,
    };
    agents[slot.idx] = placeholder;
    emit('agent', { idx: slot.idx, agent: placeholder });
  });

  // Run non-LLaVA agents in parallel
  const fastPromises = fastSlots.map(async (slot) => {
    try {
      const result = await slot.fn();
      agents[slot.idx] = result;
      emit('agent', { idx: slot.idx, agent: result });
    } catch (err) {
      const fallback = {
        team: 'blue', name: slot.name, model: 'error', icon: '⚠', axis: 'auth',
        score: 'WARN', finding: `Error: ${err.message}`, reasoning: 'Agent failed to execute.', real: false,
      };
      agents[slot.idx] = fallback;
      emit('agent', { idx: slot.idx, agent: fallback });
    }
  });

  // Run LLaVA agents strictly sequentially
  const llavaRunner = (async () => {
    for (const slot of llavaSlots) {
      if (slot.delay) await new Promise(r => setTimeout(r, slot.delay));
      try {
        const result = await slot.fn();
        agents[slot.idx] = result;
        emit('agent', { idx: slot.idx, agent: result });
      } catch (err) {
        const fallback = {
          team: 'blue', name: slot.name, model: 'error', icon: '⚠', axis: 'auth',
          score: 'WARN', finding: `Error: ${err.message}`, reasoning: 'Agent failed to execute.', real: false,
        };
        agents[slot.idx] = fallback;
        emit('agent', { idx: slot.idx, agent: fallback });
      }
    }
  })();

  await Promise.all([...fastPromises, llavaRunner]);

  // ── Weighted scoring (same weights as verifyPostReal) ──
  const completedAgents = agents.filter(Boolean);
  const weightedScore = computeWeightedScore(completedAgents);

  // ── LLM-powered Synthesis Agent ──
  console.log('[synthesis:sse] Calling LLM synthesis agent...');
  const synthResult = await callSynthesisAgent(completedAgents, post);

  let finalResult;
  if (synthResult) {
    finalResult = {
      verdict: synthResult.verdict,
      confidence: synthResult.confidence,
      synthesis: synthResult.synthesis,
      key_evidence: synthResult.key_evidence || [],
      contradictions: synthResult.contradictions || [],
      decisive_factors: synthResult.decisive_factors || '',
      weighted_score: weightedScore,
      agents: [...agents],
    };
  } else {
    // Fallback: LLM synthesis failed
    console.warn('[synthesis:sse] Falling back to weighted scoring');
    const fallbackVerdict = weightedVerdict(weightedScore);
    const fallbackTexts = {
      verified: `Weighted analysis across ${completedAgents.length} agents (score: ${weightedScore}/100). All major signals returned clean. No credible misinformation indicators detected.`,
      suspicious: `Weighted analysis across ${completedAgents.length} agents (score: ${weightedScore}/100). Mixed signals — one or more high-weight agents flagged concerns. Manual review recommended.`,
      fake: `Weighted analysis across ${completedAgents.length} agents (score: ${weightedScore}/100). Multiple high-weight agents returned critical failures. Strong indicators of manipulation.`,
    };
    finalResult = {
      verdict: fallbackVerdict,
      confidence: weightedScore,
      synthesis: fallbackTexts[fallbackVerdict],
      weighted_score: weightedScore,
      agents: [...agents],
    };
  }

  emit('verdict', finalResult);
  return finalResult;
}

// ── RL Feedback: Record ground truth and update weights ──────────────────
/**
 * Provide feedback to the RL system about a bot detection prediction
 * 
 * @param {Object} params
 * @param {string} params.username - Account username
 * @param {string} params.groundTruth - 'bot' or 'real' (actual label)
 * @param {Array} params.agents - Agent results from verification
 * @param {number} params.botScore - Bot score (0-100)
 * @param {string} params.classification - 'bot', 'real', or 'inconclusive'
 */
async function provideBotDetectionFeedback({ username, groundTruth, agents, botScore, classification }) {
  const rlOrchestrator = getRLOrchestrator();
  
  // Convert classification to prediction
  let prediction = classification;
  if (classification === 'inconclusive') {
    // For inconclusive, use bot score threshold
    prediction = botScore >= 50 ? 'bot' : 'real';
  }
  
  const result = await rlOrchestrator.recordPrediction({
    agents,
    prediction,
    groundTruth,
    username,
    botScore,
  });
  
  return result;
}

/**
 * Get RL statistics and performance metrics
 */
function getRLStats() {
  const rlOrchestrator = getRLOrchestrator();
  return {
    stats: rlOrchestrator.getStats(),
    currentWeights: rlOrchestrator.getWeights(),
  };
}

module.exports = { 
  verifyPost, 
  verifyPostReal, 
  runAgentsSse,
  provideBotDetectionFeedback,
  getRLStats,
};

