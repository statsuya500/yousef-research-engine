---
name: youtube-research
description: Research YouTube topics for YOU SEF by discovering relevant videos, collecting metadata and transcripts, analyzing individual sources and comparing the corpus to identify patterns, saturation, underrepresented angles, opportunities, and 10 evidence-backed YOU SEF concepts.
---
# YOU SEF — YouTube Research Engine

## Purpose

This skill provides the complete YouTube research workflow for the YOU SEF project.

Its purpose is to transform a research topic into an evidence-based research package:

```text
TOPIC
  ↓
YOUTUBE DISCOVERY
  ↓
SOURCE SELECTION
  ↓
METADATA
  ↓
TRANSCRIPTS
  ↓
INDIVIDUAL VIDEO ANALYSIS
  ↓
CROSS-SOURCE ANALYSIS
  ↓
PATTERNS
  ↓
SATURATION / UNDERREPRESENTATION
  ↓
POSSIBLE OPPORTUNITIES
  ↓
10 YOU SEF CONCEPTS
  ↓
RESEARCH REPORT
```

The Research Engine is an analytical system.

It is NOT an autonomous content-production system.

It must never present hypotheses as facts or claim that a topic, title, format, or concept is guaranteed to perform.

---

# 1. Scope

This skill is responsible for:

* discovering relevant YouTube videos
* collecting metadata
* selecting candidate sources
* obtaining available subtitles
* cleaning subtitle files
* analyzing individual videos
* comparing multiple videos
* detecting repeated patterns
* identifying saturated concepts
* identifying underrepresented concepts
* identifying possible opportunities
* translating evidence into YOU SEF concepts
* generating title hypotheses
* creating reusable research reports
* storing reusable knowledge

This skill does NOT handle:

* script writing
* scene generation
* image generation
* ComfyUI
* ElevenLabs
* video editing
* thumbnail generation
* YouTube publishing
* automatic episode production

---

# 2. YOU SEF Creative Context

YOU SEF is a cinematic second-person POV channel.

Core promise:

> POV: Vives una vida que normalmente nunca podrías experimentar.

The format generally targets:

* 15–30 minute immersive mini-films
* second-person narration
* present tense
* cinematic storytelling
* extraordinary lives and situations
* 2D illustrated/comic visual identity
* strong protagonist/world continuity

Primary content pillars:

* creative professions
* exclusive industries
* rise
* fall
* transformation
* history
* future
* hidden worlds

Avoid research focused on:

* organized crime / crime-centered violence
* paranormal
* conspiracy
* AI as the content niche itself

The Research Engine may encounter excluded material during discovery.

Such material must be classified appropriately rather than silently treated as valid YOU SEF inspiration.

---

# 3. Core Command

The primary command is:

```text
/research "<topic>"
```

Example:

```text
/research "stunt double"
```

Optional parameters may be supported:

```text
/research "stunt double" --sources 15
```

```text
/research "luxury hotel manager" --language en
```

If no options are supplied, use the project configuration defaults.

---

# 4. Research Lifecycle

A research run follows these stages:

```text
1. CREATE RESEARCH
2. DISCOVER SOURCES
3. CLASSIFY SOURCES
4. REQUEST HUMAN APPROVAL
5. COLLECT METADATA
6. COLLECT TRANSCRIPTS
7. CLEAN TRANSCRIPTS
8. ANALYZE INDIVIDUAL SOURCES
9. ANALYZE CORPUS
10. DETECT PATTERNS
11. DETECT SATURATION
12. DETECT UNDERREPRESENTATION
13. GENERATE OPPORTUNITIES
14. GENERATE 10 CONCEPTS
15. GENERATE TITLE HYPOTHESES
16. WRITE REPORT
17. UPDATE KNOWLEDGE BASE
```

Each stage must be resumable.

Do not repeat completed stages unnecessarily.

---

# 5. Research ID

Every research run must have a unique ID.

Preferred format:

```text
<normalized-topic>-<YYYY-MM>
```

Example:

```text
stunt-double-2026-09
```

If a collision occurs, add a deterministic suffix.

The research ID must be used consistently across generated files.

---

# 6. Research Brief

Before discovery, create or load a research brief.

The brief should contain:

