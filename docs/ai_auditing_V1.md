# Game English Text AIGC Detection — Evaluation & Product Capability Report

A combined English report synthesizing two evidence sources: a hands-on benchmark of commercial and open-source detection products against a standardized game-text dataset, and a vendor capability matrix covering pricing, compliance, multilingual support, effectiveness, and sentence-level highlighting.

---

## 1. Executive Summary

|                          |                                                                                                                                                                                   |
| :----------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
|  **Preferred candidate** | **GPTZero** — 100% AI-content recall, 90.5% F1, 89.2% valid coverage. Ranks first in the hands-on benchmark and is the recommended front-runner for the current proof-of-concept. |
|    **Benchmark scope**   |            **6 commercial + 3 open-source** — six commercial detectors tested on 37 English game texts; three open-source algorithms reproduced locally for comparison.           |
| **Capability landscape** |      **7 commercial + 12 open-source** — pricing, compliance certificates, multilingual claims, and sentence-highlighting reviewed across the broader AIGC detection market.      |

The two sources are complementary. The **benchmark** measures what actually happened on a fixed, game-specific dataset — real false-positive and false-negative rates, not vendor marketing. The **capability matrix** adds the procurement dimensions the benchmark cannot capture alone: per-1k-word cost, compliance certifications, language coverage, and whether a detector can highlight the specific spans it flags. Together they support a single conclusion: **GPTZero is the best balanced commercial choice for game English text, but no product can be used as a sole source of truth — every result still requires human review.**

---

## 2. Scope & Method

![Methodology — two complementary evidence sources](assets/images/ai_auditing/methodology-workflow.png)

### A · Hands-on benchmark

Manual testing of commercial detection products on a unified set of English game copy, evaluated on three axes:

- **Valid coverage** — how many samples return a usable verdict
- **Human-content false-positive risk** — protecting human writers from misclassification
- **AI-content detection completeness** — how much AI text is actually caught

Dataset: **37 English game texts** (18 human-written, 19 AI-generated; 99–1833 characters). Three open-source algorithms were also reproduced locally on the same 37 samples.

### B · Vendor capability research

Cross-referencing each product's official pricing and public compliance statements:

- **Price & API cost** — entry tier and per-1k-word API economics
- **Compliance** — SOC 2, GDPR, DPA, EU hosting, model-training policy
- **Multilingual** — claimed language coverage vs. verified English strength
- **Effectiveness & highlighting** — independent-test narrative and sentence-level span support

Vendor accuracy claims are generally optimistic; the "effectiveness" column leans on independent evaluations and low-false-positive narratives rather than marketing "99%".

---

## 3. Test Dataset

The benchmark uses **37 English game-text samples — 18 human-written, 19 AI-generated**, spanning short dialogue and longer narrative (99–1833 characters) to expose how detectors adapt to text type and input length.

![Test dataset composition](assets/images/ai_auditing/dataset-composition.png)

**Sources**

- **Human-written · 18 samples** — drawn from the public **MobileGameNPC** dataset and authentic in-game text published on public reference pages, primarily covering The Elder Scrolls V: Skyrim, Dark Souls, Baldur's Gate 3, The Witcher, Fallout, BioShock, Portal 2, and Elden Ring. Exact titles, reference links, and descriptions are recorded in the dataset source fields.
- **AI-generated · 19 samples** — constructed LLM-style text labeled in the dataset as **GPT-style, Claude-style, or generic-style**, covering templated, narrative, character-driven, and game-like writing at varying detection difficulty. Labels describe writing style and do not establish verifiable provenance to specific model versions.

---

## 4. Commercial Detector Evaluation

### Overall ranking

![Commercial detector overall scores](assets/images/ai_auditing/commercial-ranking.png)

> Ranking covers products with a computable score. **Copyleaks** (execution too slow to finish) is scored 0 and excluded. The composite score is **35% human-content correct rate + 30% AI recall + 20% F1 + 15% valid coverage** — a relative comparison within this sample, not a vendor capability rating. Winston AI is scored on its 11 valid results, but its 29.7% coverage makes its score less stable and representative than fully-tested products.

### Metric definitions

