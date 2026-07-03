export const PROJECT_TYPES = [
  {
    id: "resurface",
    icon: "🪵",
    name: "Resurface",
    desc: "New boards, same structure",
    photoTitle: "Photos of the existing deck",
    photoHint: "Shoot from a corner so the whole deck floor is in frame.",
  },
  {
    id: "replace",
    icon: "🛠️",
    name: "Full rebuild",
    desc: "Tear out & rebuild deck + railings",
    photoTitle: "Photos of the existing deck",
    photoHint: "Capture the whole structure — boards, railings and stairs all get rebuilt.",
  },
  {
    id: "build_new",
    icon: "✨",
    name: "New deck",
    desc: "Add a deck where there is none",
    photoTitle: "Photos of the space",
    photoHint: "Shoot the yard or patio area where the deck would go, with the house in frame.",
  },
];

export default function ModeSelector({ mode, onChange }) {
  return (
    <div className="type-grid">
      {PROJECT_TYPES.map((t) => (
        <button
          key={t.id}
          className={`type-btn ${mode === t.id ? "active" : ""}`}
          onClick={() => onChange(t.id)}
        >
          <span className="type-icon">{t.icon}</span>
          <span className="type-name">{t.name}</span>
          <span className="type-desc">{t.desc}</span>
        </button>
      ))}
    </div>
  );
}
