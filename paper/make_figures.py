"""Generate every figure used in the paper and slides from the code and results/.

Run from the project root:  python paper/make_figures.py
Requires matplotlib (figures only; the app itself needs no third-party packages).
Outputs: paper/figures/<name>.pdf (vector, for LaTeX) and <name>.png (300 dpi).
"""
import json
import os
import random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from cognifin.agents import Persona                   # noqa: E402
from cognifin.evaluate import play                    # noqa: E402
from cognifin.simulator import SHOCKS, generate_prices  # noqa: E402
from cognifin.session import Session                  # noqa: E402

OUT = os.path.join(ROOT, "paper", "figures")
RES = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)

# fixed categorical order (never cycled); text stays in ink colours
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, MUTE, GRID = "#1f1f1f", "#5f5f5a", "#dddcd6"
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5, "legend.fontsize": 6.8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "axes.edgecolor": MUTE, "axes.labelcolor": INK,
    "xtick.color": MUTE, "ytick.color": MUTE, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5,
    "axes.axisbelow": True, "legend.frameon": False, "pdf.fonttype": 42,
})
W1 = 3.45      # IEEE single-column width (in)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".pdf"), bbox_inches="tight", pad_inches=0.02)
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=300, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def load(name):
    with open(os.path.join(RES, name)) as f:
        return json.load(f)


# ---------------------------------------------------------------- architecture
def fig_architecture():
    fig, ax = plt.subplots(figsize=(7.1, 3.1))
    ax.set_xlim(0, 100); ax.set_ylim(0, 48); ax.axis("off")

    def box(x, y, w, h, title, lines, ec):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2",
                                    fc="white", ec=ec, lw=0.9))
        ax.text(x + w / 2, y + h - 1.4, title, ha="center", va="top", fontsize=7.0,
                fontweight="bold", color=INK, linespacing=1.1)
        n_title = title.count("\n") + 1
        ax.text(x + w / 2, y + h - 1.6 - 3.0 * n_title, "\n".join(lines), ha="center", va="top",
                fontsize=6.0, color=INK, linespacing=1.25)

    def layer(x, w, label, fc):
        ax.add_patch(FancyBboxPatch((x, 1), w, 41, boxstyle="round,pad=0.2,rounding_size=1.5",
                                    fc=fc, ec="none"))
        ax.text(x + w / 2, 40.8, label, ha="center", va="top", fontsize=7.2,
                fontweight="bold", color=MUTE)

    def arrow(pts, color=INK, ls="-"):
        xs, ys = zip(*pts)
        ax.plot(xs[:-1] + (xs[-1],), ys[:-1] + (ys[-1],), color=color, lw=0.8, ls=ls,
                solid_capstyle="butt")
        ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle="-|>", mutation_scale=7,
                                     lw=0.8, color=color, ls=ls))

    layer(0.5, 22, "1  PERCEPTION", "#eef4fc")
    layer(24.5, 33, "2  COGNITION / INFERENCE", "#fdf0ea")
    layer(59.5, 20, "3  GENERATION", "#eaf7f2")
    layer(81.5, 18, "4  OUTPUT & LOG", "#fdf5e3")

    box(2, 24, 19, 13, "Profiling quiz", ["15 Likert items ->", "4 trait scores q_k", "+ 3 self-claims"], C1)
    box(2, 7, 19, 13, "Decision ingest +\nevent detector", ["actions + timing ->", "6 bias events +", "3 opportunity contexts"], C1)

    # dual-layer user model group
    ax.add_patch(FancyBboxPatch((25.6, 22.8), 30.8, 15.6, boxstyle="round,pad=0.2,rounding_size=1.2",
                                fc="none", ec=C2, lw=0.8, ls="--"))
    box(26.5, 24, 13.5, 13, "Long-term\ntraits", ["Beta prior, n0 = 24", "+ fired / resisted", "-> mean +/- SD"], C2)
    box(42, 24, 13.5, 13, "Short-term\ncontext", ["drawdown,", "hasty (< 4 s) =", "System-1 proxy"], C2)
    box(26.5, 7, 13.5, 13, "Mismatch\ndetector", ["self-claim vs", "behaviour", "(blind spot)"], C2)
    box(42, 7, 13.5, 13, "Knowledge\nbase", ["trait -> finding", "-> citation", "(fixed table)"], C2)

    box(61, 24, 17, 13, "Coach selector", ["LLM + validator", "+ offline fallback |", "rule baseline | none"], C3)
    box(61, 7, 17, 13, "\"Why this?\"\nassembler", ["evidence, mechanism,", "estimate +/- SD,", "source, limits"], C3)

    box(83, 24, 15, 13, "Browser UI", ["message, trait", "bars +/- SD,", "reflection check,", "1-5 rating"], C4)
    box(83, 7, 15, 13, "CSV log", ["events, mismatches,", "coach source,", "rating, reflection"], C4)

    arrow([(21.4, 30.5), (26.1, 30.5)])                       # quiz -> long-term (prior)
    arrow([(21.4, 13.5), (26.1, 13.5)])                       # events -> mismatch
    arrow([(21.4, 17), (23.5, 17), (23.5, 27), (26.1, 27)])   # events/contexts -> long-term
    arrow([(16, 23.6), (16, 21.5), (24.2, 21.5), (24.2, 16.5), (26.1, 16.5)])  # claims -> mismatch
    arrow([(55.9, 30.5), (60.6, 30.5)])                       # user model -> coach
    arrow([(55.9, 13.5), (60.6, 13.5)])                       # KB -> why
    arrow([(33.2, 6.6), (33.2, 4.2), (58.3, 4.2), (58.3, 10), (60.6, 10)])   # mismatch -> why
    arrow([(40.4, 17), (41.0, 17), (41.0, 21.6), (58.8, 21.6), (58.8, 27), (60.6, 27)])  # mismatch -> coach
    arrow([(69.5, 23.6), (69.5, 20.4)])                       # coach -> why
    arrow([(78.4, 30.5), (82.6, 30.5)])
    arrow([(78.4, 15), (80.5, 15), (80.5, 27), (82.6, 27)])   # why -> UI
    arrow([(78.4, 11), (82.6, 11)])                           # -> log
    ax.add_patch(FancyArrowPatch((90.5, 42.6), (11.5, 42.6), arrowstyle="-|>", mutation_scale=7,
                                 lw=0.8, color=MUTE, ls="--", connectionstyle="arc3,rad=0.08"))
    ax.text(51, 46.6, "user's next decision (closed perception-action loop, 20 turns per session)",
            ha="center", va="bottom", fontsize=6.2, color=MUTE, style="italic")
    ax.set_ylim(0, 50)
    save(fig, "fig_architecture")


