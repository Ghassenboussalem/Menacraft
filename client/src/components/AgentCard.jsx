import { useState } from 'react';

const SCORE_MAP   = { OK: 'ok', WARN: 'warn', BAD: 'bad' };
const SCORE_LABEL = { OK: 'Clean', WARN: 'Flagged', BAD: 'Fail' };
const BAR_PCT     = { OK: 92, WARN: 48, BAD: 12 };
const AXIS_LABEL  = {
  auth:    'Content Authenticity',
  context: 'Contextual Consistency',
  source:  'Source Credibility',
};

// ── sub-renderers ─────────────────────────────────────────────────────────

function OcrDetails({ raw }) {
  if (!raw) return null;
  const verdictColors = {
    CONSISTENT:   { bg: 'var(--green-bg)',   color: 'var(--green)',  border: 'var(--green-border)' },
    PARTIAL:      { bg: 'var(--yellow-bg)',  color: 'var(--yellow)', border: 'var(--yellow-border)' },
    INCONSISTENT: { bg: 'var(--red-bg)',     color: 'var(--red)',    border: 'var(--red-border)' },
  };
  const manipColors = {
    NONE:                  { bg: 'var(--green-bg)',   color: 'var(--green)',  border: 'var(--green-border)' },
    FALSE_CONTEXT:         { bg: 'var(--red-bg)',     color: 'var(--red)',    border: 'var(--red-border)' },
    EXAGGERATION:          { bg: 'var(--yellow-bg)',  color: 'var(--yellow)', border: 'var(--yellow-border)' },
    FABRICATION:           { bg: 'var(--red-bg)',     color: 'var(--red)',    border: 'var(--red-border)' },
    OUT_OF_CONTEXT:        { bg: 'var(--red-bg)',     color: 'var(--red)',    border: 'var(--red-border)' },
    EMOTIONAL_MANIPULATION:{ bg: 'var(--yellow-bg)',  color: 'var(--yellow)', border: 'var(--yellow-border)' },
  };
  const vc = verdictColors[raw.verdict] || verdictColors.PARTIAL;
  const mc = manipColors[raw.manipulation_type] || { bg: 'var(--surface3)', color: 'var(--text-dim)', border: 'var(--border)' };

  return (
    <div style={{ marginTop: 10 }}>
      {/* Verdict + score row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{ background: vc.bg, color: vc.color, border: `1px solid ${vc.border}`, borderRadius: 6, padding: '3px 10px', fontSize: 11, fontWeight: 700, letterSpacing: '0.05em' }}>
          {raw.verdict}
        </span>
        <div style={{ flex: 1, background: 'var(--surface3)', borderRadius: 4, height: 6, overflow: 'hidden' }}>
          <div style={{
            height: '100%', borderRadius: 4,
            width: `${raw.match_score}%`,
            background: raw.match_score >= 80 ? 'var(--green)' : raw.match_score >= 50 ? 'var(--yellow)' : 'var(--red)',
            transition: 'width 0.6s ease',
          }} />
        </div>
        <span style={{ fontFamily: 'Geist Mono, monospace', fontSize: 11, color: 'var(--text-muted)', width: 32, textAlign: 'right' }}>{raw.match_score}%</span>
      </div>

      {/* Manipulation type */}
      {raw.manipulation_type && raw.manipulation_type !== 'NONE' && (
        <div style={{ marginBottom: 8 }}>
          <span style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.07em', marginRight: 6 }}>Manipulation</span>
          <span style={{ background: mc.bg, color: mc.color, border: `1px solid ${mc.border}`, borderRadius: 4, padding: '2px 8px', fontSize: 10, fontWeight: 600 }}>
            {raw.manipulation_type.replace(/_/g, ' ')}
          </span>
        </div>
      )}

      {/* OCR text detected */}
      {raw.ocr_detected?.length > 0 && (
        <div style={{ marginBottom: 8 }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)', marginBottom: 5 }}>Text detected in image</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {raw.ocr_detected.map((t, i) => (
              <span key={i} style={{ background: 'var(--blue-bg)', color: 'var(--blue)', border: '1px solid var(--blue-border)', borderRadius: 4, padding: '2px 7px', fontSize: 11, fontFamily: 'Geist Mono, monospace' }}>
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Visual signals */}
      {raw.visual_signals && (
        <div style={{ marginBottom: 8 }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)', marginBottom: 4 }}>Visual context</div>
          <div style={{ fontSize: 11.5, color: 'var(--text-muted)', lineHeight: 1.55 }}>{raw.visual_signals}</div>
        </div>
      )}

      {/* Red flags */}
      {raw.red_flags?.length > 0 && (
        <div style={{ marginBottom: 4 }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)', marginBottom: 5 }}>Red flags</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {raw.red_flags.map((f, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 6, fontSize: 11.5 }}>
                <span style={{ color: 'var(--red)', flexShrink: 0, marginTop: 1 }}>⚠</span>
                <span style={{ color: 'var(--text-muted)' }}>{f}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ReverseImageDetails({ raw }) {
  if (!raw) return null;
  const verdictMeta = {
    ORIGINAL:         { label: 'Original',          bg: 'var(--green-bg)',  color: 'var(--green)',  border: 'var(--green-border)',  icon: '✓' },
    PLAUSIBLE:        { label: 'Plausible',          bg: 'var(--green-bg)',  color: 'var(--green)',  border: 'var(--green-border)',  icon: '✓' },
    QUESTIONABLE:     { label: 'Questionable',       bg: 'var(--yellow-bg)', color: 'var(--yellow)', border: 'var(--yellow-border)', icon: '⚠' },
    SUSPICIOUS:       { label: 'Suspicious',         bg: 'var(--yellow-bg)', color: 'var(--yellow)', border: 'var(--yellow-border)', icon: '⚠' },
    HIGHLY_SUSPICIOUS:{ label: 'Highly Suspicious',  bg: 'var(--red-bg)',    color: 'var(--red)',    border: 'var(--red-border)',    icon: '✗' },
    FAKE:             { label: 'Fake — Predates Event', bg: 'var(--red-bg)', color: 'var(--red)',    border: 'var(--red-border)',    icon: '✗' },
  };
  const vm = verdictMeta[raw.verdict] || { label: raw.verdict, bg: 'var(--surface3)', color: 'var(--text-dim)', border: 'var(--border)', icon: '?' };

  return (
    <div style={{ marginTop: 10 }}>
      {/* Verdict badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{ background: vm.bg, color: vm.color, border: `1px solid ${vm.border}`, borderRadius: 6, padding: '3px 10px', fontSize: 11, fontWeight: 700 }}>
          {vm.icon} {vm.label}
        </span>
      </div>

      {/* Stats grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginBottom: 10 }}>
        <div style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 10px' }}>
          <div style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 2 }}>Total Matches</div>
          <div style={{ fontSize: 18, fontWeight: 600, letterSpacing: '-0.03em', color: raw.total_matches > 0 ? 'var(--red)' : 'var(--green)' }}>
            {raw.total_matches ?? '—'}
          </div>
        </div>
        <div style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 10px' }}>
          <div style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 2 }}>Oldest Found</div>
          <div style={{ fontSize: 13, fontWeight: 600, fontFamily: 'Geist Mono, monospace', color: 'var(--text)' }}>
            {raw.oldest_date || 'Not found'}
          </div>
        </div>
      </div>

      {/* Gap bar */}
      {raw.gap_days !== null && raw.gap_days !== undefined && (
        <div style={{ marginBottom: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
            <span style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Temporal Gap</span>
            <span style={{ fontFamily: 'Geist Mono, monospace', fontSize: 11, color: raw.gap_days < 0 ? 'var(--red)' : raw.gap_days > 365 ? 'var(--red)' : 'var(--text-muted)' }}>
              {raw.gap_days < 0 ? `${Math.abs(raw.gap_days)}d BEFORE claimed date` : `${raw.gap_days}d gap`}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

function AiForensicsDetails({ raw }) {
  if (!raw) return null;

  const verdictMeta = {
    likely_ai_generated:   { label: 'Likely AI-Generated',   bg: 'var(--red-bg)',    color: 'var(--red)',      border: 'var(--red-border)' },
    possibly_ai_generated: { label: 'Possibly AI-Generated', bg: 'var(--yellow-bg)', color: 'var(--yellow)',   border: 'var(--yellow-border)' },
    uncertain:             { label: 'Uncertain',              bg: 'var(--surface3)',  color: 'var(--text-dim)', border: 'var(--border)' },
    likely_authentic:      { label: 'Likely Authentic',       bg: 'var(--green-bg)',  color: 'var(--green)',    border: 'var(--green-border)' },
  };
  const sevMeta = {
    critical: { color: 'var(--red)',      bg: 'var(--red-bg)',    border: 'var(--red-border)' },
    moderate: { color: 'var(--yellow)',   bg: 'var(--yellow-bg)', border: 'var(--yellow-border)' },
    minor:    { color: 'var(--blue)',     bg: 'var(--blue-bg)',   border: 'var(--blue-border)' },
    none:     { color: 'var(--text-dim)', bg: 'var(--surface3)',  border: 'var(--border)' },
  };

  const vm  = verdictMeta[raw.verdict] || verdictMeta.uncertain;
  const pct = Math.round((raw.confidence || 0) * 100);
  const stages = raw.stages || {};
  const scene       = stages.scene_analysis || {};
  const features    = stages.features_identified || [];
  const inspections = stages.feature_inspections || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 10 }}>

      {/* ── Verdict + score breakdown ── */}
      <div style={{ background: 'var(--surface2)', border: `1px solid ${vm.border}`, borderRadius: 12, overflow: 'hidden' }}>
        <div style={{ padding: '12px 14px', background: vm.bg, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 22 }}>{raw.verdict === 'likely_authentic' ? '✅' : raw.verdict === 'likely_ai_generated' ? '🤖' : '⚠️'}</span>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: vm.color }}>{vm.label}</div>
              <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 1 }}>{raw.method === 'combined' ? 'MobileViT + Groq Vision' : 'Groq Vision Pipeline'}</div>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: vm.color, letterSpacing: '-0.03em' }}>{pct}%</div>
            <div style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>AI Confidence</div>
          </div>
        </div>
        {/* Confidence bar */}
        <div style={{ height: 5, background: 'var(--surface3)' }}>
          <div style={{ height: '100%', width: `${pct}%`, background: vm.color, transition: 'width 0.8s ease' }} />
        </div>
        {/* Score grid */}
        {raw.scores && (
          <div style={{ display: 'grid', gridTemplateColumns: raw.scores.classifier_score != null ? '1fr 1fr 1fr' : '1fr 1fr', gap: 1, background: 'var(--border)' }}>
            {raw.scores.classifier_score != null && (
              <div style={{ background: 'var(--surface2)', padding: '8px 12px', textAlign: 'center' }}>
                <div style={{ fontSize: 9, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 3 }}>MobileViT</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text)' }}>{Math.round(raw.scores.classifier_score * 100)}%</div>
              </div>
            )}
            {raw.scores.pipeline_score != null && (
              <div style={{ background: 'var(--surface2)', padding: '8px 12px', textAlign: 'center' }}>
                <div style={{ fontSize: 9, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 3 }}>Groq Vision</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text)' }}>{Math.round(raw.scores.pipeline_score * 100)}%</div>
              </div>
            )}
            {raw.scores.combined_score != null && (
              <div style={{ background: 'var(--surface2)', padding: '8px 12px', textAlign: 'center' }}>
                <div style={{ fontSize: 9, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 3 }}>Combined</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: vm.color }}>{Math.round(raw.scores.combined_score * 100)}%</div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Stage 1: Scene Analysis ── */}
      {scene.subject && (
        <div style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 12, padding: '12px 14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <span style={{ fontSize: 16 }}>🔍</span>
            <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)' }}>Stage 1 — Scene Analysis</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
            {[
              { label: 'Subject', value: scene.subject },
              { label: 'Style', value: scene.style },
              { label: 'Setting', value: scene.setting },
            ].filter(x => x.value).map(({ label, value }) => (
              <div key={label} style={{ background: 'var(--surface3)', borderRadius: 8, padding: '7px 10px' }}>
                <div style={{ fontSize: 9, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 3 }}>{label}</div>
                <div style={{ fontSize: 12, color: 'var(--text)', fontWeight: 500 }}>{value}</div>
              </div>
            ))}
          </div>
          {(scene.notable_elements || scene.elements) && (
            <div style={{ marginTop: 8, fontSize: 11.5, color: 'var(--text-muted)', lineHeight: 1.55 }}>
              <span style={{ color: 'var(--text-dim)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', marginRight: 6 }}>Elements:</span>
              {Array.isArray(scene.notable_elements || scene.elements) ? (scene.notable_elements || scene.elements).join(', ') : (scene.notable_elements || scene.elements)}
            </div>
          )}
        </div>
      )}

      {/* ── Stage 2: Features Checked ── */}
      {features.length > 0 && (
        <div style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 12, padding: '12px 14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <span style={{ fontSize: 16 }}>🧠</span>
            <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)' }}>Stage 2 — Features Inspected ({features.length})</span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
            {features.map((f, i) => {
              const name = typeof f === 'string' ? f : (f.category || f.feature || f.name || String(f));
              const priority = typeof f === 'object' ? f.priority : null;
              const priorityColor = priority === 'high' ? 'var(--red)' : priority === 'medium' ? 'var(--yellow)' : 'var(--blue)';
              return (
                <span key={i} style={{
                  fontSize: 11, padding: '3px 9px', borderRadius: 6,
                  background: 'var(--surface3)', border: '1px solid var(--border)',
                  color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 5,
                }}>
                  {priority && <span style={{ width: 6, height: 6, borderRadius: '50%', background: priorityColor, flexShrink: 0, display: 'inline-block' }} />}
                  {name.replace(/_/g, ' ')}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Stage 3: Inspection Results per feature ── */}
      {/* feature_inspections is a list parallel to features_identified */}
      {Array.isArray(inspections) && inspections.length > 0 && (
        <div style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 12, padding: '12px 14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <span style={{ fontSize: 16 }}>🔬</span>
            <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)' }}>Stage 3 — Inspection Results</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {inspections.map((data, idx) => {
              const featureName = (features[idx]?.category || features[idx]?.feature || `Feature ${idx + 1}`).replace(/_/g, ' ');
              const aiConf = data.confidence_ai != null ? Math.round(data.confidence_ai * 100) : null;
              const artifacts = Array.isArray(data.artifacts_detected) ? data.artifacts_detected : [];
              const confColor = aiConf >= 70 ? 'var(--red)' : aiConf >= 40 ? 'var(--yellow)' : 'var(--green)';
              return (
                <div key={idx} style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, overflow: 'hidden' }}>
                  <div style={{ padding: '8px 12px', background: 'var(--surface3)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', textTransform: 'capitalize' }}>{featureName}</span>
                    {aiConf != null && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ width: 80, height: 5, background: 'var(--surface2)', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${aiConf}%`, background: confColor, borderRadius: 3 }} />
                        </div>
                        <span style={{ fontSize: 11, fontWeight: 700, color: confColor, fontFamily: 'Geist Mono, monospace', width: 36, textAlign: 'right' }}>{aiConf}% AI</span>
                      </div>
                    )}
                  </div>
                  {artifacts.length > 0 && (
                    <div style={{ padding: '8px 12px', display: 'flex', flexDirection: 'column', gap: 5 }}>
                      {artifacts.map((art, ai) => {
                        const sev = art.severity || 'minor';
                        const sm = sevMeta[sev] || sevMeta.minor;
                        const label = art.label || art.type || art.name || '';
                        const desc = art.description || art.details || '';
                        return (
                          <div key={ai} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: '5px 8px', background: sm.bg, border: `1px solid ${sm.border}`, borderRadius: 7 }}>
                            <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 5px', borderRadius: 3, background: sm.color, color: '#fff', flexShrink: 0, marginTop: 1, textTransform: 'uppercase' }}>{sev}</span>
                            <div style={{ flex: 1, minWidth: 0 }}>
                              {label && <div style={{ fontSize: 11.5, fontWeight: 600, color: sm.color }}>{label}</div>}
                              {desc && <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2, lineHeight: 1.45 }}>{desc}</div>}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Key findings (fallback if no stage data) ── */}
      {Object.keys(inspections).length === 0 && raw.key_findings?.length > 0 && (
        <div style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 12, padding: '12px 14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <span style={{ fontSize: 16 }}>📋</span>
            <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)' }}>Key Findings</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {raw.key_findings.map((f, i) => {
              const isObj = f && typeof f === 'object';
              const sev = isObj ? (f.severity || 'minor') : null;
              const sm = sevMeta[sev] || sevMeta.minor;
              return (
                <div key={i} style={{ padding: '6px 10px', background: isObj ? sm.bg : 'var(--surface3)', border: `1px solid ${isObj ? sm.border : 'var(--border)'}`, borderRadius: 8 }}>
                  {isObj ? (
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 7 }}>
                      <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 5px', borderRadius: 3, background: sm.color, color: '#fff', flexShrink: 0, marginTop: 1, textTransform: 'uppercase' }}>{sev}</span>
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 600, color: sm.color }}>{f.feature || ''}</div>
                        {f.finding && <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{f.finding}</div>}
                      </div>
                    </div>
                  ) : (
                    <div style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>◆ {String(f)}</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Annotated image ── */}
      {raw.annotated_image_b64 && (
        <div style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 12, overflow: 'hidden' }}>
          <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 16 }}>🖼️</span>
            <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)' }}>Annotated Analysis — Top Artifacts Highlighted</span>
          </div>
          <img
            src={`data:image/jpeg;base64,${raw.annotated_image_b64}`}
            alt="AI Detection Annotated"
            style={{ width: '100%', display: 'block' }}
          />
        </div>
      )}
    </div>
  );
}

function BotDetectionDetails({ raw }) {
  if (!raw) return null;
  const classMeta = {
    bot:          { label: 'Bot Account',    bg: 'var(--red-bg)',    color: 'var(--red)',    border: 'var(--red-border)',    bar: 'var(--red)' },
    inconclusive: { label: 'Inconclusive',   bg: 'var(--yellow-bg)', color: 'var(--yellow)', border: 'var(--yellow-border)', bar: 'var(--yellow)' },
    real:         { label: 'Real Account',    bg: 'var(--green-bg)',  color: 'var(--green)',  border: 'var(--green-border)',  bar: 'var(--green)' },
  };
  const riskMeta = {
    HIGH:   { label: 'HIGH RISK',   bg: 'var(--red-bg)',    color: 'var(--red)',    border: 'var(--red-border)',    icon: '🚨' },
    MEDIUM: { label: 'MEDIUM RISK', bg: 'var(--yellow-bg)', color: 'var(--yellow)', border: 'var(--yellow-border)', icon: '⚠️' },
    LOW:    { label: 'LOW RISK',    bg: 'var(--green-bg)',  color: 'var(--green)',  border: 'var(--green-border)',  icon: '✅' },
  };
  const cm = classMeta[raw.classification] || classMeta.inconclusive;
  const rm = riskMeta[raw.risk_level] || riskMeta.MEDIUM;
  const acct = raw.account_data || {};
  const ratio = acct.following > 0 ? (acct.followers / acct.following).toFixed(2) : '∞';

  function fmtK(n) {
    if (n == null) return '—';
    const x = parseInt(n);
    if (isNaN(x)) return '—';
    return x >= 1000000 ? (x / 1000000).toFixed(1) + 'M' : x >= 1000 ? (x / 1000).toFixed(1) + 'K' : String(x);
  }

  return (
    <div style={{ marginTop: 10 }}>
      {/* Classification + Risk badges */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
        <span style={{ background: cm.bg, color: cm.color, border: `1px solid ${cm.border}`, borderRadius: 6, padding: '3px 10px', fontSize: 11, fontWeight: 700, letterSpacing: '0.04em' }}>
          {cm.label}
        </span>
        <span style={{ background: rm.bg, color: rm.color, border: `1px solid ${rm.border}`, borderRadius: 6, padding: '3px 10px', fontSize: 11, fontWeight: 700, letterSpacing: '0.04em' }}>
          {rm.icon} {rm.label}
        </span>
      </div>

      {/* Bot Score bar */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
          <span style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Bot Probability Score</span>
          <span style={{ fontFamily: 'Geist Mono, monospace', fontSize: 13, fontWeight: 700, color: cm.color }}>{raw.bot_score?.toFixed(1)}/100</span>
        </div>
        <div style={{ background: 'var(--surface3)', borderRadius: 5, height: 8, overflow: 'hidden', position: 'relative' }}>
          <div style={{
            height: '100%', borderRadius: 5,
            width: `${Math.min(100, raw.bot_score || 0)}%`,
            background: `linear-gradient(90deg, var(--green) 0%, var(--yellow) 50%, var(--red) 100%)`,
            transition: 'width 0.8s ease',
          }} />
          {/* Threshold markers */}
          <div style={{ position: 'absolute', left: '30%', top: 0, bottom: 0, width: 1, background: 'var(--text-dim)', opacity: 0.3 }} />
          <div style={{ position: 'absolute', left: '70%', top: 0, bottom: 0, width: 1, background: 'var(--text-dim)', opacity: 0.3 }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 3 }}>
          <span style={{ fontSize: 9, color: 'var(--text-dim)' }}>Real (0-30)</span>
          <span style={{ fontSize: 9, color: 'var(--text-dim)' }}>Inconclusive</span>
          <span style={{ fontSize: 9, color: 'var(--text-dim)' }}>Bot (70-100)</span>
        </div>
      </div>

      {/* Account Metrics Grid */}
      <div style={{ marginBottom: 10 }}>
        <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)', marginBottom: 6 }}>Account Metrics</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6 }}>
          <div style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 10px', textAlign: 'center' }}>
            <div style={{ fontSize: 9, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>Followers</div>
            <div style={{ fontSize: 16, fontWeight: 600, letterSpacing: '-0.03em', color: 'var(--text)' }}>{fmtK(acct.followers)}</div>
          </div>
          <div style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 10px', textAlign: 'center' }}>
            <div style={{ fontSize: 9, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>Following</div>
            <div style={{ fontSize: 16, fontWeight: 600, letterSpacing: '-0.03em', color: 'var(--text)' }}>{fmtK(acct.following)}</div>
          </div>
          <div style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 10px', textAlign: 'center' }}>
            <div style={{ fontSize: 9, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>Posts</div>
            <div style={{ fontSize: 16, fontWeight: 600, letterSpacing: '-0.03em', color: 'var(--text)' }}>{fmtK(acct.posts)}</div>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginTop: 6 }}>
          <div style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 10px', textAlign: 'center' }}>
            <div style={{ fontSize: 9, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>Follower Ratio</div>
            <div style={{ fontSize: 14, fontWeight: 600, fontFamily: 'Geist Mono, monospace', color: parseFloat(ratio) < 0.1 ? 'var(--red)' : 'var(--text)' }}>{ratio}</div>
          </div>
          <div style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 10px', textAlign: 'center' }}>
            <div style={{ fontSize: 9, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>Bio Length</div>
            <div style={{ fontSize: 14, fontWeight: 600, fontFamily: 'Geist Mono, monospace', color: acct.bio_length === 0 ? 'var(--red)' : 'var(--text)' }}>{acct.bio_length ?? '—'} chars</div>
          </div>
        </div>
      </div>

      {/* Suspicious Flags */}
      {raw.suspicious_flags?.length > 0 && (
        <div style={{ marginBottom: 8 }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)', marginBottom: 6 }}>Suspicious Indicators</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {raw.suspicious_flags.map((flag, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '5px 9px', background: 'var(--red-bg)', border: '1px solid var(--red-border)', borderRadius: 6 }}>
                <span style={{ color: 'var(--red)', fontSize: 12, flexShrink: 0 }}>❌</span>
                <span style={{ fontSize: 11.5, color: 'var(--red)', fontWeight: 500 }}>{String(flag)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      {raw.suspicious_flags?.length === 0 && (
        <div style={{ padding: '6px 9px', background: 'var(--green-bg)', border: '1px solid var(--green-border)', borderRadius: 6, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 7 }}>
          <span style={{ color: 'var(--green)', fontSize: 12 }}>✅</span>
          <span style={{ fontSize: 11.5, color: 'var(--green)', fontWeight: 500 }}>No major red flags detected</span>
        </div>
      )}

      {/* Account Quick Info */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 4 }}>
        {acct.has_profile_pic ? (
          <span style={{ background: 'var(--green-bg)', color: 'var(--green)', border: '1px solid var(--green-border)', borderRadius: 4, padding: '2px 7px', fontSize: 10, fontWeight: 600 }}>Has Profile Pic</span>
        ) : (
          <span style={{ background: 'var(--red-bg)', color: 'var(--red)', border: '1px solid var(--red-border)', borderRadius: 4, padding: '2px 7px', fontSize: 10, fontWeight: 600 }}>No Profile Pic</span>
        )}
        {acct.is_private ? (
          <span style={{ background: 'var(--yellow-bg)', color: 'var(--yellow)', border: '1px solid var(--yellow-border)', borderRadius: 4, padding: '2px 7px', fontSize: 10, fontWeight: 600 }}>Private</span>
        ) : (
          <span style={{ background: 'var(--surface3)', color: 'var(--text-dim)', border: '1px solid var(--border)', borderRadius: 4, padding: '2px 7px', fontSize: 10, fontWeight: 600 }}>Public</span>
        )}
        {acct.has_external_url ? (
          <span style={{ background: 'var(--green-bg)', color: 'var(--green)', border: '1px solid var(--green-border)', borderRadius: 4, padding: '2px 7px', fontSize: 10, fontWeight: 600 }}>Has URL</span>
        ) : (
          <span style={{ background: 'var(--surface3)', color: 'var(--text-dim)', border: '1px solid var(--border)', borderRadius: 4, padding: '2px 7px', fontSize: 10, fontWeight: 600 }}>No URL</span>
        )}
      </div>
    </div>
  );
}

// ── Caption-Image Alignment Details ────────────────────────────────────────
function CaptionAlignmentDetails({ raw }) {
  if (!raw) return null;
  const score = raw.alignment_score || 0;
  const pct = Math.round(score * 100);
  const verdictLabels = {
    strong_match: { label: 'Strong Match', color: 'var(--green)', bg: 'var(--green-bg)', border: 'var(--green-border)' },
    partial_match: { label: 'Partial Match', color: 'var(--yellow)', bg: 'var(--yellow-bg)', border: 'var(--yellow-border)' },
    weak_match: { label: 'Weak Match', color: 'var(--red)', bg: 'var(--red-bg)', border: 'var(--red-border)' },
    mismatch: { label: 'Mismatch', color: 'var(--red)', bg: 'var(--red-bg)', border: 'var(--red-border)' },
  };
  const vm = verdictLabels[raw.verdict] || verdictLabels.partial_match;

  return (
    <div style={{ marginTop: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{ background: vm.bg, color: vm.color, border: `1px solid ${vm.border}`, borderRadius: 6, padding: '3px 10px', fontSize: 11, fontWeight: 700 }}>
          {vm.label}
        </span>
      </div>
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
          <span style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Alignment Score</span>
          <span style={{ fontFamily: 'Geist Mono, monospace', fontSize: 13, fontWeight: 700, color: vm.color }}>{pct}%</span>
        </div>
        <div style={{ background: 'var(--surface3)', borderRadius: 5, height: 8, overflow: 'hidden' }}>
          <div style={{ height: '100%', borderRadius: 5, width: `${pct}%`, background: vm.color, transition: 'width 0.8s ease' }} />
        </div>
      </div>
      {raw.key_observations?.length > 0 && (
        <div>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)', marginBottom: 6 }}>Key Observations</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {raw.key_observations.map((obs, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 7, padding: '5px 9px', background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 6 }}>
                <span style={{ color: 'var(--text-dim)', fontSize: 11, flexShrink: 0, marginTop: 1 }}>•</span>
                <span style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>{String(obs)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Source Credibility Details ──────────────────────────────────────────────
function SourceCredibilityDetails({ raw }) {
  if (!raw) return null;
  const score = raw.credibility_score || 0;
  const pct = Math.round(score * 100);
  const verdictLabels = {
    highly_credible: { label: 'Highly Credible', color: 'var(--green)', bg: 'var(--green-bg)', border: 'var(--green-border)' },
    credible: { label: 'Credible', color: 'var(--green)', bg: 'var(--green-bg)', border: 'var(--green-border)' },
    mixed: { label: 'Mixed Signals', color: 'var(--yellow)', bg: 'var(--yellow-bg)', border: 'var(--yellow-border)' },
    low_credibility: { label: 'Low Credibility', color: 'var(--red)', bg: 'var(--red-bg)', border: 'var(--red-border)' },
    not_credible: { label: 'Not Credible', color: 'var(--red)', bg: 'var(--red-bg)', border: 'var(--red-border)' },
  };
  const vm = verdictLabels[raw.verdict] || verdictLabels.mixed;

  return (
    <div style={{ marginTop: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{ background: vm.bg, color: vm.color, border: `1px solid ${vm.border}`, borderRadius: 6, padding: '3px 10px', fontSize: 11, fontWeight: 700 }}>
          {vm.label}
        </span>
      </div>
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
          <span style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Credibility Score</span>
          <span style={{ fontFamily: 'Geist Mono, monospace', fontSize: 13, fontWeight: 700, color: vm.color }}>{pct}%</span>
        </div>
        <div style={{ background: 'var(--surface3)', borderRadius: 5, height: 8, overflow: 'hidden' }}>
          <div style={{ height: '100%', borderRadius: 5, width: `${pct}%`, background: vm.color, transition: 'width 0.8s ease' }} />
        </div>
      </div>
      {raw.risk_factors?.length > 0 && (
        <div style={{ marginBottom: 8 }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)', marginBottom: 6 }}>Risk Factors</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {raw.risk_factors.map((rf, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 7, padding: '5px 9px', background: 'var(--red-bg)', border: '1px solid var(--red-border)', borderRadius: 6 }}>
                <span style={{ color: 'var(--red)', fontSize: 11, flexShrink: 0 }}>⚠</span>
                <span style={{ fontSize: 11.5, color: 'var(--red)' }}>{String(rf)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      {raw.positive_signals?.length > 0 && (
        <div>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)', marginBottom: 6 }}>Positive Signals</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {raw.positive_signals.map((ps, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 7, padding: '5px 9px', background: 'var(--green-bg)', border: '1px solid var(--green-border)', borderRadius: 6 }}>
                <span style={{ color: 'var(--green)', fontSize: 11, flexShrink: 0 }}>✓</span>
                <span style={{ fontSize: 11.5, color: 'var(--green)' }}>{String(ps)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Link Scanner Details ───────────────────────────────────────────────────
function LinkScannerDetails({ raw }) {
  if (!raw) return null;
  const riskPct = Math.round((raw.risk_score || 0) * 100);
  const verdictLabels = {
    clean: { label: 'Clean', color: 'var(--green)', bg: 'var(--green-bg)', border: 'var(--green-border)' },
    safe: { label: 'Safe', color: 'var(--green)', bg: 'var(--green-bg)', border: 'var(--green-border)' },
    caution: { label: 'Caution', color: 'var(--yellow)', bg: 'var(--yellow-bg)', border: 'var(--yellow-border)' },
    suspicious: { label: 'Suspicious', color: 'var(--red)', bg: 'var(--red-bg)', border: 'var(--red-border)' },
    dangerous: { label: 'Dangerous', color: 'var(--red)', bg: 'var(--red-bg)', border: 'var(--red-border)' },
  };
  const vm = verdictLabels[raw.verdict] || verdictLabels.safe;

  return (
    <div style={{ marginTop: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{ background: vm.bg, color: vm.color, border: `1px solid ${vm.border}`, borderRadius: 6, padding: '3px 10px', fontSize: 11, fontWeight: 700 }}>
          {vm.label}
        </span>
        <span style={{ fontSize: 11, color: 'var(--text-dim)', fontFamily: 'Geist Mono, monospace' }}>
          {(raw.urls_found?.length || 0)} URL(s) · {(raw.domains_found?.length || 0)} domain(s)
        </span>
      </div>
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
          <span style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Risk Score</span>
          <span style={{ fontFamily: 'Geist Mono, monospace', fontSize: 13, fontWeight: 700, color: vm.color }}>{riskPct}%</span>
        </div>
        <div style={{ background: 'var(--surface3)', borderRadius: 5, height: 8, overflow: 'hidden' }}>
          <div style={{ height: '100%', borderRadius: 5, width: `${riskPct}%`, background: vm.color, transition: 'width 0.8s ease' }} />
        </div>
      </div>
      {raw.flags?.length > 0 && (
        <div style={{ marginBottom: 8 }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)', marginBottom: 6 }}>Flags</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {raw.flags.map((f, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 7, padding: '5px 9px', background: 'var(--red-bg)', border: '1px solid var(--red-border)', borderRadius: 6 }}>
                <span style={{ color: 'var(--red)', fontSize: 11, flexShrink: 0 }}>⚠</span>
                <span style={{ fontSize: 11.5, color: 'var(--red)' }}>{String(f)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      {raw.url_analysis?.length > 0 && (
        <div>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)', marginBottom: 6 }}>URL Analysis</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {raw.url_analysis.map((ua, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 7, padding: '5px 9px', background: ua.safe ? 'var(--green-bg)' : 'var(--red-bg)', border: `1px solid ${ua.safe ? 'var(--green-border)' : 'var(--red-border)'}`, borderRadius: 6 }}>
                <span style={{ color: ua.safe ? 'var(--green)' : 'var(--red)', fontSize: 11, flexShrink: 0 }}>{ua.safe ? '✓' : '✗'}</span>
                <div>
                  <div style={{ fontSize: 10.5, fontFamily: 'Geist Mono, monospace', color: 'var(--text-muted)', wordBreak: 'break-all' }}>{ua.url}</div>
                  <div style={{ fontSize: 11, color: ua.safe ? 'var(--green)' : 'var(--red)', marginTop: 2 }}>{ua.reason}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function TextContentDetails({ raw }) {
  if (!raw) return null;
  const aiPct = Math.round((raw.ai_text_probability || 0) * 100);
  const verdictColors = {
    likely_ai_generated:   { color: 'var(--red)',    bg: 'var(--red-bg)',    border: 'var(--red-border)',    label: 'Likely AI Text' },
    possibly_ai_generated: { color: 'var(--yellow)',  bg: 'var(--yellow-bg)', border: 'var(--yellow-border)', label: 'Possibly AI Text' },
    likely_authentic:      { color: 'var(--green)',   bg: 'var(--green-bg)',  border: 'var(--green-border)',  label: 'Likely Authentic' },
    uncertain:             { color: 'var(--text-dim)', bg: 'var(--surface3)', border: 'var(--border)',        label: 'Uncertain' },
  };
  const vm = verdictColors[raw.verdict] || verdictColors.uncertain;

  return (
    <div style={{ marginTop: 10 }}>
      {/* Verdict + language chip */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
        <span style={{ background: vm.bg, color: vm.color, border: `1px solid ${vm.border}`, borderRadius: 6, padding: '3px 10px', fontSize: 11, fontWeight: 700 }}>
          {vm.label}
        </span>
        {raw.content_type && (
          <span style={{ background: 'var(--surface3)', color: 'var(--text-muted)', border: '1px solid var(--border)', borderRadius: 6, padding: '3px 8px', fontSize: 10.5, textTransform: 'capitalize' }}>
            {raw.content_type}
          </span>
        )}
        {raw.language && raw.language !== 'unknown' && (
          <span style={{ background: 'var(--surface3)', color: 'var(--text-dim)', border: '1px solid var(--border)', borderRadius: 6, padding: '3px 8px', fontSize: 10.5 }}>
            🌐 {raw.language}
          </span>
        )}
      </div>

      {/* AI text probability bar */}
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
          <span style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>AI Text Probability</span>
          <span style={{ fontFamily: 'Geist Mono, monospace', fontSize: 13, fontWeight: 700, color: vm.color }}>{aiPct}%</span>
        </div>
        <div style={{ background: 'var(--surface3)', borderRadius: 5, height: 8, overflow: 'hidden' }}>
          <div style={{ height: '100%', borderRadius: 5, width: `${aiPct}%`, background: vm.color, transition: 'width 0.8s ease' }} />
        </div>
      </div>

      {/* Extracted text */}
      {raw.best_text && raw.best_text !== '[No text detected]' && (
        <div style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)', marginBottom: 6 }}>Extracted Text</div>
          <div style={{ padding: '8px 10px', background: 'var(--surface3)', border: '1px solid var(--border)', borderRadius: 7, fontSize: 11.5, color: 'var(--text-muted)', fontFamily: 'Geist Mono, monospace', whiteSpace: 'pre-wrap', maxHeight: 100, overflowY: 'auto' }}>
            {raw.best_text.slice(0, 400)}{raw.best_text.length > 400 ? '…' : ''}
          </div>
        </div>
      )}

      {/* Message */}
      {raw.message && (
        <div style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)', marginBottom: 5 }}>Message / Intent</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', fontStyle: 'italic' }}>{raw.message}</div>
        </div>
      )}

      {/* AI tells */}
      {raw.ai_tells?.length > 0 && (
        <div>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-dim)', marginBottom: 6 }}>AI Generation Tells</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {raw.ai_tells.map((tell, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 7, padding: '5px 9px', background: 'var(--red-bg)', border: '1px solid var(--red-border)', borderRadius: 6 }}>
                <span style={{ color: 'var(--red)', fontSize: 11, flexShrink: 0 }}>⚠</span>
                <span style={{ fontSize: 11.5, color: 'var(--red)' }}>{String(tell)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main AgentCard ─────────────────────────────────────────────────────────

export default function AgentCard({ agent }) {
  const [open, setOpen] = useState(true);
  const chipCls = SCORE_MAP[agent.score] || 'warn';
  const barPct  = BAR_PCT[agent.score] || 48;

  const isOcr          = agent.real && agent.name === 'OCR + Claim Checker';
  const isReverse      = agent.real && agent.name === 'Reverse Image Search';
  const isForensics    = agent.real && agent.name === 'Image Forensics';
  const isBotDetect    = agent.real && agent.name === 'Bot Pattern Detector';
  const isCaptionAlign = agent.real && agent.name === 'Caption–Image Alignment';
  const isCredibility  = agent.real && agent.name === 'Source Credibility';
  const isLinkScanner  = agent.real && agent.name === 'Link Scanner';
  const isTextContent  = agent.real && agent.name === 'Text Content Analyzer';

  return (
    <div className={`debate-agent-card ${agent.team}`}>
      {/* Header — click to collapse/expand */}
      <div className={`dac-header ${agent.team}`} onClick={() => setOpen(!open)}>
        <div className={`dac-icon-wrap ${agent.team}`}>
          <span style={{ fontSize: 20 }}>{agent.icon}</span>
        </div>
        <div className="dac-meta">
          <div className={`dac-name ${agent.team}`}>{agent.name}</div>
          <div className="dac-model">{agent.model}</div>
        </div>
        {agent.real && <span className="real-badge">LIVE</span>}
        <span className={`dac-verdict-chip ${chipCls}`}>{SCORE_LABEL[agent.score]}</span>
        <svg
          className={`dac-chevron${open ? ' open' : ''}`}
          width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </div>

      {open && (
        <div className="dac-body">
          {/* Finding section */}
          <div className="dac-section">
            <div className="dac-section-icon">🔍</div>
            <div className="dac-section-content">
              <div className="dac-section-label">Finding</div>
              <div className="dac-section-text">{agent.finding}</div>
            </div>
          </div>

          {/* Rich structured details for real agents */}
          {isForensics    && <AiForensicsDetails       raw={agent.raw} />}
          {isOcr          && <OcrDetails               raw={agent.raw} />}
          {isReverse      && <ReverseImageDetails       raw={agent.raw} />}
          {isBotDetect    && <BotDetectionDetails       raw={agent.raw} />}
          {isCaptionAlign && <CaptionAlignmentDetails   raw={agent.raw} />}
          {isCredibility  && <SourceCredibilityDetails  raw={agent.raw} />}
          {isLinkScanner  && <LinkScannerDetails        raw={agent.raw} />}
          {isTextContent  && <TextContentDetails        raw={agent.raw} />}

          {/* Reasoning section */}
          <div className="dac-section">
            <div className="dac-section-icon">💬</div>
            <div className="dac-section-content">
              <div className="dac-section-label">Reasoning</div>
              <div className="dac-section-text">{agent.reasoning}</div>
            </div>
          </div>

          {/* Confidence bar for mock agents */}
          {!agent.real && (
            <div className="dac-section">
              <div className="dac-section-icon">📊</div>
              <div className="dac-section-content">
                <div className="dac-section-label">Confidence</div>
                <div className="dac-confidence-row" style={{ marginTop: 6, marginBottom: 0 }}>
                  <span className="dac-confidence-label">Signal strength</span>
                  <div className="dac-bar-bg">
                    <div className={`dac-bar-fill ${chipCls}`} style={{ width: `${barPct}%` }} />
                  </div>
                  <span className="dac-bar-val">{barPct}%</span>
                </div>
              </div>
            </div>
          )}

          {/* Axis tag */}
          {agent.axis && (
            <div style={{ marginTop: 10 }}>
              <span className={`dac-axis-tag ${agent.axis}`}>{AXIS_LABEL[agent.axis]}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

