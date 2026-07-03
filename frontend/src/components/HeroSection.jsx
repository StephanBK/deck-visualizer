import { useState } from "react";
import { createHero, shareImage } from "../api.js";

// The "fusion hero shot": pick up to 3 rendered results, get back one
// golden-hour marketing render. Always labeled as an AI rendering.
export default function HeroSection({ doneJobs, projectId }) {
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
    const names = picked.length ? picked : [doneJobs[0].resultName];
    const materialId = doneJobs.find((j) => j.resultName === names[0])?.materialId;
    setHero({ status: "rendering", url: null, error: null });
    try {
      const { hero_url } = await createHero(names, materialId, projectId);
      setHero({ status: "done", url: hero_url, error: null });
    } catch (e) {
      setHero({ status: "error", url: null, error: e.message });
    }
  }

  async function share() {
    const ok = await shareImage(hero.url, "Concept rendering of your new deck");
    if (!ok) window.open(hero.url, "_blank");
  }

  return (
    <div className="hero-card">
      <div className="section-title">✨ Hero shot</div>
      <p className="section-sub">
        Combine your favorite result(s) into one polished, golden-hour marketing
        render. Pick up to 3 below — or just hit the button.
      </p>

      <div className="hero-pick-row">
        {doneJobs.map((j) => {
          const idx = picked.indexOf(j.resultName);
          return (
            <button
              key={j.id}
              className={`hero-pick ${idx >= 0 ? "picked" : ""}`}
              onClick={() => togglePick(j.resultName)}
            >
              <img src={j.afterUrl} alt={`Rendered in ${j.materialName}`} />
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
            <button className="btn-secondary" onClick={share}>↗ Share</button>
            <a className="btn-secondary" href={hero.url} download>↓ Save</a>
            <button className="btn-secondary" onClick={generate}>↻ Regenerate</button>
          </div>
        </>
      )}
    </div>
  );
}
