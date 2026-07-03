import { useEffect, useState } from "react";
import { createProject, listProjects, getProject } from "../api.js";

function ProjectDetail({ id, onBack }) {
  const [proj, setProj] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    getProject(id).then(setProj).catch((e) => setError(e.message));
  }, [id]);

  if (error) return <div className="error-banner">{error}</div>;
  if (!proj) return <div className="picker-empty">Loading…</div>;
  return (
    <div>
      <button className="btn-secondary" onClick={onBack}>← All projects</button>
      <h3 className="proj-title">{proj.name}</h3>
      {proj.items.length === 0 && <div className="picker-empty">No saved renders yet.</div>}
      {[...proj.items].reverse().map((item, i) => (
        <div className="result-card" key={i}>
          <div className="proj-pair">
            <img src={item.before_url} alt="Before" loading="lazy" />
            <img src={item.after_url} alt="After" loading="lazy" />
          </div>
          <div className="result-footer">
            <span className="result-meta">
              <strong>{item.material_name}</strong> · {item.mode.replace("_", " ")}
            </span>
            <a className="btn-secondary" href={item.after_url} download>↓</a>
          </div>
        </div>
      ))}
      {proj.heroes?.length > 0 && (
        <>
          <h3 className="proj-title">Hero shots</h3>
          {[...proj.heroes].reverse().map((h, i) => (
            <div className="result-card" key={i}>
              <img src={h.hero_url} alt="Hero rendering" loading="lazy" />
            </div>
          ))}
        </>
      )}
    </div>
  );
}

export default function ProjectBar({ project, onSelect }) {
  const [open, setOpen] = useState(false);
  const [projects, setProjects] = useState(null);
  const [name, setName] = useState("");
  const [viewing, setViewing] = useState(null);
  const [error, setError] = useState(null);

  async function refresh() {
    try {
      setProjects(await listProjects());
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    if (open) refresh();
  }, [open]);

  async function create(e) {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      const p = await createProject(name.trim());
      onSelect(p);
      setName("");
      setOpen(false);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <>
      <div className="project-bar">
        <button className="project-chip" onClick={() => setOpen(true)}>
          📁 {project ? project.name : "No project — renders won't be saved"}
          <span className="chev">▾</span>
        </button>
      </div>

      {open && (
        <div className="modal-backdrop" onClick={() => setOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            {viewing ? (
              <ProjectDetail id={viewing} onBack={() => setViewing(null)} />
            ) : (
              <>
                <h3 className="proj-title">Customer projects</h3>
                <p className="section-sub" style={{ margin: "0 0 12px" }}>
                  Renders in a project are kept — start one per customer visit.
                </p>
                <form className="proj-create" onSubmit={create}>
                  <input
                    className="picker-search"
                    placeholder="New project, e.g. Henderson — 12 Oak Ln"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                  <button className="btn-secondary" type="submit" disabled={!name.trim()}>+ Create</button>
                </form>
                {error && <div className="error-banner">{error}</div>}
                {project && (
                  <button className="btn-secondary proj-row-btn" onClick={() => { onSelect(null); setOpen(false); }}>
                    ✕ Continue without a project
                  </button>
                )}
                {projects === null && !error && <div className="picker-empty">Loading…</div>}
                {projects?.map((p) => (
                  <div className="proj-row" key={p.id}>
                    <button
                      className={`proj-row-main ${project?.id === p.id ? "current" : ""}`}
                      onClick={() => { onSelect({ id: p.id, name: p.name }); setOpen(false); }}
                    >
                      <span className="proj-name">{p.name}</span>
                      <span className="proj-meta">
                        {p.item_count} render{p.item_count === 1 ? "" : "s"} ·{" "}
                        {new Date(p.updated_at * 1000).toLocaleDateString()}
                      </span>
                    </button>
                    <button className="btn-secondary" onClick={() => setViewing(p.id)}>View</button>
                  </div>
                ))}
              </>
            )}
            <button className="viewer-close modal-close" onClick={() => setOpen(false)} aria-label="Close">✕</button>
          </div>
        </div>
      )}
    </>
  );
}
