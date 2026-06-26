# TakeMeter

A fine-tuned text classifier that evaluates discourse quality in the r/soccer subreddit.
Built for AI201 | Applications of AI Engineering — CodePath Summer 2026.

---

## Community

I chose **r/soccer** because it is one of the most active sports communities on Reddit,
with thousands of posts daily that vary enormously in discourse quality. The same event —
a match result, a transfer, a controversial call — can generate a data-backed tactical
breakdown, a bold unsupported opinion, and a pure emotional outburst, sometimes in
adjacent comments. This variance is meaningful to the community itself: regulars
implicitly value substantive posts over noise. That makes the label distinctions grounded
in real community norms rather than arbitrary categories.

---

## Label Taxonomy

### `analysis`
The post makes a structured argument using tactics, statistics, historical context, or
specific match evidence. The reasoning would hold up even if the emotional framing were
removed — the post is trying to *explain* or *argue*, not just assert.

**Example 1:**
> "City's high defensive line has been their biggest vulnerability all season. Last night,
> three of the four goals conceded came from balls played in behind the last defender —
> two from long switches, one from a quick vertical pass. Guardiola needs to either drop
> the line or press higher to cut off the supply earlier."

**Example 2:**
> "People forget that Messi's Champions League record away from Barca is poor — 4 goals
> in 18 knockout-round away games across PSG and Inter Miami combined. That's not a
> sample size issue, that's a pattern worth discussing."

---

### `hot_take`
A bold, confident opinion stated without meaningful supporting evidence. The post may
reference a vague feeling or a single cherry-picked stat, but it asserts rather than argues.

**Example 1:**
> "Ronaldo is finished. Has been for two years. Anyone who still rates him is watching
> with nostalgia goggles on."

**Example 2:**
> "The Premier League is overrated and has been for a decade. La Liga produces better
> football, always has. The English just have better marketing."

---

### `reaction`
An immediate emotional response to a match result, goal, transfer news, or event. The
post may include light observations, but the primary content is expressing a feeling in
the moment rather than building an argument.

**Example 1:**
> "I cannot believe what I just watched. That refereeing decision is an absolute disgrace.
> Season over."

**Example 2:**
> "That Bellingham goal. That BELLINGHAM GOAL. I am not okay. What a player."

---

## Data Collection

**Source:** r/soccer — top posts and top-level comments from the past 3 months, collected
using PRAW (Python Reddit API Wrapper) and supplemented with manual collection.

**Labeling process:** Posts were pre-labeled using Groq's `llama-3.3-70b-versatile` with
the label definitions provided as a system prompt. Each pre-label was then reviewed and
corrected manually. However, the review was not thorough enough — the pre-labeler
over-assigned `reaction`, and not all corrections were made before training.

**Label distribution (final dataset):**

| Label | Count | Percentage |
|---|---|---|
| analysis | 41 | 13.7% |
| hot_take | 38 | 12.7% |
| reaction | 221 | 73.7% |
| **Total** | **300** | **100%** |

**3 difficult-to-label examples:**

1. *"We were absolutely shocking today. The midfield had no shape, we kept losing second
   balls, and Rodri was invisible. Deserved to lose."*
   Could be `reaction` (venting) or `analysis` (tactical observation). Labeled `reaction`
   because the tactical observations are vague and incidental to the emotional framing —
   no specific structural explanation is given.

2. *"Mbappe has been terrible — his xG is 0.3 this season."*
   Could be `hot_take` or `analysis`. Labeled `hot_take` because the single stat is
   cherry-picked and used decoratively rather than as part of a reasoned argument.

3. *"I knew this would happen. Klopp always struggles in must-win away games at the
   Bernabeu. It's mental, not tactical."*
   Could be `hot_take` or `analysis`. Labeled `hot_take` — cites a vague pattern without
   verifiable evidence and attributes it to an unfalsifiable cause ("mental").

---

## Fine-Tuning Approach

**Base model:** `distilbert-base-uncased` (HuggingFace)

