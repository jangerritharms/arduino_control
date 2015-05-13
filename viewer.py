import csv
import sys
import ast
import matplotlib.pyplot as plt
import numpy as np

csv.field_size_limit(sys.maxsize)

series = {}
with open('diesdas_result.csv', 'rb') as f:
    r = csv.reader(f)
    series = dict(x for x in r)

print series.keys()
counter = ast.literal_eval(series['counter'])
fcnt = ast.literal_eval(series['thrust_force_0'])
if 'counter' in series:
    plt.plot(np.linspace(0, counter[-1]/50, len(fcnt)), \
            fcnt)
    plt.show()
