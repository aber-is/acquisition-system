# Domain Model

This document defines the core concepts used by the opportunity-matching system.

The implementation should follow these concepts, but this document is intentionally independent of any specific database or API.

## PersonProfile

Represents one person who may be matched against individual freelance or consulting opportunities.

A person profile contains:

* unique identifier
* name
* current availability
* maximum workload
* preferred workload
* location
* remote/on-site preferences
* languages
* demonstrated skills and capabilities
* industry/domain experience
* preferred role types
* excluded role types
* credentials, certifications or qualifications, where relevant
* work or contracting eligibility constraints, when relevant
* minimum commercial expectations, if applicable
* references to the evidence supporting claimed skills and experience

Availability should be stored as structured data. Simple current availability is sufficient for the first implementation and may include available hours per week, earliest start date, and known future changes. A sophisticated scheduling model is not required.

Skills must not be inferred simply because a person has worked on a vaguely related project.

Important claims should be backed by explicit evidence.

## CompanyProfile

Represents Aber Industrial Solutions as a delivery organisation.

The company profile contains:

* the organisation's name and identity
* its contracting entities
* capabilities
* technologies
* industries/domains
* supported commercial arrangements
* geographic constraints
* credentials and certifications, including status, scope, validity, expected completion where one is still in progress, and supporting evidence
* supplier qualifications, if relevant
* project references
* available employees or delivery capacity
* commercial constraints

The company's available capacity may be derived from the combined availability of its employees.

The company can be matched independently of individual employees.

For example, an opportunity may be a strong company match even if no single employee covers the entire required capability set.

### ContractingEntity

A delivery organisation is not necessarily one legal entity. It may contract through several, in different jurisdictions and legal forms.

Capabilities, evidence and project references belong to the organisation and are held once, because the same people do the work whichever entity contracts for it. Legal identity belongs to the entity. Each entity records:

* legal name, and trading name where it differs
* legal form
* country of registration or establishment
* registration number, where the legal form has one — a sole trader may not
* tax or VAT identifier
* registered office or place of establishment
* when it began trading, if known

Which entity contracts is often a commercial or fiscal decision. It is not only that. An entity's jurisdiction and trading history can decide whether a buyer may award to it at all, so the choice affects eligibility and belongs in the model rather than being left to whoever writes the bid.

Two consequences follow, and both matter more for tenders than for ordinary matching:

* **Credentials may cover some entities and not others.** A credential naming no entity covers all of them; one naming specific entities covers only those. A supplier registration typically belongs to a single entity, and quoting the wrong entity's reference in a bid is a real error.
* **A project reference records which entity delivered it.** Procurement commonly asks for references delivered by the bidding entity itself, so a reference earned under a predecessor or sibling entity may not be citable in every bid, even though the organisation genuinely did the work.

An opportunity is still matched against the organisation, not against an entity. Which entity would contract is a commercial-fit question, answered in the match result rather than by producing a separate match per entity.

## Workload

Workload is a small structured value used by person profiles and opportunities.

Where available, it retains:

* minimum percentage
* maximum percentage
* minimum hours per week
* maximum hours per week
* original textual representation

Percentage and hours must not be treated as interchangeable unless the full-time weekly workload used for the conversion is known and retained. Open-ended or qualitative values such as `at least 60%`, `full-time`, or `negotiable` may retain only the fields that can be normalized safely.

A workload that retains only its original text is still a valid workload. It simply carries no comparable number, which is a fact about the source rather than a defect.

## Evidence

Evidence supports claims made in a PersonProfile or CompanyProfile.

Examples:

* project
* customer engagement
* production system
* certification project
* technology implementation
* documented responsibility

Evidence should contain enough information to explain why a skill, capability, credential, or experience claim is considered demonstrated. Each evidence item contains:

* unique identifier
* description
* claims or capabilities it supports
* source or provenance
* relevant date or period, if known

Evidence forms a shared library. One project is frequently evidence for both a person and the company, so an evidence item belongs to neither profile and is written down exactly once. Profiles hold references into the library, not copies of it.

A reference states the involvement. A person claiming a capability and citing an evidence item is the explicit statement that this person's work on it demonstrates that capability, and the reference carries a note describing what that person contributed. Company evidence therefore cannot become a personal claim by accident: someone has to write the citation into that person's profile and say what they did.

Example evidence item, and the reference that cites it from a person profile:

```
id: cloud-server-config
capabilities:
  - nixos
  - linux
  - infrastructure
  - monitoring
  - backups
  - security
description:
  Production NixOS infrastructure including declarative provisioning,
  encrypted disks, secrets management, monitoring, backups and CI.
```