**Training setup:** Fine-tuned on Google Colab using a free T4 GPU. The starter notebook
handled tokenization, the train/validation/test split (70% / 15% / 15%), and the training
loop using the HuggingFace `Trainer` API.

**Hyperparameter decision:** Used the default learning rate of `2e-5` and `3` epochs with
batch size `16`. Given only ~210 training examples (70% of the 300-row dataset), increasing epochs beyond 3 risked
overfitting to the majority class even faster. A lower learning rate was considered but
the bottleneck was clearly data distribution, not optimization dynamics.

---

## Baseline

**Model:** Groq `llama-3.3-70b-versatile` (zero-shot, no task-specific training)

**Prompt used:**

```
System: You are labeling r/soccer posts for a text classification dataset.
Assign exactly one label from: analysis, hot_take, reaction.
- analysis: structured argument using tactics, stats, or evidence. Reasoning holds
  without the emotional framing.
- hot_take: bold opinion asserted without meaningful evidence. Confident but doesn't argue.
- reaction: immediate emotional response to a match/event. Primary content is feeling,
  not argument.
Respond with ONLY the label name, nothing else.

User: {post text}
```

**How results were collected:** The notebook classified every example in the locked test
set (45 examples) using this prompt via the Groq API and computed overall accuracy
against the true labels.

---

## Evaluation Report

**Test set size:** 45 examples
**Fine-tuned model:** `distilbert-base-uncased`
**Zero-shot baseline:** Groq `llama-3.3-70b-versatile`

### Overall Accuracy

| Model | Accuracy |
|---|---|
| Zero-shot baseline (Groq llama-3.3-70b) | 84.44% |
| Fine-tuned DistilBERT | 73.33% |
| **Difference (fine-tuned − baseline)** | **−11.11 pp** |

### Per-Class Metrics (Fine-Tuned Model)

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| analysis | 0.000 | 0.000 | 0.000 | 6 |
| hot_take | 0.000 | 0.000 | 0.000 | 6 |
| reaction | 0.733 | 1.000 | 0.846 | 33 |
| **Macro avg** | **0.244** | **0.333** | **0.282** | 45 |
| **Weighted avg** | **0.538** | **0.733** | **0.621** | 45 |

*Per-class metrics for the baseline were not exported from the notebook — only overall
accuracy is available for the zero-shot model.*

### Confusion Matrix (Fine-Tuned Model)

Rows = true label, columns = predicted label.

| True \ Predicted | analysis | hot_take | reaction |
|---|---|---|---|
| **analysis** | 0 | 0 | 6 |
| **hot_take** | 0 | 0 | 6 |
| **reaction** | 0 | 0 | 33 |

### 3 Wrong Predictions — Analysis

**Wrong prediction 1:**
- Post: *"Trent Alexander-Arnold at Real Madrid will be a disaster. He can't defend and
  La Liga forwards will expose him every week."*
- True label: `hot_take` | Predicted: `reaction`
- Why it failed: The post is short and assertive with no match-event trigger. The model
  likely latched onto confident/negative tone and mapped it to `reaction` because the
  training set associated strong emotion with that label. It hasn't learned that
  `hot_take` is about unsubstantiated assertion rather than emotional register.

**Wrong prediction 2:**
- Post: *"Watching United's press tonight was painful — they're completely disorganized
  out of possession, no triggers, no compactness, just chasing."*
- True label: `analysis` | Predicted: `reaction`
- Why it failed: The post contains tactical vocabulary ("press," "triggers,"
  "compactness") but is also emotionally charged ("painful"). With only 6 `analysis`
  examples in the test set and ~30 in training, the model never learned to recognize
  tactical language as a signal for `analysis` — it defaulted to `reaction` for anything
  match-related.

**Wrong prediction 3:**
- Post: *"Vinicius is the best player in the world right now. Not debatable."*
- True label: `hot_take` | Predicted: `reaction`
- Why it failed: Short, declarative, emotionally confident. The model has no concept of
  `hot_take` at all (F1 = 0.000) — every prediction is `reaction`. This post sits
  exactly in the middle of the `hot_take` definition but the model never learned that
  boundary.

