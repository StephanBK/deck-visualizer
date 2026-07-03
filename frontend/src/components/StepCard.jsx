// One collapsible step in the flow. Collapsed + complete -> shows a one-line
// summary of the choice; tap the header any time to reopen and change it.
export default function StepCard({ number, title, summary, complete, open, onToggle, children }) {
  return (
    <div className="step-card">
      <button className="step-header" onClick={onToggle}>
        <span className={`step-badge ${complete ? "complete" : ""}`}>
          {complete ? "✓" : number}
        </span>
        <span className="step-titles">
          <span className="step-title">{title}</span>
          {!open && summary && <span className="step-summary">{summary}</span>}
        </span>
        <span className={`step-chevron ${open ? "open" : ""}`}>▾</span>
      </button>
      {open && <div className="step-body">{children}</div>}
    </div>
  );
}
