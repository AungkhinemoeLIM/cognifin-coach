# CogniFin Coach User Guide

## Purpose

CogniFin Coach is a browser-based financial-decision simulation for exploring
cognitive biases. It does not provide real investment advice and does not use real
money or real market data.

Each session has two parts:

1. A 15-item profile quiz.
2. A 20-turn investment simulation using three synthetic assets.

The app observes decisions, identifies a limited set of behavioural patterns, and can
offer a coaching explanation.

## Before starting

Start the local server:

```bash
python app.py
```

Open <http://localhost:8000>. Enter a participant ID and select a coach mode.
You may also enter a short session intention, such as “pause before reacting to a price
drop.” Avoid personal financial details.

## Profile quiz

The quiz asks participants to rate statements from 1 (strongly disagree) to 5
(strongly agree). Neutral value 3 is selected by default.

The app derives scores for:

- Loss aversion
- Overconfidence
- Herding / FOMO
- Panic selling

It also records three self-report measures used to compare stated beliefs with actual
behaviour:

- Comfort with high-risk investments
- Calmness during losses
- Frequency of changing investments

Items with reversed wording are scored in the opposite direction. Missing answers are
treated as neutral.

**Important:** the quiz is a prototype and is not a validated psychometric instrument.

## Playing the simulation

The participant starts with $10,000 in cash and can trade:

- **Steady Bond**: low expected movement and low synthetic volatility
- **Broad Index**: moderate expected movement and volatility
- **Hot Tech Fund**: higher expected movement and volatility

For each turn, choose an action independently for each asset:

- **Buy**: allocate a percentage of the cash available at the start of the turn
- **Sell**: sell a percentage of that asset's existing holding
- **Hold**: make no trade

The three buy allocations together cannot exceed 100% of starting cash. Sell percentages
apply separately to each asset's holding. After all three decisions are confirmed, the
app applies them, advances one turn, and shows the updated value, cash, holdings, prices,
and return.

The allocation preview estimates the portfolio mix if you confirm those actions. The
optional quick reflection records a reason for your choices and, if you opt in, a 1-5
confidence rating. Skip either whenever you prefer; these are learning notes, not scores.
When a notable market move coincides with a decision, the coach panel may also show a
neutral context observation—for example, a buy after a recent rise. This is not a claim
about your motive or a bias diagnosis.

The deterministic seed of a session produces the same set of market phases and scripted
shocks: an early rally, a minor dip, a crash, and a recovery. These synthetic shocks
make comparable patterns available across sessions.

## Coach modes

The quiz screen provides four modes:

- **LLM coach**: uses a configured Google AI Studio Gemini API key when available. The interface
  explicitly labels responses as `LLM` or `offline generator`.
- **Baseline**: shows fixed templates that do not use the participant profile.
- **No coach**: omits coaching for a control condition.
- **Random**: randomly assigns the session to baseline or LLM and logs the resulting
  mode.

With no API key, or when an API request or validation fails, the app uses the offline
structured generator.

## Why this?

In LLM mode, a coaching message may include a **Why this?** panel. Expand it to see:

- The exact evidence the detector used and the threshold-based pattern hypothesis
- A definition of the concept and how it can relate to the observed decision
- Quiz and adaptive profile estimates, explicitly described as heuristics rather than
  probabilities or diagnoses
- Supporting research and citations, plus short-term session context
- Any quiz-versus-behaviour mismatch and a question for personal reflection
- What the rule cannot infer, including the participant's motive or a stable tendency

The explanation's trait, research, and citation are assembled from the app's knowledge
base. The language model writes the natural-language message only. The explanation is a
transparent rule-based interpretation of synthetic decisions, not personalized financial
advice.
Detected patterns are tentative reflections based on prototype rules, not diagnoses or
investment advice.

## Ratings

After a coach message, participants can rate it from 1 to 5. The rating answers whether
the message matches how they were thinking. Ratings are stored in memory for the active
session and in the exported CSV.

## Exporting the session

At the end of 20 turns, use **Download session log (CSV)**. The server also writes:

```text
logs/session_<session-id>.csv
```

The log records actions, timing, portfolio value, drawdown, detected events, mismatch
flags, coach source, coach text, and participant ratings.

If a turn does not meet any behavioural-event rule, the coach does not generate a message
for that turn. In the CSV this is shown explicitly as `event_types=none` and
`coach_source=not_triggered`; the Gemini API can be connected while no coach message is
needed. In no-coach mode, `coach_source=disabled`.

The completion screen includes a process-focused recap of the intention, actions by asset,
strict rule-based bias signals, neutral market-context observations, and recorded
reflections. The simulated portfolio return is shown as an outcome, not a measure of
decision quality.
