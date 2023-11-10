from copy import copy
from typing import Optional, List

import numpy as np
import pandas as pd
from astropy.table import Table

from pyobs.images import Image


class _SourceCatalog:
    def __init__(self, sources: pd.DataFrame):
        self.sources = sources

    @classmethod
    def from_array(cls, sources: np.ndarray):
        source_dataframe = pd.DataFrame(sources)
        return cls(source_dataframe)

    @classmethod
    def from_table(cls, sources: Table):
        sources.rename_column("xcentroid", "x")
        sources.rename_column("ycentroid", "y")

        source_dataframe = sources.to_pandas()
        return cls(source_dataframe)

    def filter_detection_flag(self):
        if "flag" not in self.sources:
            return

        self.sources = self.sources[self.sources["flag"] < 8]

    def clip_rotation_angle(self):
        if "theta" not in self.sources:
            return

        self.sources["theta"] = self.sources["theta"].clip(lower=np.pi / 2, upper=np.pi / 2)

    def rotation_angle_to_degree(self):
        if "theta" not in self.sources:
            return

        self.sources["theta"] = np.degrees(self.sources["theta"])

    def apply_fits_origin_convention(self):
        self.sources["x"] += 1
        self.sources["y"] += 1

    def save_to_image(self, image: Image, keys: List[str]) -> Image:
        cat = self.sources[keys]

        output_image = copy(image)
        output_image.catalog = Table.from_pandas(cat)
        return output_image