|     Metric    |                                                       Meaning                                                       |
| :-----------: | :-----------------------------------------------------------------------------------------------------------------: |
|  **Coverage** | Share of the 37 texts that returned a clear verdict. Failures or too-short texts are not counted as human verdicts. |
| **Human FPR** |                  Share of human texts misjudged as AI. Lower = better protection for human writers.                 |
| **AI Recall** |                       Share of AI texts correctly identified. Higher = fewer missed AI texts.                       |
| **Precision** |                              Among all "AI" verdicts, the share that is truly AI text.                              |
|     **F1**    |                           Harmonic mean of precision and recall; higher = better balance.                           |
|    **MCC**    |                    Correlation across all correct/incorrect verdicts; closer to 1 = more stable.                    |

### Cross-product comparison

|   Product  | Score |     Input limit    | Valid |  Cov.  |  TP |  FP |  TN |  FN |  Acc. |  Prec. | Recall |  FPR  |   F1  |  MCC |
| :--------: | :---: | :----------------: | :---: | :----: | :-: | :-: | :-: | :-: | :---: | :----: | :----: | :---: | :---: | :--: |
|   GPTZero  |  86.5 |   ≥250 characters  | 33/37 |  89.2% |  19 |  4  |  10 |  0  | 87.9% |  82.6% | 100.0% | 28.6% | 90.5% | 0.77 |
|  Pangram 4 |  82.5 |  ≥50 English words | 30/37 |  81.1% |  19 |  4  |  7  |  0  | 86.7% |  82.6% | 100.0% | 36.4% | 90.5% | 0.73 |
| Winston AI |  77.6 |   ≥500 characters  | 11/37 |  29.7% |  5  |  0  |  4  |  2  | 81.8% | 100.0% |  71.4% |  0.0% | 83.3% | 0.69 |
|   ZeroGPT  |  72.5 |    none observed   | 37/37 | 100.0% |  11 |  4  |  14 |  8  | 67.6% |  73.3% |  57.9% | 22.2% | 64.7% | 0.36 |
|   Sapling  |  64.4 |  ≥50 English words | 34/37 |  91.9% |  17 |  11 |  4  |  2  | 61.8% |  60.7% |  89.5% | 73.3% | 72.3% | 0.21 |
|  Copyleaks |  0.0  | execution too slow |  0/37 |  0.0%  |  —  |  —  |  —  |  —  |   —   |    —   |    —   |   —   |   —   |   —  |

> Score coloring: **>80 good**, **60–80 fair**, **<60 poor**. TP = AI correctly flagged; FP = human misflagged as AI; TN = human correctly cleared; FN = AI missed.

> **Fair-comparison caveat:** the texts that Pangram, GPTZero, and Sapling failed to process are mostly short human texts, so their FPR reflects only the successfully-tested subset and may understate the real short-text false-positive risk. Winston AI's 0% FPR across 11 samples must not be read as superior to other products.

### Product-by-product analysis

**GPTZero — 86.5 · Preferred overall candidate**

- Valid coverage 89.2% (33/37) · AI recall 100.0% (0 of 19 missed) · Human FPR 28.6% (4 of 14 flagged)
- **Strengths:** all 19 valid AI samples detected — ideal first-pass screen; leads comparable products on F1 and MCC; 33/37 samples returned a result.
- **Weaknesses:** 4 of 14 detected human texts misflagged — review still required; 4 short human texts returned no result; ≥250-character minimum limits short dialogue and brief item descriptions.
- **Recommendation:** preferred candidate for the current proof-of-concept, paired with human review and a second detector.

**Pangram 4 — 82.5 · High-recall alternative**

- Valid coverage 81.1% (30/37) · AI recall 100.0% · Human FPR 36.4% (4 of 11 flagged)
- **Strengths:** 100% AI recall — low miss risk; 90.5% F1 — strong AI discrimination.
- **Weaknesses:** only 30/37 covered, all 7 missing are human texts; 36.4% FPR on detected human text — not for attribution; ≥50-word minimum blocks unconcatenated short dialogue.
- **Recommendation:** fits a "rather over-screen than miss AI" first-pass workflow.

**Winston AI — 77.6 · Limited input compatibility**

