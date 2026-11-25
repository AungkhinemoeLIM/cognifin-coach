# Demonstration script (5 points) — live or pre-recorded, 90–120 s

The guidelines ask the demo to show three artifacts. Each step below is tagged with the
one it covers: **[A] Input & Perception**, **[B] Cognitive Processing / Inference**,
**[C] Outputs & Evaluation UI**.

## Before class (5 min)

```bash
cd cognifin_coach
python -m pytest -q tests            # expect: 39 passed
python app.py                        # "CogniFin Coach running at http://localhost:8000 (LLM: Google AI Studio)"
```

- Open **http://localhost:8000/?seed=42**. The seed fixes the price path, so the rally and
  crash happen at the same turns as in rehearsal.
- If the header tag says *offline generator*, the API key is missing or the quota is used
  up. The demo still works, and messages are labelled as offline.
- Free-tier Gemini keys are rate-limited (HTTP 429 after a few quick calls), so don't run
  `--llm-check` just before presenting.
- Delete `profiles/DEMO.json` if it exists, so the demo starts from a fresh prior.

## Live script

| Time | Do | Say | Artifact |
|---|---|---|---|
| 0:00 | Participant ID `DEMO`, Coach = *LLM coach*, intention "pause before reacting to a drop" | "This is the profiling quiz: 15 items, four traits plus three self-claims." | A |
| 0:10 | Answer: **sr1 = 5, sr2 = 5** (risk-tolerant, calm), **hf3 = 5, hf2 = 1** (ignore trends), others neutral. Start. | "I claim to be calm and immune to trends. The trait bars are the prior; the ± is how unsure the model is." | A |
| 0:25 | Turn 1: buy INDEX 40%, TECH 20%. Note the allocation preview. | "One decision per asset; buys come from starting cash." | A |
| 0:35 | Hold until TECH has rallied (turns 4–6), then buy TECH 60% **quickly**. | "A ~20% three-turn run-up: perception logs a buy-after-rise, the detector fires a FOMO event, and the mismatch detector catches my 'ignore trends' claim." | A → B |
| 0:55 | Point at the **reflection check** and the herding bar moving. | "The Bayesian layer counted one fired opportunity, and the bar moved." | B |
| 1:05 | Hold into the crash (turns 12–13), then **sell all TECH within ~2 s**. | "Panic sale below cost, decided in two seconds during a 20% drawdown. That's hasty plus stress context, and it contradicts both self-claims." | B |
| 1:20 | Read the coach message (tag **LLM**). Open **“Why might this pattern apply?”**. | "The LLM wrote these words. Everything in this panel — evidence, estimate ± SD, citation, reflection question — comes from code, not the model." | C |
| 1:35 | Rate the message 4/5. Hold through the remaining turns (submit quickly) and show the **Reflection recap**. | "Ratings are the perceived-personalisation measure for a human study." | C |
| 1:45 | Click **Download session log (CSV)**. | "Every turn is logged: events, mismatches, coach source, rating." | C |

## Backup if the network or API fails

```bash
python demo/trace_demo.py          # offline; prints perception -> inference -> output per turn
python demo/trace_demo.py --llm    # same with Gemini messages (needs GEMINI_API_KEY)
```

The trace uses the same seed and script: FOMO buy on turn 6, panic sale on turn 13, then
hold-loser on INDEX. It shows the posterior (mean ± SD) for every trait after each turn,
which is the clearest view of the inference step.

## Recording a video instead (allowed by the guidelines)

Use the macOS screenshot toolbar (Shift-Cmd-5 → *Record Selected Portion*). Record the
browser at 1280×800 following the table above (≈ 2 min), then export to MP4. Save it as
`demo/CogniFin_Coach_demo.mp4` and link it from the slides if needed.
