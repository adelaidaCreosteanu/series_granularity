# Introduction
This is a pure python solution which equalizes the granularity of a time series.

# How to run
Provide an input file as the first command line argument:

```bash
python equalizer.py my_input_file.json
```

Optionally, you can also provide the name of an output file as the second argument:

```bash
python equalizer.py my_input_file.json my_output_file.json
```

# Assumptions made
What happens if a datapoint lasts over a half hour mark?
For example:

```
{'timestamp': datetime.datetime(2020, 2, 13, 18, 00), 'value': 100},
{'timestamp': datetime.datetime(2020, 2, 13, 18, 20), 'value': 16},
{'timestamp': datetime.datetime(2020, 2, 13, 18, 35), 'value': 5},
{'timestamp': datetime.datetime(2020, 2, 13, 19, 00), 'value': null},
```

The second datapoint lasts from 18:20 to 18:35, over the half-hour mark.
My current solution includes the 'whole' datapoint in the first half-hour and ignores it for the second.

I think the correct behaviour should be that we break up the datapoint by introducing a new one with the same value, at the half-hour mark:

```
{'timestamp': datetime.datetime(2020, 2, 13, 18, 00), 'value': 100},
{'timestamp': datetime.datetime(2020, 2, 13, 18, 20), 'value': 16},
{'timestamp': datetime.datetime(2020, 2, 13, 18, 30), 'value': 16},
{'timestamp': datetime.datetime(2020, 2, 13, 18, 35), 'value': 5},
{'timestamp': datetime.datetime(2020, 2, 13, 19, 00), 'value': null},
```

Then we would count the datapoint for the correct half-hour.
However, I'm not sure if this would be desired, so I haven't implemented this fix.

# Extensions proposed
I would love to use the python library `click` to create a nicer command line 
interface complete with extensive argument validation.
