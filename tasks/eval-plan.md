# Test & Eval Suite Plan (2026-07-07)

**Status: discussed and agreed in principle — NOT yet built.**
Waiting on Stephan to provide a good set of deck photos (expected 2026-07-08).
No code changes made yet. Next session: re-read this doc, collect answers to the
open questions at the bottom, then build.

## Goal

Fast, safe iteration on prompts/model/pipeline: drop a folder of input photos in,
run the whole corpus through the pipeline, inspect all outputs side by side.
Modeled on how top companies (Google etc.) do it.

## Background: the two testing worlds

The app spans two different worlds; each gets a different treatment.

**World 1 — deterministic code** (prompt assembly, catalog, PIN, watermark,
persistence). Same input → same output. Classic testing: unit tests + **golden
file testing** (a.k.a. snapshot testing):

- `testdata/` folder of input fixtures.
- Test compares actual output to a stored known-good file (the "golden").
- Mismatch = failure with a diff. Intentional change = rerun with
  `--update-goldens`, review the diff, commit new goldens. The goldens diff
  becomes part of code review — reviewers see exactly what a prompt change did.
- Highest-value golden test here: **final prompt string** for each
  (photo metadata, material, options, custom instructions, refine text) combo,
  including the hidden QUALITY_CLAUSE. Free, instant, no network.

**World 2 — generative output** (the Gemini render). Non-deterministic: same
input can yield different images. Never exact-match; teams call this
**evaluation (evals)**, not testing. Google's real-world analog is **Skia Gold**
(Chrome/Android graphics): run a fixed corpus, upload result images, humans
triage new vs. approved baseline side by side, approvals become new baselines.

The generative-AI version of that pattern:

- **Fixed eval corpus**: folder of real deck photos + a manifest saying, per
  case, which material/options/instructions to apply. Keep stable so runs are
  comparable over time. Include easy / medium / known-hard cases (weird
  lighting, partial decks, cluttered yards).
- **Batch runner**: feeds every case through the real pipeline; saves outputs
  to a timestamped run folder along with exact prompt, model, cost, latency.
- **Comparison gallery**: generated static HTML — one row per case, columns:
  input photo | baseline run | new run. Eyeball 30 cases in two minutes.
- **Optional automated judging**: second AI call scores each output ("deck
  clearly the requested material? house unchanged? artifacts? 1–5").
  LLM-as-judge is noisy per case, useful in aggregate ("prompt v2 avg 4.3,
  v3 avg 3.6 → revert").
- **Baselines / A-B**: on a prompt tweak, run corpus on old + new prompt,
  gallery shows both side by side. Prompt changes become decisions, not vibes.

Operational habits worth keeping:

- **Hermetic where possible, real where necessary.** Unit/golden tests never
  hit the network (mock Gemini) → run in seconds, could go in CI. Eval runs hit
  the real model, cost real money (~$0.04/render), and are triggered manually
  when prompts/model change — not on every commit.
- **Version everything in the run record.** Each eval run logs git commit,
  prompt text, model name — so "what changed?" is answerable weeks later.

## Proposed structure for this repo

1. `evals/corpus/` — 15–30 deck photos + `manifest.json`
   (material, options, instructions per case).
2. `evals/run.py` — batch runner hitting the render pipeline, writing a
   timestamped run folder (`evals/runs/<timestamp>/`) with images + metadata.
3. `evals/gallery.py` — builds a static HTML side-by-side gallery comparing any
   two runs (input | run A | run B); viewable on Mac or iPad.
4. `backend/tests/` — pytest golden tests for prompt construction and other
   deterministic logic, no network.
5. Later, optional: LLM-as-judge scoring appended to the gallery.

## Open questions (ask Stephan before building)

1. **Corpus source** — his own photo set (arriving ~2026-07-08), and/or pull
   real project photos already saved on the Railway volume?
2. **Cost tolerance per eval run** — 20 cases ≈ $0.80/run. Run freely, or
   support "subset"/smoke runs (e.g., 5 cases)?
3. **Where it runs** — local script against locally-run backend (safer/faster)
   vs. against the deployed Railway API (true prod path)?
4. **Human-review gallery only for now, or judge scoring too?** Recommendation:
   gallery first, judge later — gallery alone is ~80% of the speedup.

## Reminders

- Deploy rule still applies to any frontend change: `cd frontend && npm run
  build` before push (Railway serves committed `dist/`). Eval/test work is
  backend/tooling-only, so no build needed for it.
- `evals/runs/` output should be gitignored (big binaries); corpus photos are
  probably fine to commit if reasonably sized — confirm with Stephan.
