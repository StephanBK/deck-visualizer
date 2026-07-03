import { useCallback, useRef } from "react";
import { compressImage, renderPhoto } from "../api.js";

// Renders take 10-30s each; two at a time keeps the queue moving without
// tripping Gemini rate limits. If 429s ever show up, drop this to 1.
const CONCURRENCY = 2;

// A tiny promise queue with per-photo status updates. Each photo goes
// queued -> rendering -> done | error, written back via setPhotos so the
// gallery re-renders as results land.
export function useRenderQueue(setPhotos) {
  const queueRef = useRef([]);
  const runningRef = useRef(0);

  const update = useCallback(
    (id, patch) =>
      setPhotos((prev) => prev.map((p) => (p.id === id ? { ...p, ...patch } : p))),
    [setPhotos]
  );

  const pump = useCallback(() => {
    while (runningRef.current < CONCURRENCY && queueRef.current.length) {
      const { photo, settings } = queueRef.current.shift();
      runningRef.current += 1;
      update(photo.id, { status: "rendering" });
      (async () => {
        try {
          const file = await compressImage(photo.file);
          const result = await renderPhoto(file, settings);
          update(photo.id, {
            status: "done",
            afterUrl: result.after_url,
            resultName: result.after_url.split("/").pop(),
            materialName: result.material?.name,
            error: null,
          });
        } catch (e) {
          update(photo.id, { status: "error", error: e.message });
        } finally {
          runningRef.current -= 1;
          pump();
        }
      })();
    }
  }, [update]);

  const enqueue = useCallback(
    (photos, settings) => {
      for (const photo of photos) {
        update(photo.id, { status: "queued", error: null, afterUrl: null, resultName: null });
        queueRef.current.push({ photo, settings });
      }
      pump();
    },
    [pump, update]
  );

  return { enqueue };
}
