import { useState } from "react";
import { SERVICES } from "../services.js";

function ComingSoonSheet({ service, onClose }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="soon-head">
          <span className="soon-icon">{service.icon}</span>
          <div>
            <h3 className="proj-title" style={{ margin: 0 }}>{service.name}</h3>
            <span className="soon-chip">Coming soon</span>
          </div>
        </div>
        <p className="soon-headline">{service.pitch.headline}</p>
        <ul className="soon-points">
          {service.pitch.points.map((p, i) => (
            <li key={i}>{p}</li>
          ))}
        </ul>
        <p className="soon-note">
          This visualizer isn't live yet — we're showing it to gauge interest.
          Tell your rep what you'd want to see and it shapes what we build first.
        </p>
        <button className="generate-btn" onClick={onClose}>Got it</button>
        <button className="viewer-close modal-close" onClick={onClose} aria-label="Close">✕</button>
      </div>
    </div>
  );
}

export default function HomeScreen({ onOpenService }) {
  const [pitch, setPitch] = useState(null);

  return (
    <>
      <p className="home-lead">What are we visualizing today?</p>
      <div className="service-grid">
        {SERVICES.map((s) => (
          <button
            key={s.id}
            className={`service-card ${s.available ? "live" : "soon"}`}
            onClick={() => (s.available ? onOpenService(s.id) : setPitch(s))}
          >
            <span className="service-icon">{s.icon}</span>
            <span className="service-name">{s.name}</span>
            <span className="service-tag">{s.tagline}</span>
            {s.available
              ? <span className="service-cta">Open →</span>
              : <span className="soon-chip">Coming soon</span>}
          </button>
        ))}
      </div>
      {pitch && <ComingSoonSheet service={pitch} onClose={() => setPitch(null)} />}
    </>
  );
}
