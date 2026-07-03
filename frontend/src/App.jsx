import { useEffect, useMemo, useRef, useState } from "react";
import { fetchMaterials } from "./api.js";
import { useRenderQueue } from "./hooks/useRenderQueue.js";
import StepCard from "./components/StepCard.jsx";
import PhotoStrip from "./components/PhotoStrip.jsx";
import MaterialPicker from "./components/MaterialPicker.jsx";
import ModeSelector, { PROJECT_TYPES } from "./components/ModeSelector.jsx";
import Toggles from "./components/Toggles.jsx";
import ResultsGallery from "./components/ResultsGallery.jsx";
import HeroSection from "./components/HeroSection.jsx";

let nextId = 1;

export default function App() {
  const [materials, setMaterials] = useState([]);
  const [loadError, setLoadError] = useState(null);
  const [photos, setPhotos] = useState([]);
  const [materialId, setMaterialId] = useState(null);
  const [mode, setMode] = useState(null); // the sales conversation starts here
  const [declutter, setDeclutter] = useState(false);
  const [stageFurniture, setStageFurniture] = useState(false);
  const [openStep, setOpenStep] = useState("type");

  const { enqueue } = useRenderQueue(setPhotos);
  const resultsRef = useRef(null);

  useEffect(() => {
    fetchMaterials()
      .then(setMaterials)
      .catch((e) => setLoadError(e.message));
  }, []);

  const projectType = PROJECT_TYPES.find((t) => t.id === mode);
  const selectedMaterial = useMemo(
    () => materials.find((m) => m.id === materialId),
    [materials, materialId]
  );

  function toggleStep(step) {
    setOpenStep((cur) => (cur === step ? null : step));
  }

  function pickType(id) {
    setMode(id);
    setOpenStep("photos"); // advance the conversation
  }

  function pickMaterial(id) {
    setMaterialId(id);
    setOpenStep("options");
  }

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
    setOpenStep(null); // fold the controls away, results take the stage
    enqueue(photos, settings);
    setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth" }), 150);
  }

  const busyCount = photos.filter((p) => p.status === "queued" || p.status === "rendering").length;
  const doneCount = photos.filter((p) => p.status === "done").length;
  const donePhotos = photos.filter((p) => p.status === "done");
  const isBusy = busyCount > 0;

  const touches = [declutter && "Declutter", stageFurniture && "Stage furniture"].filter(Boolean);

  const buttonLabel = isBusy
    ? `Rendering ${Math.min(doneCount + 1, photos.length)} of ${photos.length}…`
    : photos.length > 1
      ? `Visualize ${photos.length} photos`
      : "Visualize it";

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

      <StepCard
        number={1}
        title="Project type"
        summary={projectType && <>{projectType.icon}&nbsp; <strong>{projectType.name}</strong> — {projectType.desc}</>}
        complete={!!mode}
        open={openStep === "type"}
        onToggle={() => toggleStep("type")}
      >
        <ModeSelector mode={mode} onChange={pickType} />
      </StepCard>

      <StepCard
        number={2}
        title={projectType ? projectType.photoTitle : "Photos"}
        summary={
          photos.length
            ? <><strong>{photos.length} photo{photos.length > 1 ? "s" : ""}</strong> added</>
            : "No photos yet"
        }
        complete={photos.length > 0}
        open={openStep === "photos"}
        onToggle={() => toggleStep("photos")}
      >
        <p className="photo-hint">
          {projectType ? projectType.photoHint : "Snap or add one or more photos."}
        </p>
        <PhotoStrip photos={photos} onAdd={addPhotos} onRemove={removePhoto} />
        {photos.length > 0 && (
          <button
            className="btn-secondary"
            style={{ marginTop: 12 }}
            onClick={() => setOpenStep("material")}
          >
            Next: choose material →
          </button>
        )}
      </StepCard>

      <StepCard
        number={3}
        title="Material"
        summary={
          selectedMaterial && (
            <>
              <strong>
                {selectedMaterial.brand ? `${selectedMaterial.brand} ` : ""}
                {selectedMaterial.name}
              </strong>
              {selectedMaterial.collection ? ` · ${selectedMaterial.collection}` : ""}
            </>
          )
        }
        complete={!!materialId}
        open={openStep === "material"}
        onToggle={() => toggleStep("material")}
      >
        <MaterialPicker
          materials={materials}
          selectedId={materialId}
          onSelect={pickMaterial}
        />
      </StepCard>

      <StepCard
        number={4}
        title="Finishing touches"
        summary={touches.length ? <strong>{touches.join(" + ")}</strong> : "None — photo stays as-is"}
        complete
        open={openStep === "options"}
        onToggle={() => toggleStep("options")}
      >
        <Toggles
          declutter={declutter}
          stageFurniture={stageFurniture}
          onDeclutter={setDeclutter}
          onStage={setStageFurniture}
        />
      </StepCard>

      <div ref={resultsRef}>
        {photos.some((p) => p.status !== "idle") && (
          <div className="results-title">Results</div>
        )}
        <ResultsGallery
          photos={photos}
          onRetry={(photo) => enqueue([photo], settings)}
        />
      </div>

      {donePhotos.length > 0 && !isBusy && (
        <div style={{ marginTop: 20 }}>
          <HeroSection donePhotos={donePhotos} materialId={materialId} />
        </div>
      )}

      <div className="generate-bar">
        <button
          className="generate-btn"
          disabled={!photos.length || !materialId || !mode || isBusy}
          onClick={generateAll}
        >
          {isBusy && <span className="spinner" />}
          {buttonLabel}
        </button>
      </div>
    </div>
  );
}
