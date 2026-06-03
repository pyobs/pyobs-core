# ── shared mock responses ────────────────────────────────────────────────────

OBSERVATIONS_RESPONSE = {
    "count": 1,
    "next": None,
    "previous": None,
    "results": [
        {
            "id": 1020277,
            "request": {
                "id": 98260,
                "observation_note": "",
                "optimization_type": "AIRMASS",
                "state": "PENDING",
                "acceptability_threshold": 90,
                "configuration_repeats": 1,
                "extra_params": {},
                "modified": "2026-06-03T08:13:43.639768Z",
                "duration": 151,
                "configurations": [
                    {
                        "id": 98262,
                        "instrument_type": "0M5 IAG50CM SBIG6303E",
                        "type": "EXPOSE",
                        "repeat_duration": None,
                        "extra_params": {},
                        "priority": 1,
                        "instrument_configs": [
                            {
                                "optical_elements": {"filter": "Clear"},
                                "mode": "sbig6303e_2x2",
                                "exposure_time": 30,
                                "exposure_count": 1,
                                "rotator_mode": "",
                                "extra_params": {"binning": 2},
                                "rois": [],
                            }
                        ],
                        "constraints": {
                            "max_airmass": 3,
                            "min_lunar_distance": 30,
                            "max_lunar_phase": 1,
                            "extra_params": {},
                        },
                        "merits": [],
                        "acquisition_config": {"mode": "OFF", "extra_params": {}},
                        "guiding_config": {
                            "optional": True,
                            "mode": "OFF",
                            "optical_elements": {},
                            "exposure_time": None,
                            "extra_params": {},
                        },
                        "target": {
                            "type": "ICRS",
                            "name": "Polaris",
                            "ra": 250.423475,
                            "dec": 36.4613194444,
                            "proper_motion_ra": 0,
                            "proper_motion_dec": 0,
                            "parallax": 0,
                            "epoch": 2000,
                            "hour_angle": None,
                            "extra_params": {},
                        },
                        "configuration_status": 1020277,
                        "state": "PENDING",
                        "instrument_name": "kb03",
                        "guide_camera_name": "",
                        "summary": {},
                    }
                ],
            },
            "site": "goe",
            "enclosure": "roof",
            "telescope": "0m5a",
            "start": "2026-06-03T21:25:26Z",
            "end": "2026-06-03T21:27:57Z",
            "priority": 10,
            "state": "PENDING",
            "proposal": "test",
            "submitter": "husser",
            "name": "Test",
            "ipp_value": 1.05,
            "observation_type": "NORMAL",
            "request_group_id": 94515,
            "created": "2026-06-03T08:20:41.348952Z",
            "modified": "2026-06-03T08:20:41.348945Z",
        }
    ],
}

SCHEDULABLE_REQUESTS_RESPONSE = [
    {
        "id": 94515,
        "submitter": "husser",
        "proposal": "test",
        "name": "Test",
        "observation_type": "NORMAL",
        "operator": "SINGLE",
        "ipp_value": 1.05,
        "state": "PENDING",
        "created": "2026-06-03T08:13:43.630204Z",
        "modified": "2026-06-03T08:13:43.630217Z",
        "requests": [
            {
                "id": 98260,
                "observation_note": "",
                "optimization_type": "AIRMASS",
                "state": "PENDING",
                "acceptability_threshold": 90,
                "configuration_repeats": 1,
                "extra_params": {},
                "modified": "2026-06-03T08:13:43.639768Z",
                "duration": 151,
                "configurations": [
                    {
                        "id": 98262,
                        "instrument_type": "0M5 IAG50CM SBIG6303E",
                        "type": "EXPOSE",
                        "repeat_duration": None,
                        "extra_params": {},
                        "priority": 1,
                        "instrument_configs": [
                            {
                                "optical_elements": {"filter": "Clear"},
                                "mode": "sbig6303e_2x2",
                                "exposure_time": 30,
                                "exposure_count": 1,
                                "rotator_mode": "",
                                "extra_params": {"binning": 2},
                                "rois": [],
                            }
                        ],
                        "constraints": {
                            "max_airmass": 3,
                            "min_lunar_distance": 30,
                            "max_lunar_phase": 1,
                            "extra_params": {},
                        },
                        "merits": [],
                        "acquisition_config": {"mode": "OFF", "extra_params": {}},
                        "guiding_config": {
                            "optional": True,
                            "mode": "OFF",
                            "optical_elements": {},
                            "exposure_time": None,
                            "extra_params": {},
                        },
                        "target": {
                            "type": "ICRS",
                            "name": "Polaris",
                            "ra": 250.423475,
                            "dec": 36.4613194444,
                            "proper_motion_ra": 0,
                            "proper_motion_dec": 0,
                            "parallax": 0,
                            "epoch": 2000,
                            "hour_angle": None,
                            "extra_params": {},
                        },
                    }
                ],
                "location": {"telescope_class": "0m5"},
                "windows": [
                    {
                        "start": "2026-06-03T10:07:00Z",
                        "end": "2026-06-04T10:07:00Z",
                    }
                ],
            }
        ],
        "is_staff": True,
    }
]

LAST_SCHEDULED_RESPONSE = {"last_schedule_time": "2026-05-27T08:18:50.228196Z"}

SUBMIT_OBSERVATION_RESPONSE = {
    "site": "goe",
    "enclosure": "roof",
    "telescope": "0m5a",
    "start": "2026-06-03T21:25:26Z",
    "end": "2026-06-03T21:27:57Z",
    "priority": 10,
    "configuration_statuses": [],
    "request": 98260,
    "state": "PENDING",
    "modified": "2026-06-03T08:33:33.701120Z",
    "created": "2026-06-03T08:33:33.701128Z",
}

CONFIG_STATUS_RESPONSE = {
    "id": 1020277,
    "summary": {
        "start": "2026-06-03T21:25:26Z",
        "end": "2026-06-03T21:27:57Z",
        "state": "COMPLETED",
        "reason": "",
        "time_completed": 100,
        "events": {},
    },
    "instrument_name": "kb03",
    "guide_camera_name": "",
    "state": "COMPLETED",
    "configuration": 98262,
}

INSTRUMENTS_RESPONSE = {
    "0M5 IAG50CM SBIG6303E": {
        "type": "IMAGE",
        "class": "0m5",
        "name": "SBIG 6303e (50cm)",
        "optical_elements": {
            "filters": [
                {"name": "Clear", "code": "Clear", "schedulable": True, "default": True},
            ]
        },
        "modes": {
            "readout": {
                "type": "readout",
                "modes": [
                    {
                        "name": "Full Frame 2x2",
                        "overhead": 8.4241,
                        "code": "sbig6303e_2x2",
                        "schedulable": True,
                        "validation_schema": {},
                    }
                ],
                "default": "sbig6303e_2x2",
            }
        },
        "camera_type": {
            "science_field_of_view": 0,
            "autoguider_field_of_view": 0,
            "pixel_scale": 0,
            "pixels_x": 3072,
            "pixels_y": 2048,
            "orientation": 0,
        },
    }
}
