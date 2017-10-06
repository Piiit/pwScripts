#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 10:13:43 2017

@author: pemoser
"""

import sys
import re
import os

def main():

    if len(sys.argv) <= 2:
        print("USAGE: pw_stats2data.py <prefix> list-of-files")
        print()
        print("  Extract from a list of files containing experiments (TSV)")
        print("  the execution time. Remove <prefix> from each filename, and choose the remaining")
        print("  text as varying parameter name.")
        print("  The full filename pattern looks like this: <prefix><parameter-name><parameter-value>")
        print()
        print("  The result is then a table with the prefix as first column name, and all algorithms as following")
        print("  column names. The cells contain the average of all execution times within a single file.")
        print()
        sys.exit(0)

    # Collect data
    results = {}
    algorithms = []
    parameters = []
    parameterName = "X"
    oldParameterName = None
    prefix = sys.argv[1]
    for arg in sys.argv[2:]:

        # Get the varying variable name and value from the filename
        filename = os.path.splitext(os.path.basename(arg))[0]
        m = re.match(r"%s([a-zA-Z]+)([0-9\.]+).*" % prefix, filename)
        if not m:
            print("ERROR: Prefix does not match with filename")
            sys.exit(1)

        parameterName = m.groups()[0]
        parameterValue = m.groups()[1]

        if oldParameterName == None:
            oldParameterName = parameterName
        elif parameterName != oldParameterName:
            print("ERROR: Parameter name mismatch. First it was '%s', then '%s'." % (oldParameterName, parameterName))
            sys.exit(1)

        if not parameterName in parameters:
            parameters.append(parameterValue)

        if not parameterValue in results:
            results[parameterValue] = {}

        with open(arg, 'r') as f:
            headerDone = False
            try:
                for line in f:
                    if not headerDone:
                        headerDone = True
                        continue

                    try:
                        cells = line.split("\t")
                        algo = cells[0]

                        if not algo in algorithms:
                            algorithms.append(algo)

                        if algo in results[parameterValue]:
                            results[parameterValue][algo][0] += int(cells[1])
                            results[parameterValue][algo][1] += 1
                        else:
                            results[parameterValue][algo] = [int(cells[1]), 1]
                    except:
                        continue
                results[parameterValue][algo][0] /= results[parameterValue][algo][1]
            except:
                continue

    # Print header
    print(parameterName, end='')
    for a in algorithms:
        print("\t%s" % a, end='')
    print()

    # Print data lines (first field = varying parameter)
    for parameter in parameters:
        print(parameter + "\t", end='')
        res = results[parameter]
        for a in algorithms:
            if a in res:
                print("%d\t" % res[a][0], end='')
            else:
                print("nan\t", end='')
        print()

if __name__ == '__main__':
    main()