```
capabilities:
  - subject: monitoring
    evidence:
      - evidence_id: cloud-server-config
        note: Grafana, Loki and Alloy over mTLS, with custom dashboards and alerts.
```

Match results should reference evidence rather than making unsupported claims. Every evidence reference, in a profile or in a match result, must resolve to an item in the library.

## Normalized values and extraction provenance

A normalized value is a value normalization produced from a source, together with enough context to audit it later. It is used wherever a field feeds a deterministic filter.

A normalized value retains:

* its state: `known`, `unknown`, or `conflicting`
* the value, only when the state is `known`
* the incompatible values observed, only when the state is `conflicting`
* the supporting source text or source metadata field
* the extraction method

Missing information is `unknown`, never satisfied. An `unknown` or `conflicting` value must not cause a deterministic rejection; it passes through for later assessment or human review.

`conflicting` means the source said two incompatible things — prose contradicting a structured field, or two fields disagreeing. Both observations are retained and neither is adopted.

### Qualitative values

Sources state many values qualitatively rather than numerically, in whatever language and idiom the source uses. Some such phrases carry a determinate value; most do not.

A qualitative phrase may be normalized only where a rule for it is recorded in [normalization rules](normalization-rules.md). Anything else retains its original text alone, with no value derived from it.

The rules live outside this document because they are properties of particular sources and languages rather than of the concepts modelled here, and they will grow as real sources are observed. They are written down rather than left inside extraction code so that a normalizer and a human reviewer reach the same reading of the same posting, and so that a mapping can be argued with.

### Extraction method

The extraction method records how a value was obtained, because a value read from a structured source field and a value inferred by a language model do not deserve equal trust:

| Method | Meaning |
| --- | --- |
| `source_metadata` | Read directly from a structured field the source publishes. |
| `rule_based` | Derived from text by a deterministic rule, parser or pattern. |
| `llm` | Extracted by a language model. |
| `manual` | Entered or corrected by a person. |
| `unknown` | The method was not recorded. |

The name and version of the rule, parser or model may also be retained, along with a reported confidence where the extractor provides one. Neither should be populated with a placeholder: an unnamed extractor is more honest than a fictional one.

This detail is not required for purely descriptive fields.

## Requirement

A requirement represents something requested by an opportunity.

It contains:

* description
* category, such as capability, language, qualification, experience, or eligibility
* normalized subject, when possible
* importance: mandatory, preferred, optional, or unknown
* supporting source text or metadata

Only an explicit mandatory requirement supported by the source may directly cause deterministic rejection. Preferred, optional, unknown, ambiguous, or conflicting requirements may affect matching but must not cause hard rejection.

## Opportunity

Represents a potential piece of work.

Every opportunity retains:

* unique identifier
* title
* client, if known
* source identifier
* source URL
* original posting text
* first-seen date
* last-seen date
* publication date, if known
* application deadline, if known
* listing status: open, closed, expired, or unknown
* location, if known
* work location mode — on-site, hybrid, remote, or unknown — with the on-site days per week or remote share where the source quantifies it
* structured workload, if known
* requirements
* whether it is a formal tender
* commercial arrangements, if known
* published commercial terms, such as rates, budget, payment terms, estimated contract value, and whether B2B contracting is allowed
* travel requirements, if any

