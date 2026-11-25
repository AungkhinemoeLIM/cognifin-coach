"""Paper content (single source for the LaTeX and the PDF renderer).

Markup inside strings: <i>, <b>, <tt>, <sub>, <super>; {c:key1,key2} = citation.
Every number quoted from the evaluation is read from results/*.json, so re-running the
evaluation and then `python paper/build_paper.py` keeps the paper consistent with the code.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name):
    with open(os.path.join(ROOT, "results", name)) as f:
        return json.load(f)


def numbers():
    ev = _load("eval_summary.json")
    ex = _load("extra_summary.json")
    R = {}
    d = ev["detection"]
    R["n"] = ev["n_personas"]
    R["n_gt"] = d["n_gt_mismatch"]
    R["recall"], R["precision"], R["fpr"] = d["recall"], d["precision"], d["false_positive_rate"]
    R["any_flag"] = d["share_sessions_with_any_mismatch_flag"]
    sw = {(r["threshold"], r["min_flagged_turns"]): r for r in ex["detector_sweep"]}
    R["k2"] = sw[(0.7, 2)]
    R["t8"] = sw[(0.8, 1)]
    ab = ex["ablation_update_rule"]
    for c in ("honest_quiz", "blind_spot_quiz"):
        R[c] = {"quiz_acc": ab[c]["bayesian"]["top_trait_acc_quiz_only"],
                "quiz_mae": ab[c]["bayesian"]["mae_quiz_only"],
                "bayes_acc": ab[c]["bayesian"]["top_trait_acc_quiz_plus_behaviour"],
                "bayes_mae": ab[c]["bayesian"]["mae_quiz_plus_behaviour"],
                "legacy_acc": ab[c]["legacy_additive"]["top_trait_acc_quiz_plus_behaviour"],
                "legacy_mae": ab[c]["legacy_additive"]["mae_quiz_plus_behaviour"]}
    sh = ev["shift_sensitivity"]
    R["shift"] = sh
    R["grounding"] = ev["grounding"]
    try:
        R["llm"] = _load("llm_check.json")["summary"]
    except OSError:
        R["llm"] = None
    return R


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def pct(x):
    return f"{100 * x:.0f}%"


REFERENCES = [
    ("kt79", "D. Kahneman and A. Tversky, “Prospect theory: An analysis of decision under risk,” <i>Econometrica</i>, vol. 47, no. 2, pp. 263–291, 1979."),
    ("tk92", "A. Tversky and D. Kahneman, “Advances in prospect theory: Cumulative representation of uncertainty,” <i>J. Risk Uncertainty</i>, vol. 5, no. 4, pp. 297–323, 1992."),
    ("ss85", "H. Shefrin and M. Statman, “The disposition to sell winners too early and ride losers too long: Theory and evidence,” <i>J. Finance</i>, vol. 40, no. 3, pp. 777–790, 1985."),
    ("odean98", "T. Odean, “Are investors reluctant to realize their losses?” <i>J. Finance</i>, vol. 53, no. 5, pp. 1775–1798, 1998."),
    ("bo00", "B. M. Barber and T. Odean, “Trading is hazardous to your wealth: The common stock investment performance of individual investors,” <i>J. Finance</i>, vol. 55, no. 2, pp. 773–806, 2000."),
    ("bo01", "B. M. Barber and T. Odean, “Boys will be boys: Gender, overconfidence, and common stock investment,” <i>Q. J. Econ.</i>, vol. 116, no. 1, pp. 261–292, 2001."),
    ("banerjee92", "A. V. Banerjee, “A simple model of herd behavior,” <i>Q. J. Econ.</i>, vol. 107, no. 3, pp. 797–817, 1992."),
    ("bhw92", "S. Bikhchandani, D. Hirshleifer, and I. Welch, “A theory of fads, fashion, custom, and cultural change as informational cascades,” <i>J. Political Econ.</i>, vol. 100, no. 5, pp. 992–1026, 1992."),
    ("simon55", "H. A. Simon, “A behavioral model of rational choice,” <i>Q. J. Econ.</i>, vol. 69, no. 1, pp. 99–118, 1955."),
    ("kahneman11", "D. Kahneman, <i>Thinking, Fast and Slow</i>. New York, NY, USA: Farrar, Straus and Giroux, 2011."),
    ("es13", "J. St. B. T. Evans and K. E. Stanovich, “Dual-process theories of higher cognition: Advancing the debate,” <i>Perspect. Psychol. Sci.</i>, vol. 8, no. 3, pp. 223–241, 2013."),
    ("loewenstein96", "G. Loewenstein, “Out of control: Visceral influences on behavior,” <i>Organ. Behav. Hum. Decis. Process.</i>, vol. 65, no. 3, pp. 272–292, 1996."),
    ("pronin02", "E. Pronin, D. Y. Lin, and L. Ross, “The bias blind spot: Perceptions of bias in self versus others,” <i>Pers. Soc. Psychol. Bull.</i>, vol. 28, no. 3, pp. 369–381, 2002."),
    ("flavell79", "J. H. Flavell, “Metacognition and cognitive monitoring: A new area of cognitive–developmental inquiry,” <i>Amer. Psychol.</i>, vol. 34, no. 10, pp. 906–911, 1979."),
    ("fischhoff82", "B. Fischhoff, “Debiasing,” in <i>Judgment Under Uncertainty: Heuristics and Biases</i>, D. Kahneman, P. Slovic, and A. Tversky, Eds. Cambridge, U.K.: Cambridge Univ. Press, 1982, pp. 422–444."),
    ("larrick04", "R. P. Larrick, “Debiasing,” in <i>Blackwell Handbook of Judgment and Decision Making</i>, D. J. Koehler and N. Harvey, Eds. Oxford, U.K.: Blackwell, 2004, pp. 316–337."),
    ("morewedge15", "C. K. Morewedge, H. Yoon, I. Scopelliti, C. W. Symborski, J. H. Korris, and K. S. Kassam, “Debiasing decisions: Improved decision making with a single training intervention,” <i>Policy Insights Behav. Brain Sci.</i>, vol. 2, no. 1, pp. 129–140, 2015."),
    ("ts08", "R. H. Thaler and C. R. Sunstein, <i>Nudge: Improving Decisions About Health, Wealth, and Happiness</i>. New Haven, CT, USA: Yale Univ. Press, 2008."),
    ("as68", "R. C. Atkinson and R. M. Shiffrin, “Human memory: A proposed system and its control processes,” in <i>The Psychology of Learning and Motivation</i>, vol. 2, K. W. Spence and J. T. Spence, Eds. New York, NY, USA: Academic Press, 1968, pp. 89–195."),
    ("actr04", "J. R. Anderson, D. Bothell, M. D. Byrne, S. Douglass, C. Lebiere, and Y. Qin, “An integrated theory of the mind,” <i>Psychol. Rev.</i>, vol. 111, no. 4, pp. 1036–1060, 2004."),
    ("ca94", "A. T. Corbett and J. R. Anderson, “Knowledge tracing: Modeling the acquisition of procedural knowledge,” <i>User Model. User-Adapt. Interact.</i>, vol. 4, no. 4, pp. 253–278, 1994."),
    ("grossberg87", "S. Grossberg, “Competitive learning: From interactive activation to adaptive resonance,” <i>Cogn. Sci.</i>, vol. 11, no. 1, pp. 23–63, 1987."),
    ("miller19", "T. Miller, “Explanation in artificial intelligence: Insights from the social sciences,” <i>Artif. Intell.</i>, vol. 267, pp. 1–38, 2019."),
    ("lewis20", "P. Lewis <i>et al.</i>, “Retrieval-augmented generation for knowledge-intensive NLP tasks,” in <i>Proc. Adv. Neural Inf. Process. Syst. (NeurIPS)</i>, vol. 33, 2020, pp. 9459–9474."),
    ("ji23", "Z. Ji <i>et al.</i>, “Survey of hallucination in natural language generation,” <i>ACM Comput. Surv.</i>, vol. 55, no. 12, pp. 1–38, 2023."),
    ("dpr19", "F. D’Acunto, N. Prabhala, and A. G. Rossi, “The promises and pitfalls of robo-advising,” <i>Rev. Financial Stud.</i>, vol. 32, no. 5, pp. 1983–2020, 2019."),
    ("flm14", "D. Fernandes, J. G. Lynch, Jr., and R. G. Netemeyer, “Financial literacy, financial education, and downstream financial behaviors,” <i>Manage. Sci.</i>, vol. 60, no. 8, pp. 1861–1883, 2014."),
    ("lm14", "A. Lusardi and O. S. Mitchell, “The economic importance of financial literacy: Theory and evidence,” <i>J. Econ. Literature</i>, vol. 52, no. 1, pp. 5–44, 2014."),
]


def build(author):
    R = numbers()
    H, B = R["honest_quiz"], R["blind_spot_quiz"]
    s15, s20 = R["shift"]["1.5"], R["shift"]["2.0"]
    d15, d20 = s15["paired_baseline_minus_llm_mistakes"], s20["paired_baseline_minus_llm_mistakes"]
    G = R["grounding"]
    L = R["llm"]

    title = ("CogniFin Coach: A Cognitive-Profile-Aware Financial Decision Coach with "
             "Bayesian Bias Modelling and Self-Report Grounding")

    abstract = (
        "Retail investors repeat the same emotionally driven mistakes—selling in a panic after a drop, "
        "chasing a rally, over-concentrating, or riding losers—even when they know the textbook advice, "
        "and generic financial education rarely changes this behaviour. We present CogniFin Coach, a "
        "cognitive computing system that couples a dual-layer user model with grounded natural-language "
        "coaching inside a turn-based investing simulation on synthetic prices. A 15-item quiz supplies a "
        "prior over four bias traits (loss aversion, overconfidence, herding/FOMO, panic selling); a "
        "perception layer converts each decision into six behavioural events and three opportunity "
        "contexts; a long-term layer maintains a Beta–Bernoulli belief per trait that is updated from "
        "fired-versus-resisted opportunities, while a short-term layer tracks drawdown stress and "
        "decision speed as a System-1 proxy. A mismatch detector, motivated by the bias blind spot, "
        "contrasts what users claimed with what they did. A large language model writes the coaching "
        "message behind a validator and an offline fallback, whereas the “Why this?” explanation—"
        "evidence, mechanism, estimate ± uncertainty and citation—is assembled deterministically from a "
        f"knowledge base so it cannot hallucinate. In an evaluation with {R['n']} simulated personas, the "
        f"Bayesian update matched or improved quiz-only top-trait accuracy ({f3(H['bayes_acc'])} vs. "
        f"{f3(H['quiz_acc'])}; {f3(B['bayes_acc'])} vs. {f3(B['quiz_acc'])} under an under-reporting "
        f"quiz), whereas a naive additive rule degraded it ({f3(H['legacy_acc'])}; {f3(B['legacy_acc'])}); "
        f"the mismatch detector reached {f2(R['recall'])} recall at {f2(R['precision'])} precision; and "
        "personalised messages cited the user’s own numbers, unlike rule templates. We discuss why "
        "simulated results bound, rather than establish, efficacy for people."
    )
    keywords = ("cognitive computing, user modelling, behavioural finance, cognitive biases, "
                "Bayesian inference, large language models, explainable AI, debiasing")

    B_ = []          # body blocks
    h1 = lambda t: B_.append(("h1", t))
    h2 = lambda t: B_.append(("h2", t))
    p = lambda t: B_.append(("p", t))

    # ------------------------------------------------------------------ I
    h1("Introduction")
    p("Individual investors lose money in systematic, predictable ways. Households that trade the most "
      "earn the lowest net returns {c:bo00}, investors realise gains far more readily than losses "
      "{c:ss85,odean98}, and sharp market falls trigger sales that lock in losses just before recoveries. "
      "These patterns are not primarily failures of knowledge: a meta-analysis of 168 studies found "
      "that financial-literacy interventions explain only about 0.1% of the variance in downstream "
      "financial behaviour, and that the effect decays within months {c:flm14}, even though literacy "
      "itself matters for outcomes {c:lm14}. Robo-advisers can reduce some behavioural biases, but they "
      "do so largely by taking the decision away from the investor rather than helping the investor "
      "understand it {c:dpr19}.")
    p("Cognitive science suggests why. Under time pressure and loss, fast intuitive (System-1) "
      "processing and visceral states dominate slower deliberation {c:kahneman11,es13,loewenstein96}, "
      "and people readily see biases in others but not in themselves—the <i>bias blind spot</i> "
      "{c:pronin02}. Debiasing work shows that feedback which is timely, specific and tied to the "
      "person’s own decision can reduce biased judgement, sometimes durably {c:fischhoff82,larrick04,"
      "morewedge15}. A coach that helps therefore has to (i) <i>perceive</i> decisions as they happen, "
      "(ii) maintain a <i>model of the user</i> that combines self-report with behavioural evidence and "
      "knows how uncertain it is, (iii) <i>reason</i> about which bias plausibly drove a decision, and "
      "(iv) <i>explain</i> that inference transparently enough to support the user’s own metacognitive "
      "monitoring {c:flavell79}.")
    p("This paper describes CogniFin Coach, a prototype that implements these four capabilities in a "
      "closed perception–action loop and evaluates each one. We ask four research questions. "
      "<b>RQ1:</b> Can a quiz prior and in-task behaviour be fused into trait estimates at least as "
      "accurate as the quiz alone, including when self-report is biased? <b>RQ2:</b> Can conflicts "
      "between self-report and behaviour be detected reliably enough to serve as reflective prompts? "
      "<b>RQ3:</b> Does profile- and event-conditioned generation yield more grounded messages than a "
      "static rule baseline, without hallucinated citations? <b>RQ4:</b> Under which assumptions about "
      "user responsiveness would personalisation reduce repeated mistakes? Our contributions are:")
    B_.append(("bullets", [
        "An end-to-end cognitive architecture—perception, a dual-layer user model, grounded generation "
        "and a deterministic explanation channel—running in an open-source web prototype with no "
        "third-party runtime dependencies.",
        "An opportunity-based Beta–Bernoulli long-term user model whose prior strength is derived from "
        "the quiz’s reliability and whose uncertainty is shown to the user; an ablation shows that it "
        "removes the accuracy loss of a naive additive update.",
        "A self-report–behaviour mismatch detector grounded in the bias blind spot, and a “Why this?” "
        "panel whose evidence and citations are separated from the language model by design.",
        "A reproducible evaluation harness (simulated personas, ablations, threshold sweeps, and a "
        "message-level comparison with a rule baseline and a live LLM), together with a QA audit and an "
        "explicit account of what simulated personas can and cannot show.",
    ]))

    # ------------------------------------------------------------------ II
    h1("Related Work")
    h2("Behavioural finance")
    p("Prospect theory models losses as looming larger than equivalent gains {c:kt79}, with a "
      "loss-aversion coefficient of about 2.25 in its cumulative form {c:tk92}. Its main market "
      "signature is the disposition effect—selling winners too early and riding losers too long "
      "{c:ss85,odean98}. Overconfidence predicts excessive trading and concentrated bets that reduce net "
      "returns {c:bo00,bo01}. Herding can arise rationally from informational cascades or emotionally "
      "from fear of missing out {c:banerjee92,bhw92}. These four constructs define our trait space, and "
      "their market signatures define our six behavioural event detectors (Table I).")
    h2("Dual-process theories and bounded rationality")
    p("Simon’s bounded rationality {c:simon55} and later dual-process accounts {c:kahneman11,es13} "
      "distinguish fast, associative processing from slow, rule-based reasoning; visceral states such "
      "as fear can override planned behaviour {c:loewenstein96}. We operationalise this distinction "
      "crudely but transparently: decision latency below 4 s marks a decision as <i>hasty</i>, and "
      "portfolio drawdown approximates affective load. Both enter the short-term context, not the "
      "long-term trait estimates.")
    h2("User models and cognitive architectures")
    p("Cognitive architectures such as ACT-R separate durable declarative knowledge from transient "
      "buffers {c:actr04}, echoing the classical distinction between long-term memory and working "
      "memory {c:as68}. Our dual-layer user model follows the same division. Its long-term layer is "
      "closest to Bayesian knowledge tracing {c:ca94}, which updates the probability that a learner has "
      "mastered a skill from correct or incorrect responses at each <i>opportunity</i> to use it; we "
      "instead estimate the probability that a bias is expressed when the situation allows it. How "
      "quickly such a model should change is an instance of the stability–plasticity dilemma "
      "{c:grossberg87}, which we revisit in Section V.")
    h2("Debiasing, nudges and metacognition")
    p("Debiasing interventions range from warnings to training and decision aids {c:fischhoff82,"
      "larrick04}; a single interactive training session can reduce several biases for weeks "
      "{c:morewedge15}. Nudges alter choice environments without restricting options {c:ts08}. Our coach "
      "is a <i>reflective</i> nudge: it never tells the user what to trade, but names a possible "
      "pattern, shows the evidence, and asks a reflection question. Its mismatch prompts target the "
      "bias blind spot {c:pronin02} by confronting a specific claim with a specific action, supporting "
      "metacognitive monitoring {c:flavell79}.")
    h2("Grounded generation and explanation")
    p("Large language models produce fluent but sometimes unsupported text {c:ji23}. "
      "Retrieval-augmented generation conditions output on retrieved evidence {c:lewis20}, and "
      "social-science work on explanation argues that good explanations are contrastive, selective and "
      "tied to the recipient’s question {c:miller19}. We push grounding further than retrieval: the LLM "
      "writes only the surface message, while the explanation’s evidence, estimate and citation come "
      "from deterministic code and a fixed knowledge base, so they cannot be invented.")

    # ------------------------------------------------------------------ III
    h1("System Architecture and Methodology")
    p("Fig. 1 shows the architecture. Each of the 20 turns in a session runs a full "
      "perception–inference–generation cycle, and the user’s next decision closes the loop. The four "
      "layers are described below; Algorithm 1 summarises one turn.")
    h2("Simulated environment")
    p("Three synthetic assets follow a random walk <i>r</i><sub>t</sub> = μ + σε<sub>t</sub> + "
      "<i>s</i><sub>t</sub>, with ε<sub>t</sub> ~ N(0,1), returns clipped to ±40%, and (μ, σ) = "
      "(0.0005, 0.004) for a bond, (0.004, 0.025) for a broad index and (0.006, 0.055) for a "
      "technology fund. Scripted shocks <i>s</i><sub>t</sub> create the same decision points for every "
      "user: a rally (turns 3–5), a minor dip (8), a crash (12–13) and a recovery (15–16) (Fig. 2). A "
      "fixed seed reproduces the path exactly. Each turn the user makes one decision per asset—buy a "
      "fraction of the cash available at the start of the turn, sell a fraction of the holding, or "
      "hold—with combined buys capped at 100% of that cash. Users may also record a reason and a "
      "1–5 confidence rating. No real money, prices or financial data are involved.")
    B_.append(("fig", "fig_prices", "Example synthetic price path (seed 42). Shaded bands mark the "
               "scripted rally, dip, crash and recovery that every participant faces."))
    h2("Perception layer")
    p("<i>Quiz.</i> Fifteen Likert items (1–5) are mapped to [0, 1] by (<i>a</i> − 1)/4, reverse-coded "
      "where needed, and averaged into four trait scores <i>q</i><sub>k</sub> (three items each) and "
      "three self-claims: comfort with high risk, calm under loss, and trading rarely. "
      "<i>Decisions.</i> For each asset decision, the event detector applies the rules in Table I to "
      "the price history, cost basis and post-trade weights. It also emits three <i>opportunity "
      "contexts</i>, situations in which a bias could have shown: <tt>dip</tt> (holding a risky asset "
      "that fell ≥ 5% in one turn), <tt>rally</tt> (a risky asset up ≥ 10% over three turns while cash "
      "is available) and <tt>loser</tt> (holding a risky asset ≥ 10% below cost). Weaker, descriptive "
      "<i>market-context observations</i> (e.g., buying after a 5% rise) are shown and logged but never "
      "treated as evidence of a bias.")
    B_.append(("table", "Behavioural event detectors and the trait each one evidences",
               ["Event", "Trigger (prototype heuristic)", "Trait"],
               [["panic_sell", "sell ≥ 50% of a holding after a ≥ 5% one-turn or ≥ 7% two-turn drop while below cost", "panic selling"],
                ["fomo_buy", "buy ≥ 30% of cash into a risky asset up ≥ 10% over three turns", "herding / FOMO"],
                ["overconc.", "a buy leaves > 70% of portfolio value in one risky asset", "overconfidence"],
                ["overtrading", "trades on five consecutive turns", "overconfidence"],
                ["hold_loser", "keep a risky asset ≥ 10% below cost for ≈ 3 turns", "loss aversion"],
                ["early_profit", "sell ≥ 50% of a < 5% gain while holding another asset ≥ 10% below cost", "loss aversion"]],
               [0.22, 0.56, 0.22]))
    h2("Long-term layer: Bayesian trait model")
    p("For each trait <i>k</i> we treat the probability θ<sub>k</sub> that the bias is expressed, given "
      "an opportunity, as a Beta-distributed belief. The quiz supplies the prior mean and the "
      "behavioural record supplies Bernoulli evidence:")
    B_.append(("eq", r"\theta_k \sim \mathrm{Beta}\big(n_0 q_k + F_k,\; n_0 (1-q_k) + R_k\big)",
               "θ<sub>k</sub> ~ Beta( <i>n</i><sub>0</sub><i>q</i><sub>k</sub> + <i>F</i><sub>k</sub> , "
               "<i>n</i><sub>0</sub>(1 − <i>q</i><sub>k</sub>) + <i>R</i><sub>k</sub> )", "1"))
    p("where <i>F</i><sub>k</sub> counts turns in which an event of trait <i>k</i> fired and "
      "<i>R</i><sub>k</sub> counts turns that offered the matching opportunity context but in which the "
      "bias did not fire. A turn contributes at most one trial per trait. The estimate shown to the user "
      "and passed to the coach is the posterior mean, and its uncertainty is the posterior standard "
      "deviation:")
    B_.append(("eq", r"\hat\theta_k = \frac{a_k}{a_k+b_k}, \qquad "
                     r"\mathrm{sd}_k = \sqrt{\frac{a_k b_k}{(a_k+b_k)^2 (a_k+b_k+1)}}",
               "E[θ<sub>k</sub>] = <i>a</i><sub>k</sub> / (<i>a</i><sub>k</sub> + <i>b</i><sub>k</sub>)<br/>"
               "sd<sub>k</sub> = √[ <i>a</i><sub>k</sub><i>b</i><sub>k</sub> / ((<i>a</i><sub>k</sub> + "
               "<i>b</i><sub>k</sub>)<super>2</super>(<i>a</i><sub>k</sub> + <i>b</i><sub>k</sub> + 1)) ]", "2"))
    p("<i>Prior strength.</i> Rather than tune <i>n</i><sub>0</sub>, we derive it from the instrument. "
      "With per-item noise of about 0.17 on the unit scale, a three-item mean has a standard error "
      "near 0.10. A Beta prior with that standard deviation at mean 0.5 has <i>n</i><sub>0</sub> = "
      "<i>q</i>(1 − <i>q</i>)/SE<super>2</super> − 1 ≈ 24 pseudo-observations, so the quiz counts as "
      "much as 24 behavioural opportunities.")
    p("<i>Why opportunities matter.</i> Event types have very different base rates. Across our simulated "
      "sessions a FOMO buy fires 2.64 times per session but an early profit-take only 0.04 times. The "
      "original prototype added 0.15(1 − θ) whenever an event fired. Without a count of opportunities, "
      "that rule treats frequent detectors as strong evidence and inflates their traits, which harmed "
      "accuracy (Section IV-B). Counting fired-versus-resisted trials corrects this and yields a "
      "principled uncertainty.")
    p("<i>Asymmetric evidence.</i> Overconfidence has no well-defined resisted opportunity, since any "
      "turn could be an overconfident one. Treating every turn or every trade as a trial made the "
      "estimate collapse towards zero in pilot runs, so overtrading and over-concentration contribute "
      "confirming evidence only. <i>Persistence.</i> A completed session saves "
      "(<i>F</i><sub>k</sub>, <i>R</i><sub>k</sub>); the next session builds a fresh prior from a new "
      "quiz and carries the old evidence over with a forgetting factor γ = 0.5. Estimates map to "
      "<i>high</i> (≥ 0.67), <i>moderate</i> (≥ 0.40) or <i>low</i> intensity labels for the coach.")
    h2("Short-term layer")
    p("The short-term layer holds the current drawdown from the session’s portfolio peak, whether the "
      "last decision was hasty (latency < 4 s), and the last five event types. It conditions the "
      "message—e.g., the coach notes that a quick decision after a fall makes gut reactions more "
      "likely—but never changes the long-term traits, so a single stressful turn cannot rewrite the "
      "profile.")
    h2("Metacognitive grounding: mismatch detector")
    p("Because self-report is vulnerable to the bias blind spot {c:pronin02}, the system checks claims "
      "against behaviour. A panic sale by a user who claimed high risk tolerance or calm under loss "
      "(self-claim ≥ 0.7), overtrading by a user who claimed to trade rarely, a FOMO buy by a user whose "
      "quiz herding score was ≤ 0.35, and over-concentration by a user whose quiz overconfidence score "
      "was ≤ 0.35 each raise a mismatch. Mismatches are shown as a neutral <i>reflection check</i> "
      "(“you reported that you …, while this turn you …”), are passed to the coach, and are logged.")
    h2("Knowledge base and coach generation")
    p("A fixed knowledge base maps each trait to a definition, a research finding and its citations, "
      "and each event to a trait, a description of what the rule detects, and a reflection question. "
      "Three interchangeable coaches consume the same events. The <i>rule baseline</i> returns one "
      "static template per event type and ignores the profile. The <i>personalised coach</i> builds a "
      "structured JSON prompt containing the event and its numbers, the bias hypothesis, the "
      "intensity label of every trait, the short-term context, the estimate’s uncertainty and any "
      "mismatch. A system prompt limits the reply to two or three sentences and at most 70 words, and "
      "forbids real-world advice, price predictions, security recommendations and shaming. The reply "
      "comes from Gemini 3 Flash at a low thinking level with a 1,024-token budget. A validator rejects "
      "replies that were cut off, exceed 110 words, or match forbidden patterns (e.g., “guaranteed”, "
      "“will recover”, “you should buy”). On rejection or API failure (after one retry on rate-limit "
      "or overload errors), a deterministic <i>offline generator</i> fills intensity-, haste- and mismatch-conditioned templates from the same inputs. "
      "Every message carries a visible source tag (<tt>LLM</tt> or <tt>offline generator</tt>) in both "
      "the UI and the log. Because identical prompts repeated every turn habituate and lose salience, "
      "the same (event, asset) pair is not re-coached within three turns; the event is still logged "
      "and still updates the user model. A third mode, <i>none</i>, is the control, and a <i>random</i> mode assigns "
      "an arm for studies.")
    p("<i>“Why this?”.</i> The explanation panel is assembled entirely by code. It contains what the "
      "rule noticed (in the user’s own numbers), the mechanism and definition, the quiz score and "
      "current estimate ± SD with the number of opportunities observed, session context, the research "
      "finding and citation, a reflection question, and an explicit statement of the inference’s limits. "
      "The LLM never sees or writes the citation. Following Miller {c:miller19}, the panel is "
      "contrastive (claim versus action) and selective (one hypothesis per event, at most two "
      "prompts per turn).")
    B_.append(("alg", "Algorithm 1: One turn of the CogniFin loop", [
        (0, "<b>input:</b> decisions <i>D</i> (one per asset), latency <i>t</i>, prices, portfolio, model <i>M</i>"),
        (0, "events <i>E</i> ← {};  contexts <i>C</i> ← {};  cash<sub>0</sub> ← cash"),
        (0, "<b>for each</b> decision <i>d</i> in <i>D</i> <b>do</b>"),
        (1, "(<i>e</i>, <i>c</i>) ← DETECT(prices, portfolio, <i>d</i>, history)"),
        (1, "add <i>e</i> to <i>E</i>;  add <i>c</i> to <i>C</i>;  apply <i>d</i> using cash<sub>0</sub>"),
        (0, "update drawdown; <i>M</i>.short ← (drawdown, <i>t</i> < 4 s, last 5 events)"),
        (0, "<i>X</i> ← MISMATCH(<i>M</i>.claims, <i>M</i>.quiz, <i>E</i>)"),
        (0, "<b>for each</b> trait <i>k</i>: <i>F</i><sub>k</sub> += 1 if <i>k</i> fired; <i>R</i><sub>k</sub> += 1 if ctx<sub>k</sub> in <i>C</i> and not fired"),
        (0, "<b>for each</b> <i>e</i> in the first two events of <i>E</i> <b>do</b>"),
        (1, "msg ← COACH<sub>mode</sub>(<i>e</i>, <i>M</i>, <i>X</i>);  why ← KB(<i>e</i>, <i>M</i>, <i>X</i>)"),
        (0, "log row; render messages, reflection checks, trait bars ± SD"),
    ]))
    h2("Implementation")
    p("The system is about 1,650 lines of Python using only the standard library: an HTTP server with a "
      "single-page browser UI, in-memory sessions, JSON profiles and CSV interaction logs. Every row "
      "records the per-asset actions, latency, portfolio value, drawdown, events, mismatch codes, coach "
      "source and message, the user’s 1–5 rating of “did this match how you were thinking?”, and the "
      "optional reason and confidence. Thirty-nine automated tests cover detection, scoring, the "
      "Bayesian update, persistence, the coaching cooldown, LLM response handling, retry and model fallback, the HTTP API (incl. the demo seed) and "
      "the evaluation metrics.")

    # ------------------------------------------------------------------ IV
    h1("Experiments and Evaluation")
    h2("Setup: simulated personas")
    p(f"No human study has been run yet, so we evaluate the pipeline with {R['n']} simulated personas "
      "(seed 7). Each persona has latent traits θ ~ Beta(2, 2). Forty percent are “mismatch-prone”: "
      "their panic-selling trait is at least 0.6, yet they claim high risk tolerance and calm (≥ 0.75). "
      "Quiz answers are the latent value plus N(0, 0.17) noise per item, rounded to the Likert scale. A "
      "second <i>blind-spot</i> condition subtracts a persona-specific U(0, 0.35) from every trait before "
      "answering, modelling under-reported bias {c:pronin02}. The policy expresses traits "
      "stochastically. On a ≥ 5% dip a persona panic-sells with probability 0.95θ<sub>ps</sub>; on a "
      "rally it buys with probability 0.9θ<sub>hf</sub>; each turn it over-concentrates with probability "
      "0.18θ<sub>oc</sub> or trades with probability 0.10 + 0.55θ<sub>oc</sub>; and it takes early "
      "profits with probability 0.5θ<sub>la</sub>. When coached, a persona heeds the message with "
      "probability <i>h</i>, suppressing the coached trait by 85% for three turns. Coaching "
      "conditions are paired: each persona replays the same price path and noise stream in every arm. "
      "Without coaching, personas produce 6.39 bias events per session.")
    p("<i>Caveat.</i> Personas are not people. The detectors and the personas share the same "
      "constructs, so detection results are optimistic upper bounds. The heed parameter is assumed, so "
      "RQ4 is a sensitivity analysis, not evidence that coaching works.")
    h2("RQ1: Trait estimation")
    B_.append(("fig", "fig_estimation", f"Top-trait accuracy over {R['n']} personas. The legacy additive rule "
               "lowers accuracy below the quiz alone; the opportunity-based Bayesian update does not, and "
               "helps when the quiz under-reports bias."))
    p("We compare the quiz alone, the legacy additive update and the Bayesian update on two metrics: "
      "top-trait accuracy (does the highest estimate identify the persona’s strongest latent trait?) "
      "and mean absolute error over all traits (Fig. 3, Table II). With an honest quiz the legacy rule "
      f"<i>reduced</i> accuracy from {f3(H['quiz_acc'])} to {f3(H['legacy_acc'])}, while the Bayesian "
      f"update kept it at {f3(H['bayes_acc'])} and lowered MAE from {f3(H['quiz_mae'])} to "
      f"{f3(H['bayes_mae'])}. Under the blind-spot quiz, behavioural evidence becomes valuable: the "
      f"Bayesian update raised accuracy from {f3(B['quiz_acc'])} to {f3(B['bayes_acc'])} and cut MAE from "
      f"{f3(B['quiz_mae'])} to {f3(B['bayes_mae'])}. The legacy rule achieved a lower MAE here "
      f"({f3(B['legacy_mae'])}), but only because it inflates <i>every</i> trait and so partly cancels a "
      f"uniform under-report. Its ranking, the quantity the coach acts on, was the worst ({f3(B['legacy_acc'])}).")
    B_.append(("table", "Trait estimation (300 personas): accuracy / MAE",
               ["Quiz condition", "Quiz only", "Legacy additive", "Bayesian (ours)"],
               [["honest", f"{f3(H['quiz_acc'])} / {f3(H['quiz_mae'])}", f"{f3(H['legacy_acc'])} / {f3(H['legacy_mae'])}", f"<b>{f3(H['bayes_acc'])}</b> / <b>{f3(H['bayes_mae'])}</b>"],
                ["blind spot", f"{f3(B['quiz_acc'])} / {f3(B['quiz_mae'])}", f"{f3(B['legacy_acc'])} / <b>{f3(B['legacy_mae'])}</b>", f"<b>{f3(B['bayes_acc'])}</b> / {f3(B['bayes_mae'])}"]],
               [0.25, 0.24, 0.26, 0.25]))
    p("Fig. 4 traces one under-reporting, panic-prone persona across three persisted sessions. The "
      "estimate rises with each panic sale and falls slightly with each resisted dip, and its band "
      "narrows. However, with only three to five opportunities per session and a 24-observation prior, "
      "it closes only a small part of the gap to the latent value: the model is stable but slow.")
    B_.append(("fig", "fig_trajectory", "Panic-selling estimate (±1 posterior SD) for one panic-prone "
               "persona who under-reported the trait, across three sessions with evidence carried over."))
    h2("RQ2: Mismatch detection")
    p(f"Ground truth marks a persona as mismatched if it claims high risk tolerance (≥ 0.7) and its "
      f"latent panic trait is ≥ 0.6 ({R['n_gt']} of {R['n']}). We score the two panic-related mismatch "
      f"codes against this label. At the default cut-off, the detector flagged {f2(R['recall'])} of "
      f"mismatched personas (recall) with {f2(R['precision'])} precision and a false-positive rate of "
      f"{f2(R['fpr'])}. Requiring at least two flagged turns raises precision to "
      f"{f2(R['k2']['precision'])} and lowers the false-positive rate to {f2(R['k2']['false_positive_rate'])}, "
      f"at {f2(R['k2']['recall'])} recall (Fig. 5). Cut-offs of 0.6 and 0.7 give identical results, as "
      "do 0.8 and 0.9, because a single Likert item can only take the values {0, 0.25, 0.5, 0.75, 1}. "
      "The cut-off is effectively ordinal. Because the prompt is phrased tentatively and a false alarm "
      "costs one moment of reflection, we keep the high-recall setting for in-session prompts; any "
      "persistent label should require k ≥ 2.")
    B_.append(("fig", "fig_detector", "Mismatch detector precision–recall when at least k turns must be "
               "flagged, for two self-claim cut-offs."))
    h2("RQ3: Message grounding versus a rule baseline")
    if L:
        lb, lo, ll = L["baseline"], L["offline"], L.get("llm") or {"n": 0}
        n_llm = ll.get("written_by_model", ll.get("n", 0))
        if n_llm:
            models = ", ".join(f"<tt>{m}</tt>" for m in ll.get("models", [])) or "Gemini"
            llm_txt = (
                f"Gemini ({models}) wrote {n_llm} of the 24 LLM-arm messages; the other "
                f"{24 - n_llm} hit free-tier quota or overload errors (HTTP 429/503) and fell back to the "
                "labelled offline generator, so the LLM row in Table III covers model-written messages only. "
                if n_llm < 24 else f"Gemini ({models}) wrote all 24 LLM-arm messages. ")
            llm_txt += (f"Those messages cited event numbers in {pct(ll['share_cites_event_number'])} of cases"
                        + (f", used the supplied mismatch in {pct(ll['share_mentions_mismatch_when_given'])} of cases"
                           if ll.get("share_mentions_mismatch_when_given") is not None else "")
                        + f", passed the validator in {pct(ll['share_valid'])} and averaged "
                        f"{ll['words_mean']:.0f} words, with a median latency of {ll['latency_s_median']:.1f} s. ")
        else:
            llm_txt = ("The live LLM arm could not be measured at submission time: the free-tier quota and "
                       "service overload (HTTP 429/503) on both models forced every call to the labelled "
                       "fallback. In earlier single calls the model returned valid, grounded 50–66-word "
                       "messages that cited the user’s numbers and the supplied mismatch. The resumable "
                       "<tt>--llm-check</tt> command fills in this row when quota is available. ")
        p("We generated messages for 24 fixed scenarios (six event types × low/high trait prior × "
          "with/without a mismatch) from the rule baseline, the offline generator and the live LLM "
          "(Table III, Fig. 6). A message <i>cites own numbers</i> if it contains a number from the "
          "event (e.g., the 15.8% drop). Rule templates never cite the user’s numbers, never use the "
          "mismatch, have no explanation panel, and produce only six distinct texts. The offline "
          f"generator cited the numbers in {pct(lo['share_cites_event_number'])} of messages and used "
          "every supplied mismatch. " + llm_txt
          + f"Across {G['messages']} offline-generated messages in full simulated sessions, "
          f"{pct(G['share_with_user_numbers'])} contained the user’s numbers and {pct(G['share_valid'])} passed "
          "the validator. Because every explanation comes from the knowledge base, the share of "
          "hallucinated citations is zero by construction.")

        def row(name, d):
            return [name, pct(d["share_cites_event_number"]), pct(d["share_mentions_mismatch_when_given"] or 0),
                    pct(d["share_with_why_this"]), f"{d['words_mean']:.0f}", str(d["distinct_messages"]),
                    str(d["n"])]
        rows = [row("rule baseline", lb), row("offline gen.", lo)]
        if n_llm:
            rows.append(row("LLM (Gemini)", ll))
        B_.append(("table", "Message-level comparison on 24 fixed scenarios",
                   ["Generator", "Own nos.", "Uses mismatch", "Why this?", "Words", "Distinct", "n"],
                   rows, [0.22, 0.12, 0.16, 0.13, 0.12, 0.14, 0.11]))
        B_.append(("fig", "fig_messages", "Grounding properties of the coach generators on the same 24 "
                   "scenarios" + (" (LLM: model-written messages only)." if n_llm else ".")))
    h2("RQ4: Behavioural shift under assumed responsiveness")
    p(f"With heed <i>h</i> = 0.35 for the baseline, coaching reduced bias events from "
      f"{R['shift']['1.0']['none']['mistakes_mean']:.2f} to {R['shift']['1.0']['baseline']['mistakes_mean']:.2f} "
      "per session (Fig. 7). We then let the personalised coach be heeded ρ times as often. At ρ = 1 the "
      "two coaches are identical by construction, which serves as a check of the paired design. At ρ = "
      f"1.5 the paired reduction relative to the baseline was {f2(d15['mean'])} events [95% bootstrap CI "
      f"{f2(d15['ci_lo'])}, {f2(d15['ci_hi'])}], and at ρ = 2 it was {f2(d20['mean'])} "
      f"[{f2(d20['ci_lo'])}, {f2(d20['ci_hi'])}]. The rate of repeating a coached bias within three turns "
      f"fell from {f2(R['shift']['1.0']['baseline']['repeat_rate_mean'])} to "
      f"{f2(s20['llm']['repeat_rate_mean'])}. These numbers describe the assumed model, not people. They "
      "show that personalisation pays off only to the extent that it increases how often messages are "
      "acted on—exactly the quantity a human study must measure. The persona model has no "
      "habituation, so the coaching cooldown can only shrink these simulated effects (with "
      "<tt>COACH_COOLDOWN_TURNS = 0</tt> the baseline reaches 5.77 events). Whether fewer, non-repeated prompts are heeded more often is "
      "a question the human study must answer.")
    B_.append(("fig", "fig_shift", "Bias events per session versus the assumed heed ratio ρ; Δ is the "
               "paired baseline − personalised difference with a 95% bootstrap CI."))
    h2("Verification and QA audit")
    p("Acting as product owner, analyst and tester, we audited the prototype against its own claims "
      "before this evaluation, and found five defects. (i) The evaluation’s mismatch metric tested "
      "whether the log field was non-empty, but empty values were logged as the string "
      "“none”, so every session counted as flagged. (ii) The mismatch ground truth covered only "
      "panic-related claims, yet it was scored against all five mismatch codes. (iii) The grounding check "
      "counted the placeholder “no pattern detected” as a coaching message. (iv) Gemini 3 models spend "
      "thinking tokens out of the output budget—we measured about 510–590 per reply even at the low "
      "level—so under the original 220-token cap, which also used the model’s default (higher) thinking "
      "level, replies came back empty or truncated. Empty replies silently fell back to the offline "
      "generator, and truncated ones could pass the validator because the finish reason was never checked. (v) The “losses hurt about twice as much” claim "
      "lacked its proper source {c:tk92}. All five are fixed and covered by regression tests, and every "
      "number in this section was regenerated afterwards. The lesson: a fallback that is labelled in "
      "the UI can still hide a failure in aggregate metrics unless its source is logged and checked.")

    # ------------------------------------------------------------------ V
    h1("Discussion and Future Work")
    p("<i>Event is not motive.</i> A sale after a drop may be rebalancing, and an early profit-take may "
      "reflect a liquidity need. The system therefore says “may”, asks a reflection question, records "
      "the user’s stated reason, and states its own limits in every explanation. Each event also maps to "
      "a single trait, although a panic sale can equally express loss aversion. A natural extension "
      "replaces this hard mapping with event-to-trait likelihoods in a small Bayesian network, so that "
      "one event can update several traits in proportion to how diagnostic it is.")
    p("<i>Stability versus plasticity.</i> Deriving <i>n</i><sub>0</sub> from the quiz’s reliability "
      "protects the profile from noisy detectors, but Fig. 4 shows the cost: learning is slow when "
      "self-report is strongly biased. Hierarchical pooling across users, opportunity-specific "
      "likelihoods, and an <i>n</i><sub>0</sub> estimated from test–retest data would let the model trust "
      "behaviour sooner when the evidence warrants it. The confirming-only evidence for overconfidence "
      "drifts upward over long horizons and needs a principled counterfactual opportunity.")
    p("<i>Instrument and thresholds.</i> The quiz has three unvalidated items per trait, the detector "
      "thresholds (5%, 10%, 70%, 4 s) are hand-set, and the System-1 proxy ignores individual "
      "differences in baseline speed. Future work should calibrate items with item-response theory and "
      "learn thresholds and per-user latency baselines from data.")
    p("<i>Simulation circularity.</i> Because personas are built from the same constructs as the "
      "detectors, RQ1–RQ2 verify that the pipeline is internally coherent and RQ4 bounds what "
      "personalisation could achieve. None of them shows that the coach helps people.")
    p("<i>Language-model risks.</i> The validator is lexical and cannot catch subtle advice or "
      "overconfident framing. We observed the LLM stating “suggests panic selling” more assertively than "
      "the evidence warrants. Entailment-based checks of each message against the structured evidence, "
      "and human ratings of tone, are the next safeguards. Only structured tags—never names or "
      "logs—are sent to the API.")
    p("<i>Edge cases handled.</i> Buying with zero cash, selling an empty position, multiple asset "
      "decisions in one turn, over-allocated buys, duplicate assets, legacy profiles and extreme quiz "
      "answers (priors clipped to [0.01, 0.99]) are all handled and tested.")
    p("<i>Human study.</i> The prototype already supports a randomised, pre-registrable study. Using the "
      "random arm (personalised, baseline or none), the primary outcome is the rate of repeated coached "
      "biases; secondary outcomes are perceived personalisation (1–5 ratings), mismatch frequency and "
      "confidence calibration. It requires ethics approval, informed consent and de-identified logs.")

    # ------------------------------------------------------------------ VI
    h1("Conclusion")
    p("CogniFin Coach shows how a small, transparent cognitive architecture can perceive financial "
      "decisions, maintain an uncertainty-aware model of a user’s biases, confront self-report with "
      "behaviour, and explain each inference without letting a language model invent its grounds. "
      "Replacing an ad-hoc additive update with an opportunity-based Bayesian model, whose prior "
      "strength follows from the instrument’s reliability, turned behavioural evidence from a liability "
      "into a modest gain. The audit showed that silent fallbacks and sentinel values can invalidate an "
      "evaluation without breaking a single test. The decisive next step is a study with people.")

    appendix = [
        ("p", f"<b>Code repository:</b> {author['repo_url']}"),
        ("p", "<b>Environment:</b> Python ≥ 3.9 (tested on 3.13); the application uses only the standard "
              "library. <tt>pytest</tt> runs the tests and <tt>matplotlib</tt> regenerates the figures. "
              "Gemini is optional: put <tt>GEMINI_API_KEY</tt> (and optionally <tt>COGNIFIN_MODEL</tt>, "
              "default <tt>gemini-3-flash-preview</tt>) in <tt>.env</tt>; without a key the labelled "
              "offline generator is used."),
        ("code", [f"git clone {author['repo_url']}",
                  "cd cognifin-coach",
                  "pip install -r requirements.txt  # pytest, matplotlib",
                  "python app.py           # open http://localhost:8000",
                  "python -m pytest -q tests        # 39 tests",
                  "python -m cognifin.evaluate --n 300 --out results",
                  "python -m cognifin.evaluate --extra --out results",
                  "python -m cognifin.evaluate --llm-check --out results",
                  "python paper/make_figures.py && python paper/build_paper.py"]),
        ("p", "<b>Repository layout:</b> <tt>cognifin/</tt> (quiz, simulator, user model, mismatch, "
              "knowledge base, coaches, session, personas, evaluation), <tt>static/</tt> (UI), "
              "<tt>tests/</tt>, <tt>results/</tt> (evaluation outputs), <tt>paper/</tt> (this paper, "
              "figures, LaTeX source), <tt>presentation/</tt> (slides, speaker notes) and <tt>demo/</tt> "
              "(demonstration script)."),
    ]
    return {"title": title, "abstract": abstract, "keywords": keywords, "body": B_,
            "appendix": appendix, "references": REFERENCES}
