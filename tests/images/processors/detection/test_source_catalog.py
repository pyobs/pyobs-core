import numpy as np
import numpy.testing
import pandas as pd

from pyobs.images.processors.detection._source_catalog import  _SourceCatalog


def test_filter_detection_flag_default():
    data = {"test": [1, 2, 3, 4, 5, 6, 7, 8]}
    catalog = _SourceCatalog(pd.DataFrame({"test": [1, 2, 3, 4, 5, 6, 7, 8]}))
    catalog.filter_detection_flag()

    numpy.testing.assert_array_equal(catalog.sources["test"], data["test"])


def test_filter_detection_flag():
    catalog = _SourceCatalog(pd.DataFrame({"flag": [1, 2, 3, 4, 5, 6, 7, 8]}))
    catalog.filter_detection_flag()

    assert 8 not in catalog.sources["flag"]


def test_clip_rotation_angle_default():
    data = {"test": [1, 2, 3, 4, 5, 6, 7, 8]}
    catalog = _SourceCatalog(pd.DataFrame({"test": [1, 2, 3, 4, 5, 6, 7, 8]}))
    catalog.clip_rotation_angle()

    numpy.testing.assert_array_equal(catalog.sources["test"], data["test"])


def test_clip_rotation_angle():
    catalog = _SourceCatalog(pd.DataFrame({"theta": [np.pi, 0]}))
    catalog.clip_rotation_angle()

    numpy.testing.assert_array_equal(catalog.sources["theta"], [np.pi/2, 0])


def test_rotation_angle_to_degree_default():
    data = {"test": [1, 2, 3, 4, 5, 6, 7, 8]}
    catalog = _SourceCatalog(pd.DataFrame({"test": [1, 2, 3, 4, 5, 6, 7, 8]}))
    catalog.rotation_angle_to_degree()

    numpy.testing.assert_array_equal(catalog.sources["test"], data["test"])


def test_rotation_angle_to_degree():
    catalog = _SourceCatalog(pd.DataFrame({"theta": [np.pi, 0]}))
    catalog.rotation_angle_to_degree()

    numpy.testing.assert_array_equal(catalog.sources["theta"], [180, 0])
