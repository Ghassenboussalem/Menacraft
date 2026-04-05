import { useState, useEffect } from 'react';
import { useStore } from '../store/useStore.js';
import { connectSupabase, fetchPostsFromServer } from '../lib/api.js';
import { toast } from './Toast.jsx';

export default function ConfigModal() {
  const { showConfigModal, closeConfig, loadDemo, setPosts, setDbLoading, setDbError } = useStore();
  const [url, setUrl] = useState('');
  const [key, setKey] = useState('');
  const [table, setTable] = useState('instagram_posts');
  const [autoConnectTried, setAutoConnectTried] = useState(false);

  // ── Auto-connect on first mount using server .env credentials ──
  useEffect(() => {
    if (autoConnectTried) return;
    setAutoConnectTried(true);

    // Try to auto-connect using the server's .env Supabase credentials
    setDbLoading('Auto-connecting via server .env…');
    fetchPostsFromServer()
      .then((data) => {
        if (data && data.length > 0) {
          setPosts(data, `Connected · ${data.length} posts`);
          toast(`Auto-connected: ${data.length} posts loaded`);
          closeConfig();
        } else {
          // Server returned empty — fall back to manual config
          setDbError('No posts found');
        }
      })
      .catch(() => {
        // Server .env not configured or error — show config modal
        setDbError('');
        // Reset to idle to not show error state, just show the modal
        useStore.setState({ dbStatus: 'idle', dbLabel: 'Not connected', showConfigModal: true });
      });
  }, []);

  if (!showConfigModal) return null;

  async function handleConnect() {
    if (!url || !key) { toast('Fill in URL and key'); return; }
    setDbLoading('Connecting…');
    closeConfig();
    try {
      const data = await connectSupabase(url, key, table);
      setPosts(data, `Connected · ${data.length} posts`);
      toast(`${data.length} posts loaded`);
    } catch (e) {
      setDbError('Connection failed');
      toast('Could not connect — check credentials');
    }
  }

  async function handleServerConnect() {
    setDbLoading('Connecting via server config…');
    closeConfig();
    try {
      const data = await fetchPostsFromServer();
      setPosts(data, `Connected · ${data.length} posts`);
      toast(`${data.length} posts loaded`);
    } catch (e) {
      setDbError('Connection failed');
      toast('Server Supabase not configured');
    }
  }

  return (
    <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) closeConfig(); }}>
      <div className="modal">
        <div className="modal-title">Connect to Supabase</div>
        <div className="modal-sub">
          Enter your project credentials to load Instagram posts scraped by the Chrome extension.
        </div>
        <div className="modal-note">
          Your server .env is pre-configured — click "Use server .env" below, or load demo data.
        </div>

        <div className="modal-field">
          <label>Project URL</label>
          <input value={url} onChange={(e) => setUrl(e.target.value)} type="text" placeholder="https://xxxx.supabase.co" />
        </div>
        <div className="modal-field">
          <label>Anon Key</label>
          <input value={key} onChange={(e) => setKey(e.target.value)} type="password" placeholder="eyJhbGci..." />
        </div>
        <div className="modal-field">
          <label>Table Name</label>
          <input value={table} onChange={(e) => setTable(e.target.value)} type="text" />
        </div>

        <div className="modal-actions">
          <button className="modal-secondary" onClick={() => { loadDemo(); toast('Demo data loaded'); }}>
            Load demo
          </button>
          <button className="modal-primary" onClick={handleConnect}>
            Connect &amp; fetch
          </button>
        </div>

        <button
          className="modal-secondary"
          style={{ width: '100%', marginTop: 8, textAlign: 'center' }}
          onClick={handleServerConnect}
        >
          Use server .env credentials
        </button>
      </div>
    </div>
  );
}
