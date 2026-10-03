import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api, ApiClientError } from '../services/api';
import type { AnalysisDetail } from '../types';
import MedicalImageViewer from '../components/MedicalImageViewer';
import DisclaimerBanner from '../components/DisclaimerBanner';

export default function Analysis() {
  const { id } = useParams<{ id: string }>();
  const [analysis, setAnalysis] = useState<AnalysisDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    api.getAnalysis(id)
      .then(setAnalysis)
      .catch((e) => setError(e instanceof ApiClientError ? e.message : 'Failed to load analysis.'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="max-w-5xl mx-auto px-4 py-10 text-clinical-textMuted">Loading analysis…</div>;
  if (error) return <div className="max-w-5xl mx-auto px-4 py-10 text-red-600">{error}</div>;
  if (!analysis || !id) return null;

  const isDicom = analysis.original_filename.toLowerCase().endsWith('.dcm');
  const m = analysis.measurements;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <h1 className="text-xl font-semibold">{analysis.original_filename}</h1>
          <p className="text-xs text-clinical-textMuted">
            Analysis ID: {analysis.id} · {new Date(analysis.created_at).toLocaleString()} · Status: <StatusPill status={analysis.status} />
          </p>
        </div>
        <div className="flex gap-2">
          <a href={api.exportUrl(id, 'json')} className="btn-secondary" download>Export JSON</a>
          <a href={api.exportUrl(id, 'pdf')} className="btn-secondary" download>Export PDF</a>
        </div>
      </div>

      {analysis.status === 'failed' && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-md px-4 py-3 mb-4">
          Analysis failed: {analysis.error_message}
        </div>
      )}

      {analysis.status === 'completed' && (
        <>
          <div className="mb-4">
            <MedicalImageViewer
              originalUrl={isDicom ? null : api.originalUrl(id)}
              maskUrl={api.maskUrl(id)}
              isDicom={isDicom}
              imageDimensions={m?.image_dimensions}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="clinical-card p-5">
              <h3 className="font-semibold mb-3">Finding Summary</h3>
              <dl className="text-sm space-y-2">
                <Row label="Detected" value={analysis.detected ? 'Yes — hypodense region flagged' : 'No significant region flagged'} />
                <Row label="Confidence / lesion load" value={analysis.confidence ?? 'N/A'} />
                <Row label="Model used" value={analysis.model_used ?? 'N/A'} />
                <Row label="Processing time" value={analysis.processing_time_ms ? `${analysis.processing_time_ms} ms` : 'N/A'} />
              </dl>
            </div>

            <div className="clinical-card p-5">
              <h3 className="font-semibold mb-3">Quantitative Measurements</h3>
              {m?.available ? (
                <dl className="text-sm space-y-2">
                  <Row label="Image dimensions" value={`${m.image_dimensions?.width} × ${m.image_dimensions?.height} px`} />
                  <Row label="Foreground pixels" value={String(m.total_foreground_pixels)} />
                  <Row label="Foreground %" value={`${m.foreground_percentage}%`} />
                  <Row label="Region count" value={String(m.region_count)} />
                  {m.region_size_distribution && (
                    <Row label="Region size (min/median/max px)" value={`${m.region_size_distribution.min_px ?? '—'} / ${m.region_size_distribution.median_px ?? '—'} / ${m.region_size_distribution.max_px ?? '—'}`} />
                  )}
                </dl>
              ) : <p className="text-sm text-clinical-textMuted">Not available.</p>}
            </div>
          </div>

          {m?.available && m.regions && m.regions.length > 0 && (
            <div className="clinical-card p-5 mb-6 overflow-x-auto">
              <h3 className="font-semibold mb-3">Detected Regions</h3>
              <table className="text-sm w-full">
                <thead className="text-left text-clinical-textMuted border-b border-clinical-border">
                  <tr><th className="py-1.5 pr-4">#</th><th className="py-1.5 pr-4">Area (px)</th><th className="py-1.5 pr-4">Bounding Box (x, y, w, h)</th><th className="py-1.5 pr-4">Centroid</th></tr>
                </thead>
                <tbody>
                  {m.regions.map((r) => (
                    <tr key={r.region_id} className="border-b border-gray-100 last:border-0">
                      <td className="py-1.5 pr-4">{r.region_id}</td>
                      <td className="py-1.5 pr-4">{r.area_px}</td>
                      <td className="py-1.5 pr-4">{r.bounding_box.x}, {r.bounding_box.y}, {r.bounding_box.width}, {r.bounding_box.height}</td>
                      <td className="py-1.5 pr-4">({r.centroid.x}, {r.centroid.y})</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {m.physical_units_note && <p className="text-xs text-clinical-textMuted mt-3">{m.physical_units_note}</p>}
            </div>
          )}
        </>
      )}

      <DisclaimerBanner />
      <p className="text-xs text-clinical-textMuted mt-4"><Link to="/history" className="underline">View analysis history</Link></p>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (<div className="flex justify-between gap-4"><dt className="text-clinical-textMuted">{label}</dt><dd className="font-medium text-right">{value}</dd></div>);
}

function StatusPill({ status }: { status: string }) {
  const colors: Record<string, string> = { completed: 'text-emerald-700', failed: 'text-red-700', processing: 'text-amber-700', pending: 'text-gray-500' };
  return <span className={`font-medium ${colors[status] || ''}`}>{status}</span>;
}
