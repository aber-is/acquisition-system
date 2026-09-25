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
* work or contracting eligibility constraints, when relevant
* minimum commercial expectations, if applicable
* evidence supporting claimed skills and experience

Availability should be stored as structured data. Simple current availability is sufficient for the first implementation and may include available hours per week, earliest start date, and known future changes. A sophisticated scheduling model is not required.

Skills must not be inferred simply because a person has worked on a vaguely related project.

Important claims should be backed by explicit evidence.

## CompanyProfile

Represents Aber Industrial Solutions Ltd as a delivery organisation.

The company profile contains:

* company identity
* capabilities
* technologies
* industries/domains
* supported commercial arrangements
* geographic constraints
* credentials and certifications, including status, scope, validity, and supporting evidence
* supplier qualifications, if relevant
* project references
* available employees or delivery capacity
* commercial constraints

The company's available capacity may be derived from the combined availability of its employees.

The company can be matched independently of individual employees.

For example, an opportunity may be a strong company match even if no single employee covers the entire required capability set.

## Workload

Workload is a small structured value used by person profiles and opportunities.

Where available, it retains:

* minimum percentage
* maximum percentage
* minimum hours per week
* maximum hours per week
* original textual representation

Percentage and hours must not be treated as interchangeable unless the full-time weekly workload used for the conversion is known and retained. Open-ended or qualitative values such as `at least 60%`, `full-time`, or `negotiable` may retain only the fields that can be normalized safely.

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
* identifiers of the person, people, or company it supports
* source or provenance
* relevant date or period, if known

Company evidence must not be used to claim that a particular person has a capability unless that person's involvement is supported explicitly.

Example:

```
id: cloud-server-config
supports:
  - person:salomon
  - company:aber-industrial-solutions-ltd
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

Match results should reference evidence rather than making unsupported claims.

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
* structured workload, if known
* requirements
* whether it is a formal tender
* commercial arrangements, if known
* published commercial terms, such as rates, budget, payment terms, estimated contract value, and whether B2B contracting is allowed
* travel requirements, if any

For information used by hard filters, normalization should retain the normalized value, whether it is known, unknown, or conflicting, the supporting source text or metadata, and the extraction method. This detail is not required for every descriptive field.

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

Deterministic filters may use normalized information extracted from source metadata or the original posting text. An opportunity should be rejected only when the relevant constraint is explicit and supported by the source, such as being outside the configured search geography, requiring permanent employment, missing a mandatory qualification, exceeding available workload, or having a passed deadline. Each rejection must include a reason code. Missing, ambiguous, or conflicting information must pass through for later assessment or human review.

The initial discovery geography is Switzerland, but it is configuration rather than a domain-model restriction. Opportunities retain their actual locations, and adding sources or changing the configured geography should allow the same pipeline to cover other countries without changing the domain model.

Opportunities that pass the hard filters are evaluated for semantic fit. A model may assess capability, domain, and evidence fit using a structured output schema. Application code then calculates the overall score from those component assessments using a fixed, documented scale and weights.

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

2. Missing information is unknown rather than assumed true.

3. Every important positive match should be explainable using stored evidence.

4. Hard constraints such as workload, geography, deadlines, availability, and contract type should be evaluated deterministically.

5. Original opportunity text must be retained for auditing and later reprocessing.

6. Rejections should be retained with structured reason codes.

7. The data model should support all current matching candidates from the beginning, even if the first implementation only contains one profile.

8. The company must be matchable independently of individual employees.

9. The weekly report is the primary output. A dashboard is optional.

10. OpportunityType describes what the client is buying. CommercialArrangement describes the contracting or pricing arrangements.

11. Avoid adding new domain concepts until real opportunities demonstrate that they are necessary.

12. The initial implementation should remain simple enough that the matching and scoring logic can be understood and tested manually.
