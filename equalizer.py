import dataclasses
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Union


def floor_to_half_hour(ts: datetime) -> datetime:
    if ts.minute < 30:
        return datetime(ts.year, ts.month, ts.day, ts.hour, minute=0)
    else:
        return datetime(ts.year, ts.month, ts.day, ts.hour, minute=30)


input_file = "input_c.json"
output_file = Path(input_file).stem + "_out.json"

with open(input_file, "r") as f:
    input = json.load(f)


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


time_values = [TimeValue(**t) for t in input["timeseries"]]
out_values = []

interval_start = floor_to_half_hour(time_values[0].timestamp)
sum_values = 0
half_hour = timedelta(minutes=30)

for t_start, t_end in zip(time_values, time_values[1:]):
    # Add to current interval
    elapsed = (t_end.timestamp - t_start.timestamp).total_seconds()
    sum_values += elapsed * t_start.value

    if interval_start + half_hour <= t_end.timestamp:
        # Calculate value for this interval
        mean_values = sum_values / half_hour.total_seconds()
        interval = TimeValue(interval_start, mean_values)
        out_values.append(interval)

        # We need to start a new interval
        interval_start = floor_to_half_hour(t_end.timestamp)
        sum_values = 0

print(time_values)
print("after:")
print(out_values)
out_values = [dataclasses.asdict(tv) for tv in out_values]
