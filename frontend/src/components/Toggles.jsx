function Switch({ checked, onChange }) {
  return (
    <label className="switch">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span className="track" />
    </label>
  );
}

export default function Toggles({ declutter, stageFurniture, onDeclutter, onStage }) {
  return (
    <div className="toggle-list">
      <div className="toggle-row">
        <div className="toggle-text">
          <div className="toggle-name">Declutter</div>
          <div className="toggle-desc">Remove hoses, toys, bins & stray clutter</div>
        </div>
        <Switch checked={declutter} onChange={onDeclutter} />
      </div>
      <div className="toggle-row">
        <div className="toggle-text">
          <div className="toggle-name">Stage furniture</div>
          <div className="toggle-desc">Add tasteful modern outdoor furniture</div>
        </div>
        <Switch checked={stageFurniture} onChange={onStage} />
      </div>
    </div>
  );
}
