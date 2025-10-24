from dataclasses import dataclass
from typing import Any

import dacite
import requests
from urllib.parse import urljoin


@dataclass
class CameraType:
    id: int
    size: str
    pscale: float
    name: str
    code: str
    pixels_x: int
    pixels_y: int
    max_rois: int


@dataclass
class OpticalElement:
    name: str
    code: str
    schedulable: bool


@dataclass
class OpticalElementGroup:
    name: str
    type: str
    optical_elements: list[OpticalElement]
    element_change_overhead: float
    default: str


@dataclass
class Camera:
    id: int
    code: str
    camera_type: CameraType
    orientation: float
    optical_element_groups: list[OpticalElementGroup]
    host: str


@dataclass
class Mode:
    name: str
    overhead: float
    code: str
    schedulable: bool
    validation_schema: dict[str, Any]


@dataclass
class ModeType:
    type: str
    default: str
    modes: list[Mode]


@dataclass
class ConfigurationType:
    name: str
    code: str
    config_change_overhead: float
    schedulable: bool
    force_acquisition_off: bool
    requires_optical_elements: bool
    validation_schema: dict[str, Any]


@dataclass
class InstrumentType:
    id: int
    name: str
    code: str
    fixed_overhead_per_exposure: float
    instrument_category: str
    observation_front_padding: float
    acquire_exposure_time: float
    default_configuration_type: str
    mode_types: list[ModeType]
    default_acceptability_threshold: float
    config_front_padding: float
    allow_self_guiding: bool
    configuration_types: list[ConfigurationType]
    validation_schema: dict[str, Any]


@dataclass
class Instrument:
    id: int
    code: str
    state: str
    telescope: str
    autoguider_camera: Camera
    science_cameras: list[Camera]
    instrument_type: InstrumentType


@dataclass
class Telescope:
    id: int
    serial_number: str
    name: str
    code: str
    active: bool
    aperture: float
    lat: float
    slew_rate: float
    minimum_slew_overhead: float
    instrument_change_overhead: float
    long: float
    enclosure: str
    horizon: float
    ha_limit_pos: float
    ha_limit_neg: float
    telescope_front_padding: float
    zenith_blind_spot: float
    instrument_set: list[Instrument]


@dataclass
class Enclosure:
    id: int
    name: str
    code: str
    active: bool
    site: str
    telescope_set: list[Telescope]


@dataclass
class Site:
    id: int
    name: str
    code: str
    active: bool
    timezone: int
    restart: str
    tz: str
    lat: float
    long: float
    enclosure_set: list[Enclosure]


class ConfigDB:
    def __init__(self, url: str):
        self.url = url
        self.config = self._download_config()

    def _download_config(self) -> list[Site]:
        json = requests.get(urljoin(self.url, "sites")).json()
        return [dacite.from_dict(Site, site) for site in json["results"]]

    def get_instrument_type_locations(
        self, instrument_type: str
    ) -> list[tuple[Site, Enclosure, Telescope, Instrument]]:
        locations: list[tuple[Site, Enclosure, Telescope, Instrument]] = []
        for site in self.config:
            for enclosure in site.enclosure_set:
                for telescope in enclosure.telescope_set:
                    for instrument in telescope.instrument_set:
                        if instrument.instrument_type.code == instrument_type:
                            locations.append((site, enclosure, telescope, instrument))
        return locations


__all__ = ["ConfigDB"]
