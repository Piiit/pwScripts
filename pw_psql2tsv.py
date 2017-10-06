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
        print("USAGE: res2tsv.py <prefix> list-of-files")
        print()
        print("  Extract from a list of files containing experiments (EXPLAIN ANALYZE) conducted with")
        print("  PostgreSQL the execution time. Remove <prefix> from each filename, and choose the remaining")
        print("  text as varying parameter name. The next token until an underscore (_) is the varying")
        print("  parameter value, and the remainder is the algorithm name used as column name.")
        print("  The full filename pattern looks like this: <prefix><parameter-name><parameter-value>_<algorithm>")
        print()
        print("  The result is then a table with the prefix as first column name, and all algorithms as follwing")
        print("  column names. The cells contain the average of all execution times within a single file.")
        print()
        sys.exit(0)

    # Collect data
    results = {}
    algorithms = []
    parameters = []
    prefix = sys.argv[1]
    for arg in sys.argv[2:]:
        sum = 0
        count = 0
        with open(arg, 'r') as f:
            try:
                for line in f:
                    if re.search("xecution", line):
                        sum += float(line.split()[2])
                        count += 1
            except:
                continue
        filename = os.path.basename(arg)
        m = re.match(r"%s([a-zA-Z0-9]+)_(.*)" % prefix, filename)
        if m:
            g = m.groups()
            varying = g[0]
            algo = g[1]
            if not algo in algorithms:
                algorithms.append(algo)
            if not varying in parameters:
                parameters.append(varying)

            if varying in results:
                results[varying][algo] = round(sum/count)
            else:
                results[varying] = {algo: round(sum/count)}

        headerVar = []
        var = re.split(r"([a-zA-Z]+)([0-9]+)", varying)
        for i in range(0, len(var)-1, 3):
            headerVar.append(var[i+1])

    # Print header
    print("\t".join(headerVar), end='')
    for a in algorithms:
        print("\t%s" % a, end='')
    print()

    # Print data lines (first field = varying parameter)
    for parameter in parameters:
        var = re.split(r"([a-zA-Z]+)([0-9]+)", parameter)
        for i in range(0, len(var)-1, 3):
            print("%d\t" % int(var[i+2]), end='')
        res = results[parameter]
        for a in algorithms:
            print("%d\t" % res[a], end='')
        print()

if __name__ == '__main__':
    main()