- Valid coverage 29.7% (11/37) · AI recall 71.4% (2 of 7 missed) · Human FPR 0.0% (0 of 4 flagged)
- **Strengths:** no human false positives among completed samples; 100% precision on the limited AI sample.
- **Weaknesses:** only 29.7% coverage — poorly matched to short game text; only 7 valid AI samples, 2 missed; ≥500-character minimum caused 26 missed results.
- **Recommendation:** suitable for longer documents meeting its requirements, not a general short-dialogue detector.

**ZeroGPT — 72.5 · Full-coverage supplemental**

- Valid coverage 100.0% (37/37) · AI recall 57.9% (8 of 19 missed) · Human FPR 22.2% (4 of 18 flagged)
- **Strengths:** all 37 samples processed — best short-text compatibility this round; 22.2% FPR is the lowest among high-coverage products; no length limit observed.
- **Weaknesses:** 8 of 19 AI texts missed — only 57.9% recall; not suitable as a sole detector.
- **Recommendation:** low-cost auxiliary signal or short-text backfill; do not use alone for final judgment.

**Sapling — 64.4 · Supplemental signal only**

- Valid coverage 91.9% (34/37) · AI recall 89.5% (2 of 19 missed) · Human FPR 73.3% (11 of 15 flagged)
- **Strengths:** 91.9% coverage; 89.5% AI recall.
- **Weaknesses:** 11 of 15 human texts flagged as AI — 73.3% FPR; only 60.7% precision, sharply raising review cost; ≥50-word minimum requires merging short texts first.
- **Recommendation:** not as a primary detector; retain only as a weak auxiliary feature in a multi-model ensemble.

**Copyleaks — 0.0 · Not adopted for this project**

- **Weakness:** execution took too long to finish the unified benchmark within an acceptable window.
- **Recommendation:** not adopted; reassess only if a future scenario allows long-cycle asynchronous processing.

### Performance by game text type

|  Product  |       NPC dialogue (11)      |        Quest text (10)       |     Item description (7)    |      Worldbuilding (9)     |
| :-------: | :--------------------------: | :--------------------------: | :-------------------------: | :------------------------: |
|  GPTZero  |  F1 90.9% · 7/11 · FPR 50.0% | F1 90.9% · 10/10 · FPR 20.0% |  F1 88.9% · 7/7 · FPR 33.3% | F1 90.9% · 9/9 · FPR 25.0% |
|  ZeroGPT  | F1 44.4% · 11/11 · FPR 33.3% |  F1 88.9% · 10/10 · FPR 0.0% |  F1 57.1% · 7/7 · FPR 33.3% | F1 66.7% · 9/9 · FPR 25.0% |
| Pangram 4 |  F1 100.0% · 7/11 · FPR 0.0% | F1 90.9% · 10/10 · FPR 20.0% |   F1 100.0% · 4/7 · FPR —   | F1 76.9% · 9/9 · FPR 75.0% |
|  Sapling  |  F1 83.3% · 8/11 · FPR 66.7% | F1 71.4% · 10/10 · FPR 80.0% | F1 44.4% · 7/7 · FPR 100.0% | F1 83.3% · 9/9 · FPR 50.0% |

> Cell format: F1 · coverage (valid/total) · human FPR. FPR is computed on successfully-tested human texts only; "—" means no human text was tested in that cell.

### Scenario-based selection

|            Scenario           |                                                     Pick                                                    |
| :---------------------------: | :---------------------------------------------------------------------------------------------------------: |
|  **Balanced screening first** |       **GPTZero** — recall, F1, and MCC are well balanced; AI verdicts still route into human review.       |
|   **AI-completeness first**   |      **GPTZero / Pangram 4** — both hit 100% AI recall, but Pangram has higher FPR and short-text gaps.     |
| **Short-text coverage first** | **ZeroGPT** — the only product to return results for all 37, but misses ~42% of AI text; use as supplement. |
|      **Do not use alone**     |                          **Sapling** — 73.3% FPR inflates review workload and cost.                         |
|    **Input compatibility**    |                     **Winston AI** — 29.7% coverage; not a general short-text detector.                     |
|        **Not adopted**        |                      **Copyleaks** — execution too slow for this project's turnaround.                      |

### Representative classification errors

These cases show that game slang, character-driven voice, and highly templated authentic game text can all trip detectors.

