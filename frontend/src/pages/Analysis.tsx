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

  if (loading) return <div className="max-w-[1240px] mx-auto px-10 py-10 text-clinical-textMuted">Loading analysis…</div>;
  if (error) return <div className="max-w-[1240px] mx-auto px-10 py-10 text-clinical-danger">{error}</div>;
  if (!analysis || !id) return null;

  const isDicom = analysis.original_filename.toLowerCase().endsWith('.dcm');
  const m = analysis.measurements;

  return (
    <div className="max-w-[1240px] mx-auto px-10 py-9">
      <div className="flex items-start justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="font-serif font-semibold text-[22px] text-clinical-primary mb-1.5">{analysis.original_filename}</h1>
          <div className="text-xs text-clinical-textFaint font-mono">
            {analysis.id.slice(0, 8)} · {new Date(analysis.created_at).toLocaleString()} ·{' '}
            <span className="font-sans"><StatusPill status={analysis.status} /></span>
          </div>
        </div>
        <div className="flex gap-2.5">
          <a href={api.exportUrl(id, 'json')} className="btn-secondary" download>Export JSON</a>
          <a href={api.exportUrl(id, 'pdf')} className="btn-secondary" download>Export PDF</a>
        </div>
      </div>

      {analysis.status === 'failed' && (
        <div className="bg-red-50 border border-red-200 text-clinical-danger text-sm rounded-md px-4 py-3 mb-5">
          Analysis failed: {analysis.error_message}
        </div>
      )}

      {analysis.status === 'completed' && (
        <>
          <div className="mb-5">
            <MedicalImageViewer
              originalUrl={isDicom ? null : api.originalUrl(id)}
              maskUrl={api.maskUrl(id)}
              isDicom={isDicom}
              imageDimensions={m?.image_dimensions}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-5">
            <div className="clinical-card p-6">
              <h3 className="font-semibold text-sm mb-4 text-clinical-primary">Finding Summary</h3>
              <dl className="text-[13.5px] space-y-2.5">
                <Row label="Detected" value={analysis.detected ? 'Yes — hypodense region flagged' : 'No significant region flagged'} danger={!!analysis.detected} />
                <Row label="Confidence" value={analysis.confidence ?? 'N/A'} />
                <Row label="Model used" value={analysis.model_used ?? 'N/A'} />
                <Row label="Processing time" value={analysis.processing_time_ms ? `${analysis.processing_time_ms} ms` : 'N/A'} />
              </dl>
            </div>

            <div className="clinical-card p-6">
              <h3 className="font-semibold text-sm mb-4 text-clinical-primary">Quantitative Measurements</h3>
              {m?.available ? (
                <dl className="text-[13.5px] space-y-2.5 font-mono">
                  <Row label="Image dimensions" value={`${m.image_dimensions?.width} × ${m.image_dimensions?.height} px`} mono />
                  <Row label="Foreground pixels" value={String(m.total_foreground_pixels)} mono />
                  <Row label="Foreground %" value={`${m.foreground_percentage}%`} mono />
                  <Row label="Region count" value={String(m.region_count)} mono />
                  {m.region_size_distribution && (
                    <Row label="Region size (min/median/max px)" value={`${m.region_size_distribution.min_px ?? '—'} / ${m.region_size_distribution.median_px ?? '—'} / ${m.region_size_distribution.max_px ?? '—'}`} mono />
                  )}
                </dl>
              ) : (
                <p className="text-sm text-clinical-textMuted">Not available.</p>
              )}
            </div>
          </div>

          {m?.available && m.regions && m.regions.length > 0 && (
            <div className="clinical-card p-6 mb-5 overflow-x-auto">
              <h3 className="font-semibold text-sm mb-4 text-clinical-primary">Detected Regions</h3>
              <table className="text-[13px] w-full">
                <thead className="text-left text-clinical-textFaint border-b border-clinical-border">
                  <tr>
                    <th className="py-1.5 pr-4 font-medium">#</th>
                    <th className="py-1.5 pr-4 font-medium">Area (px)</th>
                    <th className="py-1.5 pr-4 font-medium">Bounding Box (x, y, w, h)</th>
                    <th className="py-1.5 pr-4 font-medium">Centroid</th>
                  </tr>
                </thead>
                <tbody className="font-mono">
                  {m.regions.map((r) => (
                    <tr key={r.region_id} className="border-b border-clinical-borderLight last:border-0">
                      <td className="py-2.5 pr-4">{r.region_id}</td>
                      <td className="py-2.5 pr-4">{r.area_px}</td>
                      <td className="py-2.5 pr-4">{r.bounding_box.x}, {r.bounding_box.y}, {r.bounding_box.width}, {r.bounding_box.height}</td>
                      <td className="py-2.5 pr-4">({r.centroid.x}, {r.centroid.y})</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {m.physical_units_note && (
                <p className="text-[11.5px] text-clinical-textFaint mt-3.5 font-sans">{m.physical_units_note}</p>
              )}
            </div>
          )}
        </>
      )}

      <DisclaimerBanner />
      <p className="text-xs text-clinical-textFaint mt-4">
        <Link to="/history" className="underline">View analysis history</Link>
      </p>
    </div>
  );
}

function Row({ label, value, mono, danger }: { label: string; value: string; mono?: boolean; danger?: boolean }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className={`text-clinical-textFaint ${mono ? 'font-sans' : ''}`}>{label}</dt>
      <dd className={`font-medium text-right ${danger ? 'text-clinical-danger' : 'text-clinical-text'}`}>{value}</dd>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: 'text-clinical-accent',
    failed: 'text-clinical-danger',
    processing: 'text-clinical-warn',
    pending: 'text-clinical-textFaint',
  };
  return <span className={`font-medium ${colors[status] || ''}`}>● {status}</span>;
}
