"use client";
import { useEffect, useState } from 'react';

interface Toast { id: number; type: 'success' | 'error'; message: string; }

export function ToastViewport() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail as { type?: string; message?: string };
      if (!detail?.message) return;
  setToasts(t => [...t, { id: Date.now() + Math.random(), type: (detail.type === 'error' ? 'error' : 'success'), message: detail.message || '' }]);
      setTimeout(() => {
        setToasts(t => t.slice(1));
      }, 3500);
    };
    window.addEventListener('toast', handler as EventListener);
    return () => window.removeEventListener('toast', handler as EventListener);
  }, []);
  if (!toasts.length) return null;
  return (
    <div className="fixed top-4 right-4 space-y-2 z-50">
      {toasts.map(t => (
        <div key={t.id} className={`px-4 py-2 rounded shadow text-sm text-white ${t.type === 'error' ? 'bg-red-600' : 'bg-green-600'}`}>
          {t.message}
        </div>
      ))}
    </div>
  );
}
