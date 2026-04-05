import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{
          position: 'fixed', inset: 0, display: 'flex', alignItems: 'center',
          justifyContent: 'center', background: 'var(--bg)', flexDirection: 'column', gap: 12,
        }}>
          <div style={{ fontSize: 28 }}>⚠</div>
          <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text)' }}>Something went wrong</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', maxWidth: 360, textAlign: 'center', lineHeight: 1.55 }}>
            {this.state.error.message}
          </div>
          <button
            onClick={() => this.setState({ error: null })}
            style={{
              marginTop: 8, background: 'var(--text)', color: 'var(--surface)', border: 'none',
              borderRadius: 9, padding: '8px 20px', fontSize: 13, cursor: 'pointer',
              fontFamily: 'Geist, sans-serif',
            }}
          >
            Dismiss
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
