"""Dual-layer adaptive user model.

long_term : stable trait estimates. Each trait k is a Beta(a_k, b_k) belief over the
            probability that the bias shows when the situation allows it.
              * prior      : mean = quiz score q_k, strength = PRIOR_STRENGTH pseudo-
                             observations (set from the quiz's reliability, see below)
              * evidence   : each turn that offers an *opportunity* for the bias is a
                             Bernoulli trial: the bias fired (a_k += 1) or was resisted
                             (b_k += 1). Opportunities come from simulator.detect contexts.
              * estimate   : posterior mean a/(a+b); uncertainty = posterior SD.
            Persisted between sessions in profiles/<user>.json (evidence is carried over
            with a forgetting factor so old sessions count less).
short_term: per-session context (recent mistakes, drawdown stress, decision speed)

Why a Beta-Bernoulli model rather than "add 0.15 whenever an event fires": event types
have very different base rates (in simulation a FOMO buy fires ~60x more often than an
early profit-take), so counting events without counting opportunities over-weights the
noisiest detector. Counting fired-vs-resisted per opportunity removes that bias and gives
an explicit uncertainty that the "Why this?" panel can show.
"""
import json
import math
import os
import time

from .knowledge import TRAIT_KEYS, EVENT_TO_TRAIT

# Prior strength. A trait score is the mean of 3 Likert items; with per-item noise of
# ~0.17 on the 0-1 scale its standard error is ~0.10, and a Beta prior with that SD at
# mean 0.5 has a+b = 0.25/0.01 - 1 ~= 24 pseudo-observations.
PRIOR_STRENGTH = 24.0
CARRY_OVER = 0.5        # forgetting factor for evidence from earlier sessions
HASTY_MS = 4000         # decisions faster than this count as "hasty" (System-1 proxy)

# simulator context -> trait for which it is an opportunity. Overconfidence has no
# well-defined "resisted" opportunity (any turn could be an overconfident one), so it
# only receives confirming evidence when overtrading/overconcentration fires.
CONTEXT_TO_TRAIT = {"dip": "panic_selling", "rally": "herding_fomo", "loser": "loss_aversion"}


def _safe_name(user_id):
    return "".join(c for c in user_id if c.isalnum() or c in "-_")[:40] or "anon"


class UserModel:
    def __init__(self, user_id, traits, self_report):
        self.user_id = user_id
        self.quiz_traits = {k: float(traits.get(k, 0.5)) for k in TRAIT_KEYS}
        self.prior_mean = dict(self.quiz_traits)       # Beta prior mean (quiz, or blended legacy)
        self.self_report = dict(self_report)
        # behavioural evidence: trait -> [times fired, times resisted]
        self.evidence = {k: [0.0, 0.0] for k in TRAIT_KEYS}
        self.long_term = {}
        self._recompute()
        self.short_term = {"recent_events": [], "drawdown": 0.0, "hasty": False,
                           "decision_ms": None, "mistakes_this_session": 0}

    # ---- Bayesian core -------------------------------------------------------
    def _ab(self, k):
        q = min(0.99, max(0.01, self.prior_mean[k]))
        fired, resisted = self.evidence[k]
        return PRIOR_STRENGTH * q + fired, PRIOR_STRENGTH * (1 - q) + resisted

    def _recompute(self):
        for k in TRAIT_KEYS:
            a, b = self._ab(k)
            self.long_term[k] = round(a / (a + b), 4)

    def uncertainty(self, trait):
        """Posterior standard deviation of the trait estimate."""
        a, b = self._ab(trait)
        return round(math.sqrt(a * b / ((a + b) ** 2 * (a + b + 1))), 4)

    def n_observations(self, trait):
        return int(round(sum(self.evidence[trait])))

    # ---- updates -------------------------------------------------------------
    def update_short_term(self, events, drawdown, decision_ms):
        st = self.short_term
        st["drawdown"] = round(drawdown, 4)
        st["decision_ms"] = decision_ms
        st["hasty"] = decision_ms is not None and decision_ms < HASTY_MS
        st["recent_events"] = (st["recent_events"] + [e["type"] for e in events])[-5:]
        st["mistakes_this_session"] += len(events)

    def update_long_term(self, events, contexts):
        """One Bernoulli trial per trait per turn in which the trait had an opportunity."""
        fired = {EVENT_TO_TRAIT[e["type"]] for e in events}
        for t in fired:
            self.evidence[t][0] += 1
        for c in set(contexts):
            t = CONTEXT_TO_TRAIT.get(c)
            if t and t not in fired:
                self.evidence[t][1] += 1
        self._recompute()

    # ---- helpers -------------------------------------------------------------
    def intensity(self, trait):
        v = self.long_term[trait]
        return "high" if v >= 0.67 else ("moderate" if v >= 0.4 else "low")

    def top_trait(self):
        return max(self.long_term, key=self.long_term.get)

    def snapshot(self):
        return {"user_id": self.user_id, "long_term": dict(self.long_term),
                "uncertainty": {k: self.uncertainty(k) for k in TRAIT_KEYS},
                "evidence": {k: list(v) for k, v in self.evidence.items()},
                "quiz_traits": dict(self.quiz_traits), "self_report": dict(self.self_report),
                "short_term": dict(self.short_term)}

    # ---- persistence ---------------------------------------------------------
    def save(self, directory="profiles"):
        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(directory, _safe_name(self.user_id) + ".json"), "w") as f:
            json.dump({"long_term": self.long_term, "evidence": self.evidence,
                       "self_report": self.self_report, "saved": time.time()}, f, indent=2)

    @classmethod
    def load_or_new(cls, user_id, traits, self_report, directory="profiles"):
        """Fresh quiz = new prior; earlier behavioural evidence is carried over, discounted."""
        path = os.path.join(directory, _safe_name(user_id) + ".json")
        um = cls(user_id, traits, self_report)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                if "evidence" in data:
                    for k in TRAIT_KEYS:
                        fired, resisted = data["evidence"].get(k, [0, 0])
                        um.evidence[k] = [CARRY_OVER * float(fired), CARRY_OVER * float(resisted)]
                    um._recompute()
                else:                       # legacy profile (point estimates only): blend
                    for k in TRAIT_KEYS:
                        old = float(data["long_term"].get(k, um.prior_mean[k]))
                        um.prior_mean[k] = round(0.5 * um.prior_mean[k] + 0.5 * old, 4)
                    um._recompute()
            except (OSError, ValueError, KeyError, TypeError):
                pass
        return um
