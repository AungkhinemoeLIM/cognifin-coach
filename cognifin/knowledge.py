"""Explicit knowledge base: trait -> definition, research finding, citation.

The coach's "Why this?" panel is built from this table, NOT from LLM output, so the
cited findings cannot be hallucinated. The LLM only writes the natural-language message.
"""

TRAITS = {
    "loss_aversion": {
        "label": "Loss aversion / disposition effect",
        "definition": "Losses feel roughly twice as painful as equal gains feel good, "
                      "which pushes people to hold losers and cash in winners too early.",
        "finding": "Prospect theory shows losses loom larger than equivalent gains "
                   "(loss-aversion coefficient about 2.25); investors realize gains more "
                   "readily than losses (the disposition effect).",
        "citation": "Kahneman & Tversky (1979); Tversky & Kahneman (1992); "
                    "Shefrin & Statman (1985); Odean (1998)",
    },
    "overconfidence": {
        "label": "Overconfidence",
        "definition": "Overestimating how much you know or can control, leading to "
                      "concentrated bets and excessive trading.",
        "finding": "Households that trade the most earn lower net returns, an effect "
                   "linked to overconfidence.",
        "citation": "Barber & Odean (2000, 2001)",
    },
    "herding_fomo": {
        "label": "Herding / fear of missing out (FOMO)",
        "definition": "Following the crowd or chasing recent winners because others "
                      "appear to be profiting.",
        "finding": "Individuals rationally or emotionally imitate others and ignore "
                   "their own information, producing herds.",
        "citation": "Banerjee (1992); Bikhchandani et al. (1992)",
    },
    "panic_selling": {
        "label": "Panic selling (System-1 reaction under stress)",
        "definition": "Fast, emotion-driven selling after a drop, before slower "
                      "deliberate reasoning can weigh the decision.",
        "finding": "Under pressure people rely on fast intuitive processing and "
                   "simplifying heuristics, and visceral states can override planned "
                   "behaviour.",
        "citation": "Simon (1955); Kahneman (2011); Loewenstein (1996)",
    },
}

TRAIT_KEYS = list(TRAITS.keys())

# which behavioural event type is evidence for which trait
EVENT_TO_TRAIT = {
    "panic_sell": "panic_selling",
    "fomo_buy": "herding_fomo",
    "overconcentration": "overconfidence",
    "overtrading": "overconfidence",
    "hold_loser": "loss_aversion",
    "early_profit_take": "loss_aversion",
}

REFERENCES = sorted([
    "Banerjee, A. V. (1992). A simple model of herd behavior. Quarterly Journal of Economics, 107(3), 797-817.",
    "Barber, B. M., & Odean, T. (2000). Trading is hazardous to your wealth. Journal of Finance, 55(2), 773-806.",
    "Barber, B. M., & Odean, T. (2001). Boys will be boys: Gender, overconfidence, and common stock investment. Quarterly Journal of Economics, 116(1), 261-292.",
    "Bikhchandani, S., Hirshleifer, D., & Welch, I. (1992). A theory of fads, fashion, custom, and cultural change as informational cascades. Journal of Political Economy, 100(5), 992-1026.",
    "Kahneman, D. (2011). Thinking, Fast and Slow. Farrar, Straus and Giroux.",
    "Kahneman, D., & Tversky, A. (1979). Prospect theory: An analysis of decision under risk. Econometrica, 47(2), 263-291.",
    "Pronin, E., Lin, D. Y., & Ross, L. (2002). The bias blind spot: Perceptions of bias in self versus others. Personality and Social Psychology Bulletin, 28(3), 369-381.",
    "Shefrin, H., & Statman, M. (1985). The disposition to sell winners too early and ride losers too long: Theory and evidence. Journal of Finance, 40(3), 777-790.",
    "Tversky, A., & Kahneman, D. (1992). Advances in prospect theory: Cumulative representation of uncertainty. Journal of Risk and Uncertainty, 5(4), 297-323.",
    "Loewenstein, G. (1996). Out of control: Visceral influences on behavior. Organizational Behavior and Human Decision Processes, 65(3), 272-292.",
    "Odean, T. (1998). Are investors reluctant to realize their losses? Journal of Finance, 53(5), 1775-1798.",
    "Simon, H. A. (1955). A behavioral model of rational choice. Quarterly Journal of Economics, 69(1), 99-118.",
])