# ---------------------------------------------------------------- price paths
def fig_prices(seed=42):
    p = generate_prices(seed)
    fig, ax = plt.subplots(figsize=(W1, 1.75))
    t = range(len(p["BOND"]))
    for a, c, lab in (("BOND", C3, "Steady Bond"), ("INDEX", C1, "Broad Index"), ("TECH", C2, "Hot Tech Fund")):
        ax.plot(t, p[a], color=c, lw=1.4, label=lab)
    for (lo, hi, lab) in ((2.5, 5.5, "rally"), (7.5, 8.5, "dip"), (11.5, 13.5, "crash"), (14.5, 16.5, "recovery")):
        ax.axvspan(lo, hi, color="#000000", alpha=0.06, lw=0)
        ax.text((lo + hi) / 2, ax.get_ylim()[1] if False else 1.0, lab, transform=ax.get_xaxis_transform(),
                ha="center", va="bottom", fontsize=6.3, color=MUTE)
    ax.set_xlabel("turn"); ax.set_ylabel("synthetic price")
    ax.set_xlim(0, 20); ax.set_xticks(range(0, 21, 4))
    ax.set_ylim(top=max(max(v) for v in p.values()) * 1.12)
    ax.legend(loc="upper left", ncol=3, handlelength=1.4, borderaxespad=0.1, columnspacing=0.9)
    assert set(SHOCKS) == {3, 4, 5, 8, 12, 13, 15, 16}
    save(fig, "fig_prices")


