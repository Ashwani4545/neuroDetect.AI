import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { HealthStatus } from '../types';

const THEME_KEY = 'neurodetect_theme';
const OPACITY_KEY = 'neurodetect_default_opacity';

export default function Settings() {
  const [theme, setTheme] = useState<'light' | 'dark'>((localStorage.getItem(THEME_KEY) as 'light' | 'dark') || 'light');
  const [defaultOpacity, setDefaultOpacity] = useState<number>(parseFloat(localStorage.getItem(OPACITY_KEY) || '0.45'));
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    document.documentElement.classList.toggle('dark-theme', theme === 'dark');
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  useEffect(() => { localStorage.setItem(OPACITY_KEY, String(defaultOpacity)); }, [defaultOpacity]);
  useEffect(() => { api.health().then(setHealth).catch(() => setHealth(null)); }, []);

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-xl font-semibold mb-6">Settings</h1>

      <div className="clinical-card p-5 mb-4">
        <h3 className="font-semibold mb-3">Appearance</h3>
        <div className="flex gap-2">
          <button onClick={() => setTheme('light')} className={theme === 'light' ? 'btn-primary' : 'btn-secondary'}>Light</button>
          <button onClick={() => setTheme('dark')} className={theme === 'dark' ? 'btn-primary' : 'btn-secondary'}>Dark</button>
        </div>
        <p className="text-xs text-clinical-textMuted mt-2">Applies a minimal dark background across the app. Saved to this browser.</p>
      </div>

      <div className="clinical-card p-5 mb-4">
        <h3 className="font-semibold mb-3">Visualization Defaults</h3>
        <label className="text-sm text-clinical-textMuted block mb-2">Default overlay opacity for new analyses: {Math.round(defaultOpacity * 100)}%</label>
        <input type="range" min={0} max={1} step={0.05} value={defaultOpacity} onChange={(e) => setDefaultOpacity(parseFloat(e.target.value))} className="w-56" />
      </div>

      <div className="clinical-card p-5 mb-4">
        <h3 className="font-semibold mb-2">Data Retention</h3>
        <p className="text-sm text-clinical-textMuted">
          Analyses are kept until you delete them from the History page. Automatic time-based purging is configured
          server-side (currently a documented default, not yet an enforced scheduled job) — see <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">backend/README.md</code> if you want to add one.
        </p>
      </div>

      <div className="clinical-card p-5">
        <h3 className="font-semibold mb-2">Application Status</h3>
        <p className="text-sm text-clinical-textMuted">
          Backend: {health ? <span className="text-emerald-700 font-medium">{health.status} (DB: {health.database})</span> : <span className="text-red-600">unreachable</span>}
        </p>
      </div>
    </div>
  );
}
