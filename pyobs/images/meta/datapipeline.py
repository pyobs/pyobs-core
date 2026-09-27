from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DataPipelineName:
    name: str | None


__all__ = ["DataPipelineName"]
