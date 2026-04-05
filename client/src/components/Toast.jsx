import { useEffect, useRef } from 'react';

let _addToast = null;

export function toast(msg) {
  _addToast?.(msg);
}

export default function ToastContainer() {
  const containerRef = useRef(null);

  useEffect(() => {
    _addToast = (msg) => {
      if (!containerRef.current) return;
      const el = document.createElement('div');
      el.className = 'toast';
      el.textContent = msg;
      containerRef.current.appendChild(el);
      setTimeout(() => el.remove(), 3200);
    };
    return () => { _addToast = null; };
  }, []);

  return <div className="toast-container" ref={containerRef} />;
}