Information used by hard filters — status, location, work location mode, workload and commercial arrangements — is retained as a normalized value, with the state, supporting source text or metadata, and extraction method described under [Normalized values and extraction provenance](#normalized-values-and-extraction-provenance). This detail is not required for every descriptive field.

Work location mode is retained because it decides viability together with location rather than on its own: a fully remote engagement in another country may be workable where the same engagement on site five days a week is not. On-site days per week and remote share must not be converted into one another, for the same reason percentages and hours must not be — the length of the working week is not necessarily known.

`closed` means the source explicitly indicates that the opportunity is no longer accepting responses. `expired` means a known deadline has passed. An opportunity disappearing from a source does not prove that it is closed; `last-seen date` records observation only.

An opportunity is one of the following types.

### IndividualOpportunity

The client primarily wants a particular person or specialist capacity.

Examples:

* freelance developer
* AI consultant
* technical project manager
* infrastructure engineer
* part-time external specialist

The work may still be contracted and invoiced through Aber Industrial Solutions Ltd.

An IndividualOpportunity therefore does not mean that the person must contract privately.

Typical commercial arrangements include:

* direct freelance
* B2B through Aber Industrial Solutions Ltd
* subcontractor

The defining characteristic is that the client is mainly buying access to a specific person's time and capabilities.

### CompanyOpportunity

The client is primarily buying an outcome or deliverable from Aber Industrial Solutions Ltd rather than a specific person's capacity.

Examples:

* build an internal AI automation system
* modernize an industrial application
* implement monitoring and backup infrastructure
* migrate a legacy system
* build a software tool
* implement SCADA/MES integration
* deliver a technical assessment
* automate an engineering process

A CompanyOpportunity may involve one or several employees.

The defining characteristic is that Aber Industrial Solutions Ltd is responsible for delivering the agreed result.

Formal tenders may be IndividualOpportunities or CompanyOpportunities. The tender indicator keeps them identifiable for filtering and reporting without introducing another opportunity type.

## CommercialArrangement

CommercialArrangement captures a contracting or pricing arrangement explicitly stated or reliably derived from an opportunity. An opportunity may have more than one commercial arrangement.

Initial values may include:

* direct_freelance
* b2b
* subcontractor
* fixed_price
* hourly_or_daily_rate
* unknown

These values are independent of OpportunityType.

For example:

```
opportunity_type: individual_opportunity
commercial_arrangements:
  - b2b
```

means that the client wants a particular consultant, but Aber Industrial Solutions Ltd invoices the client.

## Rejection

A rejection records why an opportunity was excluded.

A rejection must contain a machine-readable reason code.

Examples:

* workload_too_high
* outside_geography
* employment_only
* missing_required_skill
* missing_required_qualification
* language_requirement
* eligibility_requirement
* rate_too_low
* unsuitable_role_type
* no_b2b_option
* unavailable_capacity
* deadline_passed
* opportunity_closed

Human-readable details may accompany the reason code.

Rejected opportunities should normally remain stored so that rejection patterns can be analysed later.

### A rejection is a label, not a deletion

Because rejections are retained, a reason code does not remove an opportunity. It records a conclusion about it. What matters is the effect the conclusion has, and there are two:

* **Suppressing** — the opportunity does not appear in the weekly report at all.
* **Annotating** — the opportunity remains reportable, and the conclusion appears as a reason or a gap against its match.

A reason code may suppress only where the conclusion is a fact that needs no interpretation: given the same source, any careful reader would reach the same answer, and there is no plausible reading under which the opportunity is still worth a human's attention. Anything that depends on judgment, on a negotiable position, or on an inference about intent must annotate instead.

The distinction matters because the two mistakes are not symmetric. A suppression that is wrong is invisible: the opportunity never reaches the report and nobody learns that it was missed. An annotation that is wrong costs a line in a report a human is already reading. Where it is unclear which effect a reason code should have, it annotates.

Whether a given reason code suppresses or annotates is a matter of configured policy rather than of the domain model, so that it can be revised as real sources are observed without changing the model. The current assignment is recorded in [filtering policy](filtering-policy.md), where a reason annotates unless it is listed as suppressing.

## MatchResult

Represents the result of matching one opportunity against one person or the company as a whole.

A match result contains:

* overall score
* target type: person or company
* identifier of the person or company
* opportunity identifier
* relevant people for a company match, if any
* strong matches
* capability gaps
* relevant evidence
* workload fit
* availability fit
* domain fit
* qualification fit
* commercial fit
* geographic fit
* concise summary

Commercial fit compares the opportunity's published terms with the commercial expectations or constraints of the person or company. It is assessed independently from technical fit because a technically strong match may still be commercially unsuitable.

Positive claims must reference information contained in the relevant profile or evidence.

Missing information must be treated as unknown, not as satisfied.

A MatchResult should explain why the score was produced. The model should return structured component assessments, reasons, gaps, and evidence references. The overall score should then be calculated deterministically from those components rather than accepted as an unexplained model output.

## WeeklyReport

The weekly report is the primary human review interface.

It should eventually contain sections such as:

* strongest individual opportunities
* strongest company opportunities
* new tenders
* opportunities with upcoming deadlines
* opportunities suitable for more than one employee
* recurring capability gaps
* basic statistics for the week

The report does not make application or bidding decisions automatically.

Its purpose is to reduce a large number of raw opportunities to a small number worth human attention.

## Source

Source identifies where the opportunity was discovered.

Examples:

* freelancermap
* PROSTAFF
* GHR
* LinkedIn
* SIMAP

The system should preserve source information because source quality can later be evaluated.

## Original Content

The original opportunity text must always be retained.

Normalization and LLM processing must not replace the original source material.

This allows:

* auditing
* rescoring
* debugging extraction errors
* improving prompts later
* reviewing the exact client wording

## Pipeline

The intended processing pipeline is:

```
raw opportunity
    ↓
normalization
    ↓
deduplication
    ↓
deterministic hard filters
    ↓
semantic matching
    ↓
scoring
    ↓
opportunity database
    ↓
weekly report
```

Deterministic rules should be used wherever possible before invoking an LLM.

Deterministic filters may use normalized information extracted from source metadata or the original posting text. An opportunity should be rejected only when the relevant constraint is explicit and supported by the source. Each rejection must include a reason code. Missing, ambiguous, or conflicting information must pass through for later assessment or human review.

The filtering stage decides facts, not judgments. A constraint belongs here when it can be settled by comparing recorded values — a date against today, a status the source stated outright, a credential a requirement demands by name. A constraint that depends on interpreting intent, on weighing partial evidence, or on a position that is in practice negotiable belongs in semantic matching and scoring, where it lowers a score and appears as a stated gap instead of removing the opportunity.

This division matters more than the volume of work it saves. Filtering exists because a reproducible, reason-coded conclusion can be audited and re-run, while a model's verdict cannot. It does not exist to reduce the number of opportunities a model sees: at the volumes this system is designed for, evaluating an opportunity is cheap, and a wrongly suppressed opportunity is the expensive outcome. Filters should therefore be kept few and certain rather than broad, and only a suppressing reason code — see [A rejection is a label, not a deletion](#a-rejection-is-a-label-not-a-deletion) and [filtering policy](filtering-policy.md) — keeps an opportunity out of the report.

The initial discovery geography is Switzerland, but it is configuration rather than a domain-model restriction. Opportunities retain their actual locations, and adding sources or changing the configured geography should allow the same pipeline to cover other countries without changing the domain model.

Opportunities that were not suppressed are evaluated for semantic fit. A model may assess capability, domain, and evidence fit using a structured output schema. Application code then calculates the overall score from those component assessments using a fixed, documented scale and weights.

## Example 1: Individual Opportunity

```
title:
  Freelance IT Project Manager

opportunity_type:
  individual_opportunity

commercial_arrangements:
  - b2b

workload:
  minimum_percentage: 20
  maximum_percentage: 30
  original_text: 20-30%

location:
  Zürich

matched_person:
  Salomon
```

This means the client mainly wants Salomon's capacity, while Aber Industrial Solutions Ltd may still be the contractual supplier.

## Example 2: Company Opportunity

```
title:
  Automate engineering document processing using AI

opportunity_type:
  company_opportunity

commercial_arrangements:
  - b2b
  - fixed_price

location:
  Switzerland

matched_target:
  Aber Industrial Solutions Ltd
```

This means the client is buying an outcome delivered by Aber Industrial Solutions Ltd.

## Example 3: Tendered Company Opportunity

```
title:
  Framework agreement for industrial software engineering

opportunity_type:
  company_opportunity

commercial_arrangements:
  - b2b

formal_tender:
  true

source:
  SIMAP
```

The system should first evaluate whether Aber Industrial Solutions Ltd satisfies the procurement requirements and then assess possible delivery capacity. The tender indicator allows these opportunities to receive their own report section without introducing a separate opportunity type.

## Design Principles

1. LLMs must not invent candidate skills, project experience, or company capabilities.

   Preferences must not be inferred from them either. Past work evidences what a person can do, not what they want to do next, and an inferred exclusion would suppress whole categories of work on the grounds that they are unfamiliar. Role preferences are stated, or they are absent.

2. Missing information is unknown rather than assumed true.

3. Every important positive match should be explainable using stored evidence.

4. Constraints that can be settled by comparing recorded values should be evaluated deterministically. Constraints that require interpretation, or that are negotiable in practice, belong in matching and scoring instead, and lower a score rather than removing an opportunity.

5. Original opportunity text must be retained for auditing and later reprocessing.

6. Rejections should be retained with structured reason codes.

7. The data model should support all current matching candidates from the beginning, even if the first implementation only contains one profile.

8. The company must be matchable independently of individual employees.

9. The weekly report is the primary output. A dashboard is optional.

10. OpportunityType describes what the client is buying. CommercialArrangement describes the contracting or pricing arrangements.

11. Avoid adding new domain concepts until real opportunities demonstrate that they are necessary.

12. The initial implementation should remain simple enough that the matching and scoring logic can be understood and tested manually.
