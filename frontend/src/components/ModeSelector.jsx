const MODES = [
  { id: "resurface", name: "Resurface", desc: "New boards, same structure" },
  { id: "replace", name: "Replace", desc: "Rebuild deck & railings" },
  { id: "build_new", name: "Build new", desc: "Add a deck where none exists" },
];

export default function ModeSelector({ mode, onChange }) {
  return (
    <div className="mode-row">
      {MODES.map((m) => (
        <button
          key={m.id}
          className={`mode-btn ${mode === m.id ? "active" : ""}`}
          onClick={() => onChange(m.id)}
        >
          <span className="mode-name">{m.name}</span>
          <span className="mode-desc">{m.desc}</span>
        </button>
      ))}
    </div>
  );
}
