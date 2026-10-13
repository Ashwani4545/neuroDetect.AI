export default function DisclaimerBanner({ compact = false }: { compact?: boolean }) {
  return (
    <div
      className={`bg-clinical-warnBg border border-clinical-warnBorder text-clinical-warnText rounded-md ${
        compact ? 'text-xs px-3 py-2' : 'text-[13.5px] px-4 py-3'
      }`}
    >
      <strong>AI-generated segmentation — requires expert review.</strong>{' '}
      This is a research / decision-support tool. It does not diagnose stroke, determine
      treatment, or replace a qualified radiologist.
    </div>
  );
}
