# CogniFin Coach API Reference

The app is a local HTTP server at `http://localhost:8000` by default. Port can be
changed with the `PORT` environment variable.

All JSON request bodies use `Content-Type: application/json`.

## `GET /`

Returns the browser application as HTML.

## `GET /index.html`

Also returns the browser application.

## `GET /api/quiz`

Returns quiz items and LLM availability.

```json
{
  "items": [
    {
      "id": "la1",
      "text": "A $100 loss bothers me much more than a $100 gain pleases me."
    }
  ],
  "llm_available": false
}
```

## `POST /api/start`

Creates a session.

```json
{
  "user_id": "P01",
  "answers": {
    "la1": 4,
    "la2": 3
  },
  "coach_mode": "llm",
  "plan": "Pause before reacting to a price drop",
  "seed": 42
}
```

`seed` is optional: a non-negative integer that fixes the synthetic price path (the browser
sends it when the page is opened as `/?seed=42`). Anything else is ignored and a random seed
is used.

`coach_mode` accepts `llm`, `baseline`, `none`, or `random`. In random mode the server
assigns `llm` or `baseline` and records the selected mode.

Returns a session state object. Missing quiz answers use a neutral score of 3. The state's
`profile` contains `quiz_traits`, `long_term` (posterior mean per trait), `uncertainty`
(posterior SD), `evidence` (`[fired, resisted]` per trait), `self_report` and `short_term`.

## `POST /api/session/{session_id}/step`

Applies one turn. The browser sends one decision for each asset:

```json
{
  "actions": [
    {"type": "hold", "asset": "BOND", "fraction": 0},
    {"type": "buy", "asset": "INDEX", "fraction": 0.4},
    {"type": "sell", "asset": "TECH", "fraction": 0.5}
  ],
  "decision_ms": 4200,
  "decision_reason": "managing_allocation",
  "confidence": 4
}
```

Action types are `buy`, `sell`, and `hold`. Each request must include exactly one
decision for `BOND`, `INDEX`, and `TECH`. For buys, `fraction` is a share of the cash
available at the start of the turn; all buy fractions together must not exceed 1.0.
For sells, `fraction` is the share of that asset's holding to sell. Hold amounts are
ignored. A single `action` object using the previous API shape is still accepted for
compatibility. `decision_reason` may be `following_plan`, `reacting_to_price_change`,
`managing_allocation`, `exploring`, `other`, or `not_recorded`. `confidence` is an
optional 1-5 value for the turn.

Response fields:

```json
{
  "events": [],
  "mismatches": [],
  "coaching": [],
  "observations": [],
  "state": {}
}
```

`observations` are neutral market-context notes, such as a buy after a recent rise
(at least 5% over three turns), a sell after a decline, a sale below average cost, or
holding a risky asset during a sharp drop. They are distinct from bias-triggering
`events` and are not passed into the adaptive trait updater. Existing event/context
signals from the simulator continue to update adaptive traits under their own rules.

A fully completed turn returns the same state shape plus the updated portfolio and profile.

Error responses:

- `400 {"error": "bad action type"}`
- `400 {"error": "provide one decision for each asset"}`
- `400 {"error": "buy allocations cannot exceed 100% of starting cash"}`
- `400 {"error": "invalid decision reason"}`
- `400 {"error": "unknown session"}`
- `400 {"error": "simulation finished"}`
- `404 {"error": "unknown session"}`

## `POST /api/session/{session_id}/rate`

Records a 1-5 relevance rating for a completed turn.

```json
{
  "turn": 5,
  "rating": 4
}
```

Returns:

```json
{
  "ok": true
}
```

Ratings outside 1-5 are clamped to that range.

## `GET /api/session/{session_id}/state`

Returns the current session state:

- Session and coach mode
- Turn number and completion status
- Price history
- Cash and holdings
- Portfolio value and weights
- Quiz and adaptive profile snapshot

## `GET /api/session/{session_id}/summary`

Returns the reflection recap: the participant's intention, action counts by asset,
detected event counts, neutral observation counts, number of turns with a recorded
reason, and average confidence.

## `GET /api/session/{session_id}/export`

Returns the session interaction log as `text/csv` and prompts the browser to download it.
The server also writes the CSV to `logs/session_<session_id>.csv`.

When no event or mismatch occurs, the corresponding CSV field contains `none` rather
than an empty cell. `coach_source` is `not_triggered` when no behavioural event qualifies
for coaching, and `disabled` in the no-coach condition. In those cases, `coach_message`
explains why no coaching was produced. A blank `user_rating` means no rating was submitted.
Each turn remains one CSV row. The `actions` field contains a JSON array with each
asset's decision. For multi-asset turns, `action_type` is `multi`; `asset` lists the
asset codes, while `fraction` is blank because each fraction is recorded in `actions`.
The `plan`, `decision_reason`, and `confidence` columns preserve the session intention
and optional per-turn reflection. `confidence` remains blank when the participant skips
that rating. `market_observations` contains the neutral context notes for the turn as JSON.

## State shape

The state object includes:

| Field | Meaning |
|---|---|
| `session_id` | Short random session identifier |
| `coach_mode` | Selected or randomly resolved coach mode |
| `turn` | Number of completed turns |
| `n_turns` | 20 |
| `done` | Whether the simulation is complete |
| `prices` | Observed synthetic price history |
| `assets` | Display names for asset codes |
| `cash` | Available cash |
| `units` | Holding quantity for each asset |
| `cost` | Weighted average cost for each asset |
| `value` | Total portfolio value |
| `weights` | Current portfolio weight for each asset |
| `profile` | Quiz and adaptive profile snapshot |
