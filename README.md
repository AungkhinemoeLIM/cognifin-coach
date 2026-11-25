# CogniFin Coach

A cognitive-profile-aware financial decision coaching system (CPE 663 Cognitive Computing
term project). A short quiz profiles four decision biases. A turn-based investing simulation
then runs on **synthetic prices** (no real money, no real data), and an AI coach explains
which bias likely drove each decision. A "Why this?" panel shows the evidence, and the coach
flags places where the quiz and the actual play disagree.

## Submission deliverables (CPE 663 guidelines)

| Deliverable | File(s) |
|---|---|
| Written paper (80 pts), IEEE double-column PDF | [`paper/CogniFin_Coach_IEEE.pdf`](paper/CogniFin_Coach_IEEE.pdf), with IEEEtran LaTeX source [`paper/CogniFin_Coach_IEEE.tex`](paper/CogniFin_Coach_IEEE.tex) and [`paper/figures/`](paper/figures/) |
| Presentation (15 pts), 10 slides, ≈ 6:45 | [`presentation/CogniFin_Coach_Slides.pdf`](presentation/CogniFin_Coach_Slides.pdf), [`presentation/SPEAKER_NOTES.md`](presentation/SPEAKER_NOTES.md) |
| Demonstration (5 pts) | `python app.py` → `http://localhost:8000/?seed=42`; [`demo/DEMO_SCRIPT.md`](demo/DEMO_SCRIPT.md); backup [`demo/trace_demo.py`](demo/trace_demo.py) |
| Code repository + setup (paper appendix) | this repository; see *Run* below |

See [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md) for the guideline-by-guideline
checklist and the items you still need to fill in (name, student ID, repo URL).

## Requirements

- Python 3.9+ (tested on 3.13). **The demo needs no third-party packages.**
- `pytest` to run the tests and `matplotlib` + `reportlab` to rebuild the figures, paper and
  slides (`pip install -r requirements.txt`).
- Optional: a Google AI Studio API key for the Gemini coach.

## Run the demo

```bash
python app.py                      # then open http://localhost:8000  (add ?seed=42 for a repeatable path)
# optional Google AI Studio Gemini coach
echo 'GEMINI_API_KEY=your-api-key' > .env
echo 'COGNIFIN_MODEL=gemini-3-flash-preview' >> .env   # optional, this is the default
echo 'COGNIFIN_THINKING_LEVEL=low' >> .env             # optional; "default" sends no thinking config
echo 'COGNIFIN_FALLBACK_MODEL=gemini-3.8-flash' >> .env  # optional; tried when the primary is rate-limited/overloaded ("none" disables)
python app.py
```

Without an API key, the coach uses an **offline structured generator**. It fills
profile- and event-conditioned text from the same inputs the LLM would receive. Each coach
message is tagged `LLM` or `offline generator` in the UI and in the CSV log, so the two can't
be confused. The offline generator is also used when an API call fails or the validator
rejects the output. Rejected output is a reply that was cut off (finish reason not `STOP`),
is too long, or contains predictions, "guarantee", or "you should buy".

Demo flow: quiz with an optional learning intention, then a 20-turn simulation with a
separate decision for each asset and an allocation preview. Each turn has an optional
reason/confidence reflection, and the market runs a scripted rally, minor dip, crash and
recovery. The coach responds with tentative prompts and neutral market-context
observations, and the session ends with a reflection recap and CSV export.
Coach modes: `llm`, `baseline` (static rule templates), `none` (control), and `random`
(random assignment for a study; the arm is logged).

## Run the tests, evaluation, figures, paper and slides

```bash
python -m pytest -q tests                              # 39 tests
python -m cognifin.evaluate --n 300 --out results      # results/eval_summary.json + eval_sessions.csv
python -m cognifin.evaluate --extra --out results      # threshold sweep, estimation variants, update-rule ablation
python -m cognifin.evaluate --llm-check --out results  # baseline / offline / Gemini on 24 fixed scenarios (uses API quota)
python paper/make_figures.py                           # paper/figures/*.pdf|png
python paper/build_paper.py                            # paper/CogniFin_Coach_IEEE.{tex,pdf}
python presentation/build_slides.py                    # presentation/CogniFin_Coach_Slides.pdf
python demo/trace_demo.py                              # terminal trace: perception -> inference -> output
```

## Architecture

| Module | Role |
|---|---|
| `cognifin/quiz.py` | 15-item Likert profiling quiz -> 4 trait scores + 3 self-report claims |
| `cognifin/simulator.py` | Synthetic prices, portfolio, 6 behavioural events + 3 opportunity contexts (`dip`, `rally`, `loser`) |
| `cognifin/user_model.py` | Dual-layer model. **Long-term:** a Beta–Bernoulli belief per trait (quiz prior worth n0 = 24 observations, updated by fired vs. resisted opportunities, posterior mean ± SD, evidence carried across sessions at 0.5). **Short-term:** drawdown, decision speed (System-1 proxy), recent events |
| `cognifin/mismatch.py` | Grounds self-report against behaviour (bias blind spot), e.g. "comfortable with risk" vs. a panic sale |
| `cognifin/knowledge.py` | Trait -> research finding -> citation table; the source of the "Why this?" panel |
| `cognifin/coach_baseline.py` | Baseline: static templates that ignore the profile |
| `cognifin/coach_llm.py` | Prompt builder, Gemini call (thinking level, finish-reason check), validator, offline fallback, "Why this?" |
| `cognifin/session.py` | Orchestration, coaching cooldown (no repeat of the same event/asset within 3 turns), CSV logs |
| `cognifin/agents.py`, `evaluate.py` | Simulated personas (incl. a bias-blind-spot quiz condition) and the evaluation harness |
| `app.py`, `static/index.html` | Local web demo |

