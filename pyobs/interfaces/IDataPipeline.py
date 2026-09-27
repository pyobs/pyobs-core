from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..utils.time import Time
from .interface import Interface


@dataclass
class DataPipelineState:
    pipeline: str | None  # None = no pipeline, raw data is stored
    time: Time = field(default_factory=Time.now)


@dataclass
class DataPipelineCapabilities:
    pipelines: list[str] = field(default_factory=list)  # names configured in YAML


class IDataPipeline(Interface, metaclass=ABCMeta):
    """The module can run a selected, named pipeline on its data before storing it."""

    __module__ = "pyobs.interfaces"

    state = DataPipelineState
    capabilities = DataPipelineCapabilities

    @abstractmethod
    async def set_pipeline(self, pipeline: str | None = None, **kwargs: Any) -> None:
        """Select the pipeline to run on all following grabs.

        The pipeline result replaces the raw data: only the processed result is stored and
        broadcast.

        Args:
            pipeline: Name of a configured pipeline, or None to store raw data.

        Raises:
            InvalidArgumentError: If no pipeline with this name is configured.
        """
        ...


__all__ = ["IDataPipeline", "DataPipelineState", "DataPipelineCapabilities"]