# ---------------------------------------------------------------- posterior trajectory
def fig_trajectory(n_sessions=3):
    """Panic-selling estimate (+/-1 SD) across persisted sessions for a panic-prone persona
    who under-reports the trait in the quiz (bias blind spot)."""
    import tempfile
    rng = random.Random(3)
    best = None
    for _ in range(80):
        p = Persona(random.Random(rng.random()), mismatch_prone=True)
        ans = p.quiz_answers(blind_spot=0.35)
        seeds = [rng.randrange(10**6) for _ in range(n_sessions)]
        with tempfile.TemporaryDirectory() as d:
            est, lo, hi, fired, quiz = [], [], [], [], None
            for k, sd in enumerate(seeds):
                s = Session("traj", ans, coach_mode="none", seed=sd, use_api=False, persist=True,
                            profile_dir=d)
                quiz = s.um.quiz_traits["panic_selling"]
                p.rng = random.Random(sd + 1)
                v, u = s.um.long_term["panic_selling"], s.um.uncertainty("panic_selling")
                est.append(v); lo.append(v - u); hi.append(v + u)
                while s.turn < 20:
                    act, ms = p.act(s.state(), s.prices)
                    r = s.step(act, ms)
                    v, u = s.um.long_term["panic_selling"], s.um.uncertainty("panic_selling")
                    est.append(v); lo.append(v - u); hi.append(v + u)
                    if any(e["type"] == "panic_sell" for e in r["events"]):
                        fired.append(len(est) - 1)
        gain = est[-1] - est[0]
        if p.true["panic_selling"] - quiz > 0.25 and (best is None or gain > best[0]):
            best = (gain, p.true["panic_selling"], quiz, est, lo, hi, fired)
    _, truth, quiz, est, lo, hi, fired = best
    fig, ax = plt.subplots(figsize=(W1, 1.75))
    t = range(len(est))
    ax.fill_between(t, lo, hi, color=C1, alpha=0.16, lw=0, label="posterior $\\pm$1 SD")
    ax.plot(t, est, color=C1, lw=1.4, label="Bayesian estimate")
    ax.axhline(truth, color=INK, lw=0.9, ls="--"); ax.text(len(est) + 0.5, truth, "true", va="center", fontsize=6.3)
    ax.axhline(quiz, color=MUTE, lw=0.9, ls=":"); ax.text(len(est) + 0.5, quiz, "quiz", va="center", fontsize=6.3, color=MUTE)
    for f in fired:
        ax.plot([f], [est[f]], marker="v", color=C2, ms=4, mec="white", mew=0.5, ls="none")
    ax.plot([], [], marker="v", color=C2, ms=4, ls="none", label="panic_sell fired")
    for k in range(1, n_sessions):
        ax.axvline(21 * k - 0.5, color=MUTE, lw=0.6)
    for k in range(n_sessions):
        ax.text(21 * k + 10, 0.03, f"session {k + 1}", ha="center", fontsize=6.2, color=MUTE)
    ax.set_xlim(0, len(est) - 1); ax.set_ylim(0, 1.08)
    ax.set_xticks([]); ax.set_xlabel("turn (three sessions, evidence carried over at 0.5)")
    ax.set_ylabel("panic-selling estimate")
    ax.legend(loc="upper left", ncol=3, handlelength=1.2, columnspacing=0.8, fontsize=6.2)
    save(fig, "fig_trajectory")


# ---------------------------------------------------------------- estimation ablation
def fig_estimation():
    ab = load("extra_summary.json")["ablation_update_rule"]
    conds = [("honest_quiz", "honest quiz"), ("blind_spot_quiz", "blind-spot quiz")]
    vals = {
        "quiz only": [ab[c]["bayesian"]["top_trait_acc_quiz_only"] for c, _ in conds],
        "legacy additive": [ab[c]["legacy_additive"]["top_trait_acc_quiz_plus_behaviour"] for c, _ in conds],
        "Bayesian (ours)": [ab[c]["bayesian"]["top_trait_acc_quiz_plus_behaviour"] for c, _ in conds],
    }
    fig, ax = plt.subplots(figsize=(W1, 1.75))
    w = 0.26
    for i, (lab, ys) in enumerate(vals.items()):
        xs = [j + (i - 1) * (w + 0.02) for j in range(2)]
        bars = ax.bar(xs, ys, width=w, color=(MUTE, C2, C1)[i], label=lab, hatch=(None, "////", None)[i],
                      edgecolor="white", lw=0.6)
        for b, y in zip(bars, ys):
            ax.text(b.get_x() + b.get_width() / 2, y + 0.008, f"{y:.3f}", ha="center", va="bottom", fontsize=6.2, color=INK)
    ax.set_xticks(range(2)); ax.set_xticklabels([n for _, n in conds])
    ax.set_ylim(0.5, 0.86); ax.set_ylabel("top-trait accuracy")
    ax.legend(loc="upper right", ncol=3, handlelength=1.2, columnspacing=0.8, bbox_to_anchor=(1.0, 1.14))
    save(fig, "fig_estimation")


