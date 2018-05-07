from timecard import _iter_ranges, _count_total_hours
from datetime import datetime
import pytest


def log_generator():
    yield '2017/01/01 15:13:06 Seclab listener started\n'
    yield '2017/01/01 15:13:07 Received request: close\n'
    yield '2017/01/01 15:13:08 Received request: open\n'
    yield '2017/01/01 15:13:09 Received request: open\n'
    yield '2017/01/01 15:13:10 Received request: close\n'
    yield '2017/01/01 15:13:11 Received request: open\n'
    yield '2017/01/01 15:13:12 Received request: close\n'
    yield '2017/01/01 15:13:13 Received request: close\n'
    yield '2017/01/01 15:13:14 Received request: open\n'


@pytest.fixture
def logfile():
    return log_generator()


def test_iter_ranges(logfile):
    ranges = list(_iter_ranges(logfile))
    assert ranges == [
        (datetime(2017, 1, 1, 15, 13, 8), datetime(2017, 1, 1, 15, 13, 10)),
        (datetime(2017, 1, 1, 15, 13, 11), datetime(2017, 1, 1, 15, 13, 12)),
    ]


def test_count_total_hours_empty():
    assert _count_total_hours(None, None) == [0] * (24 * 7)


def test_count_total_hours():
    totals = _count_total_hours(datetime(2017, 1, 1), datetime(2017, 1, 1))
    assert totals == [0] * (6 * 24) + [1] + [0] * 23

if __name__ == '__main__':
    test_iter_ranges(logfile())
    test_count_total_hours_empty()
    test_count_total_hours()