```yaml
research_id:
topic:
audience:
goal:
format:
languages:
competitor_count:
questions:
```

Example:

```yaml
research_id: stunt-double-2026-09

topic:
  stunt double

audience:
  people interested in extraordinary careers

goal:
  determine whether the topic contains viable YOU SEF opportunities

format:
  15-30 minute cinematic second-person POV

languages:
  - en
  - es

competitor_count:
  target: 12
  maximum: 20

questions:
  - What hooks are repeatedly used?
  - What title patterns recur?
  - What narrative structures recur?
  - Which concepts appear saturated?
  - Which concepts appear underrepresented?
  - Which elements can translate into second-person POV?
```

---

# 7. Discovery

Discovery should use deterministic tooling where possible.

Preferred tool:

```text
yt-dlp
```

Discovery must NOT download full videos.

The objective is to find candidate sources and collect available metadata.

Candidate information should include:

* video ID
* URL
* title
* channel
* publication date
* duration
* view count when available
* language when available
* search query
* discovery timestamp

Missing values must remain unknown/null.

Never invent metadata.

---

# 8. Search Strategy

Do not rely on one search query.

Generate several query formulations around the topic.

For example, for:

```text
stunt double
```

possible queries include:

```text
stunt double career
life as a stunt double
stunt performer behind the scenes
what it's like being a stunt double
stunt double documentary
stunt performer job
```

Search queries should explore:

* direct topic
* profession
* lifestyle
* behind-the-scenes
* career
* economics
* difficulty
* risks
* exclusive access
* first-person experiences

Do not artificially inflate the corpus with unrelated videos.

---

# 9. Source Classification

Each candidate must be classified as one of:

```text
DIRECT_COMPETITOR
ADJACENT
REFERENCE
LOW_VALUE
REJECT
```

Classification requires a reason.

Example:

```text
classification:
  ADJACENT

reason:
  Covers the same profession but uses a third-person documentary format rather than immersive POV.
```

Classification is descriptive.

Do not assign a "best" source.

---

# 10. Human Approval

The Research Engine must not silently choose the final corpus.

After discovery and classification, present the candidate list to the user.

Example:

```text
RESEARCH: stunt-double-2026-09

14 relevant candidates found.

1. [ ] Title
   Channel
   Views
   Date
   Duration
   Classification

2. [ ] Title
   Channel
   Views
   Date
   Duration
   Classification

...
```

Allow the user to approve a set of sources.

Example:

```text
approve 1 2 4 6 8 9 11 13
```

Only approved sources become the analytical corpus.

---

# 11. Source Files

Discovered sources:

```text
sources/discovered/<research_id>.json
```

Approved sources:

```text
sources/approved/<research_id>.json
```

Rejected sources should remain available for auditability.

Do not delete them automatically.

---

# 12. Metadata

Collect metadata for approved sources.

Never replace unknown data with guesses.

Use:

```text
null
```

when information is unavailable.

Do not interpret view count as quality.

A video's views are one observable metric among many.

Always preserve:

* publication date
* duration
* channel
* views
* title

as separate observations.

---

# 13. Transcript Collection

For approved sources:

1. prefer manually provided subtitles
2. use auto-generated subtitles if necessary
3. use configured fallback only if explicitly enabled

Default:

```yaml
allow_whisper_fallback: false
```

Do not download full video files by default.

If no transcript is available:

```text
TRANSCRIPT_STATUS = unavailable
```

Do not fabricate one.

---

# 14. Raw Transcript Preservation

Raw subtitle files must never be modified.

Store them under:

```text
transcripts/raw/<research_id>/<video_id>/
```

Preserve original timestamps and source information.

---

# 15. Transcript Cleaning

Create cleaned transcripts separately:

```text
transcripts/cleaned/<research_id>/<video_id>.md
```

Cleaning may:

* remove duplicate subtitle fragments
* remove formatting artifacts
* normalize whitespace
* normalize obvious subtitle segmentation problems
* preserve timestamps
* preserve semantic content

Cleaning must NOT:

* summarize
* rewrite
* invent missing text
* remove meaningful dialogue
* change the narrative meaning

The cleaner is a preprocessing operation, not an analysis operation.

---

# 16. Timestamp Format

