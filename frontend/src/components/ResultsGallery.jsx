import CompareSlider from "./CompareSlider.jsx";

function ResultCard({ photo, onRetry }) {
  if (photo.status === "queued" || photo.status === "rendering") {
    return (
      <div className="result-card">
        <div className="skeleton skeleton-result">
          <span className="status-text">
            {photo.status === "queued" ? "Waiting in queue…" : "Rendering — usually 10–30 s…"}
          </span>
        </div>
      </div>
    );
  }

  if (photo.status === "error") {
    return (
      <div className="result-card">
        <div className="result-error">
          <div className="msg">{photo.error || "Render failed."}</div>
          <button className="btn-secondary btn-danger" onClick={() => onRetry(photo)}>
            ↻ Retry this photo
          </button>
        </div>
      </div>
    );
  }

  // done
  return (
    <div className="result-card">
      <div className="result-body">
        <CompareSlider beforeSrc={photo.previewUrl} afterSrc={photo.afterUrl} />
      </div>
      <div className="result-footer">
        <span className="result-meta">
          Rendered in <strong>{photo.materialName}</strong>
        </span>
        <a className="btn-secondary" href={photo.afterUrl} download>
          ↓ Save
        </a>
      </div>
    </div>
  );
}

export default function ResultsGallery({ photos, onRetry }) {
  const visible = photos.filter((p) => p.status !== "idle");
  if (!visible.length) return null;
  return (
    <div>
      {visible.map((p) => (
        <ResultCard key={p.id} photo={p} onRetry={onRetry} />
      ))}
    </div>
  );
}