Design choice: the LLM writes only the message text. The trait, evidence, estimate ± SD,
research finding and citation in "Why this?" come from code and `knowledge.py`, so the
explanation panel cannot hallucinate a citation.

## Evaluation results (300 simulated personas)

| Question | Result |
|---|---|
| RQ1 trait estimation (top-trait accuracy) | quiz 0.790 → Bayesian 0.797 (legacy additive rule: 0.720). With a blind-spot quiz: 0.717 → 0.730 (legacy 0.657) |
| RQ2 mismatch detection | recall 0.91, precision 0.64, FPR 0.34. Requiring ≥ 2 flagged turns: precision 0.74, FPR 0.12 |
| RQ3 message grounding (24 scenarios) | rule templates cite the user's numbers 0% of the time; offline generator 83%, with every supplied mismatch used. The live LLM arm is still pending: the 25 Nov recheck produced 0/24 model-written messages (all used offline fallback); rerun `--llm-check` when API access is available |
| RQ4 shift (assumed heed) | identical at ρ = 1 by construction; Δ = 0.33 [0.18, 0.49] at ρ = 1.5 and 0.75 [0.53, 0.99] at ρ = 2 |

## Audit log (QA pass before submission)

1. `evaluate.py` counted the logged string `"none"` as a mismatch flag, so 100% of sessions
   were "flagged". The results files in the repo were stale and could not be reproduced. **Fixed**.
2. Mismatch ground truth covers only panic-related claims, but it was scored against all
   five codes. **Fixed**: scored against the two panic codes, with the any-code share reported separately.
3. The grounding check counted the placeholder "No behavioural pattern…" as a coach message. **Fixed**.
4. Gemini 3 thinking tokens (~510–590 per reply even at `low`) count against
   `maxOutputTokens`. The old 220-token cap produced empty or truncated replies, so the
   "LLM" coach silently fell back to the template. **Fixed**: thinking level `low`,
   1,024 tokens, finish-reason check, and thought parts skipped.
5. The additive trait update (+0.15 per event) ignored opportunities. It *lowered* top-trait
   accuracy below the quiz (0.790 → 0.720) because FOMO events are ~60× more frequent than
   early profit-taking. **Replaced** with the Beta–Bernoulli model; an ablation is in `--extra`.
6. The "losses hurt about twice as much" claim cited Kahneman & Tversky (1979). The 2.25
   coefficient comes from Tversky & Kahneman (1992). **Added**, together with Shefrin &
   Statman (1985) for the disposition effect and Pronin et al. (2002) for the blind spot.
7. Identical prompts repeated every turn (e.g. hold-loser). **Added** a 3-turn cooldown per
   (event, asset); events are still logged and still update the model.
8. The README said "CPE 633". **Fixed** to CPE 663.
9. Transient Gemini errors (HTTP 429/503 "high demand") went straight to the fallback.
   **Added** one retry after 1.5 s, then a second model (`gemini-3.8-flash`, which has a
   separate quota), before falling back. The model that answered is recorded.
10. `--llm-check` reported fallback text as "LLM" output. **Fixed**: the check is resumable
    (it keeps model-written messages and calls the API only for missing ones), and the LLM
    row covers model-written messages only.

## Known limitations (stated in the paper)

- The quiz items are short statements written for this prototype, **not a validated
  psychometric instrument**. A single item takes only 5 values, so claim cut-offs of 0.6
  and 0.7 behave identically.
- Behavioural event rules (5% drop, 10% run-up, 70% concentration, 4 s) are hand-set
  heuristics, not calibrated on human data. Each event maps to one trait.
- **The evaluation in `results/` uses simulated personas, not people.** The personas share
  the detectors' constructs, so detection results are optimistic. Their reaction to coaching
  is an assumed parameter, so the "behavioural shift" numbers are a sensitivity analysis.
  Perceived-personalisation ratings can only come from real participants; the UI already
  collects them (1–5 per message) and logs them to CSV.
- The Bayesian prior (n0 = 24) makes the profile stable but slow to move within a 20-turn
  session. Overconfidence receives confirming evidence only.
- A "Mainali & Weber (2025)" reference mentioned in an earlier draft could not be verified
  and is **not** cited. Add it to `paper/content.py` only with a full, checked reference.

## Study protocol (for real participants)

1. Run `python app.py`, set Coach = `random`, and give each participant an ID.
2. After each session, download the CSV (also saved in `logs/session_<id>.csv`).
3. Compare the ratings (`user_rating`), mistakes per turn (`event_types`) and mismatch
   flags (`mismatch_codes`) between `coach_mode` = `baseline` and `llm`.

## Documentation

- [User guide](docs/USER_GUIDE.md): quiz, simulation, coach modes, and CSV export
- [System overview](docs/SYSTEM_OVERVIEW.md): components, data flow, and behavioural detection
- [API reference](docs/API.md): HTTP routes and JSON shapes
- [Study and evaluation guide](docs/STUDY_GUIDE.md): experiment setup and limitations
