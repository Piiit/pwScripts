#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 18 11:02:01 2017

@author: pemoser
"""

import matplotlib.pyplot as plt
import sys
import os
import math
from operator import itemgetter

BUCKETCOUNT = 100

def main():

    if len(sys.argv) != 3:
        print("USAGE: %s input prefix" % os.path.basename(sys.argv[0]))
        print("       input     filename of a temporal data file (TSV)")
        print("       prefix    filename prefix for results, i.e., prefix-TYPE.tsv")
        print()
        print("   TYPE is on of the following:")
        print("       start     start points histogram output")
        print("       duration  duration histogram output")
        print("       overlap   concurrent overlapping tuples histogram output")
        sys.exit(1)

    inputf = sys.argv[1]
    prefix = sys.argv[2]
    startf = prefix + "-start.csv"
    durationf = prefix + "-duration.csv"
    overlapf = prefix + "-overlap.csv"

    statistics = {
        'lengths'   : [],
        'starts'    : [],
        'ends'      : []
    }
    with open(inputf, 'r') as file:
        for rawline in file:
            line = [int(x) for x in rawline.split("\t")]
            statistics['starts'].append(line[0])
            statistics['ends'].append(line[1])
            statistics['lengths'].append(line[1] - line[0])
            if len(line) > 2:
                for i, d in enumerate(line[2:]):
                    statistics['data%02d' % i].append(d)

    domainstart = min(statistics['starts'])
    domainend = max(statistics['ends'])
    domainlength = domainend - domainstart
    bucketlength = math.ceil(domainlength / BUCKETCOUNT)

    # Find concurrently open intervals
    START = 0
    END = 1
    epindex = [(x, START) for x in statistics['starts']]
    epindex += [(x, END) for x in statistics['ends']]
    epindex = sorted(epindex, key=itemgetter(0,1))
    openints = [0] * BUCKETCOUNT
    bucket = 1
    overlaps = 0
    maxoverlaps = 0
    for (time, type) in epindex:
        while time > domainstart + bucket * bucketlength:
            openints[bucket - 1] = maxoverlaps
            maxoverlaps = overlaps
            bucket += 1

        if type == START:
            overlaps += 1
            if maxoverlaps < overlaps:
                maxoverlaps = overlaps
        else:
            overlaps -= 1
    openints[BUCKETCOUNT - 1] = maxoverlaps
    printHistogram(range(1, BUCKETCOUNT + 1), openints, overlapf)

    # Create start-points histogram in percentage
    startmaxp = domainend / 100
    statistics['starts'] = [x / startmaxp for x in statistics['starts']]
    freq, bins, _ = plt.hist(statistics['starts'], BUCKETCOUNT, lw=0, label='start points')
    freq = [x / len(freq) / 100 for x in freq]
    print("START POINTS -- " + statsToString(statistics['starts']))
    printHistogram(bins, freq, startf)

    # Create duration histogram in percentage
    statistics['lengths'] = [x / domainlength for x in statistics['lengths']]
    freq, bins, _ = plt.hist(statistics['lengths'], BUCKETCOUNT, lw=0, label='duration')#, range=[10**7-1,10**7])
#    print(freq, bins)
#    bins = [x / len(bins) / 100 for x in bins]
#    print(freq, bins)
    print("DURATION -- " + statsToString(statistics['lengths']))
    printHistogram(bins, freq, durationf)

    print("READY.")

    sys.exit(0)



def avg(array):
    return sum(array) / len(array)

def statsToString(array):
    return "MIN=%d, MAX=%d, AVG=%.3f, LEN=%d" % (
        min(array),
        max(array),
        avg(array),
        len(array))

def printHistogram(bins, freq, filename):
    with open(filename, 'w') as file:
        file.write("x\ty\n")
        for i in range(0,len(freq)):
            file.write("%.3f\t%.3f\n" % (bins[i], freq[i]))

if __name__ == '__main__':
    main()
