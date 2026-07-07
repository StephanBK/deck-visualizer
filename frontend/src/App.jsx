import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchMaterials, refineResult, AuthError } from "./api.js";
import { useRenderQueue } from "./hooks/useRenderQueue.js";
import { WizardNav, WizardFooter } from "./components/Wizard.jsx";
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
  const [customPrompt, setCustomPrompt] = useState("");
  const [wizStep, setWizStep] = useState("type");
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

  function goStep(id) {
    setWizStep(id);
    window.scrollTo({ top: 0 });
  }

  function pickType(id) {
    setMode(id);
    goStep("photos"); // advance the conversation
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

  const settings = { mode, declutter, stageFurniture, customPrompt, projectId: project?.id };

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
    enqueue(specs, settings);
    goStep("results");
  }

  // Refine jobs run outside useRenderQueue: one direct call per tweak. The
  // "only update while still rendering" guard keeps a Cancel tap final even
  // though the fetch itself isn't aborted.
  async function runRefine(refJob) {
    setJobs((prev) =>
      prev.some((j) => j.id === refJob.id)
        ? prev.map((j) => (j.id === refJob.id
            ? { ...refJob, status: "rendering", startedAt: Date.now(), error: null, afterUrl: null }
            : j))
        : [...prev, { ...refJob, status: "rendering", startedAt: Date.now() }]
    );
    const patch = (p) =>
      setJobs((prev) => prev.map((j) => (j.id === refJob.id && j.status === "rendering" ? { ...j, ...p } : j)));
    try {
      const result = await refineResult(refJob.sourceResultName, refJob.refineInstruction, project?.id);
      patch({ status: "done", afterUrl: result.after_url, resultName: result.after_url.split("/").pop() });
    } catch (e) {
      patch({ status: "error", error: e.message });
    }
  }

  function refineJob(job, instruction) {
    runRefine({
      ...job,
      id: `${job.id}:r${nextId++}`,
      kind: "refine",
      sourceResultName: job.resultName,
      refineInstruction: instruction,
      materialName: `${job.materialName} · refined`,
      afterUrl: null,
      resultName: null,
      error: null,
    });
  }

  function retryJob(job) {
    if (job.kind === "refine") runRefine(job);
    else enqueue([job], settings);
  }

  const busyCount = jobs.filter((j) => j.status === "queued" || j.status === "rendering").length;
  const doneJobs = jobs.filter((j) => j.status === "done");
  const isBusy = busyCount > 0;
  const totalJobs = photos.length * materialIds.length;

  // "valid" drives both the ✓ badge and how far ahead the dots unlock.
  // Options has nothing required, so it only reads done once a run happened.
  const wizValid = {
    type: !!mode,
    photos: photos.length > 0,
    material: materialIds.length > 0,
    options: jobs.length > 0,
    results: jobs.length > 0,
  };

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

      <WizardNav step={wizStep} valid={wizValid} onJump={goStep} />

      {wizStep === "type" && (
        <section className="wiz-screen">
          <h2 className="wiz-title">What kind of project is this?</h2>
          <ModeSelector mode={mode} onChange={pickType} />
        </section>
      )}

      {wizStep === "photos" && (
        <section className="wiz-screen">
          <h2 className="wiz-title">{projectType ? projectType.photoTitle : "Photos"}</h2>
          <p className="photo-hint">
            {projectType ? projectType.photoHint : "Snap or add one or more photos."}
          </p>
          <PhotoStrip photos={photos} onAdd={addPhotos} onRemove={removePhoto} />
        </section>
      )}

      {wizStep === "material" && (
        <section className="wiz-screen">
          <h2 className="wiz-title">Pick materials</h2>
          <p className="photo-hint">Choose up to {MAX_MATERIALS} to compare side by side.</p>
          <MaterialPicker
            materials={materials}
            selectedIds={materialIds}
            onToggle={toggleMaterial}
            favorites={favorites}
            recents={recents}
            onToggleFav={toggleFav}
          />
        </section>
      )}

      {wizStep === "options" && (
        <section className="wiz-screen">
          <h2 className="wiz-title">Finishing touches</h2>
          <p className="wiz-recap">
            {projectType?.icon} {projectType?.name} · {photos.length} photo{photos.length > 1 ? "s" : ""} ·{" "}
            {selectedMaterials.map((m) => m.name).join(", ")}
          </p>
          <Toggles
            declutter={declutter}
            stageFurniture={stageFurniture}
            onDeclutter={setDeclutter}
            onStage={setStageFurniture}
          />
          <label className="custom-prompt-label" htmlFor="custom-prompt">
            Special requests <span className="optional">optional</span>
          </label>
          <textarea
            id="custom-prompt"
            className="custom-prompt"
            rows={2}
            maxLength={500}
            placeholder='e.g. "keep the grill where it is", "darker railing"'
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
          />
        </section>
      )}

      {wizStep === "results" && (
        <section className="wiz-screen">
          <div className="results-title">Results</div>
          <ResultsGallery
            photos={photos}
            jobs={jobs}
            onRetry={retryJob}
            onCancel={cancel}
            onRefine={refineJob}
            onOpenViewer={(job) =>
              setViewer({ beforeSrc: job.photo.previewUrl, afterSrc: job.afterUrl, label: job.materialName })
            }
          />
          {doneJobs.length > 0 && !isBusy && (
            <div style={{ marginTop: 20 }}>
              <HeroSection doneJobs={doneJobs} projectId={project?.id} />
            </div>
          )}
        </section>
      )}

      <WizardFooter
        onBack={
          {
            type: null,
            photos: () => goStep("type"),
            material: () => goStep("photos"),
            options: () => goStep("material"),
            results: () => goStep("options"),
          }[wizStep]
        }
        backLabel={wizStep === "results" ? "← Adjust" : "← Back"}
      >
        {wizStep === "type" && (
          <button className="generate-btn" disabled={!mode} onClick={() => goStep("photos")}>
            Next: photos →
          </button>
        )}
        {wizStep === "photos" && (
          <button className="generate-btn" disabled={!photos.length} onClick={() => goStep("material")}>
            Next: materials →
          </button>
        )}
        {wizStep === "material" && (
          <button className="generate-btn" disabled={!materialIds.length} onClick={() => goStep("options")}>
            Next: options →
          </button>
        )}
        {(wizStep === "options" || wizStep === "results") && (
          <button
            className="generate-btn"
            disabled={!photos.length || !materialIds.length || !mode || isBusy}
            onClick={generateAll}
          >
            {isBusy && <span className="spinner" />}
            {buttonLabel}
          </button>
        )}
      </WizardFooter>

      {viewer && <FullscreenViewer {...viewer} onClose={() => setViewer(null)} />}
    </div>
  );
}
