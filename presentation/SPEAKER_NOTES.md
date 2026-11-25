# Speaker notes — CogniFin Coach (CPE 663 class presentation, 28 Nov 2026)

Format: 5–7 min talk including the demo, then 1–3 min Q&A (10 min slot).
Deck: `presentation/CogniFin_Coach_Slides.pdf` (10 slides). Rebuild with
`python presentation/build_slides.py` after editing `paper/author.json`.

| # | Slide | Guideline section | Target time |
|---|---|---|---|
| 1 | Title | — | 0:15 |
| 2 | Investors repeat the same emotional mistakes | Problem statement | 0:35 |
| 3 | Cognitive motivation shapes every design choice | Cognitive motivation | 0:40 |
| 4 | Four-layer architecture | Architecture | 0:40 |
| 5 | A Bayesian user model that knows how sure it is | Core mechanics | 0:45 |
| 6 | Grounded coaching | Core mechanics | 0:35 |
| 7 | Live demo | Demo (1–2 min) | 1:30 |
| 8 | Results: RQ1 & RQ2 | Results | 0:40 |
| 9 | Results: RQ3 & RQ4 | Results | 0:35 |
| 10 | Lessons learned & conclusion | Lessons / conclusion | 0:30 |
| | **Total** | | **≈ 6:45** |

---

**1. Title (15 s).** "CogniFin Coach is a cognitive computing system that coaches financial
decisions. It perceives what you do, models which biases drive you and how sure it is,
and explains its reasoning."

**2. Problem (35 s).** Four biases, each with a market signature: panic selling, FOMO,
overconfidence, and loss aversion. The key number: financial-literacy training explains
about 0.1% of the variance in behaviour, and the effect fades within months. People
usually know the rule; they don't apply it in the moment. So we need something that acts
*at* the moment of decision.

**3. Cognitive motivation (40 s).** Three findings, three design responses.
(1) Under loss and time pressure, System 1 takes over, so we track drawdown and hasty
decisions as short-term context. (2) The bias blind spot: people don't see their own
biases, so the quiz alone can't be trusted. We fuse it with behaviour and flag
contradictions. (3) Metacognition: specific, personal feedback works, so every message
comes with evidence and a reflection question, never advice.

**4. Architecture (40 s).** Walk left to right. Perception: the quiz gives priors, and the
event detector turns each decision into bias events and *opportunity contexts*.
Cognition: a long-term Bayesian trait layer, a short-term context layer, a mismatch
detector, and a fixed knowledge base. Generation: an LLM writes the words behind a
validator, while code assembles "Why this?". Output: the UI and a CSV log. The user's next
decision closes the loop.

**5. Bayesian model (45 s).** Each trait is a Beta belief. The quiz is the prior, worth 24
observations; that number comes from the quiz's reliability, not from tuning. Each turn
that *allows* a bias is a trial: it either fired or was resisted. Why this matters: the
original rule added 0.15 per event, but FOMO events are 66× more common than early
profit-taking, so the old rule inflated noisy traits. The plot shows the honest
trade-off: stable, but it learns slowly.

**6. Grounded coaching (35 s).** Four steps: structured prompt → Gemini 3 Flash →
validator → labelled fallback. The right side shows a real message. Everything under
"Why this?" — the evidence, the estimate ± SD, the citation — comes from code, so it can't
be hallucinated.

**7. Demo (90 s).** See `demo/DEMO_SCRIPT.md`. Open `http://localhost:8000/?seed=42`.
- *Input & perception:* answer the quiz claiming you're calm and ignore trends; show the
  trait bars with ± SD.
- *Inference:* chase the TECH rally → buy-after-rise observation + FOMO event + reflection
  check. Then, in the crash, sell TECH quickly → panic event, hasty flag, mismatch, and
  the trait bar moves.
- *Output:* LLM tag, open "Why this?", rate the message, finish, show the recap and download
  the CSV.

Backup: `python demo/trace_demo.py` (or `--llm`), or the recorded video.

**8. Results RQ1–2 (40 s).** With an honest quiz, behaviour doesn't hurt (0.797 vs
0.790), whereas the legacy rule dropped accuracy to 0.720. When the quiz under-reports
bias, behaviour helps: 0.730 vs 0.717, with lower error. The mismatch detector has 0.91
recall at 0.64 precision; requiring two flagged turns raises precision to 0.74.

**9. Results RQ3–4 (35 s).** On the same 24 scenarios, LLM messages cite the user's own
numbers and use the mismatch; rule templates never do. In the sensitivity analysis,
personalisation reduces bias events only if it is heeded more often; at equal heed
the two coaches are identical by construction. **Say the caveat aloud:** these are
simulated personas, not people.

**10. Lessons (30 s).** Count opportunities, not events. Silent fallbacks hide failures:
the old token cap meant the "LLM" coach was usually the template. Separate facts from
fluency. And a trustworthy prior learns slowly. Next step: a randomised study, which is
already built into the app. Thank you.

---

## Likely Q&A

- **"Isn't the evaluation circular?"** Partly, yes, and the paper says so. Personas share
  the detectors' constructs, so RQ1–2 check internal coherence and RQ4 is a sensitivity
  analysis. That's why the app logs 1–5 ratings and supports random assignment for a human
  study.
- **"Why n0 = 24?"** Three Likert items with noise ≈ 0.17 give a standard error ≈ 0.10.
  A Beta prior with SD 0.10 at mean 0.5 has a + b ≈ 24.
- **"Why is overconfidence confirm-only?"** There is no well-defined moment where you
  "resisted" overconfidence. Counting every turn as a trial made the estimate collapse
  towards zero.
- **"What if the LLM gives advice?"** The prompt forbids it, the validator rejects
  forbidden phrases, and the fallback is labelled. The validator is lexical; entailment
  checks are future work.
- **"Why a cooldown on messages?"** Repeating the same prompt every turn habituates the
  user (alert fatigue). Events are still logged and still update the model.
- **"Is the 4-second threshold meaningful?"** It's a crude System-1 proxy. Per-user
  latency baselines are future work.
