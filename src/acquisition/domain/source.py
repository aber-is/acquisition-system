"""Where opportunities are discovered."""

from __future__ import annotations

from pydantic import HttpUrl

from .base import DomainModel, NonEmptyStr, SourceId
from .enums import SourceKind


class Source(DomainModel):
    """A place opportunities come from, such as freelancermap, PROSTAFF, GHR, LinkedIn or SIMAP.

    Source information is preserved on every opportunity so that source quality
    can be evaluated later.
    """

    id: SourceId
    """Stable identifier used by :class:`~acquisition.domain.opportunity.Opportunity`."""

    name: NonEmptyStr
    """The source's own name, spelled as it spells itself."""

    kind: SourceKind = SourceKind.other
    """What kind of source this is."""

    url: HttpUrl | None = None
    """Entry point of the source."""

    notes: NonEmptyStr | None = None
    """Observations about the source, for example its typical listing quality."""
