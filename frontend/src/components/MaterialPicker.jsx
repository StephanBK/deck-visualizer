import { useMemo, useState } from "react";

const COLOR_FAMILIES = ["brown", "grey", "neutral", "red", "dark"];
export const MAX_MATERIALS = 4;

function MaterialCard({ m, order, isFav, onToggle, onToggleFav }) {
  return (
    <button className={`material-card ${order >= 0 ? "selected" : ""}`} onClick={() => onToggle(m.id)}>
      <div className="swatch-wrap">
        <img src={m.swatch_url} alt={m.name} loading="lazy" />
        {m.swatch_source === "generated_placeholder" && <span className="sample-badge">sample</span>}
        {order >= 0 && <span className="check">{order + 1}</span>}
        <span
          className={`fav-star ${isFav ? "faved" : ""}`}
          role="button"
          aria-label={isFav ? "Remove from favorites" : "Add to favorites"}
          onClick={(e) => {
            e.stopPropagation();
            onToggleFav(m.id);
          }}
        >
          {isFav ? "★" : "☆"}
        </span>
      </div>
      <span className="label">{m.name}</span>
    </button>
  );
}

export default function MaterialPicker({
  materials, selectedIds, onToggle, favorites, recents, onToggleFav,
}) {
  const [search, setSearch] = useState("");
  const [color, setColor] = useState(null);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return materials.filter((m) => {
      if (color && m.color_family !== color) return false;
      if (!q) return true;
      return `${m.brand || ""} ${m.collection || ""} ${m.name}`.toLowerCase().includes(q);
    });
  }, [materials, search, color]);

  const pinned = useMemo(() => {
    const ids = [...new Set([...favorites, ...recents])];
    const byId = new Map(filtered.map((m) => [m.id, m]));
    return ids.map((id) => byId.get(id)).filter(Boolean);
  }, [filtered, favorites, recents]);

  const groups = useMemo(() => {
    const map = new Map();
    for (const m of filtered) {
      const key = m.brand ? `${m.brand} · ${m.collection}` : "Natural Wood";
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(m);
    }
    return Array.from(map.entries());
  }, [filtered]);

  const renderRow = (mats) => (
    <div className="material-row">
      {mats.map((m) => (
        <MaterialCard
          key={m.id}
          m={m}
          order={selectedIds.indexOf(m.id)}
          isFav={favorites.includes(m.id)}
          onToggle={onToggle}
          onToggleFav={onToggleFav}
        />
      ))}
    </div>
  );

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

      <p className="picker-note">
        Pick up to {MAX_MATERIALS} — each photo renders once per material, so the
        customer can compare looks side by side.
      </p>

      {pinned.length > 0 && (
        <div className="material-group">
          <h3>★ Favorites & recent</h3>
          {renderRow(pinned)}
        </div>
      )}

      {groups.length === 0 && <div className="picker-empty">No materials match.</div>}

      {groups.map(([label, mats]) => (
        <div className="material-group" key={label}>
          <h3>{label}</h3>
          {renderRow(mats)}
        </div>
      ))}
    </div>
  );
}