|   Product  | Sample |    Error   |       Type       |                                                      Excerpt                                                      |
| :--------: | :----: | :--------: | :--------------: | :---------------------------------------------------------------------------------------------------------------: |
|   GPTZero  |   53   | Human → AI |   NPC dialogue   |      "I am Andrew Ryan, and I'm here to ask you a question. Is a man not entitled to the sweat of his brow?…"     |
|   GPTZero  |   22   | Human → AI |   Worldbuilding  |             "The Witchers — once necessary guardians against the monsters that plagued the Continent…"            |
|   ZeroGPT  |   54   | Human → AI |   NPC dialogue   |  "Alright, I've been thinking. When life gives you lemons, don't make lemonade. Make life take the lemons back!…" |
|   ZeroGPT  |   60   | AI → human |    Quest text    | "The city of Vaelora had not seen rain in forty years. Its canals, once the arteries of a thriving trade empire…" |
|  Pangram 4 |   20   | Human → AI |   Worldbuilding  |          "The Aedra are the Eight Divines who sacrificed their power to create Mundus, the mortal plane…"         |
|   Sapling  |   41   | AI → human | Item description |      "Iron Ring of the Gatewarden — a simple iron band, unadorned save for a single notch on its inner face…"     |
| Winston AI |   62   | AI → human | Item description |            "The Lantern of the Drowned Chapel — a lantern of tarnished brass, its glass clouded over…"            |

---

## 5. Open-Source Detection Algorithm Evaluation

Three open-source algorithms — **DAMASHA-RMC**, **MPU / En-v3-short**, and **Fast-DetectGPT** — were reproduced locally at document level on the same 37 English game texts. Open-source results are shown independently and are **not** included in the commercial ranking.

![Open-source algorithms — F1 vs human FPR](assets/images/ai_auditing/opensource-comparison.png)

> AI is the positive class; table sorted by F1. Latency reflects this CPU-only run only. MPU used batch-amortized timing while DAMASHA-RMC and Fast-DetectGPT used per-document timing — do not rank speed from these numbers.

**Fast-DetectGPT — High-recall research candidate**

- **Strengths:** all 19 AI samples detected — 100% recall; highest F1 (74.5%) and AUROC (70.8%) of the three; all 37 samples inferred without failure.
- **Risks:** 13 of 18 human texts misflagged — 72.2% FPR; uses a memory-adapted gpt2/gpt2 config, not the paper's full setup; raw curvature score is uncalibrated — not an AI probability.
- **Use:** research on high-recall screening features; not for production or automated action.

**MPU / En-v3-short — Relatively balanced research candidate**

- **Strengths:** 33.3% FPR — lowest of the three; 66.7% precision and 66.7% human-correct rate; full input coverage, no misses.
- **Risks:** 63.2% recall — 7 of 19 AI texts missed; 64.9% F1 — insufficient for standalone final judgment; CPU run, batch-amortized timing not comparable to per-document.
- **Use:** threshold calibration and domain fine-tuning; auxiliary feature in a multi-model ensemble.

**DAMASHA-RMC — Limited reproduction fidelity**

- **Strengths:** 37/37 returned results — 100% coverage; 63.2% recall — catches some obvious AI text; reproducible CPU inference from released code + local checkpoint.
- **Risks:** only 61.5% F1, 44.4% FPR; released checkpoint/code lack the paper's BiGRU — architecture mismatch; dual encoders share RoBERTa token IDs; official demo needs ≥30 words.
- **Use:** reproduction and architecture study; not a current business detector.

The F1-vs-FPR picture shows why none of these is production-ready alone:

![F1 vs human-FPR tradeoff — commercial and open-source](assets/images/ai_auditing/f1-fpr-tradeoff.png)

---

## 6. Product Capability Matrix

Beyond the hands-on benchmark, the following matrix cross-checks each product's official pricing and public compliance statements (reviewed ~2026-08). It covers **7 commercial** detectors and **12 open-source** methods. Dimensions: **price · compliance · multilingual · effectiveness · sentence highlighting**. Prices change often — re-verify the vendor's pricing/security pages before signing or integrating.

### Commercial

