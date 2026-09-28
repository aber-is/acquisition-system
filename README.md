# Acquisition system

Identifies Swiss freelance and B2B opportunities for Aber Industrial Solutions Ltd
and its employees.

| Document | Covers |
| --- | --- |
| `AGENTS.md` | The product goal and engineering rules. |
| `docs/domain-model.md` | The concepts this code implements. |
| `docs/normalization-rules.md` | The readings normalization may make when a source states a value qualitatively. |
| `docs/filtering-policy.md` | Which rejection reasons keep an opportunity out of the report, and which only annotate it. |

## Development

The repository ships a Nix dev shell with Python 3.13, Pydantic, pytest and ruff:

```
nix develop        # or: direnv allow
pytest
ruff check .
```

`pyproject.toml` puts `src/` on the path for pytest, so no install step is needed.

## Current state

Stage 2 implements the **domain layer** only: validated Pydantic representations of
`docs/domain-model.md`, plus JSON and YAML serialization. Ingestion, deduplication,
hard filters, matching, scoring, persistence and reporting are not implemented yet.

| Concept in `docs/domain-model.md` | Module |
| --- | --- |
| identifiers, shared scalars, base model | `acquisition.domain.base` |
| closed vocabularies (`OpportunityStatus`, `CommercialArrangement`, `RejectionReason`, …) | `acquisition.domain.enums` |
| known / unknown / conflicting values, extraction provenance | `acquisition.domain.normalization` |
| `Workload`, availability, geography, work location, commercial terms, credentials, eligibility | `acquisition.domain.values` |
| `Evidence`, `EvidenceLibrary` | `acquisition.domain.evidence` |
| `PersonProfile`, `CompanyProfile` | `acquisition.domain.profiles` |
| `ProfileCatalogue` — the company, its people and the evidence they cite | `acquisition.domain.catalogue` |
| `Opportunity`, `IndividualOpportunity`, `CompanyOpportunity`, `Requirement` | `acquisition.domain.opportunity` |
| `MatchResult`, `Rejection` | `acquisition.domain.matching` |
| `Source` | `acquisition.domain.source` |
| JSON/YAML helpers | `acquisition.domain.serialization` |

Everything is importable from `acquisition.domain`.

## Data

`data/` holds the real profiles; `examples/` holds synthetic opportunities for
exercising the model. `tests/test_fixtures.py` validates both, so a model change that
breaks real data fails the suite.

```
data/company.yaml            the delivery organisation
data/people/*.yaml           one file per person
data/evidence/*.yaml         the shared evidence library, each file a list of items
data/sources.yaml            where opportunities are discovered
```

Load it as one unit, which is what checks that every citation resolves:

```python
from acquisition.domain import load_profile_catalogue

catalogue = load_profile_catalogue("data")
catalogue.cited_evidence(catalogue.person("salomon"))
```

### Invariants the models enforce

* Domain objects are immutable and reject unknown fields.
* A claimed capability or domain experience must carry at least one evidence
  reference, and every reference in the catalogue must resolve to a library item.
* Evidence is stored once and shared. A profile citing an item is the explicit
  statement of involvement, and the citation's note says what that subject
  contributed.
* A normalized value is `known`, `unknown` or `conflicting`; a value is only
  present when it is known, so missing information cannot read as satisfied.
* Percentages and hours in a `Workload` convert into one another only when the
  full-time week used for the conversion is retained. The same applies to on-site
  days and remote share in a `WorkLocationRequirement`, which never convert.
* A credential may state an expected completion only while it is unsettled.
* Only an explicit, mandatory, source-supported `Requirement` may be cited as
  the cause of a `Rejection`, and every rejection carries a reason code.
* An assessed `FitAssessment` must state a rationale; the default is `unknown`.
* `MatchResult.overall_score` uses a fixed 0-100 scale and is meant to be
  computed from the component assessments by the scoring stage.
