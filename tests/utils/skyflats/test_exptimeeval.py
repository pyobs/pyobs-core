import pytest

from pyobs.utils.skyflats.exptimeeval import ExpTimeEval


def test_parse_config_simple():
    ete = ExpTimeEval(None, 'exp(-0.9*(h+3.9))')
    assert len(ete.binnings) == 0
    assert len(ete.filters) == 0
    assert pytest.approx(ete(10), 0.1) == 3.69e-6
    assert pytest.approx(ete(10, filter_name='Clear'), 0.1) == 3.69e-6
    assert pytest.approx(ete(10, binning=(2, 2)), 0.1) == 9.22e-7


def test_parse_config_bias():
    ete = ExpTimeEval(None, {'1x1': 'exp(-0.9*(h+3.9))', '2x2': 'exp(-0.9*(h+5.9))'})
    assert ete.binnings == [(1, 1), (2, 2)]
    assert len(ete.filters) == 0
    assert pytest.approx(ete(10, binning=(1, 1)), 0.1) == 3.69e-6
    assert pytest.approx(ete(10, binning=(1, 1), filter_name='Clear'), 0.1) == 3.69e-6
    assert pytest.approx(ete(10, binning=(2, 2)), 0.1) == 6.09e-7


def test_parse_config_filter():
    ete = ExpTimeEval(None, {'Red': 'exp(-0.9*(h+3.9))', 'Blue': 'exp(-0.9*(h+5.9))'})
    assert ete.filters == ['Blue', 'Red']
    assert len(ete.binnings) == 0
    assert pytest.approx(ete(10, filter_name='Red'), 0.1) == 3.69e-6
    assert pytest.approx(ete(10, filter_name='Blue'), 0.1) == 6.09e-7
    assert pytest.approx(ete(10, filter_name='Red', binning=(2, 2)), 0.1) == 9.22e-7


def test_parse_config_full():
    ete = ExpTimeEval(None, {'1x1': {'Red': 'exp(-0.9*(h+3.9))', 'Blue': 'exp(-0.9*(h+5.9))'},
                             '2x2': {'Red': 'exp(-0.9*(h+4.9))'}})
    assert ete.filters == ['Blue', 'Red']
    assert ete.binnings == [(1, 1), (2, 2)]
    assert pytest.approx(ete(10, binning=(1, 1), filter_name='Red'), 0.1) == 3.69e-6
    assert pytest.approx(ete(10, binning=(1, 1), filter_name='Blue'), 0.1) == 6.09e-7
    assert pytest.approx(ete(10, binning=(2, 2), filter_name='Red'), 0.1) == 1.50e-6
