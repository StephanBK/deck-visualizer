import { useEffect, useState } from "react";
import CompareSlider from "./CompareSlider.jsx";
import { shareImage } from "../api.js";

function Elapsed({ since }) {
  const [, tick] = useState(0);
  useEffect(() => {
    const iv = setInterval(() => tick((n) => n + 1), 1000);
    return () => clearInterval(iv);
  }, []);
  const secs = since ? Math.round((Date.now() - since) / 1000) : 0;
  return <>{secs}s{secs > 35 ? " — almost there…" : ""}</>;
}

// Inline free-text tweak on a finished render ("make the railing white").
function RefineRow({ job, onRefine }) {
  const [text, setText] = useState("");
  return (
    <div className="refine-row">
      <input
        type="text"
        maxLength={500}
        placeholder='Tweak it — e.g. "make the railing white"'
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && text.trim() && (onRefine(job, text.trim()), setText(""))}
      />
      <button
        className="btn-secondary"
        disabled={!text.trim()}
        onClick={() => {
          onRefine(job, text.trim());
          setText("");
        }}
      >
        ✨ Go
      </button>
    </div>
  );
}

function JobBody({ job, onRetry, onCancel, onOpenViewer, onRefine }) {
  if (job.status === "queued" || job.status === "rendering") {
    return (
      <div className="skeleton skeleton-result">
        <span className="status-text">
          {job.status === "queued" ? "Waiting in queue…" : (
            <>Rendering {job.materialName}… <Elapsed since={job.startedAt} /></>
          )}
        </span>
        <button className="btn-secondary cancel-btn" onClick={() => onCancel(job.id)}>Cancel</button>
      </div>
    );
  }
  if (job.status === "error" || job.status === "canceled") {
    return (
      <div className="result-error">
        <div className="msg">{job.status === "canceled" ? "Canceled." : job.error || "Render failed."}</div>
        <button className="btn-secondary" onClick={() => onRetry(job)}>↻ {job.status === "canceled" ? "Render" : "Retry"}</button>
      </div>
    );
  }
  // done
  const label = job.materialName;
  return (
    <>
      <CompareSlider beforeSrc={job.photo.previewUrl} afterSrc={job.afterUrl} />
      <div className="result-footer">
        <span className="result-meta">
          <strong>{label}</strong>
        </span>
        <span className="result-actions">
          <button className="btn-secondary" onClick={() => onOpenViewer(job)}>⤢</button>
          <button
            className="btn-secondary"
            onClick={async () => {
              const ok = await shareImage(job.afterUrl, `Your new deck in ${label}`);
              if (!ok) window.open(job.afterUrl, "_blank");
            }}
          >
            ↗ Share
          </button>
          <a className="btn-secondary" href={job.afterUrl} download>↓</a>
        </span>
      </div>
      <RefineRow job={job} onRefine={onRefine} />
    </>
  );
}

function PhotoCard({ photo, jobs, onRetry, onCancel, onOpenViewer, onRefine }) {
  const [activeId, setActiveId] = useState(jobs[0]?.id);
  // keep a sensible active tab: prefer the first finished render
  useEffect(() => {
    if (!jobs.find((j) => j.id === activeId)) setActiveId(jobs[0]?.id);
  }, [jobs, activeId]);
  const active = jobs.find((j) => j.id === activeId) || jobs[0];
  if (!active) return null;

  return (
    <div className="result-card">
      {jobs.length > 1 && (
        <div className="job-chips">
          {jobs.map((j) => (
            <button
              key={j.id}
              className={`chip job-chip ${j.id === active.id ? "active" : ""}`}
              onClick={() => setActiveId(j.id)}
            >
              <span className={`dot ${j.status}`} />
              {j.materialName}
            </button>
          ))}
        </div>
      )}
      <JobBody job={active} onRetry={onRetry} onCancel={onCancel} onOpenViewer={onOpenViewer} onRefine={onRefine} />
    </div>
  );
}

export default function ResultsGallery({ photos, jobs, onRetry, onCancel, onOpenViewer, onRefine }) {
  if (!jobs.length) return null;
  return (
    <div>
      {photos.map((p) => {
        const photoJobs = jobs.filter((j) => j.photoId === p.id);
        if (!photoJobs.length) return null;
        return (
          <PhotoCard
            key={p.id}
            photo={p}
            jobs={photoJobs}
            onRetry={onRetry}
            onCancel={onCancel}
            onOpenViewer={onOpenViewer}
            onRefine={onRefine}
          />
        );
      })}
    </div>
  );
}
