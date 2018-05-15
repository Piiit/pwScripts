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
    print(os.path.basename(sys.argv[0]) + ": ERROR: " + msg, file=sys.stderr, flush=True)
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
    # Results have the following hierarchy: parameterValue > algo > [runtimesum, experimentcount, resultcount]
    # For example: parameterName = 'N' and the value is the cardinality, so we have a table as follows:
    #    10     algoA    [10, 2, 200]
    #           algoB    [...]
    #    20     algoA    ...
    results = {}
    algorithms = []
    parameters = []
    parameterName = "X"
    oldParameterName = None
    prefix = sys.argv[1]
    for arg in sys.argv[2:]:

        if not os.path.exists(arg):
            printErrorAndExit("File '%s' does not exist." % arg)

        # Get the varying variable name and value from the filename
        filename = os.path.splitext(os.path.basename(arg))[0]
        m = re.match(r"%s([a-zA-Z]+)([0-9\.]+).*" % prefix, filename)
        if not m:
            printErrorAndExit("Prefix '%s' does not match with filename '%s'. At least one letter must be left as parameter name." % (prefix, filename))

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

        expRun = 0

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

                        # Experiment run deterimens if we must overwrite an older experiment
                        if algo in results[parameterValue] and expRun in results[parameterValue][algo]:
                            results[parameterValue][algo][expRun][0] += int(cells[1])
                            results[parameterValue][algo][expRun][1] += 1
                        else:
                            results[parameterValue][algo] = {expRun : [int(cells[1]), 1, resultCount]}
                    except:
                        expRun += 1
                        continue
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
            val = next(iter(res[algorithms[0]].values()))
            resultCount = val[2]
        except:
            printErrorAndExit("Algorithm %s not found in results." % algorithms[0])

        for a in algorithms:
            if a in res:
                val = next(iter(res[a].values()))
                print("%d\t" % int(float(val[0]) / val[1]), end='')
                if resultCount != val[2]:
                    printErrorAndExit("Different result counts for the same parameter-value found!")
            else:
                print("nan\t", end='')

        print("%d" % resultCount)

if __name__ == '__main__':
    main()
