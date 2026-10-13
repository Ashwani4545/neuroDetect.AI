import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import DisclaimerBanner from '../components/DisclaimerBanner';
import { api } from '../services/api';
import type { ModelStatus } from '../types';

export default function Landing() {
  const [status, setStatus] = useState<ModelStatus | null>(null);
  useEffect(() => { api.modelStatus().then(setStatus).catch(() => setStatus(null)); }, []);

  return (
    <div>
      {/* HERO */}
      <div className="max-w-[1200px] mx-auto px-12 pt-20 pb-16 flex gap-16 items-center flex-wrap">
        <div className="flex-[1.1] min-w-[320px]">
          <div className="eyebrow mb-4">Research &amp; Decision-Support Prototype</div>
          <h1 className="font-serif font-semibold text-[42px] leading-[1.18] mb-5 text-clinical-primary">
            Segmenting hypodense regions from brain NCCT
          </h1>
          <p className="text-base leading-relaxed text-clinical-textMuted mb-8 max-w-[460px]">
            Upload a brain non-contrast CT image and get an AI-estimated segmentation, quantitative
            measurements, and a visual explanation — without claiming to diagnose stroke or replace a radiologist.
          </p>
          <div className="flex gap-3.5">
            <Link to="/upload" className="btn-primary">Analyze a Brain Scan</Link>
            <a href="#how-it-works" className="btn-secondary">How It Works</a>
          </div>
        </div>

        <div className="flex-1 flex justify-center min-w-[280px]">
          <div className="relative w-[340px] h-[340px]">
            <svg width="340" height="340" viewBox="0 0 360 360">
              <defs>
                <radialGradient id="scanHero" cx="50%" cy="46%" r="60%">
                  <stop offset="0%" stopColor="#3A4650" />
                  <stop offset="70%" stopColor="#1E2630" />
                  <stop offset="100%" stopColor="#141A21" />
                </radialGradient>
              </defs>
              <circle cx="180" cy="180" r="164" fill="url(#scanHero)" />
              <circle cx="180" cy="180" r="164" fill="none" stroke="#3A4650" strokeWidth="1" />
              <circle cx="180" cy="180" r="120" fill="none" stroke="#2C3540" strokeWidth="1" />
              <circle cx="180" cy="180" r="76" fill="none" stroke="#2C3540" strokeWidth="1" />
              <path d="M140 150 C 120 165, 118 200, 142 218 C 162 233, 196 228, 206 206 C 216 184, 202 158, 178 150 C 164 145, 150 143, 140 150 Z" fill="#C0392B" opacity="0.55" />
              <path d="M140 150 C 120 165, 118 200, 142 218 C 162 233, 196 228, 206 206 C 216 184, 202 158, 178 150 C 164 145, 150 143, 140 150 Z" fill="none" stroke="#E9847A" strokeWidth="1.5" opacity="0.85" />
            </svg>
            <div className="absolute bottom-2.5 left-1/2 -translate-x-1/2 bg-white border border-clinical-border rounded-full px-3.5 py-1.5 text-[11.5px] text-clinical-textMuted whitespace-nowrap shadow-sm">
              AI-estimated · not a clinical diagnosis
            </div>
          </div>
        </div>
      </div>

      {/* HOW IT WORKS */}
      <div id="how-it-works" className="max-w-[1200px] mx-auto px-12 pb-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { n: 1, title: 'Upload', text: 'Upload a brain NCCT image — JPG, PNG, or DICOM. Files are validated for type, size, and content before processing.' },
            { n: 2, title: 'Analyze', text: 'The image is preprocessed — HU windowing for DICOM, contrast normalization for JPG/PNG — then segmented.' },
            { n: 3, title: 'Review', text: 'View the segmentation overlay, adjust opacity, compare views, and export a structured report.' },
          ].map((s) => (
            <div key={s.n} className="clinical-card p-7">
              <div className="w-[30px] h-[30px] rounded-full bg-clinical-primary text-clinical-bg text-[13px] font-semibold flex items-center justify-center mb-4">{s.n}</div>
              <h3 className="font-serif text-lg font-semibold mb-2 text-clinical-primary">{s.title}</h3>
              <p className="text-sm leading-relaxed text-clinical-textMuted">{s.text}</p>
            </div>
          ))}
        </div>
      </div>

      {/* MODEL STATUS STRIP — live */}
      <div className="max-w-[1200px] mx-auto px-12 mb-16">
        <div className="clinical-card px-6 py-4 flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <span className={`w-[9px] h-[9px] rounded-full inline-block ${status?.checkpoint_loaded ? 'bg-clinical-accent' : 'bg-clinical-warn'}`} />
            <span className="text-[13.5px] text-clinical-textMuted">
              {status ? `Model status: ${status.message}` : 'Checking model status…'}
            </span>
          </div>
          <Link to="/model" className="text-[13px] text-clinical-primary underline">View Model Info →</Link>
        </div>
      </div>

      <div className="max-w-[1200px] mx-auto px-12 pb-16">
        <DisclaimerBanner />
      </div>
    </div>
  );
}
