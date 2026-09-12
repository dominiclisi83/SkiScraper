from __future__ import annotations

from typing import Protocol

from ..models import Listing, SearchConfig


class Provider(Protocol):
    name: str

    def search(self, config: SearchConfig) -> list[Listing]: ...

