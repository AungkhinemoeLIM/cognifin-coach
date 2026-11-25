# CogniFin Coach System Overview

## Runtime architecture

The app is a standard-library Python HTTP server with a static browser interface.

```text
Browser UI
  -> app.py HTTP routes
  -> Session
       -> quiz scoring
       -> synthetic simulator
       -> adaptive user model
       -> mismatch detector
       -> neutral market-context observations
       -> coach selector
  -> in-memory sessions
  -> optional CSV export
```

## Main components

### `app.py`

Defines the local HTTP server and routes. It serves the browser page, creates sessions,
accepts decisions and ratings, and exports session logs.

### `cognifin/quiz.py`

Contains the 15 quiz items and scores them into four trait values and three self-report
values. Answers are normalized to a 0-1 scale. Neutral 3 answers are used when a value
is absent.

### `cognifin/simulator.py`

Generates synthetic prices, maintains cash and holdings, calculates portfolio values,
and detects behavioural events. It contains no real market data.

The main market shocks are scripted at turns 3-5, 8, 12-13, and 15-16. Random noise
within a controlled asset model remains seed-dependent.

### `cognifin/user_model.py`

Maintains two profile layers:

- **Quiz traits**: initial scores derived from the quiz
- **Long-term adaptive scores**: one Beta–Bernoulli belief per trait. The quiz score is the
  prior mean with a strength of 24 pseudo-observations (derived from the quiz's ~0.10
  standard error). Each turn that offers an opportunity for a trait (`dip` → panic selling,
  `rally` with cash → herding/FOMO, `loser` held → loss aversion) is a trial: the bias
  fired or was resisted. Overconfidence receives confirming evidence only. The posterior
  mean is the estimate and the posterior SD its uncertainty (shown as ± in the UI and in
  "Why this?"). Evidence is carried to the next session with a factor of 0.5.
- **Short-term context**: decision speed, recent drawdown, and recent events

The adaptive profile is optional and persisted by user ID in `profiles/` after a
completed session.

### `cognifin/mismatch.py`

Compares quiz or self-report claims with observed behaviour. Examples include claiming
to ignore trends and then buying a rapidly rising asset, or claiming to be calm under
loss and then panic-selling.

### `cognifin/knowledge.py`

Provides deterministic definitions, research findings, and citations for the four traits.
This knowledge base is the source of the "Why this?" panel.

### Coach modules

- `coach_baseline.py` supplies fixed rule templates.
- `coach_llm.py` assembles a structured prompt, calls Google AI Studio Gemini when configured,
  validates the response, and falls back to a deterministic offline generator.

The LLM is not allowed to construct citations for "Why this?". Its response is validated
for length and prohibited language before use.

### `cognifin/session.py`

Coordinates one complete session, applies player actions, aggregates detected events and
mismatches, invokes coaching, records logs, and saves the adaptive profile.

## Turn data flow

1. The server receives one action per asset, the optional reason/confidence reflection,
   and total decision duration.
2. The simulator detects relevant events from the visible turn, prior turns, and each
   asset-specific action.
3. Buy allocations are drawn from the cash available at the start of the turn; combined
   buy allocations are limited to that amount. Sells apply independently per holding.
   The portfolio is then updated for all three assets.
4. Portfolio drawdown and event context update the user model.
5. The mismatch detector compares the model with quiz claims.
6. Neutral market-context observations are recorded separately from bias events.
7. The selected coach produces zero to two prompts for bias events.
8. The session state and interaction log are updated with action and reflection data.

Only the first two detected events receive coaching in any turn, and the same
(event type, asset) pair is not coached again within three turns (coach source `cooldown`
in the log). Repeated identical prompts habituate users; the event is still logged and
still updates the user model.

At completion, the session summary aggregates action counts by asset, detected event
counts, reflection completion, and average confidence. It deliberately does not convert
portfolio return into a score of decision quality.

Market-context observations (for example, buying after a recent rise or holding through
a sharp decline) are descriptive only. They are shown even when strict bias thresholds
do not fire and are not passed into the adaptive trait updater. The simulator's existing
event/context signals continue to update adaptive estimates under their original rules.

## Detected behavioural events

| Event | Trigger |
|---|---|
| `panic_sell` | Selling at least half a holding after a 5%+ one-turn or 7%+ two-turn drop while below cost |
| `fomo_buy` | Buying a non-bond asset at least 30% after a 10%+ recent run-up |
| `overconcentration` | A buy would place more than 70% of the simulated portfolio in one risky asset |
| `overtrading` | Trading activity on five consecutive turns |
| `hold_loser` | Holding an asset at least 10% below cost for an approximate streak of three turns |
| `early_profit_take` | Selling at least half of a small gain while holding a different asset down at least 10% |

All asset actions in one turn count as one turn for overtrading detection. These are
transparent prototype heuristics, not calibrated human-behaviour estimates.

## Session and persistence behavior

Sessions are held in the server's `SESSIONS` dictionary. They are lost when the server
process restarts.

Profiles in `profiles/` persist across sessions by participant ID only when session
completion and persistence settings allow it. CSV exports are written to `logs/`.

## Safety boundaries

The app:

- Uses synthetic prices and no live financial feeds
- Uses no real money or trades
- Uses no validated psychometric instrument
- Must not predict future prices or recommend real securities
- Explicitly labels LLM and offline coaching output
