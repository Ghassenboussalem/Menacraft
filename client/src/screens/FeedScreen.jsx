import { useStore } from '../store/useStore.js';
import { connectSupabase } from '../lib/api.js';
import { toast } from '../components/Toast.jsx';

function fmtN(n) {
  const x = parseInt(n);
  if (isNaN(x)) return '—';
  return x >= 1000 ? (x / 1000).toFixed(1) + 'k' : String(x);
}

const VERDICT_LABELS = { verified: 'Verified', suspicious: 'Suspicious', fake: 'Fake', pending: 'Analyzing…', unanalyzed: 'Not analyzed' };

export default function FeedScreen() {
  const {
    posts, verdicts, dbStatus, dbLabel, activeFilter,
    setFilter, setSelectedPost, openConfig, setPosts, setDbLoading, setDbError,
  } = useStore();

  const filtered = useStore((s) => s.getFilteredPosts());
  const stats = useStore((s) => s.getStats());

  async function handleRefresh() {
    if (posts.length === 0) { openConfig(); return; }
    toast('Demo mode — connect Supabase to refresh live data');
  }

  return (
    <div className="feed-panel">
      <div className="page-header">
        <div>
          <div className="page-title">Instagram Feed</div>
          <div className="page-subtitle">Chrome extension → Supabase → AI verification pipeline</div>
        </div>
        <button className="icon-btn" onClick={handleRefresh}>
          <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
          Refresh
        </button>
      </div>

      <div className="axis-row">
        <div className="axis-badge auth"><div className="axis-dot" /> Content Authenticity</div>
        <div className="axis-badge context"><div className="axis-dot" /> Contextual Consistency</div>
        <div className="axis-badge source"><div className="axis-dot" /> Source Credibility</div>
      </div>

      <div className="db-status">
        <div className={`db-dot${dbStatus === 'connected' ? ' connected' : dbStatus === 'loading' ? ' loading' : ''}`} />
        <span>{dbLabel}</span>
      </div>

      <div className="status-bar">
        <div className="stat-chip">
          <div className="stat-chip-label">Total</div>
          <div className="stat-chip-value">{stats.total || '—'}</div>
        </div>
        <div className="stat-chip">
          <div className="stat-chip-label">Verified</div>
          <div className="stat-chip-value green">{stats.verified || '—'}</div>
        </div>
        <div className="stat-chip">
          <div className="stat-chip-label">Suspicious</div>
          <div className="stat-chip-value yellow">{stats.suspicious || '—'}</div>
        </div>
        <div className="stat-chip">
          <div className="stat-chip-label">Fake</div>
          <div className="stat-chip-value red">{stats.fake || '—'}</div>
        </div>
      </div>

      <div className="filters">
        {['all', 'verified', 'suspicious', 'fake', 'unanalyzed'].map((f) => (
          <button
            key={f}
            className={`filter-btn${activeFilter === f ? ' active' : ''}`}
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? 'All' : f === 'verified' ? '✓ Verified' : f === 'suspicious' ? '⚠ Suspicious' : f === 'fake' ? '✗ Fake' : '· Unanalyzed'}
          </button>
        ))}
      </div>

      <div className="posts-grid">
        {filtered.length === 0 ? (
          posts.length === 0 ? (
            <div className="empty-feed">
              <div className="empty-feed-icon">🔗</div>
              <div className="empty-feed-title">No posts loaded</div>
              <div className="empty-feed-desc">Connect Supabase or load demo data to see posts scraped by the Chrome extension.</div>
            </div>
          ) : (
            <div className="empty-feed">
              <div className="empty-feed-icon">🔎</div>
              <div className="empty-feed-title">No posts match</div>
              <div className="empty-feed-desc">Try a different filter or analyze some posts.</div>
            </div>
          )
        ) : (
          filtered.map((p) => {
            const v = verdicts[p.id];
            const verdict = v?.verdict || 'unanalyzed';
            const date = p.post_date
              ? new Date(p.post_date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
              : p.post_date_raw || '—';
            return (
              <div
                key={p.id}
                className={`post-card`}
                onClick={() => setSelectedPost(p)}
              >
                <div className="post-card-inner">
                  {p.image_url ? (
                    <>
                      <img
                        className="post-thumb" src={p.image_url} alt=""
                        onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
                      />
                      <div className="post-thumb-placeholder" style={{ display: 'none' }}>📷</div>
                    </>
                  ) : (
                    <div className="post-thumb-placeholder">📷</div>
                  )}
                  <div className="post-body">
                    <div className="post-meta">
                      <span className="post-username">@{p.username}</span>
                      <span className="type-chip">{p.post_type || 'image'}</span>
                      <span className="post-time">{date}</span>
                    </div>
                    <div className="post-caption">{p.caption || '—'}</div>
                    <div className="post-stats">
                      <span>♥ {fmtN(p.likes_count)}</span>
                      <span>💬 {fmtN(p.comments_count)}</span>
                      {p.hashtags?.length > 0 && <span># {p.hashtags.length}</span>}
                    </div>
                  </div>
                </div>
                <div className={`verdict-badge ${verdict}`}>
                  {VERDICT_LABELS[verdict] || verdict}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
