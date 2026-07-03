import { useRef, useState } from "react";

// Hand-rolled before/after slider: the AFTER image sits in normal flow (it
// defines the box), the BEFORE image is stacked on top and clipped to the
// left of the handle. Drag anywhere to move it.
export default function CompareSlider({ beforeSrc, afterSrc }) {
  const [pos, setPos] = useState(50);
  const boxRef = useRef(null);

  function moveTo(clientX) {
    const rect = boxRef.current.getBoundingClientRect();
    const pct = ((clientX - rect.left) / rect.width) * 100;
    setPos(Math.max(0, Math.min(100, pct)));
  }

  function onPointerDown(e) {
    boxRef.current.setPointerCapture(e.pointerId);
    moveTo(e.clientX);
  }

  function onPointerMove(e) {
    if (e.buttons || e.pointerType === "touch") moveTo(e.clientX);
  }

  return (
    <div
      className="compare"
      ref={boxRef}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
    >
      <img src={afterSrc} alt="After" draggable="false" />
      <div className="before-layer" style={{ clipPath: `inset(0 ${100 - pos}% 0 0)` }}>
        <img src={beforeSrc} alt="Before" draggable="false" />
      </div>
      <div className="divider" style={{ left: `${pos}%` }} />
      <div className="handle" style={{ left: `${pos}%` }}>⇔</div>
      <span className="tag before">Before</span>
      <span className="tag after">After</span>
    </div>
  );
}
