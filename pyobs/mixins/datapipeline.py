from __future__ import annotations

import logging
from abc import ABCMeta
from typing import Any

from pyobs.images import Image, ImageProcessor
from pyobs.interfaces import DataPipelineCapabilities, DataPipelineState, IDataPipeline
from pyobs.mixins.pipeline import PipelineMixin
from pyobs.modules import Module
from pyobs.object import Object
from pyobs.utils import exceptions as exc

log = logging.getLogger(__name__)


class _NamedPipeline(Object, PipelineMixin):
    """One configured, named pipeline. Private: only addressable through DataPipelineMixin."""

    __module__ = "pyobs.mixins"


class DataPipelineMixin(IDataPipeline, metaclass=ABCMeta):
    """Implements IDataPipeline.set_pipeline() on top of a host that stores images.

    Shared by BaseCamera and BaseVideo. The host class must:
      - be a Module (comm is used to publish DataPipelineState/DataPipelineCapabilities)
      - call _datapipeline_open() from its own open()
      - call _run_data_pipeline() on every grabbed image, before storing it
    """

    __module__ = "pyobs.mixins"

    def __init__(
        self,
        pipelines: dict[str, list[dict[str, Any] | ImageProcessor]] | None = None,
        default_pipeline: str | None = None,
        **kwargs: Any,
    ):
        """Initializes the mixin.

        Args:
            pipelines: Named pipelines, each a list of image processor configs/objects.
            default_pipeline: Name of the pipeline selected on startup/reset. Must be a key in
                pipelines, if given.

        Raises:
            ValueError: If default_pipeline is not a configured pipeline, or a pipeline name is
                empty or "none" (case-insensitive), which is reserved for the PIPELINE header
                value meaning "no pipeline".
        """
        if pipelines is not None:
            for name in pipelines:
                if not name or name.strip().lower() == "none":
                    raise ValueError(f"Invalid pipeline name: {name!r}.")
        if default_pipeline is not None and (pipelines is None or default_pipeline not in pipelines):
            raise ValueError(f"default_pipeline {default_pipeline!r} is not a configured pipeline.")

        self._default_pipeline = default_pipeline
        self._data_pipeline: str | None = default_pipeline
        self._named_pipelines: dict[str, _NamedPipeline] = {}

        # Object.__init__ (which provides add_child_object) must have run before the pipeline
        # objects below are built -- it runs somewhere in this super().__init__() chain.
        super().__init__(**kwargs)

        if not isinstance(self, Object):
            raise ValueError("This class is no Object.")
        if pipelines is not None:
            for name, steps in pipelines.items():
                self._named_pipelines[name] = self.add_child_object(_NamedPipeline, _NamedPipeline, steps=steps)

    async def _datapipeline_open(self) -> None:
        """Call from the host's open() to publish capabilities and the initial pipeline state."""
        if not isinstance(self, Module):
            raise ValueError("This is not a module.")
        await self.comm.set_capabilities(
            IDataPipeline, DataPipelineCapabilities(pipelines=sorted(self._named_pipelines))
        )
        await self.comm.set_state(IDataPipeline, DataPipelineState(pipeline=self._data_pipeline))

    async def set_pipeline(self, pipeline: str | None = None, **kwargs: Any) -> None:
        """Select the pipeline to run on all following grabs.

        Args:
            pipeline: Name of a configured pipeline, or None to store raw data.

        Raises:
            InvalidArgumentError: If no pipeline with this name is configured.
        """
        if not isinstance(self, Module):
            raise ValueError("This is not a module.")

        if pipeline is not None and pipeline not in self._named_pipelines:
            raise exc.InvalidArgumentError(f"No pipeline named {pipeline!r} configured.")

        log.info("Setting data pipeline to %s...", pipeline or "none")
        self._data_pipeline = pipeline
        await self.comm.set_state(IDataPipeline, DataPipelineState(pipeline=pipeline))

    async def _run_data_pipeline(self, image: Image, pipeline: str | None) -> Image:
        """Run the given pipeline on image, replacing raw data with the pipeline's result.

        Always sets the PIPELINE header, even when no pipeline is selected.

        Args:
            image: Image to run the pipeline on.
            pipeline: Name of the pipeline to run, or None to leave the image unchanged.

        Returns:
            The image after the pipeline ran, or unchanged if no pipeline was selected.

        Raises:
            GrabImageError: If the pipeline failed. Nothing should be stored in that case.
        """
        image.header["PIPELINE"] = (pipeline or "none", "Pipeline applied before storing")
        if pipeline is None:
            return image

        try:
            return await self._named_pipelines[pipeline].run_pipeline(image)
        except Exception as e:
            raise exc.GrabImageError(f"Pipeline {pipeline} failed: {e}") from e


__all__ = ["DataPipelineMixin"]
