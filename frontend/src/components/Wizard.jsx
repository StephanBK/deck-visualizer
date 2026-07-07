// Stepper chrome for the deck flow: tappable progress dots on top, Back/Next
// pinned at the bottom. The flow is linear, but any already-unlocked step
// stays reachable so a rep can jump back, change something, and re-run.

export const WIZ_STEPS = [
  { id: "type", label: "Type" },
  { id: "photos", label: "Photos" },
  { id: "material", label: "Materials" },
  { id: "options", label: "Options" },
  { id: "results", label: "Results" },
];

export function WizardNav({ step, valid, onJump }) {
  // A step is reachable while every step before it is valid; Results also
  // needs at least one render to exist (its own `valid` flag).
  let unlocked = true;
  const items = WIZ_STEPS.map((s) => {
    const reachable = unlocked && (s.id !== "results" || valid.results);
    if (!valid[s.id]) unlocked = false;
    return { ...s, reachable };
  });

  return (
    <nav className="wiz-nav" aria-label="Steps">
      {items.map((s, i) => (
        <button
          key={s.id}
          className={`wiz-dot-btn ${s.id === step ? "active" : ""} ${valid[s.id] ? "done" : ""}`}
          disabled={!s.reachable}
          onClick={() => s.id !== step && onJump(s.id)}
        >
          <span className="wiz-dot">{valid[s.id] && s.id !== step ? "✓" : i + 1}</span>
          <span className="wiz-dot-label">{s.label}</span>
        </button>
      ))}
    </nav>
  );
}

// Bottom bar: an optional Back button next to whatever the primary action for
// the current screen is (a plain Next, or the Visualize button itself).
export function WizardFooter({ onBack, backLabel = "← Back", children }) {
  return (
    <div className="wiz-footer">
      {onBack && (
        <button className="btn-secondary wiz-back" onClick={onBack}>
          {backLabel}
        </button>
      )}
      {children}
    </div>
  );
}
