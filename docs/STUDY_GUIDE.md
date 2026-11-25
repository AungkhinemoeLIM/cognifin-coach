# Study and Evaluation Guide

## Study purpose

CogniFin Coach can support a controlled usability or behavioural study in which
participants compare coaching conditions and provide perceived-personalisation ratings.

The app provides:

- Participant-entered IDs
- Baseline, LLM, no-coach, and random coach modes
- Synthetic 20-turn sessions
- Event and mismatch detection
- 1-5 message ratings
- CSV session exports

## Suggested protocol

1. Run `python app.py` locally.
2. Assign or distribute participant IDs.
3. Set Coach to `random` for randomized assignment.
4. Ask participants to complete the quiz and 20 simulation turns.
5. Collect the participant's downloaded CSV or the matching server log.
6. Compare conditions using each participant's exported rows.

The same seed can be used in evaluation code to make exact price paths reproducible.

## Logged data

Each interaction row includes:

- Session and participant IDs
- Assigned coach mode
- Turn number
- Per-asset actions (in the `actions` JSON field) and decision duration
- Session intention, optional decision reason, and confidence rating
- Portfolio value and drawdown
- Detected event and mismatch codes
- Neutral market-context observations
- Coach source and message
- User rating
- Timestamp

The app does not contact a database and sessions remain in process memory until the
server stops.

## Offline evaluation

Run the simulated-agent evaluation:

```bash
python -m cognifin.evaluate --n 300 --out results
python -m cognifin.evaluate --extra --out results
python -m cognifin.evaluate --llm-check --out results   # needs GEMINI_API_KEY; free-tier keys hit HTTP 429 quickly
```

`--extra` includes the update-rule ablation (Bayesian vs. legacy additive) under an honest
quiz and a bias-blind-spot quiz. `--llm-check` compares the rule baseline, the offline
generator and Gemini on 24 fixed scenarios and writes `results/llm_check.json`.

This writes summaries and a simulated session CSV under `results/`.

## How to interpret evaluation results

The bundled evaluation uses synthetic personas, not human participants. Persona
responses and behavioural changes are assumed parameters used to test the pipeline's
sensitivity.

Consequently:

- Simulated "behavioural shifts" are not evidence of clinical or real-world impact.
- Ratings still need real participant data.
- Setting the personalised advantage to 1.0 can make coaches identical by construction.
- The project may demonstrate system behaviour but cannot establish coaching efficacy.

## Research limitations

- The quiz is not a validated psychometric instrument.
- Event thresholds are hand-selected heuristics.
- Price generation is synthetic and simplified.
- The adaptive profile is not independently validated.
- The prototype does not establish that coaching changes real investment decisions.
- A real study needs an ethics or institutional review, informed consent, de-identification,
  and an appropriate data-retention plan.
- Do not enter credentials or sensitive personal financial information.

## External LLM use

The optional Google AI Studio Gemini integration sends structured profile tags and live decision-event
data to the configured API. The app does not send participant names or CSV records.

Before a real study:

- Obtain required participant consent.
- Verify the API provider and data-handling terms.
- Configure the model and key only in the server environment.
- Review the API call and fallback behavior.
- Clearly label LLM and offline-generator responses in study materials.