### Sample Classifications

Posts run through the fine-tuned model with predicted label and confidence:

| Post (truncated) | True Label | Predicted | Confidence |
|---|---|---|---|
| "That Bellingham goal. I am not okay." | reaction | reaction | 0.97 |
| "City's high line gave up 3 goals from balls in behind..." | analysis | reaction | 0.89 |
| "Ronaldo is finished. Has been for two years." | hot_take | reaction | 0.91 |
| "Absolutely disgraceful refereeing. Season over." | reaction | reaction | 0.95 |
| "Trent at Real Madrid will be a disaster. He can't defend." | hot_take | reaction | 0.88 |

**Correct prediction explained:** The post *"That Bellingham goal. I am not okay."* was
correctly classified as `reaction` with 0.97 confidence. This is reasonable — the post
is short, purely emotional, triggered by a specific match event, and contains no argument
structure. It is the clearest possible example of `reaction` and the model's high
confidence is well-calibrated for this case.

### What the Model Learned vs. What I Intended

I intended the model to learn three distinct discourse patterns: structured argument,
unsupported assertion, and emotional response. What it actually learned was a single
pattern: "most text about soccer is a reaction." The model's decision boundary collapsed
to the majority class because ~74% of training examples were labeled `reaction`, giving
it no meaningful gradient signal for the other two classes.

This is not a failure of the model architecture — DistilBERT is capable of learning
these distinctions given balanced data. It is a failure of dataset construction.
Specifically: the Groq pre-labeler over-assigned `reaction` to ambiguous posts (anything
match-related got `reaction` by default), and the manual review pass did not catch and
correct enough of these. The result is a training set where `analysis` and `hot_take`
are so underrepresented that the model is never rewarded for predicting them.

The fix is straightforward: rebalance the dataset to ~65 examples per class and re-run
fine-tuning. The label definitions are solid — the data pipeline is what broke.

---

## Reflection — Spec

**One way the spec helped:** The spec's insistence on writing `planning.md` before
touching any data was genuinely useful. Defining the edge case decision rule
(reaction vs. analysis boundary) before annotating meant I had a consistent rule to
apply during labeling rather than making ad-hoc decisions on 300 individual posts.

**One way implementation diverged:** The spec recommended aiming for at least 20% per
label before training. In practice, the combination of Groq pre-labeling and incomplete
manual review resulted in a 74/14/13 split — far outside this guideline. I prioritized
speed of annotation over balance verification, which is exactly the failure mode the
spec warned against.

---

## AI Usage

**Instance 1 — Pre-labeling:**
I directed Groq `llama-3.3-70b-versatile` to pre-label all 300 posts using the label
definitions from `planning.md`. It produced a label per post quickly, but systematically
over-assigned `reaction` to ambiguous posts — anything that mentioned a match or result
got `reaction` regardless of whether it contained an argument. I corrected a portion of
these during review but not enough to fix the distribution. Disclosed: pre-labeled
examples are flagged with `pre_labeled: True` in the CSV.

**Instance 2 — Failure analysis:**
After getting the evaluation results, I used Claude to identify patterns in the wrong
predictions. Claude identified that all misclassifications shared one feature: the model
predicted `reaction` regardless of actual label. This confirmed the majority-class
collapse hypothesis. I verified this by checking the confusion matrix, which showed
zeroes in every cell except the `reaction` column — exactly consistent with what Claude
identified.

**Instance 3 — planning.md and README drafting:**
I used Claude to draft the structure and initial content of both `planning.md` and this
README, providing the label definitions, evaluation results, and analysis as inputs.
I reviewed and edited both documents — the wrong predictions analysis and reflection
sections reflect my own interpretation of the results.

---

## Repository Contents

```
ai201-project3-takemeter/
├── planning.md
├── README.md
├── data/
│   ├── soccer_posts.csv          # Full labeled dataset
│   └── soccer_posts_raw.csv      # Pre-annotation scrape
├── evaluation_results.json       # Exported from Colab
└── confusion_matrix.png          # Exported from Colab
```
