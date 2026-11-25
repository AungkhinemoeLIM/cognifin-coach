"""Simulated user personas used to exercise and evaluate the pipeline offline.

IMPORTANT: these are synthetic agents, NOT human participants. Their reaction to coaching
(`heed`) is an ASSUMED parameter, so any "behavioural shift" computed with them is a
sensitivity analysis of the pipeline, not evidence about real people.
"""
import random

from .knowledge import EVENT_TO_TRAIT
from .quiz import ITEMS
from .simulator import ret

CLIP = lambda x, lo=0.0, hi=1.0: max(lo, min(hi, x))


class Persona:
    def __init__(self, rng, mismatch_prone=None):
        self.rng = rng
        self.true = {k: CLIP(rng.betavariate(2, 2)) for k in
                     ("loss_aversion", "overconfidence", "herding_fomo", "panic_selling")}
        self.mismatch_prone = rng.random() < 0.4 if mismatch_prone is None else mismatch_prone
        if self.mismatch_prone:                      # claims calm/risk-tolerant regardless of truth
            self.true["panic_selling"] = max(self.true["panic_selling"], 0.6 + 0.4 * rng.random())
            claim = 0.75 + 0.25 * rng.random()
            self.claims = {"self_risk_tolerance": claim, "self_calm_under_loss": CLIP(claim + rng.uniform(-.1, .1)),
                           "self_trades_rarely": rng.random()}
        else:                                        # roughly honest self-report
            p = self.true["panic_selling"]
            self.claims = {"self_risk_tolerance": CLIP(1 - p + rng.gauss(0, .12)),
                           "self_calm_under_loss": CLIP(1 - p + rng.gauss(0, .12)),
                           "self_trades_rarely": CLIP(1 - self.true["overconfidence"] + rng.gauss(0, .12))}
        # ground truth label: claims high risk tolerance AND is truly panic-prone
        self.gt_mismatch = self.claims["self_risk_tolerance"] >= 0.7 and self.true["panic_selling"] >= 0.6
        self.suppress = {}          # trait -> (turns_left, strength)

    # --- quiz answers generated from the latent profile (noisy) ----------------
    def quiz_answers(self, blind_spot=0.0):
        """Noisy quiz answers. `blind_spot` > 0 models the bias blind spot (Pronin et al.,
        2002): each trait is under-reported by a persona-specific amount ~ U(0, blind_spot)."""
        ans = {}
        under = {k: self.rng.uniform(0, blind_spot) if blind_spot else 0.0 for k in self.true}
        for item_id, _, construct, rev in ITEMS:
            base = self.true.get(construct, self.claims.get(construct, 0.5)) - under.get(construct, 0.0)
            x = CLIP(base + self.rng.gauss(0, 0.17))
            a = 1 + 4 * x
            if rev:
                a = 6 - a
            ans[item_id] = int(round(CLIP(a, 1, 5)))
        return ans

    def _m(self, trait):
        left, strength = self.suppress.get(trait, (0, 0.0))
        return 1 - strength if left > 0 else 1.0

    def hear(self, coaching, heed):
        """Update reaction to coach messages. `heed` = probability a message changes behaviour."""
        for c in coaching:
            if self.rng.random() < heed:
                self.suppress[c["trait"]] = (3, 0.85)

    def tick(self):
        self.suppress = {t: (n - 1, s) for t, (n, s) in self.suppress.items() if n - 1 > 0}

    # --- policy ----------------------------------------------------------------
    def act(self, st, prices):
        r, T = self.rng, self.true
        t = st["turn"]
        px = {a: prices[a][t] for a in prices}
        units, cost = st["units"], st["cost"]
        ms = int(r.gauss(3000 if T["panic_selling"] > .6 else 7000, 1500))
        ms = max(800, ms)

        def out(a):
            return a, ms

        if t == 0:
            return out({"type": "buy", "asset": "INDEX", "fraction": 0.5})
        # panic selling on a sharp drop
        for a in ("TECH", "INDEX"):
            if units[a] > 0 and ret(prices, a, t, 1) <= -0.05:
                if r.random() < min(0.95, 0.95 * T["panic_selling"] * self._m("panic_selling")):
                    return out({"type": "sell", "asset": a, "fraction": 1.0})
        # FOMO on a rally
        if ret(prices, "TECH", t, 3) >= 0.10 and r.random() < 0.9 * T["herding_fomo"] * self._m("herding_fomo"):
            return out({"type": "buy", "asset": "TECH", "fraction": 0.6})
        # overconfident concentration
        if st["cash"] > 500 and r.random() < 0.18 * T["overconfidence"] * self._m("overconfidence"):
            return out({"type": "buy", "asset": "TECH", "fraction": 0.85})
        # loss aversion: early profit taking
        losers = [a for a in ("TECH", "INDEX") if units[a] > 0 and px[a] / cost[a] - 1 <= -0.10]
        for a in ("TECH", "INDEX"):
            if units[a] > 0 and 0 < px[a] / cost[a] - 1 < 0.05 and losers and a not in losers:
                if r.random() < 0.5 * T["loss_aversion"] * self._m("loss_aversion"):
                    return out({"type": "sell", "asset": a, "fraction": 1.0})
        # holding / selling losers
        for a in losers:
            sell_p = (1 - T["loss_aversion"]) * 0.25 + (0.5 if self.suppress.get("loss_aversion", (0,))[0] > 0 else 0)
            if r.random() < sell_p:
                return out({"type": "sell", "asset": a, "fraction": 1.0})
        # overtrading
        if r.random() < 0.10 + 0.55 * T["overconfidence"] * self._m("overconfidence"):
            if r.random() < 0.5 and st["cash"] > 200:
                return out({"type": "buy", "asset": r.choice(["BOND", "INDEX"]), "fraction": 0.1})
            held = [a for a in units if units[a] > 0 and a in ("BOND", "INDEX")]
            if held:
                return out({"type": "sell", "asset": r.choice(held), "fraction": 0.1})
        return out({"type": "hold"})
