# Project Instructions

This project identifies Swiss freelance and B2B opportunities for
Aber Industrial Solutions and its employees.

## Product Goal

The system continuously collects relevant opportunities, evaluates them
against employee and company profiles, and produces a concise weekly report
for human review.

The weekly report should eventually contain:

* top individual freelance matches
* top company/project opportunities
* new tenders
* opportunities closing soon
* match scores and reasons
* relevant employees for each opportunity
* major skill or availability gaps
* links to the original postings

The report is the primary review interface.
A web dashboard is optional and should not be assumed to be necessary.

## Context

Temporary background material is available under `context/`. It contains a company-wide work summary, individual work summaries for Salomon Aengenheyster-Aber, Mark Aber, and Günter Bernhart, and the company's ISO management system under `context/managment-system/`. Use this material to understand the company, employee capabilities, delivered projects, responsibilities, and operating context. The `context/` directory is for design and research only; application code should not depend on it, and important conclusions should eventually be distilled into durable documentation or structured profiles.

This material has already been mined into `data/`. If you mine it again, note the two ways the first pass went wrong: every case study's **Result** section was dropped, so outcomes were missing from the evidence; and capabilities expressed as *constraints* rather than technologies were missed entirely — delivering into a plant that cannot stop, working with no reporting line, owning a product alone. Read for outcomes and obstacles, not only for nouns.

## Documentation

Read these before changing anything they cover. The code is downstream of them.

| Document | Covers |
| --- | --- |
| `docs/domain-model.md` | The concepts. Every model in `src/acquisition/domain/` implements something defined here. |
| `docs/normalization-rules.md` | Which qualitative phrases normalization may read as values. Anything not listed keeps its original text alone. |
| `docs/filtering-policy.md` | Which rejection reasons keep an opportunity out of the report, and which only annotate it. Annotating is the default. |

## Current State

**Done.** The domain layer (`src/acquisition/domain/`) and the profile catalogue (`data/`).

`data/` holds real data: the company with both its contracting entities, profiles for Salomon, Mark and Günter, and a shared evidence library of 25 items. Load it with `load_profile_catalogue("data")`, which is also what validates that every evidence citation resolves. `examples/opportunities/` holds three **synthetic** postings, clearly marked as such.

**Not built.** Ingestion, deduplication, filters, matching, scoring, persistence, reporting. Nothing reads an opportunity from anywhere.

**The blocker.** There are no real opportunities in the repository. Every opportunity-side decision so far was made against synthetic postings, so the opportunity model is the least-tested part of the system. Collecting roughly twenty real postings by hand — freelancermap and SIMAP — is the prerequisite for anything downstream.

## Next Milestone

A thin end-to-end matching slice, run against real postings.

For each opportunity and each candidate — the three people and the company — produce the structured component assessments of a `MatchResult`, calculate the overall score deterministically from those components, and print a ranked list to the terminal.

Three things shape it:

* **Evidence coverage dominates.** The question a match answers is "can this be applied for realistically, given the evidence held?" — not "does this resemble past work". Weight capability and evidence fit above domain similarity.
* **The useful output is a per-requirement table**, not a number: each requirement, the evidence that covers it, or "not covered". The score summarises that table rather than replacing it.
* **Success is human judgement.** Read the ranking and say whether you agree with it. If you do, scraping and reporting are mechanical work on a proven core. If you do not, the fix is a prompt and a weights table rather than a pipeline.

Do NOT yet build:

* web scraping
* persistence beyond YAML files
* scheduled weekly report delivery
* report formatting
* automatic job applications
* a web dashboard
* autonomous outreach

unless explicitly requested.

## Open Questions

Decisions deferred rather than made. Each is recorded where it applies; none blocks the next milestone.

* Salomon's profile claims eight programming languages but no frameworks or databases (Avalonia, React, Flask, SQLite, MS SQL) and no `mes`. Is that under-selling him for SCADA/MES postings, or is adding them the keyword-stuffing the evidence discipline exists to prevent?
* Project references are attributed to the German entity by inference from trading dates, not from records. Mark can confirm. `scada-qa-tool` spans both entities and is deliberately unattributed.
* Günter's six capabilities rest on a single evidence item, which is testimony from the managing director rather than a project record. The evidence item says so.
* The company's `end-to-end-delivery` capability overlaps `long-term-maintainability` and `production-environment-delivery`, and may be padding.
* Three SCADA-prefixed capability subjects exist — `scada-architecture`, `scada-engineering-automation`, `scada-programming`. Real postings will show whether buyers make those distinctions.

## Target Pipeline

raw opportunity
→ normalization
→ deduplication
→ hard filters
→ semantic matching
→ scoring
→ opportunity database
→ weekly report
→ human review

## Engineering Rules

* Python 3.13+
* Pydantic for domain schemas
* pytest for tests
* type hints everywhere
* pure functions where practical
* external services behind interfaces
* LLM output must use structured schemas
* deterministic filtering happens before LLM scoring
* never infer candidate skills without evidence, and never infer preferences from
  history — past work shows what someone can do, not what they want next
* retain original posting text and source URL
* every rejection must have a reason code
* preserve enough structured data to generate reports without reprocessing
  the original posting
* human approval is required before any application or outreach
