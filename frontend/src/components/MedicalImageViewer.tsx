import { useEffect, useRef, useState, useCallback } from 'react';

type ViewMode = 'original' | 'mask' | 'overlay' | 'compare';

interface Props {
  originalUrl: string | null;
  maskUrl: string;
  isDicom?: boolean;
  imageDimensions?: { width: number; height: number };
}

/**
 * Draws the original (grayscale) image and a red-tinted version of the
 * binary mask on a single canvas, blended with a client-adjustable opacity —
 * true adjustable-opacity overlay, not a fixed pre-baked image. Supports
 * zoom (wheel) and pan (drag) via CSS transform on the canvas element.
 */
export default function MedicalImageViewer({ originalUrl, maskUrl, isDicom, imageDimensions }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const compareCanvasRef = useRef<HTMLCanvasElement>(null);
  const [mode, setMode] = useState<ViewMode>(originalUrl ? 'overlay' : 'mask');
  const [opacity, setOpacity] = useState(() => {
    const stored = localStorage.getItem('neurodetect_default_opacity');
    return stored ? parseFloat(stored) : 0.45;
  });
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const dragState = useRef<{ dragging: boolean; lastX: number; lastY: number }>({ dragging: false, lastX: 0, lastY: 0 });

  const originalImg = useRef<HTMLImageElement | null>(null);
  const maskImg = useRef<HTMLImageElement | null>(null);
  const [imagesReady, setImagesReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setImagesReady(false);

    const loadImg = (src: string): Promise<HTMLImageElement> =>
      new Promise((resolve, reject) => {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = src;
      });

    Promise.all([
      originalUrl ? loadImg(originalUrl) : Promise.resolve(null),
      loadImg(maskUrl),
    ])
      .then(([orig, mask]) => {
        if (cancelled) return;
        originalImg.current = orig;
        maskImg.current = mask;
        setImagesReady(true);
      })
      .catch(() => { if (!cancelled) setImagesReady(false); });

    return () => { cancelled = true; };
  }, [originalUrl, maskUrl]);

  const draw = useCallback((canvas: HTMLCanvasElement | null, drawMode: ViewMode) => {
    if (!canvas || !maskImg.current) return;
    const w = (drawMode === 'mask' ? maskImg.current : originalImg.current || maskImg.current).naturalWidth;
    const h = (drawMode === 'mask' ? maskImg.current : originalImg.current || maskImg.current).naturalHeight;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, w, h);

    if (drawMode === 'original' && originalImg.current) {
      ctx.drawImage(originalImg.current, 0, 0, w, h);
      return;
    }
    if (drawMode === 'mask') {
      ctx.drawImage(maskImg.current, 0, 0, w, h);
      return;
    }
    if (originalImg.current) {
      ctx.drawImage(originalImg.current, 0, 0, w, h);
    } else {
      ctx.fillStyle = '#000';
      ctx.fillRect(0, 0, w, h);
    }
    const off = document.createElement('canvas');
    off.width = w;
    off.height = h;
    const offCtx = off.getContext('2d')!;
    offCtx.drawImage(maskImg.current, 0, 0, w, h);
    const imgData = offCtx.getImageData(0, 0, w, h);
    for (let i = 0; i < imgData.data.length; i += 4) {
      const v = imgData.data[i];
      if (v > 10) {
        imgData.data[i] = 220;
        imgData.data[i + 1] = 38;
        imgData.data[i + 2] = 38;
        imgData.data[i + 3] = 255;
      } else {
        imgData.data[i + 3] = 0;
      }
    }
    offCtx.putImageData(imgData, 0, 0);

    ctx.globalAlpha = opacity;
    ctx.drawImage(off, 0, 0, w, h);
    ctx.globalAlpha = 1;
  }, [opacity]);

  useEffect(() => {
    if (!imagesReady) return;
    if (mode === 'compare') {
      draw(canvasRef.current, 'original');
      draw(compareCanvasRef.current, 'overlay');
    } else {
      draw(canvasRef.current, mode);
    }
  }, [imagesReady, mode, draw]);

  const resetView = () => { setZoom(1); setPan({ x: 0, y: 0 }); };
  const onWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    setZoom((z) => Math.min(6, Math.max(0.5, z - e.deltaY * 0.001)));
  };
  const onMouseDown = (e: React.MouseEvent) => {
    dragState.current = { dragging: true, lastX: e.clientX, lastY: e.clientY };
  };
  const onMouseMove = (e: React.MouseEvent) => {
    if (!dragState.current.dragging) return;
    const dx = e.clientX - dragState.current.lastX;
    const dy = e.clientY - dragState.current.lastY;
    dragState.current.lastX = e.clientX;
    dragState.current.lastY = e.clientY;
    setPan((p) => ({ x: p.x + dx, y: p.y + dy }));
  };
  const endDrag = () => { dragState.current.dragging = false; };

  const transformStyle = { transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, transformOrigin: 'center center' };

  return (
    <div className="clinical-card p-3">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex gap-1">
          {(['original', 'mask', 'overlay', 'compare'] as ViewMode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              disabled={m === 'original' && !originalUrl}
              className={`text-xs px-2.5 py-1.5 rounded-md border capitalize ${
                mode === m ? 'bg-clinical-primary text-white border-clinical-primary' : 'border-clinical-border text-clinical-textMuted hover:bg-gray-50'
              } disabled:opacity-40 disabled:cursor-not-allowed`}
            >
              {m === 'compare' ? 'Side-by-side' : m}
            </button>
          ))}
        </div>
        <button onClick={resetView} className="text-xs px-2.5 py-1.5 rounded-md border border-clinical-border hover:bg-gray-50">
          Reset view
        </button>
      </div>

      {mode === 'overlay' && (
        <div className="flex items-center gap-2 mb-3 text-xs text-clinical-textMuted">
          <span>Overlay opacity</span>
          <input type="range" min={0} max={1} step={0.05} value={opacity} onChange={(e) => setOpacity(parseFloat(e.target.value))} className="w-40" />
          <span>{Math.round(opacity * 100)}%</span>
        </div>
      )}

      {isDicom && !originalUrl && (
        <p className="text-xs text-clinical-textMuted mb-2">
          Source is a DICOM file — the raw original isn't rendered directly in-browser; the mask/overlay below were generated server-side from the DICOM pixel data.
        </p>
      )}

      <div
        className="relative overflow-hidden bg-black rounded-md flex items-center justify-center cursor-grab active:cursor-grabbing"
        style={{ height: 420 }}
        onWheel={onWheel}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={endDrag}
        onMouseLeave={endDrag}
      >
        {!imagesReady && <span className="text-white text-xs">Loading image…</span>}
        {imagesReady && mode !== 'compare' && (
          <canvas ref={canvasRef} style={transformStyle} className="max-h-full max-w-full" />
        )}
        {imagesReady && mode === 'compare' && (
          <div className="flex gap-2 w-full h-full items-center justify-center" style={transformStyle}>
            <canvas ref={canvasRef} className="max-h-full max-w-[48%] object-contain" />
            <canvas ref={compareCanvasRef} className="max-h-full max-w-[48%] object-contain" />
          </div>
        )}
      </div>
      <div className="flex justify-between mt-2 text-[11px] text-clinical-textMuted">
        <span>Scroll to zoom · Drag to pan</span>
        {imageDimensions && <span>{imageDimensions.width} × {imageDimensions.height} px</span>}
      </div>
    </div>
  );
}
