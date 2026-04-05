import { useEffect, useState, useRef } from 'react';
import { useStore } from '../store/useStore.js';
import { verifyPostStream, fetchVerdict, saveVerdict, deleteVerdict as apiDeleteVerdict } from '../lib/api.js';
import { toast } from './Toast.jsx';
import DebateVerdict from './DebateVerdict.jsx';
import AgentCard from './AgentCard.jsx';

function fmtN(n) {
  const x = parseInt(n);
  if (isNaN(x)) return '—';
  return x >= 1000 ? (x / 1000).toFixed(1) + 'k' : String(x);
}

// 7 agents: 3 blue + 4 red  — ALL LIVE
const AGENT_NAMES = [
  'Image Forensics (Groq + MobileViT)',    // 0 — blue
  'OCR + Claim Checker (Groq)',             // 1 — blue
  'Link Scanner (Groq)',                    // 2 — blue
  'Reverse Image (TinEye)',                 // 3 — red
  'Caption–Image Alignment (Groq Vision)',  // 4 — red
  'Bot Patterns (Serper)',                  // 5 — red
  'Source Credibility (Groq)',              // 6 — red
];
const BLUE_INDICES = [0, 1, 2];
const RED_INDICES  = [3, 4, 5, 6];
const LIVE_INDICES = [0, 1, 2, 3, 4, 5, 6]; // ALL agents are LIVE
const TOTAL_AGENTS = 7;

