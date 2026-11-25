"""Turn-based investing simulator on synthetic price data, plus behavioural event detection.

No real market data, money or personal data is involved. Every run with the same seed
produces the same price path, so all participants face the same scripted triggers
(a rally, a minor dip, a crash, a recovery).
"""
import random

ASSETS = {
    "BOND":  {"name": "Steady Bond",   "mu": 0.0005, "sigma": 0.004},
    "INDEX": {"name": "Broad Index",   "mu": 0.004,  "sigma": 0.025},
    "TECH":  {"name": "Hot Tech Fund", "mu": 0.006,  "sigma": 0.055},
}
N_TURNS = 20
START_CASH = 10000.0

# scripted shocks (turn index starting at 1 -> {asset: additive return})
SHOCKS = {
    3: {"TECH": 0.05}, 4: {"TECH": 0.06}, 5: {"TECH": 0.05},      # rally -> FOMO bait
    8: {"INDEX": -0.045, "TECH": -0.07},                            # minor dip
    12: {"INDEX": -0.10, "TECH": -0.17},                            # crash
    13: {"INDEX": -0.03, "TECH": -0.05},
    15: {"INDEX": 0.05, "TECH": 0.08}, 16: {"INDEX": 0.04, "TECH": 0.06},  # recovery
}


def generate_prices(seed, n_turns=N_TURNS):
    """Return {asset: [p0, p1, ..., p_n]} with p0 = 100."""
    rng = random.Random(seed)
    prices = {a: [100.0] for a in ASSETS}
    for t in range(1, n_turns + 1):
        for a, spec in ASSETS.items():
            r = spec["mu"] + spec["sigma"] * rng.gauss(0, 1) + SHOCKS.get(t, {}).get(a, 0.0)
            r = max(-0.4, min(0.4, r))
            prices[a].append(round(prices[a][-1] * (1 + r), 4))
    return prices


class Portfolio:
    def __init__(self, cash=START_CASH):
        self.cash = cash
        self.units = {a: 0.0 for a in ASSETS}
        self.cost = {a: 0.0 for a in ASSETS}   # average cost per unit

    def value(self, px):
        return self.cash + sum(self.units[a] * px[a] for a in ASSETS)

    def weights(self, px):
        v = self.value(px)
        return {a: (self.units[a] * px[a] / v if v else 0.0) for a in ASSETS}

    def buy(self, asset, fraction, price):
        spend = self.cash * max(0.0, min(1.0, fraction))
        if spend <= 0:
            return 0.0
        u = spend / price
        total = self.units[asset] + u
        self.cost[asset] = (self.cost[asset] * self.units[asset] + spend) / total
        self.units[asset] = total
        self.cash -= spend
        return spend

    def sell(self, asset, fraction, price):
        u = self.units[asset] * max(0.0, min(1.0, fraction))
        if u <= 0:
            return 0.0
        proceeds = u * price
        self.units[asset] -= u
        if self.units[asset] < 1e-9:
            self.units[asset] = 0.0
            self.cost[asset] = 0.0
        self.cash += proceeds
        return proceeds


def ret(prices, asset, turn, lookback):
    """Return over the last `lookback` turns ending at `turn` (turn = current index)."""
    start = max(0, turn - lookback)
    p0 = prices[asset][start]
    return prices[asset][turn] / p0 - 1.0


