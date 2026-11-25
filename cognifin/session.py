"""Game session: ties simulator, user model, mismatch detector, coaches and CSV logging."""
import csv
import io
import json
import random
import time
import uuid

from . import coach_baseline, coach_llm
from .knowledge import EVENT_TO_TRAIT
from .mismatch import detect_mismatches
from .quiz import score_quiz
from .simulator import ASSETS, N_TURNS, Portfolio, detect, generate_prices
from .user_model import UserModel

LOG_FIELDS = ["session_id", "user_id", "coach_mode", "turn", "action_type", "asset", "fraction",
              "decision_ms", "portfolio_value", "drawdown_pct", "event_types", "mismatch_codes",
              "coach_source", "coach_message", "user_rating", "ts", "actions", "plan",
              "decision_reason", "confidence", "market_observations"]
# Do not repeat a coach message for the same (event type, asset) within this many turns:
# identical repeated prompts habituate (alert fatigue) and lose salience. The event is still
# detected, logged and used to update the user model.
COACH_COOLDOWN_TURNS = 3
REFLECTION_REASONS = {
    "following_plan", "reacting_to_price_change", "managing_allocation", "exploring", "other",
    "not_recorded",
}


class Session:
    def __init__(self, user_id, answers, coach_mode="llm", seed=None, profile_dir="profiles",
                 use_api=True, persist=True, plan=None):
        profile = score_quiz(answers)
        self.id = uuid.uuid4().hex[:10]
        self.coach_mode = coach_mode if coach_mode in ("baseline", "llm", "none") else random.choice(["baseline", "llm"])
        self.use_api = use_api
        self.persist = persist
        self.profile_dir = profile_dir
        self.seed = seed if seed is not None else random.randrange(10**6)
        self.prices = generate_prices(self.seed)
        self.pf = Portfolio()
        self.turn = 0                       # number of completed turns
        self.peak = self.pf.value({a: 100.0 for a in ASSETS})
        self.history = []
        self.log = []
        self.last_coached = {}              # (event type, asset) -> turn of last message
        self.plan = " ".join(str(plan or "").split())[:160] or "Notice what influences my decisions."
        self.um = UserModel.load_or_new(user_id, profile["traits"], profile["self_report"], profile_dir) \
            if persist else UserModel(user_id, profile["traits"], profile["self_report"])
        self.user_id = user_id

    # ---------------------------------------------------------------------
    def px(self, t=None):
        t = self.turn if t is None else t
        return {a: self.prices[a][t] for a in ASSETS}

    def _observe_market_context(self, actions):
        observations = []
        for action in actions:
            asset = action["asset"]
            if asset not in ASSETS:
                continue
            change_1 = (self.prices[asset][self.turn] /
                        self.prices[asset][max(0, self.turn - 1)] - 1)
            change_2 = (self.prices[asset][self.turn] /
                        self.prices[asset][max(0, self.turn - 2)] - 1)
            change_3 = (self.prices[asset][self.turn] /
                        self.prices[asset][max(0, self.turn - 3)] - 1)
            if (action["type"] == "buy" and asset != "BOND" and self.pf.cash > 0
                    and action["fraction"] >= 0.1 and change_3 >= 0.05):
                observations.append({
                    "type": "buy_after_rise", "asset": asset,
                    "change_pct": round(change_3 * 100, 1),
                    "description": f"Bought {asset} after a {change_3 * 100:.1f}% three-turn rise.",
                })
            elif (action["type"] == "sell" and self.pf.units[asset] > 0
                  and action["fraction"] >= 0.1):
                if change_1 <= -0.03 or change_2 <= -0.05:
                    drop = min(change_1, change_2)
                    observations.append({
                        "type": "sell_after_drop", "asset": asset,
                        "change_pct": round(drop * 100, 1),
                        "description": f"Sold {asset} after a recent {abs(drop * 100):.1f}% decline.",
                    })
                cost = self.pf.cost[asset]
                if cost and self.px()[asset] < cost:
                    loss = (self.px()[asset] / cost - 1) * 100
                    observations.append({
                        "type": "sell_below_cost", "asset": asset,
                        "change_pct": round(loss, 1),
                        "description": f"Sold {asset} while it was {abs(loss):.1f}% below its average cost.",
                    })
            elif (action["type"] == "hold" and asset != "BOND" and self.pf.units[asset] > 0
                  and change_1 <= -0.05):
                observations.append({
                    "type": "hold_during_drop", "asset": asset,
                    "change_pct": round(change_1 * 100, 1),
                    "description": f"Held {asset} during a {abs(change_1 * 100):.1f}% single-turn decline.",
                })
        return observations

    def state(self):
        px = self.px()
        val = self.pf.value(px)
        return {
            "session_id": self.id, "coach_mode": self.coach_mode, "turn": self.turn,
            "n_turns": N_TURNS, "done": self.turn >= N_TURNS,
            "prices": {a: self.prices[a][: self.turn + 1] for a in ASSETS},
            "assets": {a: ASSETS[a]["name"] for a in ASSETS},
            "cash": round(self.pf.cash, 2), "units": {a: round(u, 4) for a, u in self.pf.units.items()},
            "cost": {a: round(c, 2) for a, c in self.pf.cost.items()},
            "value": round(val, 2), "weights": {a: round(w, 3) for a, w in self.pf.weights(px).items()},
            "profile": self.um.snapshot(),
        }

    def step(self, action, decision_ms=None, decision_reason=None, confidence=None):
        if self.turn >= N_TURNS:
            raise ValueError("simulation finished")
        multi_asset = isinstance(action, list)
        raw_actions = action if multi_asset else [action]
        if not raw_actions or not all(isinstance(item, dict) for item in raw_actions):
            raise ValueError("bad action")
        actions = []
        seen_assets = set()
        for item in raw_actions:
            atype = item.get("type", "hold")
            if atype not in ("buy", "sell", "hold"):
                raise ValueError("bad action type")
            asset = item.get("asset")
            if multi_asset and asset not in ASSETS:
                raise ValueError("unknown asset")
            if atype != "hold" and asset not in ASSETS:
                raise ValueError("unknown asset")
            if multi_asset and asset in seen_assets:
                raise ValueError("duplicate asset decision")
            if multi_asset:
                seen_assets.add(asset)
            fraction = float(item.get("fraction", 0) or 0)
            actions.append({"type": atype, "asset": asset,
                            "fraction": max(0.0, min(1.0, fraction))})
        if multi_asset and seen_assets != set(ASSETS):
            raise ValueError("provide one decision for each asset")
        if multi_asset and sum(a["fraction"] for a in actions if a["type"] == "buy") > 1.0 + 1e-9:
            raise ValueError("buy allocations cannot exceed 100% of starting cash")
        decision_reason = decision_reason or "not_recorded"
        if decision_reason not in REFLECTION_REASONS:
            raise ValueError("invalid decision reason")
        confidence = "" if confidence is None else max(1, min(5, int(confidence)))

        observations = self._observe_market_context(actions)
        px = self.px()
        starting_cash = self.pf.cash
        events, contexts = [], set()
        traded = False
        planned_sells = {a["asset"]: a["fraction"] for a in actions if a["type"] == "sell"}
        for item in actions:
            amount = starting_cash * item["fraction"] if item["type"] == "buy" else None
            new_events, new_contexts = detect(
                self.prices, self.turn, self.pf, item, self.history, buy_amount=amount)
            for event in new_events:
                if (event["type"] == "hold_loser"
                        and planned_sells.get(event["asset"], 0) >= 0.5):
                    continue
                if event not in events:
                    events.append(event)
            contexts.update(new_contexts)
            if item["type"] == "buy" and amount and self.pf.cash:
                spent = self.pf.buy(item["asset"], min(1.0, amount / self.pf.cash), px[item["asset"]])
                traded = traded or spent > 0
            elif item["type"] == "sell":
                proceeds = self.pf.sell(item["asset"], item["fraction"], px[item["asset"]])
                traded = traded or proceeds > 0

        self.history.append({"type": "buy" if traded else "hold"})
        self.turn += 1
        new_val = self.pf.value(self.px())
        self.peak = max(self.peak, new_val)
        drawdown = (self.peak - new_val) / self.peak

        self.um.update_short_term(events, drawdown, decision_ms)
        mismatches = detect_mismatches(self.um.self_report, self.um.quiz_traits, events)
        self.um.update_long_term(events, contexts)

        coaching = []
        fresh = [e for e in events
                 if self.turn - self.last_coached.get((e["type"], e.get("asset")), -99) > COACH_COOLDOWN_TURNS]
        cooled = bool(events) and not fresh
        for e in fresh[:2]:                                    # at most two prompts per turn
            ms = [m for m in mismatches if m["trait"] == EVENT_TO_TRAIT[e["type"]]]
            if self.coach_mode == "none":
                continue
            self.last_coached[(e["type"], e.get("asset"))] = self.turn
            if self.coach_mode == "baseline":
                coaching.append(coach_baseline.coach(e))
            else:
                coaching.append(coach_llm.coach(e, user_model=self.um, mismatches=ms, use_api=self.use_api))

        self._log(actions if multi_asset else actions[0], decision_ms, new_val, drawdown,
                  events, mismatches, coaching, decision_reason, confidence, observations,
                  cooled=cooled)
        if self.turn >= N_TURNS and self.persist:
            self.um.save(self.profile_dir)
        return {"events": events, "mismatches": mismatches, "coaching": coaching,
                "observations": observations, "state": self.state()}

    # ---------------------------------------------------------------------
    def _log(self, action, ms, val, dd, events, mismatches, coaching,
             decision_reason="not_recorded", confidence="", observations=None, cooled=False):
        multi_asset = isinstance(action, list)
        actions = action if multi_asset else [action]
        if coaching:
            coach_source = "|".join(c["source"] for c in coaching)
            coach_message = " || ".join(c["message"] for c in coaching)
        elif self.coach_mode == "none":
            coach_source = "disabled"
            coach_message = "Coaching is disabled for this session."
        elif cooled:
            coach_source = "cooldown"
            coach_message = "Pattern repeated; coaching paused to avoid repeating the same prompt."
        else:
            coach_source = "not_triggered"
            coach_message = "No behavioural pattern met the detection rules."
        self.log.append({
            "session_id": self.id, "user_id": self.user_id, "coach_mode": self.coach_mode,
            "turn": self.turn, "action_type": "multi" if multi_asset else action["type"],
            "asset": "|".join(a["asset"] or "" for a in actions) if multi_asset else action["asset"] or "",
            "fraction": "" if multi_asset else action["fraction"],
            "decision_ms": ms if ms is not None else "",
            "portfolio_value": round(val, 2), "drawdown_pct": round(dd * 100, 2),
            "event_types": "|".join(e["type"] for e in events) or "none",
            "mismatch_codes": "|".join(m["code"] for m in mismatches) or "none",
            "coach_source": coach_source,
            "coach_message": coach_message,
            "user_rating": "", "ts": int(time.time()),
            "actions": json.dumps(actions, separators=(",", ":")),
            "plan": self.plan, "decision_reason": decision_reason, "confidence": confidence,
            "market_observations": json.dumps(observations or [], separators=(",", ":"))})

    def rate(self, turn, rating):
        for row in self.log:
            if row["turn"] == turn:
                row["user_rating"] = max(1, min(5, int(rating)))
                return True
        return False

    def to_csv(self):
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=LOG_FIELDS)
        w.writeheader()
        w.writerows(self.log)
        return buf.getvalue()

    def summary(self):
        action_counts = {
            asset: {"buy": 0, "sell": 0, "hold": 0}
            for asset in ASSETS
        }
        event_counts = {}
        observation_counts = {}
        confidence_scores = []
        reflection_turns = 0
        for row in self.log:
            for action in json.loads(row["actions"]):
                asset = action.get("asset")
                action_type = action.get("type")
                if asset in action_counts and action_type in action_counts[asset]:
                    action_counts[asset][action_type] += 1
            for event in row["event_types"].split("|"):
                if event and event != "none":
                    event_counts[event] = event_counts.get(event, 0) + 1
            for observation in json.loads(row["market_observations"]):
                kind = observation["type"]
                observation_counts[kind] = observation_counts.get(kind, 0) + 1
            if row["decision_reason"] != "not_recorded" or row["confidence"] != "":
                reflection_turns += 1
            if row["confidence"] != "":
                confidence_scores.append(int(row["confidence"]))
        return {
            "plan": self.plan,
            "turns_completed": self.turn,
            "actions_by_asset": action_counts,
            "event_counts": event_counts,
            "observation_counts": observation_counts,
            "reflection_turns": reflection_turns,
            "average_confidence": round(sum(confidence_scores) / len(confidence_scores), 1)
            if confidence_scores else None,
        }