Clean transcripts should retain timestamp anchors.

Preferred format:

```text
[00:00:03] You are standing outside the studio.
[00:00:08] The director calls your name.
[00:00:14] You walk toward the set.
```

Never invent timestamps.

---

# 17. Individual Video Analysis

Each approved source with a usable transcript should produce:

```text
analysis/individual/<research_id>/<video_id>.md
```

Use this structure:

```markdown
# VIDEO ANALYSIS

## Metadata

## Core Promise

## Target Audience

## Opening Hook

## First 30 Seconds

## Narrative Structure

## Main Character

## Conflict

## Emotional Progression

## Curiosity Mechanisms

## Information Density

## Pacing

## Repeated Concepts

## Strong Structural Moments

## Generic / Low-Distinction Sections

## Title Strategy

## Thumbnail Concept

## Second-Person Adaptability

## Evidence

## Analyst Confidence
```

---

# 18. Evidence Discipline

Important analytical claims must have evidence.

Use timestamp references whenever possible.

Example:

```text
Observation:
The video introduces the financial dimension of the profession early.

Evidence:
[00:00:21]
[00:00:47]

Confidence:
HIGH
```

Never invent evidence.

Never fabricate timestamps.

---

# 19. Observation vs Interpretation

Always distinguish:

```text
OBSERVATION
INTERPRETATION
HYPOTHESIS
```

Example:

```text
OBSERVATION:
The creator mentions salary within the first minute.

INTERPRETATION:
This creates an immediate economic curiosity mechanism.

HYPOTHESIS:
Economic information may be useful as an early hook for YOU SEF career stories.
```

The third statement must remain explicitly a hypothesis.

---

# 20. Individual Analysis Quality

Do not reward a video simply because it has many views.

Analyze:

* title promise
* opening
* narrative structure
* curiosity
* emotional progression
* information density
* pacing
* protagonist
* conflict
* visual concepts
* second-person adaptability

View count is contextual metadata, not a quality score.

---

# 21. Corpus Analysis

Once individual analyses are available, compare them.

Create:

```text
analysis/comparative/<research_id>.md
```

Required sections:

```markdown
# CROSS-SOURCE ANALYSIS

## Corpus Overview

## Repeated Hooks

## Repeated Title Patterns

## Narrative Structures

## Common Emotional Drivers

## Common Curiosity Mechanisms

## Common Visual Concepts

## Repeated Topics

## Saturated Concepts

## Outliers

## Divergent Approaches

## Underrepresented Concepts

## Possible Gaps

## Second-Person Opportunities

## Evidence Matrix

## Confidence / Limitations
```

---

# 22. Pattern Detection

A pattern requires multiple pieces of evidence.

Represent patterns using:

```text
pattern
frequency
sources
evidence
confidence
```

Example:

```yaml
pattern:
  Videos frequently introduce economic stakes early.

frequency:
  7/12

sources:
  - video_001
  - video_003
  - video_004
  - video_006
  - video_008
  - video_010
  - video_011

confidence:
  high
```

Avoid calling a pattern "dominant" when it appears only once or twice.

---

# 23. Pattern Categories

Look specifically for:

### Hooks

* immediate danger
* money
* exclusivity
* transformation
* status
* unusual environment
* mystery
* unexpected problem
* first-day scenario
* extreme responsibility

### Titles

* POV formulas
* "what it's like"
* "inside"
* "behind the scenes"
* "day in the life"
* salary/economics
* extreme situation
* transformation

### Narrative

* chronological
* challenge-based
* rise/fall
* first-day
* career progression
* problem → escalation → resolution
* access journey

### Emotional drivers

* fear
* ambition
* curiosity
* status
* discovery
* transformation
* risk
* belonging
* exclusivity

Do not assume these drivers are effective merely because they occur.

Measure their recurrence within the corpus.

---

# 24. Saturation

A saturated concept is simply a concept that appears frequently in the analyzed corpus.

Use wording such as:

```text
This angle appears frequently within the analyzed corpus.
```

Do NOT say:

```text
This angle will fail.
```

Do not predict performance from saturation alone.

---

# 25. Underrepresentation

Underrepresentation means that a concept appears infrequently or not at all within the selected corpus.

Use wording such as:

