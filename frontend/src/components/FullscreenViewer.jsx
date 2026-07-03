import { useEffect, useRef, useState } from "react";
import { shareImage } from "../api.js";

// Fullscreen result view for handing the iPad across the table:
// pinch to zoom, drag to pan when zoomed, hold the button to flash the
// "before" photo, share/download in the corner.
export default function FullscreenViewer({ beforeSrc, afterSrc, label, onClose }) {
  const [showBefore, setShowBefore] = useState(false);
  const [t, setT] = useState({ scale: 1, x: 0, y: 0 });
  const pointers = useRef(new Map());
  const gesture = useRef(null);

  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = prev; };
  }, []);

  function onPointerDown(e) {
    e.currentTarget.setPointerCapture(e.pointerId);
    pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    const pts = [...pointers.current.values()];
    if (pts.length === 2) {
      gesture.current = {
        startDist: Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y),
        startScale: t.scale,
        startMid: { x: (pts[0].x + pts[1].x) / 2, y: (pts[0].y + pts[1].y) / 2 },
        startT: { ...t },
      };
    } else if (pts.length === 1 && t.scale > 1) {
      gesture.current = { pan: { x: e.clientX, y: e.clientY }, startT: { ...t } };
    }
  }

  function onPointerMove(e) {
    if (!pointers.current.has(e.pointerId)) return;
    pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    const pts = [...pointers.current.values()];
    const g = gesture.current;
    if (pts.length === 2 && g?.startDist) {
      const dist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
      const mid = { x: (pts[0].x + pts[1].x) / 2, y: (pts[0].y + pts[1].y) / 2 };
      const scale = Math.min(5, Math.max(1, (g.startScale * dist) / g.startDist));
      setT({
        scale,
        x: g.startT.x + (mid.x - g.startMid.x),
        y: g.startT.y + (mid.y - g.startMid.y),
      });
    } else if (pts.length === 1 && g?.pan) {
      setT({ ...g.startT, x: g.startT.x + e.clientX - g.pan.x, y: g.startT.y + e.clientY - g.pan.y });
    }
  }

  function onPointerUp(e) {
    pointers.current.delete(e.pointerId);
    if (pointers.current.size < 2) gesture.current = null;
    if (t.scale <= 1.02 && pointers.current.size === 0) setT({ scale: 1, x: 0, y: 0 });
  }

  async function share() {
    const ok = await shareImage(afterSrc, label ? `New deck visualization — ${label}` : "New deck visualization");
    if (!ok) {
      const a = document.createElement("a");
      a.href = afterSrc;
      a.download = "";
      a.click();
    }
  }

  return (
    <div className="viewer">
      <div
        className="viewer-stage"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onDoubleClick={() => setT({ scale: 1, x: 0, y: 0 })}
      >
        <img
          src={showBefore ? beforeSrc : afterSrc}
          alt={showBefore ? "Before" : "After"}
          draggable="false"
          style={{ transform: `translate(${t.x}px, ${t.y}px) scale(${t.scale})` }}
        />
      </div>

      {label && <div className="viewer-label">{label}</div>}
      {showBefore && <div className="viewer-flag">BEFORE</div>}
      <button className="viewer-close" onClick={onClose} aria-label="Close">✕</button>

      <div className="viewer-bar">
        {beforeSrc && (
          <button
            className="btn-secondary viewer-hold"
            onPointerDown={() => setShowBefore(true)}
            onPointerUp={() => setShowBefore(false)}
            onPointerLeave={() => setShowBefore(false)}
          >
            👁 Hold to see before
          </button>
        )}
        <button className="btn-secondary" onClick={share}>↗ Share</button>
        <a className="btn-secondary" href={afterSrc} download>↓ Save</a>
      </div>
    </div>
  );
}