|     Product    |                   Price (entry)                   |        API (~per 1k words)       |                       Compliance                      |           Multilingual           |                  Effectiveness (pragmatic)                  |      Sentence highlight      |
| :------------: | :-----------------------------------------------: | :------------------------------: | :---------------------------------------------------: | :------------------------------: | :---------------------------------------------------------: | :--------------------------: |
|     GPTZero    | Free 10k words/mo; Pro ~$46/mo (500k words + API) |            ~$0.09–0.15           |           SOC 2 Type II, GDPR; DPA available          | EN strongest; DE/FR/ES/PT usable |  85–95% long-form EN; weak short/rewritten; restrained FPR  |  ✅ Yes · sentence/paragraph  |
| Originality.ai |         PAYG $30 ≈ 300k words; Pro ~$15/mo        |    ~$0.10 (AI+plagiarism ~2×)    | SOC 2 / GDPR; may train by default → Opt-Out required |        claims 30 languages       | High recall, higher FPR; paraphrasing sometimes more stable |             ✅ Yes            |
|    Copyleaks   |           Personal ~$14–17/mo; API quote          | enterprise quote (legacy ~$0.03) |        PCI / SOC 2 / SOC 3 / GDPR + EU hosting        |       AI 30+ (incl. CN/JP)       |           Strong on essays; ~70% after humanizing           |      ✅ Yes · AI Phrases      |
|   Winston AI   |      Essential $18/mo (or $10/yr, 100k words)     |       ~$0.18/mo · ~$0.10/yr      |      SOC 2 Type 2, GDPR; does not train on scans      |   10+ incl. Simplified Chinese   |             Balanced, relatively controlled FPR             |    ✅ Yes · Prediction Map    |
|    Pangram 4   |           Web $20/mo; free 2k words/day           | $0.50 (P3 $0.05, EOL 2026-09-30) |   SOC 2 Type 2; Enterprise no student-data training   |       20+ incl. CN/JP/KR/AR      |     Strongest low-FPR narrative; robust mixed/humanizer     |   ✅ Yes · fine-grained span  |
|     Sapling    |             Web near-free; API ~$25/mo            |        char-billed; quote        |                  on-prem / HIPAA BAA                  |          English-focused         |                Medium; humanized misses ~30%                |   ✅ Yes · sentence + token   |
|     ZeroGPT    |                 Free + PRO ~$10/mo                |           ~$0.034–0.069          |          ⚠️ Weak public compliance materials          |        claims all; EN best       |           Coarse screening; not for final judgment          | ✅ Yes · sentence + AI% gauge |

### Open-source comparison (highlighting + language)

|         Method        |                 Sentence/span highlight                 |                       Effectiveness signal                      |             Languages             |               Cost              |      Compliance      |
| :-------------------: | :-----------------------------------------------------: | :-------------------------------------------------------------: | :-------------------------------: | :-----------------------------: | :------------------: |
|      DAMASHA-RMC      |             Native token/span multi-segment             |            token-F1 ~0.98, strict span-F1 ~0.41–0.45            |     EN-centric; model-agnostic    |       self-hosted GPU/CPU       | data stays in-domain |
|   MPU / En-v3-short   |           Sentence scores; per-sentence calls           |              HC3 sentence ~85 F1; dialogue-friendly             |        English (HC3 subset)       |           self-hosted           | data stays in-domain |
|        SeqXGPT        |             Native sentence Human/AI labels             |             90%+ Macro-F1 on same-distribution mixed            | EN-centric; architecture-agnostic |      self-hosted + proxy LM     | data stays in-domain |
| Binoculars / Lastde++ |           Whole-text default; windowing needed          |                 High long-form AUROC; weak short                |       EN + UR/RU/BG/AR tests      |       dual 7B or sampling       | data stays in-domain |
|       DetectGPT       |           None native; perturbation curvature           |            GPT-NeoX fake-news AUROC 0.95 (ICML 2023)            |    English (GPT-2/T5 backbone)    | self-hosted; ~100 perturbations | data stays in-domain |
|     Fast-DetectGPT    |           Conditional curvature; token scores           | 5-model AUROC 0.99; ChatGPT/GPT-4 0.93; 340× faster (ICLR 2024) |    English (GPT-J/Neo scoring)    |    self-hosted single forward   | data stays in-domain |
|      Ghostbuster      |            Token features → linear classifier           |     99.0 F1 cross-domain; +7.5 F1 vs prior SOTA (NAACL 2024)    |     English (weak-LM features)    |  self-hosted + weak-LM ensemble | data stays in-domain |
|         RADAR         |             None native; RoBERTa classifier             |      Robust across 8 LLMs; paraphrase-robust (NeurIPS 2023)     |      English (RoBERTa-large)      |     single GPU; HF callable     | data stays in-domain |
|     DNA-DetectLLM     |                 Token repair difficulty                 |         AUROC +5.55%, F1 +2.08% (NeurIPS 2025 Spotlight)        |         EN (Falcon-7B ref)        |    self-hosted; two forwards    | data stays in-domain |
|        GECScore       |                None; grammar-error score                |        XSum+WritingPrompts avg AUROC 98.6% (COLING 2025)        |   English (grammar-model bound)   |   self-hosted + grammar model   | data stays in-domain |
|          GLTR         | Word-level color (top10 green/100 yellow/1k red/purple) |         Human-assisted detection 54%→72% (ACL 2019 Demo)        |         Language-agnostic         |     self-hosted; GPT-2/BERT     | data stays in-domain |
|    humanize-chinese   |           20+ rules + 14 statistical features           | Chinese AI-writing fingerprints (three-part, filler, templates) |        Chinese-specialized        | pure Python CPU, zero inference | data stays in-domain |

