import { useRef } from "react";

const STATUS_LABELS = {
  queued: "Queued",
  rendering: "Rendering…",
  done: "Done",
  error: "Failed",
};

export default function PhotoStrip({ photos, onAdd, onRemove }) {
  const inputRef = useRef(null);

  function handleFiles(e) {
    const files = Array.from(e.target.files || []);
    if (files.length) onAdd(files);
    e.target.value = ""; // allow re-picking the same file
  }

  return (
    <div className="photo-strip">
      {photos.map((p) => (
        <div className="photo-thumb" key={p.id}>
          <img src={p.previewUrl} alt="Deck photo" />
          {p.status !== "idle" && (
            <span className={`status-chip ${p.status}`}>{STATUS_LABELS[p.status]}</span>
          )}
          <button
            className="remove"
            aria-label="Remove photo"
            onClick={() => onRemove(p.id)}
          >
            ✕
          </button>
        </div>
      ))}
      <button className="add-tile" onClick={() => inputRef.current?.click()}>
        <span className="plus">+</span>
        {photos.length ? "Add more" : "Take / add photos"}
      </button>
      <input
        ref={inputRef}
        className="visually-hidden"
        type="file"
        accept="image/*"
        capture="environment"
        multiple
        onChange={handleFiles}
      />
    </div>
  );
}
