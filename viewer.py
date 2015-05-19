import csv
import sys
import ast
import matplotlib.pyplot as plt
import numpy as np

csv.field_size_limit(sys.maxsize)

series = {}
with open('%s'%sys.argv[1], 'rb') as f:
    r = csv.reader(f)
    series = dict(x for x in r)

print series.keys()
counter = ast.literal_eval(series['counter'])
curves = []
for i in range(2, len(sys.argv)):
    curves.append(ast.literal_eval(series[sys.argv[i]]))

if all(['lift' in sys.argv[i] for i in range(2, len(sys.argv))]):
    resultant = [sum(row[i] for row in curves) for i in range(len(curves[0]))]

plt.plot(np.linspace(0, (counter[-1]-counter[0])/50, len(resultant)), resultant, label='resultant')
plt.legend()
for curve in curves:
    plt.plot(np.linspace(0, (counter[-1]-counter[0])/50, len(curve)), \
            curve)

plt.show()
