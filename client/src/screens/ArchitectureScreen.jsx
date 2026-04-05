export default function ArchitectureScreen() {
  return (
    <div className="feed-panel">
      <div className="page-header">
        <div>
          <div className="page-title">System Architecture</div>
          <div className="page-subtitle">MenaCraft Instagram Verification · Technical Blueprint</div>
        </div>
      </div>

      {/* Data Flow */}
      <div className="arch-section">
        <div className="arch-title">Data Flow</div>
        <div className="arch-flow">
          {[
            { label: 'Instagram DOM', sub: 'Browser-rendered' },
            { label: 'Chrome Extension', sub: 'MV3 Content Script' },
            { label: 'Supabase', sub: 'Storage layer' },
            { label: 'Express Backend', sub: '/api/verify' },
            { label: 'AI Pipeline', sub: 'Blue + Red + Synthesis' },
          ].reduce((acc, node, i, arr) => {
            acc.push(
              <div key={`node-${i}`} className="arch-node">
                <div className="arch-node-label">{node.label}</div>
                <div className="arch-node-sub">{node.sub}</div>
              </div>
            );
            if (i < arr.length - 1) acc.push(<div key={`arrow-${i}`} className="arch-arrow">→</div>);
            return acc;
          }, [])}
        </div>
        <div style={{ fontSize: 11.5, color: 'var(--text-muted)', lineHeight: 1.6, padding: '10px 13px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, marginBottom: 16 }}>
          The extension runs entirely in the browser — reading the already-rendered DOM without triggering Instagram's anti-bot protections. No Instagram credentials are stored.
        </div>
      </div>

      {/* Agent Pipeline */}
      <div className="arch-section">
        <div className="arch-title">Agent Pipeline</div>
        <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginBottom: 12, lineHeight: 1.5 }}>
          Inspired by cybersecurity red/blue team methodology. Both teams independently analyse the same post, then a Synthesis Agent reconciles their findings.
        </div>
        <div className="team-section-grid">
          <div className="team-box blue">
            <div className="team-box-title blue">
              <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
              Blue Team — Detection
            </div>
            <div className="agent-row-arch">
              {[
                { name: 'Image Forensics', model: 'Groq Llama 4 Scout + MobileViT', what: 'AI-generated image detection, manipulation artifacts', live: true },
                { name: 'OCR + Claim Checker', model: 'Groq Llama 4 Scout', what: 'Text overlaid on image vs. caption claim verification', live: true },
                { name: 'Link Scanner', model: 'Groq Llama 4 Scout', what: 'URL extraction, phishing detection, domain reputation analysis', live: true },
              ].map((a) => (
                <div key={a.name} className="agent-item">
                  <div className="agent-item-name">
                    {a.name}
                    {a.live && <span style={{ marginLeft: 6, fontSize: 9, fontWeight: 700, padding: '1px 5px', borderRadius: 3, background: 'var(--text)', color: 'var(--surface)' }}>LIVE</span>}
                  </div>
                  <div className="agent-item-model">{a.model}</div>
                  <div className="agent-item-what">{a.what}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="team-box red">
            <div className="team-box-title red">
              <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
              Red Team — Verification
            </div>
            <div className="agent-row-arch">
              {[
                { name: 'Reverse Image Search', model: 'TinEye via Selenium + ImgBB', what: 'Historical reuse; different event or country', live: true },
                { name: 'Caption–Image Alignment', model: 'Groq Llama 4 Scout (Vision)', what: 'Semantic alignment between caption text and image content', live: true },
                { name: 'Bot Pattern Detector', model: 'Serper API + Rule-based Scoring', what: 'Account scraping, feature extraction, bot probability scoring', live: true },
                { name: 'Source Credibility', model: 'Groq Llama 4 Scout', what: 'Username patterns, writing style, engagement analysis', live: true },
              ].map((a) => (
                <div key={a.name} className="agent-item">
                  <div className="agent-item-name">
                    {a.name}
                    {a.live && <span style={{ marginLeft: 6, fontSize: 9, fontWeight: 700, padding: '1px 5px', borderRadius: 3, background: 'var(--text)', color: 'var(--surface)' }}>LIVE</span>}
                  </div>
                  <div className="agent-item-model">{a.model}</div>
                  <div className="agent-item-what">{a.what}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="synth-box">
          <div className="synth-box-title">
            <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>
            Synthesis Agent · Groq Llama 4 Scout
          </div>
          <div className="synth-box-desc">LLM-powered meta-reasoning agent. Receives all agent outputs as structured JSON, identifies agreements and contradictions, applies weighted scoring (Image Forensics 20%, Reverse Image 18%, OCR 15%, ...), and produces a written verdict with key evidence and decisive factors.</div>
        </div>
      </div>

      {/* Tech Stack */}
      <div className="arch-section">
        <div className="arch-title">Tech Stack</div>
        <table className="stack-table">
          <thead><tr><th>Layer</th><th>Technology</th><th>Rationale</th></tr></thead>
          <tbody>
            {[
              ['Extension', 'Chrome MV3 · Shadow DOM', 'DOM access, no scraping'],
              ['API Backend', 'Node.js Express', 'REST API, proxies Supabase + AI'],
              ['AI Microservice', 'Python Flask', '8 real agents + LLM Synthesis Agent'],
              ['Storage', 'Supabase (PostgreSQL)', 'Real-time, REST API'],
              ['Image AI', 'Groq Llama 4 Scout + MobileViT', 'AI-generated image detection (30/70 weighted)'],
              ['Caption Alignment', 'Groq Llama 4 Scout (Vision)', 'Visual-semantic caption vs image analysis'],
              ['OCR + Credibility', 'Groq Llama 4 Scout', 'Claim verification, source analysis, link scanning'],
              ['Reverse Image', 'TinEye via Selenium + ImgBB', 'Temporal provenance detection'],
              ['Bot Detection', 'Serper + Feature Extraction + Scoring', 'Account-level bot probability scoring'],
              ['Synthesis', 'Groq Llama 4 Scout (Meta-reasoning)', 'Weighted verdict with conflict resolution'],
              ['Frontend', 'Vite + React + Zustand', 'Fast SPA, minimal overhead'],
              ['Deploy', 'Railway / Render / Cloud Run', 'One-click HTTPS'],
            ].map(([layer, tech, why]) => (
              <tr key={layer}><td>{layer}</td><td>{tech}</td><td>{why}</td></tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Hackathon Criteria */}
      <div className="arch-section">
        <div className="arch-title">Hackathon Scoring Criteria</div>
        <table className="criteria-table">
          <thead><tr><th>Criterion</th><th>How this delivers</th><th>Score</th></tr></thead>
          <tbody>
            {[
              ['AI-Driven Verification', 'Multi-agent pipeline with deepfake detection, CLIP, and LLM reasoning', '★★★★★'],
              ['Innovation', 'Chrome extension as anti-scraping bypass; real-time inline overlay', '★★★★★'],
              ['Content Authenticity', 'EfficientNet deepfake detector + OCR + metadata analysis', '★★★★★'],
              ['Contextual Consistency', 'CLIP image–caption alignment + TinEye reverse image search', '★★★★½'],
              ['Source Credibility', 'Domain trust DB + LLM writing-style analysis + bot heuristics', '★★★★½'],
              ['Explainability', 'Per-agent breakdown + plain-language synthesis in every verdict', '★★★★★'],
              ['Practicality', 'Works on the platform users already use; zero friction to adopt', '★★★★½'],
            ].map(([crit, how, stars]) => (
              <tr key={crit}><td>{crit}</td><td>{how}</td><td className="stars">{stars}</td></tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Roadmap */}
      <div className="arch-section">
        <div className="arch-title">Implementation Roadmap</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {[
            { phase: 'Phase 1', color: 'blue', title: 'Core (4 hrs)', desc: 'Express skeleton + /verify endpoint · OCR + Claim Checker (Groq) · Chrome extension MV3 + button injection' },
            { phase: 'Phase 2', color: 'purple', title: 'Agents (4 hrs)', desc: 'Reverse Image Search (TinEye) · AI Image Detection (MobileViT + Groq) · Link scanner + Bot detection' },
            { phase: 'Phase 3', color: 'green', title: 'Polish (3 hrs)', desc: 'Synthesis agent prompt + confidence calibration · Verdict card UI in shadow DOM · Bot-comment heuristics' },
            { phase: 'Phase 4', color: 'yellow', title: 'Demo (1 hr)', desc: 'Record 3 demo cases (verified / suspicious / fake) · Deploy backend to Railway · Slide deck' },
          ].map(({ phase, color, title, desc }) => (
            <div key={phase} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '11px 13px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 9 }}>
              <div style={{ fontSize: 10, fontWeight: 700, background: `var(--${color}-bg)`, color: `var(--${color})`, border: `1px solid var(--${color}-border)`, borderRadius: 4, padding: '2px 7px', whiteSpace: 'nowrap', marginTop: 1 }}>{phase}</div>
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 2 }}>{title}</div>
                <div style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
