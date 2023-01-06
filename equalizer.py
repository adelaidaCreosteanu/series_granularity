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


input_file = sys.argv[1]
if len(sys.argv) > 2:
    output_file = sys.argv[2]
else:
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

    def serialize(self) -> Dict:
        time_ms = int(self.timestamp.timestamp() * 1000)
        return {"timestamp": time_ms, "value": self.value}


time_values = [TimeValue(**t) for t in input["timeseries"]]
out_values = []

interval_start = floor_to_half_hour(time_values[0].timestamp)
sum_values = 0
sum_seconds = 0
half_hour = timedelta(minutes=30)

for t_start, t_end in zip(time_values, time_values[1:]):
    # Add to current interval
    elapsed = (t_end.timestamp - t_start.timestamp).total_seconds()
    sum_values += elapsed * t_start.value
    sum_seconds += elapsed

    if interval_start + half_hour <= t_end.timestamp:
        if sum_seconds < half_hour.total_seconds():
            print(f"Incomplete interval, skipping {t_start}")
        else:
            # Calculate value for this interval
            mean_values = sum_values / half_hour.total_seconds()
            out_values.append(TimeValue(interval_start, mean_values))

        # We need to start a new interval
        interval_start = floor_to_half_hour(t_end.timestamp)
        sum_values = 0
        sum_seconds = 0

print(time_values)
print("after:")
print(out_values)
out_values = [tv.serialize() for tv in out_values]

output = copy(input)
output["timeseries"] = out_values
with open(output_file, "w") as f:
    json.dump(output, f)
