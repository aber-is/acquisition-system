# Normalization Rules

This document records the readings normalization is permitted to make when a source states
a value qualitatively rather than as structured data.

It is separate from [the domain model](domain-model.md) because these rules are properties
of particular sources and languages, not of the concepts being modelled. They will grow and
change as real sources are observed; the domain model should not.

## Why write them down

A phrase such as `full-time` or `nach Vereinbarung` has to be read the same way every time,
by a normalizer and by whoever reviews its output. If that reading lives only inside
extraction code, three things follow: nobody can review it without reading the code, two
extractors can disagree without anyone noticing, and a reader of stored data cannot tell
whether a value was stated or inferred.

Recording the reading here makes it reviewable and arguable. A mapping in this document can
be challenged; a regular expression buried in a parser cannot.

## When a rule is warranted

Add a rule only when a real source has demanded it, and only when the phrase has a
determinate value that any careful reader would agree on.

Most qualitative phrasing does not qualify. Terms that signal flexibility, negotiation or
absence of commitment carry no value at all, and a value must not be invented for them —
they leave the field retaining its original text alone, which the domain model treats as a
legitimate outcome rather than a failure.

Prefer no rule to a speculative one. An unnormalized value passes through to human review;
a wrongly normalized one is acted upon as though it were stated.

## Applicability

Each rule states the language or source it applies to. A reading that holds for one
language's job postings does not automatically hold for another's, and a phrase that a
particular source uses as a structured category may be free text elsewhere.

## Format

Each rule records:

* the concept it normalizes
* the phrases it applies to, and the language or source they belong to
* the value they normalize to
* why the reading is safe

## Rules

### Workload: full-time

| | |
| --- | --- |
| **Concept** | `Workload` |
| **Applies to** | `full-time` (English), `Vollzeit`, `Vollzeitstelle`, `100%-Stelle` (German) |
| **Normalizes to** | minimum and maximum percentage of 100 |

Safe because full time is 100% *by definition* as a proportion, so the reading introduces
no assumption about the length of the working week.

It must not be read as weekly hours unless the full-time week is separately known and
retained. That is the conversion the domain model's `Workload` section prohibits, and it is
prohibited here too: a rule may not be used to smuggle in a conversion the model forbids.

The practical reason this rule exists is comparison. A source that states `Vollzeit` in prose
and a percentage range in a structured field has said two things, and the two can only be
recognised as agreeing or conflicting if both are expressed in the same terms.
