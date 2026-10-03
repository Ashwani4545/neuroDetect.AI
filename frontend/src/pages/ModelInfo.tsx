import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { ModelStatus } from '../types';

export default function ModelInfo() {
  const [status, setStatus] = useState<ModelStatus | null>(null);
  useEffect(() => { api.modelStatus().then(setStatus).catch(() => setStatus(null)); }, []);

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-xl font-semibold mb-4">Model Information</h1>
      {!status ? (
        <p className="text-clinical-textMuted text-sm">Loading…</p>
      ) : (
        <div className="clinical-card p-5 space-y-4">
          <Row label="Architecture" value={status.architecture} />
          <Row label="Checkpoint status" value={status.checkpoint_loaded ? 'Trained checkpoint loaded' : 'No trained checkpoint installed'} highlight={!status.checkpoint_loaded} />
          <Row label="Fallback pipeline" value={status.fallback_pipeline} />
          <Row label="Supported input formats" value="JPG, PNG, DICOM (.dcm)" />
          <Row label="Input preprocessing" value="HU windowing (WL=35/WW=100) for DICOM; CLAHE contrast normalization for JPG/PNG" />
          <Row label="Output interpretation" value="Binary segmentation mask — foreground pixels indicate the model's hypodense-region prediction, not a confirmed diagnosis" />
          <Row label="Evaluation metrics" value="Not available — no trained model has been evaluated yet" highlight />
          <div className="bg-amber-50 border border-amber-200 text-amber-900 text-sm rounded-md px-4 py-3">{status.message}</div>
          <div className="text-xs text-clinical-textMuted">
            No Dice score, IoU, sensitivity, specificity, or clinical validation claim is made here — none has been measured.
            This page reflects the backend's actual, live checkpoint status, not a static description.
          </div>
        </div>
      )}
    </div>
  );
}

function Row({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (<div><dt className="text-xs text-clinical-textMuted uppercase tracking-wide">{label}</dt><dd className={`text-sm mt-0.5 ${highlight ? 'text-amber-700 font-medium' : ''}`}>{value}</dd></div>);
}
