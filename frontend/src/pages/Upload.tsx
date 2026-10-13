import { useCallback, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, ApiClientError } from '../services/api';
import DisclaimerBanner from '../components/DisclaimerBanner';

const ALLOWED = ['.jpg', '.jpeg', '.png', '.dcm'];
const MAX_MB = 20;

export default function Upload() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const validate = (f: File): string | null => {
    const ext = '.' + (f.name.split('.').pop() || '').toLowerCase();
    if (!ALLOWED.includes(ext)) return `Unsupported file type "${ext}". Accepted: ${ALLOWED.join(', ')}`;
    if (f.size / (1024 * 1024) > MAX_MB) return `File too large (${(f.size / (1024 * 1024)).toFixed(1)} MB). Max allowed: ${MAX_MB} MB.`;
    return null;
  };

  const handleFile = (f: File) => {
    const err = validate(f);
    if (err) { setError(err); setFile(null); setPreviewUrl(null); return; }
    setError(null);
    setFile(f);
    setPreviewUrl(f.type.startsWith('image/') ? URL.createObjectURL(f) : null);
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) handleFile(f);
  }, []);

  const clearFile = () => {
    setFile(null); setPreviewUrl(null); setError(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const startAnalysis = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const uploaded = await api.uploadAnalysis(file);
      await api.predictAnalysis(uploaded.id);
      navigate(`/analysis/${uploaded.id}`);
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : 'Upload failed — please try again.');
      setUploading(false);
    }
  };

  return (
    <div className="max-w-[1000px] mx-auto px-12 py-16">
      <div className="eyebrow mb-3">Step 1 of 2</div>
      <h1 className="font-serif font-semibold text-[30px] mb-2 text-clinical-primary">Upload a Brain NCCT Image</h1>
      <p className="text-[14.5px] text-clinical-textMuted mb-10">Accepted formats: JPG, PNG, DICOM (.dcm). Max {MAX_MB} MB.</p>

      <div className="flex gap-8 items-start flex-wrap">
        {/* DROP ZONE */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={`flex-[1.4] min-w-[320px] clinical-card border-dashed border-[1.5px] p-14 text-center cursor-pointer transition-colors ${
            dragOver ? 'border-clinical-primary bg-[#FAF8F3]' : 'border-[#C9C2B2]'
          }`}
        >
          {!file && (
            <>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#9A9382" strokeWidth="1.5" className="mx-auto mb-4.5 block">
                <path d="M12 15V4M12 4l-4 4M12 4l4 4" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" strokeLinecap="round" />
              </svg>
              <p className="text-[15px] text-clinical-textMuted mb-1">Drag &amp; drop a file here, or click to browse</p>
              <p className="text-xs text-clinical-textFaint mb-5">JPG · PNG · DICOM</p>
              <span className="inline-block btn-primary">Browse Files</span>
            </>
          )}
          {file && previewUrl && <img src={previewUrl} alt="preview" className="max-h-56 mx-auto rounded-md" />}
          {file && !previewUrl && <p className="text-clinical-textMuted">DICOM file selected: {file.name} (no browser preview)</p>}
          <input
            ref={inputRef}
            type="file"
            accept={ALLOWED.join(',')}
            className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
          />
        </div>

        {/* TIPS PANEL */}
        <div className="flex-1 min-w-[260px] clinical-card p-6">
          <h3 className="text-sm font-semibold mb-4 text-clinical-primary">Before you upload</h3>
          <div className="flex flex-col gap-3.5">
            {[
              'A single axial slice works best for JPG/PNG uploads',
              'DICOM files preserve rescale slope/intercept for accurate HU windowing',
              'Low-quality or heavily cropped scans may limit analysis reliability',
            ].map((tip) => (
              <div key={tip} className="flex gap-2.5 items-start">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2F7B6B" strokeWidth="2.2" className="flex-shrink-0 mt-0.5">
                  <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <span className="text-[13px] text-clinical-textMuted leading-relaxed">{tip}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <p className="text-sm text-clinical-danger mt-4 bg-red-50 border border-red-200 rounded-md px-3 py-2">{error}</p>
      )}

      {file && (
        <div className="clinical-card mt-6 px-5 py-4 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#13293D" strokeWidth="1.6">
              <rect x="4" y="3" width="16" height="18" rx="2" />
              <path d="M8 8h8M8 12h8M8 16h5" strokeLinecap="round" />
            </svg>
            <div>
              <div className="text-[13.5px] font-medium">{file.name}</div>
              <div className="text-xs text-clinical-textFaint">{(file.size / (1024 * 1024)).toFixed(1)} MB — ready to analyze</div>
            </div>
          </div>
          <div className="flex gap-2.5">
            <button onClick={clearFile} className="btn-secondary" disabled={uploading}>Remove</button>
            <button onClick={startAnalysis} className="btn-primary" disabled={uploading}>
              {uploading ? 'Processing…' : 'Run Analysis'}
            </button>
          </div>
        </div>
      )}

      <div className="mt-7">
        <DisclaimerBanner compact />
      </div>
    </div>
  );
}
