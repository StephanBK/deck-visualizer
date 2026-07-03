import { useEffect, useMemo, useRef, useState } from "react";
import { fetchMaterials } from "./api.js";
import { useRenderQueue } from "./hooks/useRenderQueue.js";
import PhotoStrip from "./components/PhotoStrip.jsx";
import MaterialPicker from "./components/MaterialPicker.jsx";
import ModeSelector from "./components/ModeSelector.jsx";
import Toggles from "./components/Toggles.jsx";
import ResultsGallery from "./components/ResultsGallery.jsx";
import HeroSection from "./components/HeroSection.jsx";

let nextId = 1;

export default function App() {
  const [materials, setMaterials] = useState([]);
  const [loadError, setLoadError] = useState(null);
  const [photos, setPhotos] = useState([]);
  const [materialId, setMaterialId] = useState(null);
  const [mode, setMode] = useState("resurface");
  const [declutter, setDeclutter] = useState(false);
  const [stageFurniture, setStageFurniture] = useState(false);

  const { enqueue } = useRenderQueue(setPhotos);
  const resultsRef = useRef(null);

  useEffect(() => {
    fetchMaterials()
      .then(setMaterials)
      .catch((e) => setLoadError(e.message));
  }, []);

  function addPhotos(files) {
    setPhotos((prev) => [
      ...prev,
      ...files.map((file) => ({
        id: nextId++,
        file,
        previewUrl: URL.createObjectURL(file),
        status: "idle",
        afterUrl: null,
        resultName: null,
        error: null,
      })),
    ]);
  }

  function removePhoto(id) {
    setPhotos((prev) => {
      const gone = prev.find((p) => p.id === id);
      if (gone) URL.revokeObjectURL(gone.previewUrl);
      return prev.filter((p) => p.id !== id);
    });
  }

  const settings = { materialId, mode, declutter, stageFurniture };

  function generateAll() {
    enqueue(photos, settings);
    // Give React a beat to show the skeletons, then bring them into view.
    setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth" }), 150);
  }

  const busyCount = photos.filter((p) => p.status === "queued" || p.status === "rendering").length;
  const doneCount = photos.filter((p) => p.status === "done").length;
  const donePhotos = photos.filter((p) => p.status === "done");
  const isBusy = busyCount > 0;

  const selectedMaterial = useMemo(
    () => materials.find((m) => m.id === materialId),
    [materials, materialId]
  );

  const buttonLabel = isBusy
    ? `Rendering ${Math.min(doneCount + 1, photos.length)} of ${photos.length}…`
    : photos.length > 1
      ? `Visualize ${photos.length} photos`
      : "Visualize my deck";

  return (
    <div className="app">
      <header className="header">
        <h1>
          Deck <em>Visualizer</em>
        </h1>
        <span className="tagline">See the new deck before it's built</span>
      </header>

      {loadError && (
        <div className="error-banner">
          Couldn't reach the server: {loadError}. Check the connection and reload.
        </div>
      )}

      <section className="section">
        <div className="section-title">
          <span className="step">1</span> Photos
        </div>
        <p className="section-sub">Snap or add one or more photos of the space.</p>
        <PhotoStrip photos={photos} onAdd={addPhotos} onRemove={removePhoto} />
      </section>

      <section className="section">
        <div className="section-title">
          <span className="step">2</span> Material
          {selectedMaterial && (
            <span className="tagline" style={{ fontWeight: 500 }}>
              — {selectedMaterial.brand ? `${selectedMaterial.brand} ` : ""}
              {selectedMaterial.name}
            </span>
          )}
        </div>
        <p className="section-sub">Pick the decking the customer is considering.</p>
        <MaterialPicker
          materials={materials}
          selectedId={materialId}
          onSelect={setMaterialId}
        />
      </section>

      <section className="section">
        <div className="section-title">
          <span className="step">3</span> Project type
        </div>
        <p className="section-sub">What are we doing to this space?</p>
        <ModeSelector mode={mode} onChange={setMode} />
      </section>

      <section className="section">
        <div className="section-title">
          <span className="step">4</span> Finishing touches
        </div>
        <p className="section-sub">Optional — applied to every photo.</p>
        <Toggles
          declutter={declutter}
          stageFurniture={stageFurniture}
          onDeclutter={setDeclutter}
          onStage={setStageFurniture}
        />
      </section>

      <section className="section" ref={resultsRef}>
        <ResultsGallery
          photos={photos}
          onRetry={(photo) => enqueue([photo], settings)}
        />
      </section>

      {donePhotos.length > 0 && !isBusy && (
        <section className="section">
          <HeroSection donePhotos={donePhotos} materialId={materialId} />
        </section>
      )}

      <div className="generate-bar">
        <button
          className="generate-btn"
          disabled={!photos.length || !materialId || isBusy}
          onClick={generateAll}
        >
          {isBusy && <span className="spinner" />}
          {buttonLabel}
        </button>
      </div>
    </div>
  );
}
