import json

from pyobs.robotic.lco import LcoTask
from pyobs.robotic.lco._portal import LcoSchedulableRequest
from pyobs.robotic.scripts import Script

REQUEST_CONFIG = """
{
    "created": "2026-01-16T14:42:35.493049Z",
    "id": 90622,
    "ipp_value": 1.05,
    "is_staff": true,
    "modified": "2026-01-16T14:42:35.493070Z",
    "name": "Kochab",
    "observation_type": "NORMAL",
    "operator": "SINGLE",
    "proposal": "dummy",
    "state": "PENDING",
    "submitter": "husser",
    "requests": [
        {
            "acceptability_threshold": 90.0,
            "configuration_repeats": 1,
            "configurations": [
                {
                    "acquisition_config": {
                        "extra_params": {},
                        "mode": "OFF"
                    },
                    "constraints": {
                        "extra_params": {},
                        "max_airmass": 1.6,
                        "max_lunar_phase": 0.7,
                        "min_lunar_distance": 60.0
                    },
                    "extra_params": {},
                    "guiding_config": {
                        "exposure_time": null,
                        "extra_params": {},
                        "mode": "OFF",
                        "optical_elements": {},
                        "optional": true
                    },
                    "id": 94322,
                    "instrument_configs": [
                        {
                            "exposure_count": 30,
                            "exposure_time": 60.0,
                            "extra_params": {},
                            "mode": "dummy",
                            "optical_elements": {
                                "filter": "Clear"
                            },
                            "rois": [],
                            "rotator_mode": ""
                        }
                    ],
                    "instrument_type": "DUMMY",
                    "merits": [
                        {
                            "params": {
                                "count": 3
                            },
                            "type": "PerNight"
                        }
                    ],
                    "priority": 1,
                    "repeat_duration": null,
                    "target": {
                        "dec": 74.1555039444,
                        "epoch": 2000.0,
                        "extra_params": {},
                        "hour_angle": null,
                        "name": "Kochab",
                        "parallax": 0.0,
                        "proper_motion_dec": 0.0,
                        "proper_motion_ra": 0.0,
                        "ra": 222.6763575,
                        "type": "ICRS"
                    },
                    "type": "EXPOSE"
                }
            ],
            "duration": 1925,
            "extra_params": {
                "multi_obs": true
            },
            "id": 94320,
            "location": {
                "telescope_class": "0m0"
            },
            "modified": "2026-01-16T14:42:35.495326Z",
            "observation_note": "",
            "optimization_type": "TIME",
            "state": "PENDING",
            "windows": [
                {
                    "end": "2026-12-31T23:59:59Z",
                    "start": "2026-01-01T00:00:00Z"
                }
            ]
        }
    ]
}
"""


def test_create_lcoschedulablerequest() -> None:
    request_config = json.loads(REQUEST_CONFIG)
    schedulable_request = LcoSchedulableRequest.model_validate(request_config)

    # task
    assert schedulable_request.name == "Kochab"

    # request
    assert len(schedulable_request.requests) == 1
    request = schedulable_request.requests[0]
    assert request.state == "PENDING"

    # configurations
    assert len(request.configurations) == 1
    config = request.configurations[0]
    assert config.instrument_type == "DUMMY"

    # acquisition, guiding, constraints, target
    assert config.acquisition_config.mode == "OFF"
    assert config.guiding_config.mode == "OFF"
    assert config.constraints.max_airmass == 1.6
    assert config.target.name == "Kochab"

    # instrument configs
    assert len(config.instrument_configs) == 1
    instrument_config = config.instrument_configs[0]
    assert instrument_config.mode == "dummy"

    # merits
    assert len(config.merits) == 1
    merit = config.merits[0]
    assert merit.type == "PerNight"

    # windows
    assert len(request.windows) == 1
    window = request.windows[0]
    assert window.start.isot == "2026-01-01T00:00:00.000"


def test_lcoschedulablerequest_to_lcotask() -> None:
    request_config = json.loads(REQUEST_CONFIG)
    schedulable_request = LcoSchedulableRequest.model_validate(request_config)
    script = Script()
    tasks = LcoTask.from_schedulable_request(schedulable_request, script)

    assert len(tasks) == 1
    task = tasks[0]
    assert task.name == "Kochab"
