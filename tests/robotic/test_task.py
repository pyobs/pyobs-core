import yaml

from pyobs.robotic import Task
from pyobs.robotic.scheduler.constraints import AirmassConstraint

TASK_CONFIG = """
---
class: pyobs.robotic.Task
id: kochab
name: Kochab
priority: 1
duration: 2253
constraints:
  - class: pyobs.robotic.scheduler.constraints.AirmassConstraint
    max_airmass: 1.3
  - class: pyobs.robotic.scheduler.constraints.MoonSeparationConstraint
    min_distance: 30.0
merits:
  - class: pyobs.robotic.scheduler.merits.PerNightMerit
    count: 3
target:
  class: pyobs.robotic.scheduler.targets.SiderealTarget
  name: Kochab
  ra: 222.6763575
  dec: 74.1555039444
script:
  class: pyobs.robotic.scripts.Script
"""


def test_create_task() -> None:
    task_config = yaml.safe_load(TASK_CONFIG)
    task = Task.model_validate(task_config)

    # task
    assert task.name == "Kochab"

    # constraints
    assert len(task.constraints) == 2
    constraint = task.constraints[0]
    assert isinstance(constraint, AirmassConstraint)
    assert constraint.max_airmass == 1.3
