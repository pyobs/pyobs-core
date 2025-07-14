from copy import copy
from typing import List

import numpy as np
import pandas as pd
from astropy.table import Table

from pyobs.images import Image


class _SourceCatalog:
    def __init__(self, sources: pd.DataFrame):
        self.sources = sources

    @classmethod
    def from_array(cls, sources: np.ndarray) -> "_SourceCatalog":
        source_dataframe = pd.DataFrame(sources)
        return cls(source_dataframe)

    @classmethod
    def from_table(cls, sources: Table) -> "_SourceCatalog":
        sources.rename_column("xcentroid", "x")
        sources.rename_column("ycentroid", "y")

        source_dataframe = sources.to_pandas()
        return cls(source_dataframe)

    def filter_detection_flag(self) -> None:
        if "flag" not in self.sources:
            return

        self.sources = self.sources[self.sources["flag"] < 8]

    def wrap_rotation_angle_at_ninty_deg(self) -> None:
        if "theta" not in self.sources:
            return

        self.sources["theta"] = np.arcsin(np.sin(self.sources["theta"]))

    def rotation_angle_to_degree(self) -> None:
        if "theta" not in self.sources:
            return

        self.sources["theta"] = np.degrees(self.sources["theta"])

    def apply_fits_origin_convention(self) -> None:
        self.sources["x"] += 1
        self.sources["y"] += 1

    def save_to_image(self, image: Image, keys: List[str]) -> Image:
        cat = self.sources[keys]

        output_image = copy(image)
        output_image.catalog = Table.from_pandas(cat)
        return output_image
