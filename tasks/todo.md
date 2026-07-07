# Deck Visualizer — 5-Feature Upgrade (2026-07-06)

Plan approved by Stephan. Order: safest first. One commit per feature.
Deploy rule: `cd frontend && npm run build` before push (Railway serves committed dist/).

- [ ] **F1 — Photo library upload**: two tiles in PhotoStrip (Take photo w/ `capture`, Photo library w/o)
- [ ] **F2 — Hidden quality boosters**: `QUALITY_CLAUSE` appended server-side in prompt_builder (render + fusion)
- [ ] **F3 — Console + Refine**: `custom_instructions` field through render pipeline; `POST /api/refine` + Refine button on result cards
- [ ] **F4 — Wizard flow**: one screen per step (Type → Photos → Materials → Options → Results), stepper nav, delete StepCard
- [ ] **F5 — Conversation recording**: RecorderPanel (MediaRecorder) → `/api/transcribe` (Gemini audio) → editable summary → merges into custom_instructions; notes saved to project
- [ ] Verify each feature locally (backend + vite preview), ~3–5 Gemini test calls
- [ ] Final: `npm run build`, commit dist, push once → Railway; smoke-check live URL

## Review
(filled in at the end)
