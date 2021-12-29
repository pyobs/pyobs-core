from astroplan import Observer
import pytest

from pyobs.utils.skyflats import Scheduler
from pyobs.utils.skyflats.priorities import ConstSkyflatPriorities
from pyobs.utils.time import Time


async def test_scheduler():
    # init observer and time
    observer = Observer.at_site('SAAO')
    now = Time('2019-11-21T17:10:00Z')

    # have some test functions
    functions = {
        'B': ' exp(-1.22034 * (h + 3.16086))',
        'V': ' exp(-1.27565 * (h + 3.48265))',
        'R': ' exp(-1.39148 * (h + 3.63401))',
    }

    # set constant priorities
    priorities = ConstSkyflatPriorities({('B', (1, 1)): 1, ('V', (1, 1)): 2, ('R', (1, 1)): 3})

    # create scheduler
    scheduler = Scheduler(functions, priorities, observer)
    await scheduler(now)

    # test order
    assert scheduler[0].filter_name == 'B'
    assert scheduler[1].filter_name == 'V'
    assert scheduler[2].filter_name == 'R'

    # test start/end times
    assert scheduler[0].start == 1160
    assert pytest.approx(scheduler[0].end, 0.01) == 1200.46
    assert scheduler[1].start == 1270
    assert pytest.approx(scheduler[1].end, 0.01) == 1310.59
    assert scheduler[2].start == 1330
    assert pytest.approx(scheduler[2].end, 0.01) == 1370.59