export default function PostModal() {
  const {
    showPostModal, selectedPost, closePostModal,
    verdicts, analyzing, setVerdict, setAnalyzing, deleteVerdict,
  } = useStore();

  const [loadingCached, setLoadingCached] = useState(false);
  const [streamingAgents, setStreamingAgents] = useState(null);
  const cancelRef = useRef(null);

  // On open: try to load persisted verdict from Supabase
  useEffect(() => {
    if (!showPostModal || !selectedPost) return;
    const p = selectedPost;
    if (verdicts[p.id]) return;

    setLoadingCached(true);
    fetchVerdict(p.id)
      .then((cached) => {
        if (cached) {
          setVerdict(p.id, cached);
          toast('Loaded cached verdict from database');
        }
      })
      .catch(() => {})
      .finally(() => setLoadingCached(false));
  }, [showPostModal, selectedPost?.id]);

  useEffect(() => {
    return () => { if (cancelRef.current) cancelRef.current(); };
  }, []);

  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') closePostModal(); }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [closePostModal]);

  if (!showPostModal || !selectedPost) return null;

  const p         = selectedPost;
  const verdict   = verdicts[p.id];
  const isAnalyzing = analyzing[p.id] || loadingCached;

  const date = p.post_date
    ? new Date(p.post_date).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })
    : p.post_date_raw || '—';

  function runVerification() {
    setAnalyzing(p.id, true);
    setStreamingAgents(new Array(TOTAL_AGENTS).fill(null));
    toast('Running 7 agents in parallel…');

    const cancel = verifyPostStream(p, {
      onAgent: (idx, agent) => {
        setStreamingAgents(prev => {
          const next = [...(prev || new Array(TOTAL_AGENTS).fill(null))];
          next[idx] = agent;
          return next;
        });
      },
      onVerdict: (result) => {
        setVerdict(p.id, result);
        setStreamingAgents(null);
        setAnalyzing(p.id, false);
        saveVerdict(p.id, result).then(ok => {
          if (ok) toast(`Pipeline complete: ${result.verdict.toUpperCase()} · ${result.confidence}/100 — auto-saved ✓`);
          else toast(`Pipeline complete: ${result.verdict.toUpperCase()} · ${result.confidence}/100`);
        }).catch(() => {
          toast(`Pipeline complete: ${result.verdict.toUpperCase()} · ${result.confidence}/100`);
        });
      },
      onError: (err) => {
        toast(`Error: ${err.message}`);
        setStreamingAgents(null);
        setAnalyzing(p.id, false);
      },
    });

    cancelRef.current = cancel;
  }

  async function reRun() {
    deleteVerdict(p.id);
    apiDeleteVerdict(p.id).catch(() => {});
    runVerification();
  }

  const resolvedCount = streamingAgents ? streamingAgents.filter(Boolean).length : 0;

  return (
    <div
      className="post-modal-overlay open"
      onClick={(e) => { if (e.target === e.currentTarget) closePostModal(); }}
    >
      <div className="post-modal">
        <div className="post-modal-header">
          <div>
            <div style={{ fontSize: 16, fontWeight: 600, letterSpacing: '-0.02em' }}>@{p.username}</div>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', fontFamily: 'Geist Mono, monospace', marginTop: 2 }}>{date}</div>
          </div>
          <button className="post-modal-close" onClick={closePostModal}>
            <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="post-modal-body">
          {/* ── LEFT: post details ── */}
          <div className="post-modal-left">
            {p.image_url ? (
              <>
                <img
                  style={{ width: '100%', borderRadius: 10, objectFit: 'cover', maxHeight: 220, display: 'block', marginBottom: 14, background: 'var(--surface3)' }}
                  src={p.image_url} alt=""
                  onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
                />
                <div style={{ width: '100%', height: 140, borderRadius: 10, background: 'var(--surface3)', display: 'none', alignItems: 'center', justifyContent: 'center', fontSize: 32, marginBottom: 14, color: 'var(--text-dim)' }}>📷</div>
              </>
            ) : (
              <div style={{ width: '100%', height: 140, borderRadius: 10, background: 'var(--surface3)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 32, marginBottom: 14, color: 'var(--text-dim)' }}>📷</div>
            )}

            <div style={{ fontSize: 12.5, color: 'var(--text-muted)', lineHeight: 1.65, marginBottom: 14, padding: '12px 14px', background: 'var(--surface2)', borderRadius: 8, border: '1px solid var(--border)' }}>
              {(p.caption || '').split('\n').map((l, i) => <span key={i}>{l}<br /></span>)}
            </div>

            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-dim)', fontWeight: 500, marginBottom: 7 }}>Engagement</div>
              <div style={{ display: 'flex', gap: 16, fontSize: 13, color: 'var(--text-muted)', fontFamily: 'Geist Mono, monospace' }}>
                <span>♥ {fmtN(p.likes_count)} likes</span>
                <span>💬 {fmtN(p.comments_count)} comments</span>
              </div>
            </div>

            {p.hashtags?.length > 0 && (
              <div style={{ marginBottom: 14 }}>
                <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-dim)', fontWeight: 500, marginBottom: 7 }}>Hashtags</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {p.hashtags.map((h, i) => (
                    <span key={i} style={{ background: 'var(--blue-bg)', border: '1px solid var(--blue-border)', borderRadius: 5, padding: '2px 7px', fontSize: 11, color: 'var(--blue)', fontFamily: 'Geist Mono, monospace' }}>{h}</span>
                  ))}
                </div>
              </div>
            )}

            {verdict && !isAnalyzing && (
              <div style={{ marginBottom: 14, display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--green)', fontFamily: 'Geist Mono, monospace' }}>
                <svg width="10" height="10" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                Verdict auto-saved to database
              </div>
            )}

            <a
              href={p.post_url} target="_blank" rel="noopener noreferrer"
              style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 13, color: 'var(--text-muted)', textDecoration: 'none', padding: '6px 11px', border: '1px solid var(--border)', borderRadius: 8 }}
            >
              <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" />
              </svg>
              View on Instagram
            </a>
          </div>

          {/* ── RIGHT: AI pipeline ── */}
          <div className="post-modal-right">
            <div className="ai-box" style={{ border: 'none', background: 'transparent', padding: 0 }}>
              <div className="ai-box-title" style={{ fontSize: 14, marginBottom: 3 }}>
                <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
                AI Verification Pipeline
              </div>
              <div className="ai-box-desc">
                Blue Team (detection forensics) + Red Team (context verification) → Synthesis Agent verdict
              </div>

              {/* ── STREAMING STATE: show agents progressively ── */}
              {streamingAgents && !verdict ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, padding: '10px 0' }}>
                  {/* Progress bar */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 8 }}>
                    <div className="loading-spinner" />
                    <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                      {resolvedCount < TOTAL_AGENTS ? `Agents running — ${resolvedCount}/${TOTAL_AGENTS} complete…` : 'Computing synthesis verdict…'}
                    </span>
                  </div>
                  <div style={{ background: 'var(--surface3)', borderRadius: 4, height: 4, overflow: 'hidden', marginBottom: 6 }}>
                    <div style={{ height: '100%', borderRadius: 4, background: 'var(--blue)', transition: 'width 0.4s ease', width: `${(resolvedCount / TOTAL_AGENTS) * 100}%` }} />
                  </div>

                  {/* Blue Team */}
                  <div className="debate-section-label">
                    <svg width="11" height="11" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                    </svg>
                    Blue Team — Detection Forensics
                  </div>
                  {BLUE_INDICES.map((idx) => (
                    streamingAgents[idx]
                      ? <AgentCard key={`stream-${idx}`} agent={streamingAgents[idx]} uid={`stream-${idx}`} />
                      : <div key={`pending-${idx}`} className="debate-agent-card blue" style={{ opacity: 0.4, padding: '10px 13px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <div className="loading-spinner" style={{ width: 12, height: 12, borderWidth: 1.5 }} />
                            <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>{AGENT_NAMES[idx]}…</span>
                            {LIVE_INDICES.includes(idx) && <span style={{ fontSize: 9, fontWeight: 700, padding: '1px 4px', borderRadius: 3, background: 'var(--blue)', color: '#fff' }}>LIVE</span>}
                          </div>
                        </div>
                  ))}

                  <div className="vs-divider"><div className="vs-pill">VS</div></div>

                  {/* Red Team */}
                  <div className="debate-section-label">
                    <svg width="11" height="11" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                    Red Team — Context Verification
                  </div>
                  {RED_INDICES.map((idx) => (
                    streamingAgents[idx]
                      ? <AgentCard key={`stream-${idx}`} agent={streamingAgents[idx]} uid={`stream-${idx}`} />
                      : <div key={`pending-${idx}`} className="debate-agent-card red" style={{ opacity: 0.4, padding: '10px 13px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <div className="loading-spinner" style={{ width: 12, height: 12, borderWidth: 1.5 }} />
                            <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>{AGENT_NAMES[idx]}…</span>
                            {LIVE_INDICES.includes(idx) && <span style={{ fontSize: 9, fontWeight: 700, padding: '1px 4px', borderRadius: 3, background: 'var(--blue)', color: '#fff' }}>LIVE</span>}
                          </div>
                        </div>
                  ))}
                </div>
              ) : isAnalyzing && !streamingAgents ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: '14px 0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 9, fontSize: 13, color: 'var(--text-muted)' }}>
                    <div className="loading-spinner" />
                    {loadingCached ? 'Loading cached verdict…' : 'Initializing pipeline…'}
                  </div>
                </div>
              ) : verdict ? (
                <DebateVerdict verdict={verdict} onReRun={reRun} />
              ) : (
                <>
                  <div className="team-explainer">
                    <div className="team-card blue">
                      <div className="team-card-title blue">
                        <svg width="11" height="11" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
                        Blue Team
                      </div>
                      <div className="team-card-desc">Image forensics (Groq + MobileViT), OCR claim checking (Groq), link safety scanning (Groq)</div>
                    </div>
                    <div className="team-card red">
                      <div className="team-card-title red">
                        <svg width="11" height="11" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
                        Red Team
                      </div>
                      <div className="team-card-desc">Reverse image search (TinEye), caption–image alignment (Groq Vision), bot detection (Serper), source credibility (Groq)</div>
                    </div>
                  </div>
                  <button className="verify-btn" onClick={runVerification}>
                    <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                    </svg>
                    Run agent pipeline
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
