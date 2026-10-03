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
    <div className="max-w-2xl mx-auto px-4 py-10">
      <h1 className="text-xl font-semibold mb-1">Upload a Brain NCCT Image</h1>
      <p className="text-sm text-clinical-textMuted mb-6">Accepted formats: JPG, PNG, DICOM (.dcm). Max {MAX_MB} MB.</p>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`clinical-card p-10 text-center cursor-pointer transition-colors ${dragOver ? 'border-clinical-primary bg-blue-50' : ''}`}
      >
        {!file && (<><p className="text-clinical-textMuted mb-1">Drag & drop a file here, or click to browse</p><p className="text-xs text-gray-400">JPG · PNG · DICOM</p></>)}
        {file && previewUrl && <img src={previewUrl} alt="preview" className="max-h-56 mx-auto rounded-md" />}
        {file && !previewUrl && <p className="text-clinical-textMuted">DICOM file selected: {file.name} (no browser preview)</p>}
        <input ref={inputRef} type="file" accept={ALLOWED.join(',')} className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
      </div>

      {error && <p className="text-sm text-red-600 mt-3 bg-red-50 border border-red-200 rounded-md px-3 py-2">{error}</p>}

      {file && (
        <div className="flex items-center justify-between mt-4">
          <button onClick={clearFile} className="btn-secondary" disabled={uploading}>Remove</button>
          <button onClick={startAnalysis} className="btn-primary" disabled={uploading}>{uploading ? 'Processing…' : 'Run Analysis'}</button>
        </div>
      )}

      <div className="mt-8"><DisclaimerBanner compact /></div>
    </div>
  );
}
