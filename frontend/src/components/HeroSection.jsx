import { useState } from "react";
import { createHero } from "../api.js";

// The "fusion hero shot": pick up to 3 rendered results, get back one
// golden-hour marketing render. Always labeled as an AI rendering.
export default function HeroSection({ donePhotos, materialId }) {
  const [picked, setPicked] = useState([]);
  const [hero, setHero] = useState({ status: "idle", url: null, error: null });

  function togglePick(resultName) {
    setPicked((prev) =>
      prev.includes(resultName)
        ? prev.filter((n) => n !== resultName)
        : prev.length < 3
          ? [...prev, resultName]
          : prev
    );
  }

  async function generate() {
    const names = picked.length ? picked : [donePhotos[0].resultName];
    setHero({ status: "rendering", url: null, error: null });
    try {
      const { hero_url } = await createHero(names, materialId);
      setHero({ status: "done", url: hero_url, error: null });
    } catch (e) {
      setHero({ status: "error", url: null, error: e.message });
    }
  }

  return (
    <div className="hero-card">
      <div className="section-title">
        <span className="step">★</span> Hero shot
      </div>
      <p className="section-sub">
        Combine your favorite result(s) into one polished, golden-hour marketing
        render. Pick up to 3 below — or just hit the button.
      </p>

      <div className="hero-pick-row">
        {donePhotos.map((p) => {
          const idx = picked.indexOf(p.resultName);
          return (
            <button
              key={p.id}
              className={`hero-pick ${idx >= 0 ? "picked" : ""}`}
              onClick={() => togglePick(p.resultName)}
            >
              <img src={p.afterUrl} alt="Rendered result" />
              {idx >= 0 && <span className="order">{idx + 1}</span>}
            </button>
          );
        })}
      </div>

      {hero.status === "rendering" ? (
        <div className="skeleton skeleton-result" style={{ borderRadius: 10 }}>
          <span className="status-text">Creating hero shot…</span>
        </div>
      ) : (
        <button className="generate-btn" onClick={generate}>
          ✨ Create hero shot
        </button>
      )}

      {hero.status === "error" && <div className="error-banner">{hero.error}</div>}

      {hero.status === "done" && (
        <>
          <div className="hero-result">
            <img src={hero.url} alt="Hero rendering" />
            <span className="ai-badge">AI rendering — not a photograph</span>
          </div>
          <div className="hero-actions">
            <a className="btn-secondary" href={hero.url} download>
              ↓ Save hero shot
            </a>
            <button className="btn-secondary" onClick={generate}>
              ↻ Regenerate
            </button>
          </div>
        </>
      )}
    </div>
  );
}
