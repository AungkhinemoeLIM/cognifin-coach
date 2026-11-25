# CPE 663 term project — submission checklist

Presentation: **Sat 28 Nov 2026** · Paper due: **Mon 30 Nov 2026 via LEB2** (PDF only)

## Status of the remaining items

- [x] `paper/author.json` filled in (name, student ID, e-mail, repo URL); paper and slides rebuilt.
- [x] Code pushed to https://github.com/AungkhinemoeLIM/cognifin-coach (`.env` is git-ignored and was
      not committed). Make sure the repository is visible to the instructor (public, or add them).
- [ ] Optional: compile `paper/CogniFin_Coach_IEEE.tex` on Overleaf (upload the `.tex` + `figures/`,
      pdfLaTeX) for the official IEEEtran PDF. `paper/CogniFin_Coach_IEEE.pdf` is the same content in
      an IEEE-style two-column layout rendered with ReportLab, and is ready to submit as-is.
- [ ] **Live-LLM row (Table III, Fig. 6, slides 6 and 9).** At build time both Gemini models returned
      HTTP 429 (quota exhausted) on the configured key, so the paper states that this arm is pending
      and reports only verified numbers. Rechecked on 25 Nov: 0/24 responses were model-written;
      all used the offline fallback, so the live result remains pending. When API access is available, run:
      `python -m cognifin.evaluate --llm-check --out results && python paper/make_figures.py && python paper/build_paper.py && python presentation/build_slides.py`
      The check is resumable; rerun it until `written_by_model` in `results/llm_check.json` is 24, then
      commit and push the updated `results/`, `paper/` and `presentation/` files.
- [ ] Rehearse the demo with `demo/DEMO_SCRIPT.md` (or record the ≈ 2 min video it describes). If the
      API is still rate-limited in class, messages appear tagged *offline generator*; the demo works.

## Written paper (80 pts) — `paper/CogniFin_Coach_IEEE.pdf`

| Guideline requirement | Where |
|---|---|
| 6–8 pages excl. references/appendix | body ≈ 6.3 pages; references + appendix follow |
| IEEE double-column, PDF | ReportLab PDF + IEEEtran `.tex` |
| Abstract 200–250 words | 240 words (printed by `build_paper.py`) |
| Introduction: context, motivation, goals, explicit contributions | §I, RQ1–RQ4, 4 contributions |
| Related work | §II A–E (behavioural finance, dual process, user models/architectures, debiasing, grounded generation) |
| Architecture & methodology with block diagram/flowchart | §III, Fig. 1, Table I, Eq. (1)–(2), Algorithm 1 |
| Experiments: empirical analysis, baselines, metrics, results | §IV: legacy-rule ablation, rule-template baseline, no-coach control; accuracy, MAE, precision/recall, grounding, paired bootstrap CIs; Figs. 3–7, Tables II–III |
| Discussion & future work: cognitive limitations, edge cases | §V |
| Conclusion | §VI |
| References + appendix with repo link, setup, environment, commands | 28 IEEE-style references; Appendix A |

## Presentation (15 pts) — `presentation/CogniFin_Coach_Slides.pdf`

| Required slide group | Slides |
|---|---|
| Problem statement & cognitive motivation (1–2) | 2, 3 |
| System architecture & core mechanics (2–3) | 4, 5, 6 |
| Live demo / video (1–2 min) | 7 |
| Key results & evaluation (1–2) | 8, 9 |
| Lessons learned & conclusion (1) | 10 |
| 5–7 min incl. demo | ≈ 6:45 (timings in `SPEAKER_NOTES.md`, plus likely Q&A answers) |

## Demonstration (5 pts) — `demo/DEMO_SCRIPT.md`

| Key artifact | Shown by |
|---|---|
| Input & perception layer | quiz → priors with ± SD; per-asset decisions; market-context observations; event detection |
| Cognitive processing / inference | Bayesian trait bars moving with ± SD; mismatch reflection check; hasty/drawdown context; `demo/trace_demo.py` prints the posterior every turn |
| Outputs & evaluation UI | LLM/offline-tagged message, "Why this?" with estimate ± SD and citation, 1–5 rating, reflection recap, CSV export |

## Verified on this machine (25 Nov 2026)

- `python -m pytest -q tests` → 39 passed
- `python demo/trace_demo.py` completed the deterministic offline rehearsal trace
- Evaluation, extra analyses, figures, paper and slides remain built from the current code
- An earlier 24 Nov Gemini run produced valid, grounded 50–66-word messages before its quota
  was exhausted. The 25 Nov resumable check produced 0/24 model-written messages; live-LLM
  claims therefore remain pending.