def detect(prices, turn, pf, action, history, buy_amount=None):
    """Detect behavioural events for the action taken at `turn` (before it is applied).

    Returns (events, contexts). `events` are emotional-mistake patterns; `contexts` are
    situations in which a bias *could* have fired (used to credit resisted opportunities).
    history: list of previous turn summaries (each with 'type').
    """
    px = {a: prices[a][turn] for a in ASSETS}
    typ, asset, frac = action["type"], action.get("asset"), float(action.get("fraction", 0))
    buy_is_trade = (buy_amount > 0 and pf.cash > 0) if buy_amount is not None else (
        frac > 0 and pf.cash > 0)
    events, contexts = [], set()

    # contexts = opportunities in which a bias *could* show (used by the Bayesian user model
    # to count "resisted" opportunities, i.e. evidence AGAINST a trait)
    #   dip   : holding a risky asset that just fell >= 5% in one turn     -> panic_selling
    #   rally : a risky asset is up >= 10% over three turns and cash exists -> herding_fomo
    #   loser : holding a risky asset >= 10% below its average cost         -> loss_aversion
    for a in ASSETS:
        if a == "BOND":
            continue
        if pf.units[a] > 0 and ret(prices, a, turn, 1) <= -0.05:
            contexts.add("dip")
        if ret(prices, a, turn, 3) >= 0.10 and pf.cash > 0:
            contexts.add("rally")
        if pf.units[a] > 0 and pf.cost[a] and px[a] / pf.cost[a] - 1.0 <= -0.10:
            contexts.add("loser")

    if typ == "sell" and asset in ASSETS and pf.units[asset] > 0:
        drop1 = ret(prices, asset, turn, 1)
        drop2 = ret(prices, asset, turn, 2)
        gain = px[asset] / pf.cost[asset] - 1.0 if pf.cost[asset] else 0.0
        if (drop1 <= -0.05 or drop2 <= -0.07) and gain < 0 and frac >= 0.5:
            events.append({"type": "panic_sell", "asset": asset,
                           "drop_pct": round(min(drop1, drop2) * 100, 1),
                           "loss_vs_cost_pct": round(gain * 100, 1)})
        elif 0 < gain < 0.05 and frac >= 0.5:
            losers = [a for a in ASSETS if pf.units[a] > 0 and a != asset
                      and px[a] / pf.cost[a] - 1 <= -0.10]
            if losers:
                events.append({"type": "early_profit_take", "asset": asset,
                               "gain_pct": round(gain * 100, 1), "loser": losers[0]})

    if typ == "buy" and buy_is_trade and asset in ASSETS and asset != "BOND" and frac >= 0.3:
        r3 = ret(prices, asset, turn, 3)
        if r3 >= 0.10:
            events.append({"type": "fomo_buy", "asset": asset,
                           "recent_gain_pct": round(r3 * 100, 1)})

    # hold a deep loser (checked on every action type that is not selling that asset)
    for a in ASSETS:
        if a == "BOND" or pf.units[a] <= 0:
            continue
        loss = px[a] / pf.cost[a] - 1.0
        if loss <= -0.10 and not (typ == "sell" and asset == a and frac >= 0.5):
            streak = 0
            for k in range(turn, max(0, turn - 5), -1):
                # approximate: was it below cost at past turns? use current cost basis
                if prices[a][k] / pf.cost[a] - 1.0 <= -0.10:
                    streak += 1
                else:
                    break
            if streak >= 3:
                events.append({"type": "hold_loser", "asset": a,
                               "loss_vs_cost_pct": round(loss * 100, 1), "turns": streak})
                break

    # concentration / overtrading (evaluated on the post-action portfolio)
    sim = Portfolio(pf.cash)
    sim.units, sim.cost = dict(pf.units), dict(pf.cost)
    if typ == "buy" and asset in ASSETS:
        if buy_amount is None:
            sim.buy(asset, frac, px[asset])
        elif sim.cash > 0:
            sim.buy(asset, min(1.0, buy_amount / sim.cash), px[asset])
    elif typ == "sell" and asset in ASSETS:
        sim.sell(asset, frac, px[asset])
    w = sim.weights(px)
    for a in ("TECH", "INDEX"):
        if w[a] > 0.70 and typ == "buy" and buy_is_trade:
            events.append({"type": "overconcentration", "asset": a, "weight_pct": round(w[a] * 100)})
            break
    sell_is_trade = (typ == "sell" and asset in ASSETS
                     and pf.units[asset] * max(0.0, min(1.0, frac)) > 0)
    current_type = typ if (typ == "buy" and buy_is_trade) or sell_is_trade else "hold"
    recent = [h["type"] for h in history[-4:]] + [current_type]
    if len(recent) >= 5 and all(t in ("buy", "sell") for t in recent):
        events.append({"type": "overtrading", "trades_in_last_5": 5})

    return events, sorted(contexts)