# ---------------------------------------------------------------- detector sweep
def fig_detector():
    sw = load("extra_summary.json")["detector_sweep"]
    fig, ax = plt.subplots(figsize=(W1, 1.8))
    for thr, c, mk in ((0.7, C1, "o"), (0.9, C2, "s")):
        pts = sorted([r for r in sw if r["threshold"] == thr], key=lambda r: r["min_flagged_turns"])
        ax.plot([r["recall"] for r in pts], [r["precision"] for r in pts], color=c, lw=1.4, marker=mk,
                ms=4.5, mec="white", mew=0.6,
                label=f"claim cut-off {'0.6/0.7' if thr == 0.7 else '0.8/0.9'}")
        for r in pts:
            ax.annotate(f"k={r['min_flagged_turns']}", (r["recall"], r["precision"]), textcoords="offset points",
                        xytext=(4, -8 if thr == 0.7 else 4), fontsize=6.2, color=INK)
    ax.set_xlabel("recall"); ax.set_ylabel("precision"); ax.set_xlim(0, 1); ax.set_ylim(0.55, 1.05)
    ax.legend(loc="lower left")
    save(fig, "fig_detector")


# ---------------------------------------------------------------- shift sensitivity
def fig_shift():
    d = load("eval_summary.json")["shift_sensitivity"]
    rhos = sorted(d, key=float)
    fig, ax = plt.subplots(figsize=(W1, 1.75))
    x = [float(r) for r in rhos]
    for mode, c, mk, lab in (("none", MUTE, "^", "no coach"), ("baseline", C2, "s", "rule baseline"),
                             ("llm", C1, "o", "personalised coach")):
        ax.plot(x, [d[r][mode]["mistakes_mean"] for r in rhos], color=c, marker=mk, lw=1.4, ms=4.5,
                mec="white", mew=0.6, label=lab)
    for r in rhos:
        ci = d[r]["paired_baseline_minus_llm_mistakes"]
        if ci["mean"]:
            ax.text(float(r), d[r]["llm"]["mistakes_mean"] - 0.17,
                    f"$\\Delta$={ci['mean']:.2f}\n[{ci['ci_lo']:.2f}, {ci['ci_hi']:.2f}]",
                    ha="center", va="top", fontsize=5.9, color=INK)
    ax.set_xticks(x); ax.set_xlabel(r"assumed heed ratio $\rho$ (personalised / baseline)")
    ax.set_ylabel("bias events / session"); ax.set_ylim(4.4, 6.7)
    ax.legend(loc="lower left", ncol=1)
    save(fig, "fig_shift")


# ---------------------------------------------------------------- message comparison
def fig_messages():
    path = os.path.join(RES, "llm_check.json")
    if not os.path.exists(path):
        print("skip fig_messages (run: python -m cognifin.evaluate --llm-check)")
        return
    s = load("llm_check.json")["summary"]
    gens = [g for g in ("baseline", "offline", "llm") if g in s and s[g].get("n")]
    labels = {"baseline": "rule baseline", "offline": "offline generator", "llm": "LLM (Gemini)"}
    metrics = [("share_cites_event_number", "cites own\nnumbers"),
               ("share_mentions_mismatch_when_given", "uses mismatch\nwhen given"),
               ("share_with_why_this", "has \"Why\nthis?\" panel"), ("share_valid", "passes\nvalidator")]
    fig, ax = plt.subplots(figsize=(W1, 1.8))
    w = 0.26
    for i, g in enumerate(gens):
        xs = [j + (i - (len(gens) - 1) / 2) * (w + 0.02) for j in range(len(metrics))]
        ys = [s[g][m] or 0 for m, _ in metrics]
        ax.bar(xs, ys, width=w, color={"baseline": C2, "offline": C3, "llm": C1}[g],
               label=labels[g] + (f" (n={s[g]['n']})" if g == "llm" else ""), edgecolor="white", lw=0.6,
               hatch="////" if g == "baseline" else None)
    ax.set_xticks(range(len(metrics))); ax.set_xticklabels([l for _, l in metrics])
    ax.set_ylim(0, 1.18); ax.set_ylabel("share of messages")
    ax.legend(loc="upper left", ncol=3, handlelength=1.2, columnspacing=0.8, bbox_to_anchor=(0, 1.16))
    save(fig, "fig_messages")


if __name__ == "__main__":
    for f in (fig_architecture, fig_prices, fig_trajectory, fig_estimation, fig_detector, fig_shift, fig_messages):
        f()
        print("ok", f.__name__)
