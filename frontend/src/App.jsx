import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchMaterials, AuthError } from "./api.js";
import { useRenderQueue } from "./hooks/useRenderQueue.js";
import StepCard from "./components/StepCard.jsx";
import PhotoStrip from "./components/PhotoStrip.jsx";
import MaterialPicker, { MAX_MATERIALS } from "./components/MaterialPicker.jsx";
import ModeSelector, { PROJECT_TYPES } from "./components/ModeSelector.jsx";
import Toggles from "./components/Toggles.jsx";
import ResultsGallery from "./components/ResultsGallery.jsx";
import HeroSection from "./components/HeroSection.jsx";
import PinScreen from "./components/PinScreen.jsx";
import ProjectBar from "./components/ProjectBar.jsx";
import FullscreenViewer from "./components/FullscreenViewer.jsx";
import HomeScreen from "./components/HomeScreen.jsx";

let nextId = 1;

function readJSON(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key)) ?? fallback;
  } catch {
    return fallback;
  }
}

export default function App() {
  const [authed, setAuthed] = useState(null); // null=checking, false=locked, true=in
  const [screen, setScreen] = useState("home"); // 'home' | 'deck'
  const [materials, setMaterials] = useState([]);
  const [loadError, setLoadError] = useState(null);
  const [photos, setPhotos] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [materialIds, setMaterialIds] = useState([]);
  const [mode, setMode] = useState(null); // the sales conversation starts here
  const [declutter, setDeclutter] = useState(false);
  const [stageFurniture, setStageFurniture] = useState(false);
  const [openStep, setOpenStep] = useState("type");
  const [project, setProject] = useState(() => readJSON("currentProject", null));
  const [favorites, setFavorites] = useState(() => readJSON("favMaterials", []));
  const [recents, setRecents] = useState(() => readJSON("recentMaterials", []));
  const [viewer, setViewer] = useState(null); // {beforeSrc, afterSrc, label}

  const { enqueue, cancel } = useRenderQueue(setJobs);

  const loadMaterials = useCallback(() => {
    setLoadError(null);
    fetchMaterials()
      .then((mats) => {
        setMaterials(mats);
        setAuthed(true);
      })
      .catch((e) => {
        if (e instanceof AuthError) setAuthed(false);
        else {
          setAuthed(true);
          setLoadError(e.message);
        }
      });
  }, []);

  useEffect(() => { loadMaterials(); }, [loadMaterials]);
  useEffect(() => { localStorage.setItem("currentProject", JSON.stringify(project)); }, [project]);
  useEffect(() => { localStorage.setItem("favMaterials", JSON.stringify(favorites)); }, [favorites]);
  useEffect(() => { localStorage.setItem("recentMaterials", JSON.stringify(recents)); }, [recents]);

  const projectType = PROJECT_TYPES.find((t) => t.id === mode);
  const selectedMaterials = useMemo(
    () => materialIds.map((id) => materials.find((m) => m.id === id)).filter(Boolean),
    [materials, materialIds]
  );

  function toggleStep(step) {
    setOpenStep((cur) => (cur === step ? null : step));
  }

  function pickType(id) {
    setMode(id);
    setOpenStep("photos"); // advance the conversation
  }

  function toggleMaterial(id) {
    setMaterialIds((prev) =>
      prev.includes(id)
        ? prev.filter((m) => m !== id)
        : prev.length < MAX_MATERIALS
          ? [...prev, id]
          : prev
    );
  }

  function toggleFav(id) {
    setFavorites((prev) => (prev.includes(id) ? prev.filter((f) => f !== id) : [id, ...prev].slice(0, 12)));
  }

  function addPhotos(files) {
    setPhotos((prev) => [
      ...prev,
      ...files.map((file) => ({
        id: nextId++,
        file,
        previewUrl: URL.createObjectURL(file),
      })),
    ]);
  }

  function removePhoto(id) {
    jobs.filter((j) => j.photoId === id && (j.status === "queued" || j.status === "rendering"))
      .forEach((j) => cancel(j.id));
    setJobs((prev) => prev.filter((j) => j.photoId !== id));
    setPhotos((prev) => {
      const gone = prev.find((p) => p.id === id);
      if (gone) URL.revokeObjectURL(gone.previewUrl);
      return prev.filter((p) => p.id !== id);
    });
  }

  const settings = { mode, declutter, stageFurniture, projectId: project?.id };

  function generateAll() {
    const specs = [];
    for (const photo of photos) {
      for (const m of selectedMaterials) {
        specs.push({
          id: `${photo.id}:${m.id}`,
          photoId: photo.id,
          photo,
          materialId: m.id,
          materialName: m.name,
          status: "queued",
          afterUrl: null,
          resultName: null,
          error: null,
          startedAt: null,
        });
      }
    }
    setJobs(specs);
    setRecents((prev) => [...new Set([...materialIds, ...prev])].slice(0, 8));
    setOpenStep(null); // fold the controls away, results take the stage
    enqueue(specs, settings);
    setTimeout(() => document.querySelector(".results-title")?.scrollIntoView({ behavior: "smooth" }), 200);
  }

  function retryJob(job) {
    enqueue([job], settings);
  }

  const busyCount = jobs.filter((j) => j.status === "queued" || j.status === "rendering").length;
  const doneJobs = jobs.filter((j) => j.status === "done");
  const isBusy = busyCount > 0;
  const totalJobs = photos.length * materialIds.length;

  const touches = [declutter && "Declutter", stageFurniture && "Stage furniture"].filter(Boolean);

  const buttonLabel = isBusy
    ? `Rendering ${Math.min(doneJobs.length + 1, jobs.length)} of ${jobs.length}…`
    : totalJobs > 1
      ? `Visualize ${totalJobs} look${totalJobs > 1 ? "s" : ""}`
      : "Visualize it";

  if (authed === false) return <PinScreen onSuccess={loadMaterials} />;

  if (screen === "home") {
    return (
      <div className="app">
        <header className="header">
          <h1>
            Home <em>Visualizer</em>
          </h1>
          <span className="tagline">See it before it's built</span>
        </header>
        <ProjectBar project={project} onSelect={setProject} />
        {loadError && (
          <div className="error-banner">
            Couldn't reach the server: {loadError}.{" "}
            <button className="btn-secondary" onClick={loadMaterials}>Retry</button>
          </div>
        )}
        <HomeScreen onOpenService={(id) => id === "deck" && setScreen("deck")} />
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <button className="back-btn" onClick={() => setScreen("home")} aria-label="Back to services">
          ←
        </button>
        <h1>
          Deck <em>Visualizer</em>
        </h1>
        <span className="tagline">See the new deck before it's built</span>
      </header>

      <ProjectBar project={project} onSelect={setProject} />

      {loadError && (
        <div className="error-banner">
          Couldn't reach the server: {loadError}.{" "}
          <button className="btn-secondary" onClick={loadMaterials}>Retry</button>
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
            Next: choose materials →
          </button>
        )}
      </StepCard>

      <StepCard
        number={3}
        title="Materials"
        summary={
          selectedMaterials.length > 0 && (
            <>
              <strong>{selectedMaterials[0].name}</strong>
              {selectedMaterials.length > 1 && <> + {selectedMaterials.length - 1} more to compare</>}
            </>
          )
        }
        complete={materialIds.length > 0}
        open={openStep === "material"}
        onToggle={() => toggleStep("material")}
      >
        <MaterialPicker
          materials={materials}
          selectedIds={materialIds}
          onToggle={toggleMaterial}
          favorites={favorites}
          recents={recents}
          onToggleFav={toggleFav}
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

      {jobs.length > 0 && <div className="results-title">Results</div>}
      <ResultsGallery
        photos={photos}
        jobs={jobs}
        onRetry={retryJob}
        onCancel={cancel}
        onOpenViewer={(job) =>
          setViewer({ beforeSrc: job.photo.previewUrl, afterSrc: job.afterUrl, label: job.materialName })
        }
      />

      {doneJobs.length > 0 && !isBusy && (
        <div style={{ marginTop: 20 }}>
          <HeroSection doneJobs={doneJobs} projectId={project?.id} />
        </div>
      )}

      <div className="generate-bar">
        <button
          className="generate-btn"
          disabled={!photos.length || !materialIds.length || !mode || isBusy}
          onClick={generateAll}
        >
          {isBusy && <span className="spinner" />}
          {buttonLabel}
        </button>
      </div>

      {viewer && <FullscreenViewer {...viewer} onClose={() => setViewer(null)} />}
    </div>
  );
}