```text
Underrepresented in this corpus.
```

Do NOT automatically call it an opportunity.

Absence of examples does not prove audience demand.

---

# 26. Opportunity Analysis

An opportunity requires:

```text
observed pattern
+
underrepresented angle
+
YOU SEF relevance
```

Each opportunity must explicitly distinguish:

```text
EVIDENCE
INTERPRETATION
HYPOTHESIS
```

Example:

```text
EVIDENCE:
0/12 analyzed videos use explicit second-person narration.

INTERPRETATION:
The selected corpus is dominated by third-person presentation.

HYPOTHESIS:
A second-person treatment could differentiate a YOU SEF version.

VALIDATION:
Required.
```

---

# 27. Opportunity File

Store:

```text
opportunities/<research_id>.yaml
```

Each opportunity:

```yaml
opportunity_id:
title:
source_evidence:
pattern:
gap:
why_relevant_to_you_sef:
possible_angle:
confidence:
requires_validation:
```

---

# 28. YOU SEF Translation

Every meaningful opportunity should be translated into:

```text
SOURCE FORMAT
↓
OBSERVED PATTERN
↓
UNDERREPRESENTED ANGLE
↓
YOU SEF TRANSLATION
```

Example:

```text
SOURCE FORMAT:
Third-person career documentary.

OBSERVED PATTERN:
Curiosity around high-risk professional situations.

UNDERREPRESENTED ANGLE:
Few examples place the viewer inside the experience.

YOU SEF TRANSLATION:
Second-person cinematic POV.
```

---

# 29. Concept Generation

After opportunity analysis, generate exactly:

```text
10 candidate YOU SEF concepts
```

Not 5.

Not 20.

Exactly 10.

Each concept must include:

```yaml
concept_id:
working_title:
identity:
situation:
core_hook:
central_conflict:
why_it_matches_you_sef:
research_evidence:
novelty_hypothesis:
validation_needed:
```

Every concept must trace back to one or more research observations.

Do not generate unrelated generic ideas.

---

# 30. Titles

Generate title hypotheses using the YOU SEF pattern:

```text
POV: Eres [IDENTIDAD] + [SITUACIÓN]
```

Titles are hypotheses.

Never describe them as guaranteed winners.

---

# 31. Final Report

Generate:

```text
reports/<research_id>.md
```

Required:

```markdown
# YOU SEF RESEARCH REPORT

## Research Metadata

## Executive Summary

## Corpus

## Market Observations

## Audience Patterns

## Hook Patterns

## Title Patterns

## Narrative Patterns

## Visual Patterns

## Saturated Concepts

## Underrepresented Concepts

## Opportunities

## YOU SEF Adaptations

## 10 Candidate Concepts

## Candidate Titles

## Evidence Matrix

## Uncertainties

## Limitations

## Sources
```

---

# 32. Knowledge Base

Store reusable findings under:

```text
knowledge/topics/
knowledge/patterns/
knowledge/opportunities/
```

Do not simply duplicate complete reports.

Store distilled reusable knowledge.

When performing new research, historical knowledge may be consulted for context.

However:

```text
CURRENT EVIDENCE > HISTORICAL ASSUMPTION
```

If current evidence conflicts with historical knowledge, explicitly show the difference.

Never silently merge contradictory evidence.

---

# 33. Resuming Research

Research must be checkpointed.

A run may stop after:

* discovery
* approval
* metadata
* transcripts
* cleaning
* individual analysis
* comparative analysis
* opportunities

The system must detect completed work.

Do not regenerate valid existing outputs unnecessarily.

A resume command may be:

```text
/research resume <research_id>
```

---

# 34. Idempotency

Repeated execution must not create:

* duplicate sources
* duplicate transcripts
* duplicate analyses
* duplicate opportunities

Use deterministic filenames and IDs.

Preserve existing valid outputs.

---

# 35. Failure Handling

Record failures explicitly.

Possible failures:

* deleted video
* private video
* unavailable subtitles
* unsupported subtitle language
* yt-dlp failure
* malformed VTT
* network failure
* metadata unavailable

Example:

```json
{
  "status": "failed",
  "stage": "transcript",
  "reason": "No subtitles available"
}
```

Never silently skip a failed source.

---

# 36. Network Rules

