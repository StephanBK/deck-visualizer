# Deck Visualizer — 5-Feature Upgrade (2026-07-06)

Plan approved by Stephan. Order: safest first. One commit per feature.
Deploy rule: `cd frontend && npm run build` before push (Railway serves committed dist/).

- [x] **F1 — Photo library upload**: two tiles in PhotoStrip (Take photo w/ `capture`, Photo library w/o) — 6ee8aa6
- [x] **F2 — Hidden quality boosters**: `QUALITY_CLAUSE` appended server-side in prompt_builder (render + fusion) — 0d0fde4
- [x] **F3 — Console + Refine**: `custom_instructions` field through render pipeline; `POST /api/refine` + refine row on result cards — 399fc45
- [x] **F4 — Wizard flow**: one screen per step (Type → Photos → Materials → Options → Results), stepper nav, deleted StepCard — 686371c
- [x] **F5 — Conversation recording**: RecorderPanel (MediaRecorder) → `/api/transcribe` (Gemini audio) → editable review → merges into custom_instructions; notes saved to project — 93c8bf7
- [x] Verify each feature locally (backend + vite preview): 4 Gemini calls (~$0.16)
- [x] Final: `npm run build`, commit dist, push once → Railway; smoke-check live URL

## Review (2026-07-06)

All five features implemented and verified locally against the real backend:
- Library input confirmed to have no `capture` attr; camera input keeps it.
- Quality clause verified in all 3 modes + fusion via `python3 render/prompt_builder.py`.
- `/api/render` with custom_instructions and `/api/refine` exercised with real
  Gemini calls — the refine request ("boards diagonal", "add olive trees")
  visibly applied while everything else held still.
- Wizard clicked through end-to-end in the preview browser incl. back-nav,
  dot-jumping, and state preservation.
- `/api/transcribe` tested with synthesized speech (`say`): verbatim transcript
  + clean preference extraction ("warm brown tone", "non-slippery for dog", …).

**Manual check left for Stephan (needs the real iPad):** mic permission prompt
+ an actual recording through the Record button; everything downstream of the
audio blob is verified.
