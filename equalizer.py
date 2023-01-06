import json
import sys
from copy import copy
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Union


def floor_to_half_hour(ts: datetime) -> datetime:
    if ts.minute < 30:
        return datetime(ts.year, ts.month, ts.day, ts.hour, minute=0)
    else:
        return datetime(ts.year, ts.month, ts.day, ts.hour, minute=30)


def force_ceil_to_half_hour(ts: datetime) -> datetime:
    if ts.minute < 30:
        return datetime(ts.year, ts.month, ts.day, ts.hour, minute=30)
    else:
        previous_hour = datetime(ts.year, ts.month, ts.day, ts.hour, minute=0)
        return previous_hour + timedelta(hours=1)


@dataclass
class TimeValue():
    timestamp: Union[datetime, int]
    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.timestamp, datetime):
            # Convert from ms to s
            ts = self.timestamp / 1000
            # Cast from epoch time to timestamp
            self.timestamp = datetime.fromtimestamp(ts)

    def serialize(self) -> Dict:
        time_ms = int(self.timestamp.timestamp() * 1000)
        return {"timestamp": time_ms, "value": self.value}


class Equalizer:

    def __init__(self, input_data) -> None:
        self._input_data = input_data
        self._data_points = None

        self._validate()
        self._break_up_long_data_points()

    def _validate(self):
        try:
            timeseries = self._input_data["timeseries"]
        except KeyError as ex:
            raise ValueError(
                f"Input file is missing attribute 'timeseries'") from ex

        try:
            self._data_points = [TimeValue(**t) for t in timeseries]
        except Exception as ex:
            raise ValueError(
                f"Unexpected format of timeseries in input file!") from ex

        if len(self._data_points) < 2:
            raise ValueError(f"At least two values are required in the "
                             f"timeseries. Got: {len(self._data_points)}")

        timestamp_set = set([tv.timestamp for tv in self._data_points])
        if len(timestamp_set) < len(self._data_points):
            raise ValueError(f"Duplicate timestamps are not accepted!")

    def _break_up_long_data_points(self):
        data_points_dict = {tv.timestamp: tv.value for tv in self._data_points}

        # We assume original data is sorted.
        for t_start, t_end in zip(self._data_points, self._data_points[1:]):
            next_half_hour = force_ceil_to_half_hour(t_start.timestamp)
            while next_half_hour < t_end.timestamp:
                # Add to dictionary
                data_points_dict[next_half_hour] = t_start.value
                next_half_hour = force_ceil_to_half_hour(next_half_hour)

        # Sort dictionary based on timestamp
        data_points = sorted(list(data_points_dict.items()),
                             key=lambda t: t[0])

        # Convert to `TimeValue`s
        self._data_points = [TimeValue(*v) for v in data_points]

    def run(self):
        interval_start = floor_to_half_hour(self._data_points[0].timestamp)
        sum_values = 0
        sum_seconds = 0
        half_hour = timedelta(minutes=30)
        out_values = []

        for t_start, t_end in zip(self._data_points, self._data_points[1:]):
            # Add to current interval
            elapsed = (t_end.timestamp - t_start.timestamp).total_seconds()
            sum_values += elapsed * t_start.value
            sum_seconds += elapsed

            if interval_start + half_hour <= t_end.timestamp:
                if sum_seconds < half_hour.total_seconds():
                    print(f"Incomplete interval, skipping {t_start}")
                elif sum_seconds > half_hour.total_seconds():
                    raise RuntimeError(
                        f"Interval is longer than half an hour! "
                        f"Check {t_start}")
                else:
                    # Calculate value for this interval
                    mean_values = sum_values / half_hour.total_seconds()
                    out_values.append(TimeValue(interval_start, mean_values))

                # We need to start a new interval
                interval_start = floor_to_half_hour(t_end.timestamp)
                sum_values = 0
                sum_seconds = 0

        output = self._build_output(out_values)
        return output

    def _build_output(self, out_values):
        out_values = [tv.serialize() for tv in out_values]
        output = copy(self._input_data)
        output["timeseries"] = out_values
        return output


if __name__ == "__main__":
    input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = Path(input_file).stem + "_out.json"

    try:
        with open(input_file, "r") as f:
            input_data = json.load(f)
    except Exception as ex:
        raise ValueError(f"Could not load {input_file} as json!") from ex

    eq = Equalizer(input_data)
    output_data = eq.run()

    try:
        with open(output_file, "w") as f:
            json.dump(output_data, f)
    except Exception as ex:
        raise RuntimeError(f"Could not save output to {output_file}!") from ex
    print(f"Saved output to {output_file}")
