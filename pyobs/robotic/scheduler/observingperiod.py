from __future__ import annotations

import datetime
from functools import cache
from typing import Literal

import numpy as np
from astroplan import Observer

from pyobs.utils.time import Time

ObservingMode = Literal["day", "night"]


class ObservingPeriods:
    """History cycles: sunrise-to-sunrise at night, sunset-to-sunset for solar observing.

    Events are calculated from fixed UTC anchors and cached per date. This makes exact
    boundary membership independent of the time passed to astroplan's interpolator.
    One instance belongs to one scheduler run and one immutable mode.
    """

    def __init__(self, observer: Observer, mode: ObservingMode = "night"):
        if mode not in ("day", "night"):
            raise ValueError("Observing mode must be 'day' or 'night'.")
        self._observer = observer
        self._mode: ObservingMode = mode

    @property
    def mode(self) -> ObservingMode:
        return self._mode

    @cache
    def _events(self, date: datetime.date) -> tuple[Time, ...]:
        start = Time(datetime.datetime.combine(date, datetime.time()), scale="utc")
        end = Time(datetime.datetime.combine(date + datetime.timedelta(days=1), datetime.time()), scale="utc")
        event_func = self._observer.sun_rise_time if self.mode == "night" else self._observer.sun_set_time
        # Advance the search reference, never the returned event or a membership boundary.
        # Starting just before midnight also retains an event exactly at midnight.
        reference = start - datetime.timedelta(minutes=1)
        events: list[Time] = []
        for _ in range(3):
            try:
                event = Time(event_func(reference, which="next"))
            except ValueError as error:
                raise ValueError(f"No finite solar reset event for {date} in {self.mode} mode.") from error
            if np.any(event.mask) or not np.all(np.isfinite(event.jd)):
                raise ValueError(f"No finite solar reset event for {date} in {self.mode} mode.")
            if event >= end:
                if len(events) > 1:
                    raise ValueError(f"Ambiguous solar reset date {date} in {self.mode} mode.")
                return tuple(events)
            if event <= reference:
                raise ValueError("Solar reset events must increase.")
            if event >= start:
                events.append(event)
            reference = event + datetime.timedelta(minutes=1)
        raise ValueError(f"Too many solar reset events for {date}.")

    def start(self, time: Time) -> Time:
        """Return the inclusive opening event of the cycle containing ``time``."""
        date = time.utc.to_datetime().date()
        candidates = [event for event in self._events(date) if event <= time]
        if not candidates:
            candidates = list(self._events(date - datetime.timedelta(days=1)))
        if not candidates:
            raise ValueError(f"No solar reset event preceding {time} in {self.mode} mode.")
        return candidates[-1]

    def key(self, time: Time) -> datetime.date:
        return self.start(time).utc.to_datetime().date()

    def bounds(self, date: datetime.date, time: Time | None = None) -> tuple[Time, Time]:
        """Resolve a unique daily cycle, validating an optional evaluation-time anchor."""
        if time is None:
            events = self._events(date)
            if len(events) != 1:
                raise ValueError(f"Date {date} has no solar reset event in {self.mode} mode.")
            start = events[0]
        else:
            start = self.start(time)
            if start.utc.to_datetime().date() != date:
                raise ValueError("Observing period key does not match its time anchor.")
        following = [event for event in self._events(date) if event > start]
        if not following:
            following = list(self._events(date + datetime.timedelta(days=1)))
        if not following:
            raise ValueError(f"No solar reset event following {start} in {self.mode} mode.")
        return start, following[0]
