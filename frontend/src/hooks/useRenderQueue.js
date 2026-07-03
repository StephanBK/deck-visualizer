import { useCallback, useRef } from "react";
import { compressImage, renderPhoto, AuthError } from "../api.js";

// Render jobs are (photo × material) pairs. The queue runs two at a time,
// drops to one if Gemini rate-limits (429), retries each job once on a
// retryable failure, and supports cancel via AbortController.
export function useRenderQueue(setJobs) {
  const queueRef = useRef([]);
  const runningRef = useRef(0);
  const concurrencyRef = useRef(2);
  const abortersRef = useRef(new Map()); // jobId -> AbortController

  const update = useCallback(
    (id, patch) => setJobs((prev) => prev.map((j) => (j.id === id ? { ...j, ...patch } : j))),
    [setJobs]
  );

  const runJob = useCallback(async (item) => {
    const { job, settings } = item;
    const aborter = new AbortController();
    abortersRef.current.set(job.id, aborter);
    update(job.id, { status: "rendering", startedAt: Date.now(), error: null });
    try {
      const file = await compressImage(job.photo.file);
      const result = await renderPhoto(
        file,
        { ...settings, materialId: job.materialId },
        aborter.signal
      );
      update(job.id, {
        status: "done",
        afterUrl: result.after_url,
        resultName: result.after_url.split("/").pop(),
        error: null,
      });
    } catch (e) {
      if (e.name === "AbortError") {
        update(job.id, { status: "canceled", error: null });
      } else if (e instanceof AuthError) {
        update(job.id, { status: "error", error: "Session expired — reload and re-enter the PIN." });
      } else {
        const retryable = e.status === 429 || e.status === 502 || e.status === undefined;
        if (e.status === 429) concurrencyRef.current = 1; // ease off Gemini
        if (retryable && !item.retried) {
          await new Promise((r) => setTimeout(r, 2000));
          queueRef.current.unshift({ ...item, retried: true });
          update(job.id, { status: "queued" });
        } else {
          update(job.id, { status: "error", error: e.message });
        }
      }
    } finally {
      abortersRef.current.delete(job.id);
    }
  }, [update]);

  const pump = useCallback(() => {
    while (runningRef.current < concurrencyRef.current && queueRef.current.length) {
      const item = queueRef.current.shift();
      runningRef.current += 1;
      runJob(item).finally(() => {
        runningRef.current -= 1;
        pump();
      });
    }
  }, [runJob]);

  const enqueue = useCallback(
    (jobs, settings) => {
      for (const job of jobs) {
        update(job.id, { status: "queued", error: null, afterUrl: null, resultName: null });
        queueRef.current.push({ job, settings, retried: false });
      }
      pump();
    },
    [pump, update]
  );

  const cancel = useCallback(
    (jobId) => {
      queueRef.current = queueRef.current.filter((it) => it.job.id !== jobId);
      const aborter = abortersRef.current.get(jobId);
      if (aborter) aborter.abort();
      else update(jobId, { status: "canceled" });
    },
    [update]
  );

  return { enqueue, cancel };
}
