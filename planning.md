# TakeMeter — Planning Document
**Project:** AI201 Week 3 | CodePath Applications of AI Engineering  
**Community:** r/soccer  
**Classifier task:** Discourse quality classification  

---

## 1. Community

I chose r/soccer because it is one of the most active sports communities on Reddit, with thousands of posts and comments daily spanning match threads, transfer news, tactical breakdowns, and fan reactions. The discourse quality varies enormously in a way that is actually meaningful to participants: regulars in the community can immediately tell the difference between a post that's just venting after a loss and one that makes a real tactical argument. This variance — and the fact that the community itself implicitly values substantive discourse — makes it a strong fit for a classification task. The labels map onto distinctions that real members of the subreddit recognize and care about, not arbitrary categories imposed from outside.

---

## 2. Labels

I defined 3 labels:

### `analysis`
A post that makes a structured argument using tactics, statistics, historical context, or specific match evidence. The reasoning would hold up even if the emotional framing were removed. The post is trying to *explain* or *argue*, not just assert.

**Example 1:**
> "City's high defensive line has been their biggest vulnerability all season. Last night, three of the four goals conceded came from balls played in behind the last defender — two from long switches, one from a quick vertical pass. Guardiola needs to either drop the line or press higher to cut off the supply earlier."

**Example 2:**
> "People forget that Messi's Champions League record away from Barca is poor — 4 goals in 18 knockout-round away games across PSG and Inter Miami combined. That's not a sample size issue, that's a pattern worth discussing."

---

### `hot_take`
A bold, confident opinion stated without meaningful supporting evidence. The post may reference a vague feeling or one cherry-picked stat, but it asserts rather than argues. The distinguishing feature is confidence without reasoning.

**Example 1:**
> "Ronaldo is finished. Has been for two years. Anyone who still rates him is watching with nostalgia goggles on."

**Example 2:**
> "The Premier League is overrated and has been for a decade. La Liga produces better football, always has. The English just have better marketing."

---

### `reaction`
An immediate emotional response to a match result, goal, transfer news, or event. The post may include light observations about the game, but the primary content is expressing a feeling in the moment rather than building an argument.

**Example 1:**
> "I cannot believe what I just watched. That refereeing decision is an absolute disgrace. Season over."

**Example 2:**
> "That Bellingham goal. That BELLINGHAM GOAL. I am not okay. What a player."

---

## 3. Hard Edge Cases

**The hardest boundary:** reaction vs. analysis — posts that react emotionally to a match result but also include a specific tactical observation.

**Example ambiguous post:**
> "We were absolutely shocking today. The midfield had no shape, we kept losing second balls, and Rodri was invisible. Deserved to lose."

