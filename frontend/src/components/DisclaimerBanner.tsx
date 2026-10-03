export default function DisclaimerBanner({ compact = false }: { compact?: boolean }) {
  return (
    <div
      className={`bg-amber-50 border border-amber-300 text-amber-900 rounded-md ${
        compact ? 'text-xs px-3 py-2' : 'text-sm px-4 py-3'
      }`}
    >
      <strong>AI-generated segmentation — requires expert review.</strong>{' '}
      This is a research / decision-support tool. It does not diagnose stroke, determine
      treatment, or replace a qualified radiologist.
    </div>
  );
}