Network access may be used for:

* YouTube discovery
* YouTube metadata
* subtitle retrieval

Do not introduce:

* telemetry
* hidden uploads
* external databases
* unnecessary third-party APIs

Research data must remain local.

---

# 37. Copyright Handling

The Research Engine is for analysis.

Prefer:

* metadata
* subtitles
* short evidence references

Do not download full videos by default.

Do not create a redistribution archive.

Do not reproduce long transcript sections in reports.

---

# 38. Truthfulness Rules

Never invent:

* views
* dates
* durations
* channels
* transcripts
* timestamps
* quotes
* source evidence

Unknown information must remain unknown.

Use:

```text
unknown
```

or:

```text
null
```

as appropriate.

---

# 39. Market Claim Rules

Never state:

```text
This will go viral.
This will definitely perform.
The algorithm will reward this.
This is guaranteed to work.
This is the best topic.
```

Instead use:

```text
The analyzed corpus shows...
Within the selected sources...
This pattern appears...
This angle is underrepresented...
This may represent an opportunity...
Validation is required.
```

---

# 40. Research Quality

The quality hierarchy is:

```text
DIRECT SOURCE EVIDENCE
        ↓
CORPUS PATTERN
        ↓
INTERPRETATION
        ↓
OPPORTUNITY HYPOTHESIS
        ↓
CREATIVE CONCEPT
```

Never reverse this hierarchy.

A creative idea cannot be used as evidence for a market claim.

---

# 41. Separation of Responsibilities

Use deterministic scripts for:

* discovery
* metadata
* subtitles
* VTT cleaning
* validation
* file management

Use Claude analysis for:

* semantic analysis
* narrative analysis
* pattern recognition
* opportunity reasoning
* creative translation

Do not put the entire workflow into one monolithic script.

---

# 42. Expected Directory Structure

Use:

```text
config/
briefs/
sources/
  discovered/
  approved/
  rejected/
transcripts/
  raw/
  cleaned/
analysis/
  individual/
  comparative/
  patterns/
opportunities/
reports/
ideas/
knowledge/
  topics/
  patterns/
  opportunities/
scripts/
.claude/
  skills/
    youtube-research/
  agents/
```

Reuse equivalent existing directories if already present.

---

# 43. Agent Responsibilities

If the project contains specialized Claude agents:

## source-analyst

Responsible only for:

* candidate classification
* source relevance
* source-selection reasoning

## video-analyst

Responsible only for:

* individual video analysis
* structural observations
* evidence extraction

## corpus-analyst

Responsible only for:

* cross-source comparison
* pattern detection
* saturation detection
* underrepresentation detection
* evidence-backed gaps

## opportunity-analyst

Responsible only for:

* YOU SEF opportunity translation
* concept generation
* title hypotheses

Agents must not silently modify unrelated project files.

---

# 44. No Automatic Episode Production

The Research Engine stops here:

```text
RESEARCH
↓
EVIDENCE
↓
PATTERNS
↓
OPPORTUNITIES
↓
10 CONCEPTS
```

It does NOT continue automatically into:

```text
SCRIPT
SCENES
IMAGES
AUDIO
VIDEO
PUBLISHING
```

A future system may consume the research output.

---

# 45. Final Output

When the research finishes, show:

```text
Research complete.

Research ID:
<research_id>

Sources discovered:
<number>

Sources approved:
<number>

Transcripts:
<number>/<number>

Individual analyses:
<number>/<number>

Patterns detected:
<number>

Possible opportunities:
<number>

YOU SEF concepts:
10

Report:
<path>
```

Clearly distinguish:

```text
COMPLETED
FAILED
SKIPPED
NOT AVAILABLE
```

---

# 46. Final Principle

The Research Engine is not a content oracle.

Its purpose is:

```text
collect evidence
      ↓
organize evidence
      ↓
analyze evidence
      ↓
compare sources
      ↓
identify patterns
      ↓
identify possible gaps
      ↓
translate evidence into YOU SEF opportunities
```

The system must always preserve the distinction between:

```text
WHAT WE OBSERVED
WHAT WE INFERRED
WHAT WE HYPOTHESIZE
WHAT WE CREATED
```

This distinction is mandatory.

End of skill.