This could be `reaction` (venting after a loss) or `analysis` (identifying specific structural causes: midfield shape, second ball duels, a key player's absence).

**Decision rule:** If the post *leads with* emotion and the tactical observations are incidental/vague, label it `reaction`. If the post identifies a *specific, named structural reason* for the outcome — even if frustrated in tone — label it `analysis`. In the example above: "midfield had no shape" and "losing second balls" are vague observations used to justify the emotional response → `reaction`. A post that said "we lost the midfield battle because we played a 4-2-3-1 against their 4-3-3 and the wide 8s had too much freedom" would be `analysis`.

**Second edge case:** hot_take vs. analysis when a stat is cited.  
Decision rule: If the stat is the *foundation* of an argument (e.g., it leads to a conclusion with reasoning), it's `analysis`. If the stat is *decorative* — dropped in to add credibility to an assertion — it's `hot_take`.

---

## 4. Data Collection Plan

**Source:** r/soccer — top posts and comments from the past 3 months, using Reddit's public interface or the PRAW Python library.

**Target distribution:**
- `analysis`: ~70 examples
- `hot_take`: ~70 examples
- `reaction`: ~70 examples
- Total: ~210 examples (buffer above the 200 minimum)

**Collection strategy:** Pull from a mix of post types to ensure diversity:
- Match threads and post-match discussions → good source of `reaction` and `analysis`
- General discussion / opinion threads → good source of `hot_take` and `analysis`
- Transfer news threads → good source of `reaction`

**If a label is underrepresented after 200 examples:** Specifically target threads where that type is likely to appear. For example, if `analysis` is underrepresented, search for tactical discussion posts or threads titled "Why did X lose?" If `reaction` is underrepresented, pull from live match threads.

**What I will NOT collect:** Posts under 10 words (too little signal), posts that are primarily image/video embeds with no text, or posts that are just sharing news links with no commentary.

---

## 5. Evaluation Metrics

I will report the following:

**Overall accuracy** — fraction of test examples correctly classified by each model. This gives a quick top-line comparison between the fine-tuned model and the baseline.

**Per-class F1 score** — the harmonic mean of precision and recall for each label. This is necessary because accuracy alone is misleading if the classes are slightly imbalanced or if the model is performing well on one class but failing on another. F1 tells me *which specific boundaries the model has and hasn't learned*.

**Precision and recall per class** — to distinguish between "the model is too conservative about this label" (high precision, low recall) vs. "the model over-predicts this label" (high recall, low precision).

**Confusion matrix** — to identify which label pairs are being confused and in which direction. I expect the `reaction`/`analysis` boundary to show up as the most confused pair, based on my experience labeling.

Accuracy alone is insufficient here because this is a 3-class task where the per-class boundaries have different difficulty levels. A model that predicts `reaction` for everything might hit 40% accuracy if that's the majority class, but that's useless. F1 per class catches this.

---

## 6. Definition of Success

A classifier is genuinely useful for r/soccer if:
- **Overall accuracy ≥ 70%** on the test set for the fine-tuned model
- **Per-class F1 ≥ 0.60** for all three labels (no class is being completely missed)
- **Fine-tuned model meaningfully outperforms the zero-shot baseline** — at minimum +10 percentage points in overall accuracy

"Good enough for deployment" in a real community tool would mean: if a moderator or community bot used this to surface high-quality analysis posts, the precision on `analysis` should be ≥ 0.70 so that most posts it flags are actually substantive. I'd accept lower recall (missing some real analysis posts) over high false positives.

If the fine-tuned model does not beat the zero-shot baseline, that's a signal the labels are inconsistent or the dataset is too small/imbalanced — I would investigate before calling it done.

---

## AI Tool Plan

### Label stress-testing
Before annotating 200 examples, I will give Claude my 3 label definitions and the edge case description and ask it to generate 10 posts that sit at the boundary between `reaction` and `analysis`, and 10 that sit between `hot_take` and `analysis`. If any of those posts can't be cleanly classified using my decision rules, I'll tighten the definitions before starting annotation.

### Annotation assistance
I will use an LLM (Claude or Groq) to pre-label batches of ~50 posts at a time by providing it the label definitions and asking it to assign one label per post. I will then review and correct every pre-assigned label individually — I will not skim. Pre-labeled examples will be flagged with a `pre_labeled` column in the CSV set to `True` so I can track which ones were AI-assisted. This will be disclosed in the README AI usage section.

### Failure analysis
After fine-tuning, I will paste my full list of wrong predictions into Claude and ask it to identify patterns: are there consistent features in misclassified posts (short length, sarcasm, a specific label pair, topic-specific language)? I will then verify each pattern by re-reading the examples myself before including it in the evaluation report. Any patterns Claude identifies that I can't verify on re-reading will be discarded.

---

## Hard Annotation Decisions (updated during Milestone 3)

*This section will be filled in during data collection. At least 3 difficult cases will be documented here with: the post text, which labels it could belong to, and the final decision + reasoning.*

---

## Stretch Features

*This section will be updated before starting any stretch features.*

- [ ] Inter-annotator reliability
- [ ] Confidence calibration
- [ ] Error pattern analysis
- [ ] Deployed interface
