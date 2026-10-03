import { Link } from 'react-router-dom';
import DisclaimerBanner from '../components/DisclaimerBanner';

export default function Landing() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-12">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-clinical-primary mb-3">
          AI-Powered Hypodense Region Segmentation from Brain NCCT
        </h1>
        <p className="text-clinical-textMuted max-w-2xl mx-auto mb-6">
          A research and decision-support prototype that analyzes brain non-contrast CT images,
          segments hypodense regions, and provides quantitative measurements and visual explanation —
          without claiming to diagnose stroke or replace a radiologist.
        </p>
        <div className="flex gap-3 justify-center">
          <Link to="/upload" className="btn-primary">Analyze a Brain Scan</Link>
          <a href="#how-it-works" className="btn-secondary">Learn How It Works</a>
        </div>
      </div>

      <div id="how-it-works" className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
        {[
          { step: '1. Upload', text: 'Upload a brain NCCT image (JPG, PNG, or DICOM). Files are validated for type, size, and content before processing.' },
          { step: '2. Analyze', text: 'The image is preprocessed (HU windowing for DICOM, contrast normalization for JPG/PNG) and segmented.' },
          { step: '3. Review', text: 'View the segmentation overlay, adjust opacity, compare views, and export a structured report.' },
        ].map((s) => (
          <div key={s.step} className="clinical-card p-5">
            <h3 className="font-semibold text-clinical-primary mb-2">{s.step}</h3>
            <p className="text-sm text-clinical-textMuted">{s.text}</p>
          </div>
        ))}
      </div>

      <div className="clinical-card p-5 mb-8">
        <h3 className="font-semibold mb-2">Model & research information</h3>
        <p className="text-sm text-clinical-textMuted">
          The segmentation pipeline prefers a trained 2.5D U-Net checkpoint when one is installed.
          Without one, it falls back to a deterministic HU-windowing / adaptive-thresholding pipeline —
          a real, explainable method, not a placeholder. Check the <Link to="/model" className="text-clinical-primary underline">Model Info page</Link> for
          the current status; no accuracy or clinical-validation claim is made without a real evaluation to back it.
        </p>
      </div>

      <DisclaimerBanner />
    </div>
  );
}
