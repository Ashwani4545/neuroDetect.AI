import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import type { AnalysisSummary } from '../types';

export default function History() {
  const [results, setResults] = useState<AnalysisSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const pageSize = 10;

  const load = () => {
    setLoading(true);
    api.history({ page, pageSize, search: search || undefined, status: statusFilter || undefined })
      .then((r) => { setResults(r.results); setTotal(r.total); })
      .finally(() => setLoading(false));
  };

  useEffect(load, [page, statusFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  const onSearchSubmit = (e: React.FormEvent) => { e.preventDefault(); setPage(1); load(); };

  const doDelete = async (id: string) => {
    await api.deleteAnalysis(id);
    setConfirmDeleteId(null);
    load();
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-xl font-semibold mb-4">Analysis History</h1>

      <form onSubmit={onSearchSubmit} className="flex flex-wrap gap-2 mb-4">
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by filename…" className="border border-clinical-border rounded-md px-3 py-1.5 text-sm flex-1 min-w-[200px]" />
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} className="border border-clinical-border rounded-md px-3 py-1.5 text-sm">
          <option value="">All statuses</option>
          <option value="completed">Completed</option>
          <option value="processing">Processing</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
        </select>
        <button type="submit" className="btn-secondary">Search</button>
      </form>

      {loading ? (
        <p className="text-clinical-textMuted text-sm">Loading…</p>
      ) : results.length === 0 ? (
        <p className="text-clinical-textMuted text-sm">No analyses found. <Link to="/upload" className="text-clinical-primary underline">Upload one</Link>.</p>
      ) : (
        <div className="clinical-card overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-clinical-textMuted border-b border-clinical-border">
              <tr><th className="px-4 py-2">Filename</th><th className="px-4 py-2">Date</th><th className="px-4 py-2">Status</th><th className="px-4 py-2">Detected</th><th className="px-4 py-2">Confidence</th><th className="px-4 py-2"></th></tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.id} className="border-b border-gray-100 last:border-0">
                  <td className="px-4 py-2"><Link to={`/analysis/${r.id}`} className="text-clinical-primary hover:underline">{r.original_filename}</Link></td>
                  <td className="px-4 py-2">{new Date(r.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-2 capitalize">{r.status}</td>
                  <td className="px-4 py-2">{r.detected === null ? '—' : r.detected ? 'Yes' : 'No'}</td>
                  <td className="px-4 py-2">{r.confidence ?? '—'}</td>
                  <td className="px-4 py-2 text-right">
                    {confirmDeleteId === r.id ? (
                      <span className="flex gap-2 justify-end">
                        <button onClick={() => doDelete(r.id)} className="text-red-600 text-xs font-medium">Confirm</button>
                        <button onClick={() => setConfirmDeleteId(null)} className="text-clinical-textMuted text-xs">Cancel</button>
                      </span>
                    ) : (
                      <button onClick={() => setConfirmDeleteId(r.id)} className="text-xs text-clinical-textMuted hover:text-red-600">Delete</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 mt-4 text-sm">
          <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="btn-secondary disabled:opacity-40">Prev</button>
          <span>Page {page} of {totalPages}</span>
          <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)} className="btn-secondary disabled:opacity-40">Next</button>
        </div>
      )}
    </div>
  );
}
