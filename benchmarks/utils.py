
"""General purpose functions"""
import math


def mean_stdev(data):
    """Compute the mean and standard deviation for the given data
    :data: a sequence of data values
    :return: mean, stdev
    :raise: ValueError if data has no item"""
    ldata = len(data)
    if ldata < 1:
        raise ValueError('No data available to compute the mean from')
    mean = sum(data) / ldata
    return mean, (math.sqrt(sum((x - mean) ** 2 for x in data) / (ldata - 1))
                  if ldata > 1 else 0)
