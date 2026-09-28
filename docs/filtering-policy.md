# Filtering Policy

[The domain model](domain-model.md#a-rejection-is-a-label-not-a-deletion) defines two
effects a rejection reason may have: **suppressing** keeps an opportunity out of the weekly
report, **annotating** leaves it reportable and records the conclusion against its match.

This document records which effect each reason currently has, and under what condition a
suppressing reason may fire at all. It is policy rather than domain model, so it is expected
to change as real sources are observed.

## Default

**A reason annotates unless it is listed as suppressing below.** Adding a reason code does
not make it suppressing; that takes a deliberate entry here.

The default is annotate because the two mistakes are not symmetric. A wrong suppression is
invisible — the opportunity never reaches the report and nobody learns it was missed. A
wrong annotation costs a line in a report a human is already reading.

## Suppressing

Each of these also states the condition under which a rejection may be recorded in the first
place. The condition is part of the policy: without it, the same reason code would be
suppressing on interpreted data.

| Reason | May fire only when | Why suppressing is safe |
| --- | --- | --- |
| `deadline_passed` | A deadline was parsed as a date and that date has passed. | Date arithmetic on a recorded value. There is nothing to be done with an opportunity whose deadline has gone. |
| `opportunity_closed` | The source stated closure outright, normally through a structured field. | The source's own assertion, not a reading of it. Disappearing from a source is not closure. |
| `outside_geography` | The country is known, the work is not remote, and that country is outside the configured search geography. | Country-level comparison of recorded values. The remote condition matters: distant work that is performed remotely is not out of reach. |
| `employment_only` | The source explicitly excludes contracting, in wording that admits no other reading. | An explicit exclusion by the client. Vague phrasing about contract form does not qualify and leaves the value unknown instead. |
| `no_b2b_option` | The source explicitly rules out contracting through a company. | As above. Unknown is the common case and must not fire. |
| `missing_required_qualification` | A mandatory requirement names a qualification, and no credential held matches it in a checkable state. | A named credential either exists in a valid state or does not. No judgment about substitutes or near-equivalents is involved. |

## Annotating

Everything else, including any reason added later. Grouped by why it cannot be settled as a
fact:

**Negotiable in practice.** `workload_too_high`, `rate_too_low` — both sides are opening
positions, and a mismatch on paper is routinely resolved in conversation. A rate below
expectation is a reason to look carefully, not a reason not to look.

**Requires weighing evidence.** `missing_required_skill` — deciding whether demonstrated
capabilities satisfy a stated requirement is exactly the semantic matching stage's work.
Treating it as deterministic would mean rejecting on a keyword comparison.

**Requires interpreting intent or partial information.** `unsuitable_role_type`,
`unavailable_capacity`, `eligibility_requirement`, `language_requirement` — each depends on
reading what a source meant, or on profile information that is often incomplete.

**Unknown by construction.** `other` — a reason that needs a free-text explanation cannot
have been settled mechanically.

An annotating rejection is not discarded. It is stored, it appears as a reason or a gap
against the match, and it lowers the score. Recurring annotations are the intended way to
discover that a reason deserves promotion.

## Review

This assignment is deliberately conservative and was made before any real postings had been
processed. The evidence that should change it:

* A suppressing reason that turns out to fire on opportunities worth attention — demote it,
  or tighten its condition.
* An annotating reason that accumulates many rejections which a human always agrees with —
  consider promoting it, but only if the underlying decision is genuinely a fact.
* Rejection patterns concentrated in one source — often a normalization problem rather than
  a filtering one.

Prefer tightening a condition over demoting a reason, and prefer demoting over leaving a
suppression that is occasionally wrong.