### How to choose by game scenario

|                        Scenario                       |                                                                                     Pick                                                                                    |
| :---------------------------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
|             **Long design-doc screening**             |   Prefer **Pangram 4** or **Copyleaks** (low FPR / compliance), with **GPTZero** / **Winston** for double-blind. Tight API budget → self-built **Binoculars / Lastde++**.   |
|      **Need span highlighting for human review**      |             All commercial products highlight sentence-level. For controllable multi-span, **DAMASHA-RMC** / **SeqXGPT**; don't trust vendor color blocks alone.            |
|             **Short dialogue / NPC lines**            | Commercial minimum lengths and short-window variance are pitfalls. **MPU short** per-sentence scoring + scene aggregation; a single-line result is not grounds for penalty. |
| **Compliance-sensitive (outsourced, data residency)** |           **Copyleaks** (EU hosting), **Winston** (no training), **Pangram Enterprise**, **Sapling on-prem**. Originality must Opt-Out. ZeroGPT use with caution.           |

---

## 7. Applications in Game Development

AIGC text detection can be embedded across the content lifecycle — from planning to live operations — to flag content that needs further checking, not to replace editors, testers, or compliance staff.

1. **Project Initiation & Worldbuilding** — worldbuilding, story outlines, character backstories, and gameplay docs — verify AI-assisted writing declarations and surface templated content that needs editorial depth.
2. **Writing & Content Production** — NPC dialogue, quest text, item descriptions, and narration — risk-tier before bulk ingestion, routing high-risk or conflicting verdicts to human review.
3. **Outsourcing & Vendor Acceptance** — writers' and content vendors' staged deliveries — combine results with contract terms, AI-usage declarations, and revision history for sampling and QA.
4. **QA Sampling & Release** — new or modified copy in release builds — incremental scanning of high-risk text, short dialogue, and concentrated edits; log undetectable samples separately.
5. **Localization & Multilingual Review** — English translation, rewriting, and localized deliverables — catch undeclared large-scale LLM rewriting. Conclusions apply to English only; do not extrapolate to other languages.
6. **Live Operations & UGC Governance** — event copy, seasonal story, ops announcements, and user submissions — queue prioritization and anomaly sampling; final action stays with humans + business rules.

> **Usage principle:** detection results are a risk signal only — never the sole basis for author identification, violation judgment, or penalties. Preserve creation process, version history, source declarations, and human-review notes alongside them.

---

## 8. Bottom Line

|                                   |                                                                                                                                                                                                                             |
| :-------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
|     **For game English text**     |                                        **GPTZero** — best overall balance: 100% AI recall, 90.5% F1, restrained FPR, sentence-level highlight, and a mature API path for a fast PoC.                                        |
| **Low-FPR / compliance priority** |                                                                     **Pangram 4 · Copyleaks** — Pangram 4 for the strongest low-false-positive narrative                                                                    |
|        **Hard constraint**        | **Human review required** — no product achieves certainty here: every detector produced false positives or misses. Use results for risk tiering and review prioritization, never for penalties, settlement, or attribution. |
