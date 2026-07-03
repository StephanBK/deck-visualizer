import { useMemo, useState } from "react";

const COLOR_FAMILIES = ["brown", "grey", "neutral", "red", "dark"];

export default function MaterialPicker({ materials, selectedId, onSelect }) {
  const [search, setSearch] = useState("");
  const [color, setColor] = useState(null);

  const groups = useMemo(() => {
    const q = search.trim().toLowerCase();
    const filtered = materials.filter((m) => {
      if (color && m.color_family !== color) return false;
      if (!q) return true;
      const hay = `${m.brand || ""} ${m.collection || ""} ${m.name}`.toLowerCase();
      return hay.includes(q);
    });
    const map = new Map();
    for (const m of filtered) {
      const key = m.brand ? `${m.brand} · ${m.collection}` : "Natural Wood";
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(m);
    }
    return Array.from(map.entries());
  }, [materials, search, color]);

  return (
    <div>
      <div className="picker-controls">
        <input
          className="picker-search"
          type="search"
          placeholder="Search materials…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="chip-row">
          {COLOR_FAMILIES.map((c) => (
            <button
              key={c}
              className={`chip ${color === c ? "active" : ""}`}
              onClick={() => setColor(color === c ? null : c)}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {groups.length === 0 && <div className="picker-empty">No materials match.</div>}

      {groups.map(([label, mats]) => (
        <div className="material-group" key={label}>
          <h3>{label}</h3>
          <div className="material-row">
            {mats.map((m) => (
              <button
                key={m.id}
                className={`material-card ${m.id === selectedId ? "selected" : ""}`}
                onClick={() => onSelect(m.id)}
              >
                <div className="swatch-wrap">
                  <img src={m.swatch_url} alt={m.name} loading="lazy" />
                  {m.swatch_source === "generated_placeholder" && (
                    <span className="sample-badge">sample</span>
                  )}
                  {m.id === selectedId && <span className="check">✓</span>}
                </div>
                <span className="label">{m.name}</span>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
