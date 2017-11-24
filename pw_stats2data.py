#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 10:13:43 2017

@author: pemoser
"""

import sys
import re
import os

def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)]

def printErrorAndExit(msg):
    print("ERROR: " + msg, file=sys.stderr, flush=True)
    sys.exit(1)

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
            printErrorAndExit("ERROR: Prefix does not match with filename")

        parameterName = m.groups()[0]
        parameterValue = m.groups()[1]

        if oldParameterName == None:
            oldParameterName = parameterName
        elif parameterName != oldParameterName:
            printErrorAndExit("Parameter name mismatch. First it was '%s', then '%s'." % (oldParameterName, parameterName))

        if not parameterName in parameters:
            parameters.append(parameterValue)

        if not parameterValue in results:
            results[parameterValue] = {}

        # Read the contents of the file
        with open(arg, 'r') as f:
            try:
                for line in f:
                    try:
                        cells = line.split("\t")
                        algo = os.path.basename(cells[0])

                        # We added timesplit to the results recently, hence result counts are at pos 7 now
                        # Before that, they were at pos 6 (since pos 7 is a filename/path we can simply check casting
                        # errors)
                        try:
                            resultCount = int(cells[7])
                        except:
                            resultCount = int(cells[6])

                        if not algo in algorithms:
                            algorithms.append(algo)

                        if algo in results[parameterValue]:
                            results[parameterValue][algo][0] += int(cells[1])
                            results[parameterValue][algo][1] += 1
                        else:
                            results[parameterValue][algo] = [int(cells[1]), 1, resultCount]
                    except:
                        continue
                results[parameterValue][algo][0] /= results[parameterValue][algo][1]
            except:
                continue



    # Print header
    print(parameterName, end='')
    for a in algorithms:
        print("\t%s" % a, end='')
    print("\tRESULTS")

    # Print data lines (first field = varying parameter)
    resultCount = -1
    for parameter in sorted(parameters, key=natural_sort_key):
        print(parameter + "\t", end='')
        res = results[parameter]
#        print(parameter)
#        print(res)
        try:
            resultCount = res[algorithms[0]][2]
        except:
            printErrorAndExit("Algorithm %s not found in results." % algorithms[0])

        for a in algorithms:
            if a in res:
                print("%d\t" % int(float(res[a][0]) / res[a][1]), end='')
                if resultCount != res[a][2]:
                    printErrorAndExit("Different result counts for the same parameter-value found!")
            else:
                print("nan\t", end='')

        print("%d" % resultCount)

if __name__ == '__main__':
    main()
