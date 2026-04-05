import AgentCard from './AgentCard.jsx';

const STATUS_ICON  = { verified: '✓', suspicious: '⚠', fake: '✗' };
const STATUS_EMOJI = { verified: '✅', suspicious: '⚠️', fake: '🚫' };

function teamScore(agents) {
  const total = agents.reduce((s, a) => s + (a.score === 'OK' ? 1 : a.score === 'WARN' ? 0.5 : 0), 0);
  return Math.round((total / agents.length) * 100);
}

export default function DebateVerdict({ verdict, onReRun }) {
  const blue = verdict.agents.filter((a) => a.team === 'blue');
  const red = verdict.agents.filter((a) => a.team === 'red');
  const blueScore = teamScore(blue);
  const redScore = teamScore(red);
  const v = verdict.verdict;

  return (
    <>
      <div className="debate-section-label">
        <svg width="11" height="11" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
        Blue Team — Detection Forensics
      </div>
      {blue.map((a, i) => (
        <AgentCard key={`blue-${i}`} agent={a} uid={`blue-${i}`} />
      ))}

      <div className="vs-divider">
        <div className="vs-pill">VS</div>
      </div>

      <div className="debate-section-label">
        <svg width="11" height="11" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        Red Team — Context Verification
      </div>
      {red.map((a, i) => (
        <AgentCard key={`red-${i}`} agent={a} uid={`red-${i}`} />
      ))}

      <div className="debate-scores">
        <div className="team-score-block">
          <div className="team-score-label blue">🛡️ Blue Team</div>
          <div className="team-score-num blue">{blueScore}</div>
          <div className="team-score-sub">detection score</div>
        </div>
        <div className="vs-center"><div className="vs-center-label">VS</div></div>
        <div className="team-score-block">
          <div className="team-score-label red">🔍 Red Team</div>
          <div className="team-score-num red">{redScore}</div>
          <div className="team-score-sub">verification score</div>
        </div>
      </div>

      <div className={`synthesis-ruling ${v}`}>
        <div className={`sr-header ${v}`}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div className={`sr-verdict-icon ${v}`}>{STATUS_EMOJI[v]}</div>
            <div>
              <div className={`sr-title ${v}`}>Synthesis Agent <span style={{ fontSize: 10, fontWeight: 500, opacity: 0.7 }}>· LLM-Powered</span></div>
              <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: '-0.02em', marginTop: 2 }}
                   className={`sr-title ${v}`}>{v.toUpperCase()}</div>
            </div>
          </div>
          <div className="sr-score-wrap">
            <div className="sr-score-label">Confidence Score</div>
            <div className={`sr-score ${v}`}>{verdict.confidence}<span style={{ fontSize: 16, fontWeight: 400 }}>/100</span></div>
            {verdict.weighted_score != null && verdict.weighted_score !== verdict.confidence && (
              <div style={{ fontSize: 10, color: 'var(--text-dim)', marginTop: 2, fontFamily: 'Geist Mono, monospace' }}>
                Weighted: {verdict.weighted_score}/100
              </div>
            )}
          </div>
        </div>
        <div className="sr-bar-bg">
          <div className={`sr-bar-fill ${v}`} style={{ width: `${verdict.confidence}%` }} />
        </div>
        <div className="sr-body">
          <div className="sr-reasoning-title">🧠 Synthesis Reasoning</div>
          <div className="sr-reasoning">{verdict.synthesis}</div>

          {/* Key Evidence */}
          {verdict.key_evidence?.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)', fontWeight: 600, marginBottom: 6 }}>Key Evidence</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {verdict.key_evidence.map((ev, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 7, padding: '5px 9px', background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 6 }}>
                    <span style={{ color: v === 'fake' ? 'var(--red)' : v === 'suspicious' ? 'var(--yellow)' : 'var(--green)', fontSize: 11, flexShrink: 0, marginTop: 1 }}>◆</span>
                    <span style={{ fontSize: 11.5, color: 'var(--text-muted)', lineHeight: 1.45 }}>{String(ev)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Contradictions */}
          {verdict.contradictions?.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--yellow)', fontWeight: 600, marginBottom: 6 }}>⚡ Agent Contradictions</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {verdict.contradictions.map((c, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 7, padding: '5px 9px', background: 'var(--yellow-bg)', border: '1px solid var(--yellow-border)', borderRadius: 6 }}>
                    <span style={{ color: 'var(--yellow)', fontSize: 11, flexShrink: 0, marginTop: 1 }}>⚠</span>
                    <span style={{ fontSize: 11.5, color: 'var(--yellow)', lineHeight: 1.45 }}>{String(c)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Decisive Factors */}
          {verdict.decisive_factors && (
            <div style={{ marginTop: 12, padding: '8px 10px', background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 7 }}>
              <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)', fontWeight: 600, marginBottom: 4 }}>Decisive Factor</div>
              <div style={{ fontSize: 12, color: 'var(--text)', fontStyle: 'italic', lineHeight: 1.5 }}>{verdict.decisive_factors}</div>
            </div>
          )}
        </div>
        <div className="sr-axes">
          <span className="sr-axes-label">Axes covered:</span>
          <span className="dac-axis-tag auth">🔬 Content Authenticity</span>
          <span className="dac-axis-tag context">🔎 Contextual Consistency</span>
          <span className="dac-axis-tag source">🏅 Source Credibility</span>
        </div>
      </div>

      <button className="verify-btn secondary" onClick={onReRun} style={{ marginTop: 12 }}>
        ↻ Re-analyze
      </button>
    </>
  );
}
