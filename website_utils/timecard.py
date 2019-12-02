from datetime import datetime, timedelta
from math import sqrt

import functools
import os
import os.path
from typing import Dict, Tuple


class MemoizedFile:
    def __init__(self, filename: str):
        self.filename = filename
        self.last_update = {}
        self.cached_values = {}

    def get_timecard(self, start_time: datetime, end_time: datetime):
        logfile = self.filename
        file_mtime = os.path.getmtime(logfile)
        last_update = self.last_update
        cache = self.cached_values
        time_range = (start_time, end_time)

        if time_range not in cache or file_mtime > last_update[time_range]:
            with open(logfile, 'r') as f:
                cache[time_range] = self._compute_timecard(start_time, end_time)
            last_update[time_range] = file_mtime
        return cache[time_range]

    def _compute_timecard(self, range_start: datetime, range_stop: datetime):
        """Compute the value and circle radius for each circle in the timecard."""
        with open(self.filename, 'r') as log_file:
            ranges = _iter_ranges(log_file)
            counts, first, last = _count_hours(ranges, range_start, range_stop)
            totals = _count_total_hours(first, last)

        # datetime's weekday=0 starts on Monday, but we want to start on Sunday
        counts = counts[-24:] + counts[:-24]
        totals = totals[-24:] + totals[:-24]

        percents = [(c / t if t else 0) for c, t in zip(counts, totals)]
        radii = [sqrt(p) for p in percents]

        return percents, radii


def get_date_or_none(obj: Dict, key: str):
    """If obj contains key and its value is a valid date, return the date.
    Otherwise, return None.
    """
    try:
        return datetime.strptime(obj[key], '%Y-%m-%d')
    except (KeyError, ValueError):
        return None


def _iter_ranges(logfile: str):
    """Yield each of the lab open-close ranges as start and stop datetimes."""
    current_start = None
    for line in logfile:
        date = datetime.strptime(line[:19], '%Y/%m/%d %H:%M:%S')
        if line[20:] == 'Received request: open\n':
            if current_start is None:
                current_start = date
        elif line[20:] == 'Received request: close\n':
            if current_start is not None:
                yield current_start, date
                current_start = None


def _count_hours(ranges: Tuple[datetime, datetime], range_start=None, range_stop=None):
    """Return a list of the cumulative total for each hour in the week."""
    buckets = [0.0] * (24 * 7)
    one_hour = timedelta(0, 60 * 60)

    first = None
    last = None

    for start, stop in ranges:
        if ((range_start is not None and start < range_start) or
                (range_stop is not None and stop > range_stop)):
            continue

        if first is None:
            first = start
        last = stop

        open_ref = datetime(start.year, start.month, start.day, start.hour)
        open_ref += one_hour
        open_ref = min(open_ref, stop)
        open_frac = (open_ref - start) / one_hour
        buckets[24 * start.weekday() + start.hour] += open_frac

        if start.date() != stop.date() or start.hour != stop.hour:
            stop_ref = datetime(stop.year, stop.month, stop.day, stop.hour)
            stop_frac = (stop - stop_ref) / one_hour
            buckets[24 * stop.weekday() + stop.hour] += stop_frac

        start_hour = 24 * open_ref.weekday() + open_ref.hour
        stop_hour = 24 * stop.weekday() + stop.hour
        if stop_hour < start_hour - 1:
            stop_hour += 24 * 7

        for hour in range(start_hour, stop_hour):
            buckets[hour % (24 * 7)] += 1

    return buckets, first, last


def _count_total_hours(start: datetime, stop: datetime):
    """Count the number of times each hour slot has occurred."""
    if start is None or stop is None:
        return [0] * (24 * 7)

    start_hour = 24 * start.weekday() + start.hour
    stop_hour = 24 * stop.weekday() + stop.hour
    num_weeks = (stop - start).days // 7
    overlap_offset = (stop_hour - start_hour + 1) % (24 * 7) - 1
    totals = []
    for hour in range(24 * 7):
        total = num_weeks
        if (hour - start_hour) % (24 * 7) <= overlap_offset:
            total += 1
        totals.append(total)
    return totals
