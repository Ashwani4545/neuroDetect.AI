import { FormEvent, useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { API_BASE, useAuth } from '../auth/AuthContext';
import type { User } from '../types';

const providers = [['google', 'Google'], ['linkedin', 'LinkedIn'], ['facebook', 'Facebook'], ['instagram', 'Instagram']];

export default function Auth({ mode }: { mode: 'signin' | 'signup' }) {
  const [name, setName] = useState(''); const [email, setEmail] = useState('');
  const [password, setPassword] = useState(''); const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { signIn } = useAuth(); const navigate = useNavigate(); const location = useLocation();

  useEffect(() => {
    const token = new URLSearchParams(location.search).get('token');
    if (!token) return;
    fetch(`${API_BASE}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => response.ok ? response.json() as Promise<User> : Promise.reject())
      .then((profile) => { signIn(token, profile); navigate('/upload', { replace: true }); })
      .catch(() => setError('Social sign-in could not be completed. Please try again.'));
  }, [location.search, navigate, signIn]);

  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError(null); setSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/auth/${mode}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: mode === 'signup' ? name : undefined, email, password }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || 'Unable to authenticate.');
      signIn(body.token, body.user); navigate('/upload', { replace: true });
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to authenticate.'); }
    finally { setSubmitting(false); }
  };

  return <div className="max-w-md mx-auto px-4 py-16"><div className="clinical-card p-8">
    <div className="eyebrow mb-3">Secure research workspace</div>
    <h1 className="font-serif text-3xl font-semibold text-clinical-primary mb-2">{mode === 'signin' ? 'Welcome back' : 'Create your account'}</h1>
    <p className="text-sm text-clinical-textMuted mb-6">{mode === 'signin' ? 'Sign in to access your analyses.' : 'Your scans and reports are kept private to your account.'}</p>
    {error && <div className="mb-4 rounded border border-clinical-danger bg-red-50 p-3 text-sm text-clinical-danger">{error}</div>}
    <form onSubmit={submit} className="space-y-4">
      {mode === 'signup' && <label className="block text-sm">Full name<input required value={name} onChange={(e) => setName(e.target.value)} className="mt-1 w-full rounded border p-2.5" /></label>}
      <label className="block text-sm">Email<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1 w-full rounded border p-2.5" /></label>
      <label className="block text-sm">Password<input required minLength={8} type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1 w-full rounded border p-2.5" /></label>
      <button disabled={submitting} className="btn-primary w-full">{submitting ? 'Please wait…' : mode === 'signin' ? 'Sign in' : 'Create account'}</button>
    </form>
    <div className="my-6 flex items-center gap-3 text-xs text-clinical-textMuted"><span className="h-px flex-1 bg-clinical-border" />or continue with<span className="h-px flex-1 bg-clinical-border" /></div>
    <div className="grid grid-cols-2 gap-2">{providers.map(([id, label]) => <a key={id} href={`${API_BASE}/auth/${id}`} className="btn-secondary text-center text-xs">{label}</a>)}</div>
    <p className="mt-6 text-center text-sm text-clinical-textMuted">{mode === 'signin' ? "Don't have an account? " : 'Already have an account? '}<Link className="text-clinical-primary underline" to={mode === 'signin' ? '/signup' : '/signin'}>{mode === 'signin' ? 'Sign up' : 'Sign in'}</Link></p>
  </div></div>;
}
