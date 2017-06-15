#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Ignoring warnings about "Used * or ** magic (star-args)"
# pylint: disable=W0142

# Author: Peter Moser <pitiz29a@gmail.com)

r"""## LaTex table and image generator for timelines and temporal tables

Generate LaTex and TIKZ files from PostgreSQL's `psql` command output

![Screenshot of Latex document](https://github.com/Piiit/pwScripts/blob/master/res/pgsql2latex-screen01.jpg)


Download
--------
 * [pw_pgsql2latex.py](https://github.com/Piiit/pwScripts/blob/master/pw_pgsql2latex.py)


Usage
-----
(automatically printed from `argparse` module)

Introduction
------------
Reads an PostgreSQL (`psql --echo-all`, see man-page of psql for further
details) output, and creates a standalone TIKZ tex-figure, or combined
table/figure LaTex file to be used with `\input{filename}`. To configure each
output table or timeline a SQL comment starting with `TIKZ:` must be provided.
In addition this script needs the following prerequisites for the input:
  1. There must be at least 2 columns for VALID TIME for each table
  2. Each relation must have a TIKZ config line as SQL comment (see below)
  3. A single timeline can be defined with `TIKZ: timeline, from, to, desc`
     This is optional.

NB: Since version 0.8 it also supports TSV files, instead of PostgreSQL output.

We do not use some Python PostgreSQL libs here, because TEMPORAL OPERATORS are
not supported yet. Another reason is that we can create output files manually,
if we do not have a (TEMPORAL) POSTGRESQL instance running.


TIKZ-comment syntax
-------------------
First argument after `TIKZ:` is the type of drawing. The following lines
describe which types are supported:
  1. `-- TIKZ: relation[-table], [abbrev], start column, [end column], [ypos],
     description` <br>
     If you put `relation-table` as drawing-type, a table and a diagram will be
     printed.
     The abbreviation is optional (it is used for tuple names). If you want to
     suppress it, do not forget to put the comma separator anyway.
     If `end column` is empty, the parser assumes a PostgreSQL rangetype at
     `start column`, or a point representation if the rangetype parsing failes.
     The optional `ypos` defines the y-position of each tuple inside the figure.
  2. `-- TIKZ: timeline, from, to, step, description`
  3. `-- TIKZ: config, key, value` <br>
     The key and value of this line is used for the combined table/figure
     picture, or for the standalone tikzpicture file. You can configure the
     label and caption of figures for instance.

```
     Possible configurations by key/value:
     key                value
     ------------------------------------------------------------------------
     label              TEX label \label
     caption            TEX figure caption
     subfigure-left     left subfigure column's width
     subfigure-right    right subfigure column's width. Both subfigure widths
                        should sum up to 0.9 (0.1 space in between is fixed).
                        However, I keep it configurable in order to not be too
                        restrictive.
     tablecaption       subfigure's table caption
     tablelabel         subfigure's table label
     graphcaption       subfigure's graph caption
     graphlabel         subfigure's graph label
     xscale             scale of the tikzpicture (on the x-axis)
     yscale             scale of the tikzpicture (on the y-axis)
```

Example
-------
If you run the following code as a file with `psql -a -d DBNAME -f FILENAME`...
```
   -- TIKZ: relation, r, ts, te,, Input relation r
   TABLE r;
   -- TIKZ: relation, s, ts, te,, Input relation s
   SELECT * FROM s WHERE a='B';
   -- TIKZ: timeline, 0, 10, 1, time
   -- TIKZ: config, figure01, This is a caption (latex-syntax possible)
```
...then you get the following output, which serves as input to
 **pw_pgsql2latex.py**.
```
   -- TIKZ: relation, r, ts, te,, Input relation r
   TABLE r;
    a | ts | te
   ---+----+----
    B |  1 |  7
    B |  3 |  9
    G |  8 | 10

   -- TIKZ: relation, s, ts, te,, Input relation s
   SELECT * FROM s WHERE a='B';
    a | ts | te
   ---+----+----
    B |  2 |  5
    B |  3 |  4
    B |  7 |  9

   -- TIKZ: timeline, 0, 10, 1, time

   -- You can refer to this figure with \ref{fig:input001}
   -- TIKZ: config, label, input001
   -- TIKZ: config, caption, Input relations \textbf{r} and \textbf{s}
```

You can also use TSV for relations, instead of PostgreSQL outputs. If you want to do
so, add `-- TIKZ: TSV` as very first line of your input file. The first non-comment
line will be interpreted as beginning of a table, that is, the header followed by
some lines representing tuples. NB: Separate each header or tuple with tabulators.

The full piped command is then: `psql -a -d DBNAME -f FILENAME |
pgsql2latex.py -o OUTPUTFILE -`.
To use the `OUTPUTFILE` inside a LaTex document, just add a input-command
 `\input{OUTPUTFILE}`.

Changelog
---------
  * 0.9thesis
      - xscale/yscale for tikz pictures
      - point representation (cross) if only one scalar value is given as time
      - steps on the time line can now be configured
      - Fast hacks for thesis: to adjust ypos of tuples given by an input attribute
  * 0.8
      - Tab-separated-values (TSV) support
      - Support for different input types (currently only Postgres and TSV)
      - Periods instead of single attributes as time point start/end (boundary
        types ignored, i.e., always closed intervals used)
  * 0.7
      - Table above graphs representation with -A or --All
  * 0.6
      - Port to Python 3
      - Inclusive intervals as option
  * 0.5
      - TIKZ-config lines are now key/value pairs
      - Additional config parameters to tweak the TEX output, i.e., subfigure
        column widths
  * 0.4.1
      - BUGFIX: captions are no longer truncated if a comma is found
  * 0.4
      - config line added to provide "label" and "caption" to LaTex
      - command line arguments (see usage output for details; i.e., `--help`)
  * 0.3
      - Parser becomes a generator (i.e., we use yield)
      - Parser simplified, returns only tokens to reuse it later for other
        projects
      - String formatting unified
  * 0.2
      - Reads configs from SQL comments with prefix `-- TIKZ`
      - Checks if TIKZ configs and data input matches
      - Different string formatting techniques tested (just for fun!)
      - Skips SQL commands
      - pylint errors and warnings fixed (most)
  * 0.1
      - Creates a standalone tikz picture from a PostgreSQL output
      - Skips comments and empty lines
      - Restriction: Hard-coded configuration


"""

import re
import os
import stat
import sys
import argparse
import io

__version__ = "0.9thesis"

def main():
    """Main, nothing more to say :-)"""

    parser = argparse.ArgumentParser(conflict_handler='resolve')

    parser.add_argument(
        '--manual',
        action='store_true',
        help='Print a short manual showing the module docstring of ' +
             os.path.basename(__file__))

    parser.add_argument(
        'FILE',
        default='-',
        type=argparse.FileType('r'),
        help='Input files taken from the "psql --echo-all" output\n'
             'Use a dash, i.e. -, if you want to use STDIN.')

    parser.add_argument(
        '-o',
        '--output',
        metavar='FILE',
        help='Put output into FILE; default is STDOUT')

    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        '-a',
        '--all',
        action='store_const',
        dest='output_type',
        const='all',
        help='OUTPUT TYPE: Output the LaTex table and the TIKZ figure '
             'side-by-side. This is the default.')

    group.add_argument(
        '-A',
        '--All',
        action='store_const',
        dest='output_type',
        const='All',
        help='OUTPUT TYPE: Output the LaTex table above the TIKZ figure.')

    group.add_argument(
        '-t',
        '--table-only',
        action='store_const',
        dest='output_type',
        const='table-only',
        help='OUTPUT TYPE: Output the LaTex table only.')

    group.add_argument(
        '-f',
        '--figure-only',
        action='store_const',
        dest='output_type',
        const='figure-only',
        help='OUTPUT TYPE: Output the TIKZ figure only.')

    group.add_argument(
        '-F',
        '--figure-standalone',
        action='store_const',
        dest='output_type',
        const='figure-standalone',
        help='OUTPUT TYPE: Output the TIKZ figure as a standalone LaTex file.')

    parser.set_defaults(output_type='all')

    # We must capture this option before we parse the arguments, because the
    # last positional argument FILE is mandatory. Hence, the parser would exit
    # with an error (There is no meaningful exception to catch, except for
    # SystemExit).
    if len(sys.argv) == 2 and sys.argv[1] == '--manual':

        docparts = __doc__.split("Usage\n-----\n(automatically printed from `argparse` module)\n", 1)

        # Print title and section before "usage"
        print (docparts[0])

        # Print usage information
        sys.stdout.write("Usage\n-----\n```\n")
        parser.print_help()
        print ("```")

        # Print the rest
        #print "\n".join(__doc__.split('\n', 1)[1:])
        print (docparts[1])

        sys.exit(0)

    # Now parse regular command line arguments
    args = parser.parse_args()

    # Stdin file stats to see if it is a pipe or redirection...
    mode = os.fstat(sys.stdin.fileno()).st_mode

    # Input files are explicitely given as a filename list
    #if type(args.FILE) is file:
    if isinstance(args.FILE, io.IOBase):
        input_file = args.FILE
        input_text = input_file.readlines()

    # We have a piped or redirected STDIN at disposal...
    elif stat.S_ISFIFO(mode) or stat.S_ISREG(mode):
        print ("READING FROM STDIN\n")
        input_text = sys.stdin.readlines()

    # No stdin, no input files... shutdown!
    else:
        parser.error("No input files, nor stdin given (i.e., a dash).")

    try:
        parse_result = pgsql_parser(input_text)

        figure = ""
        table = ""
        cfg = {}

        if args.output_type in ['all', 'All', 'table-only']:
            table_type = 1
            if args.output_type == 'all':
                table_type = 2
            if args.output_type == 'All':
                table_type = 3

            for line in parse_result:
                if line['type'] == 'relation-table':
                    if table == "":
                        table = format_latex_table(line, "", table_type)
                    else:
                        table += "    \hspace{2cm}" + format_latex_table(line, "", table_type)
                if line['type'] == 'config':
                    cfg[line['key']] = line['value']

        # If we print the whole figure/table combination, we need a "label" and
        # "caption" below the two sub-figures.
        if args.output_type in ['all', 'All']:
            if not 'label' in cfg:
                raise_error_cfgline(
                    'label',
                    "We do not know which 'label' to use for figures.")

            if not 'caption' in cfg:
                raise_error_cfgline(
                    'caption',
                    "We do not know which 'caption' to use for figures.")

        if args.output_type in ['all', 'All', 'figure-standalone', 'figure-only']:
            figure = format_tikz_figure(parse_result, cfg)

        # TODO Create text first in memory, and write it at last. Otherwise, we
        # could get half-made output files, when an error occurs
        outfile = sys.stdout
        if args.output != None:
            if os.path.isfile(args.output):
                raise_error("File '%s' already exists! Exiting..." % args.output)
            outfile = open(args.output, 'w')

        outfile.write(format_latex_header("".join(input_text)))

        if args.output_type == 'all':

            # Subfigures have a left and right column with a certain width
            # If it is not configured explicitely, we will take these defaults:
            subfigure_left = list_get(cfg, 'subfigure-left', 0.27)
            subfigure_right = list_get(cfg, 'subfigure-right', 0.63)

            outfile.write(format_latex_figure_and_table(table,
                                                        figure,
                                                        cfg['caption'],
                                                        cfg['label'],
                                                        subfigure_left,
                                                        subfigure_right))
        elif args.output_type == 'All':
            outfile.write(format_latex_figure_and_table_top(table, figure,
                                                            cfg['caption'],
                                                            cfg['label'],
                                                            cfg['tablecaption'],
                                                            cfg['tablelabel'],
                                                            cfg['graphcaption'],
                                                            cfg['graphlabel']))
        elif args.output_type == 'table-only':
            outfile.write(table)
        elif args.output_type == 'figure-only':
            outfile.write(figure)
        elif args.output_type == 'figure-standalone':
            outfile.write(format_latex_standalone(figure))
        else:
            raise_error("Unknown output type specified")

    except ValueError as valerr:
        print ("\n".join(valerr.args) + "\n")
        sys.exit(3)

def format_tikz_desc(pos, desc):
    """Prints the description of each found table on the left-hand-side of the
    tuple time lines in a standalone tikz figure"""
    return TEMPLATE_TIKZ_DESC.format(pos=pos,
                                     desc=desc)


def format_tikz_tupleline(tup, cfg, tuple_count, count):
    """Prints the tuple time lines in a standalone tikz figure"""

    template = TEMPLATE_TIKZ_TUPLE

    relation = cfg['relation']

    if relation.teid != -1:
        valid_time_ts = int(relation.getTupleTS(tup))
        valid_time_te = int(relation.getTupleTE(tup))
    else:
        # Parse range types, we ignore boundary types for now...
        match = re.search(r'.?(\d+),(\d+).?', relation.getTupleTS(tup))
        if match:
            valid_time_ts = int(match.group(1))
            valid_time_te = int(match.group(2))
        else:
            # Single point detected: Generate point representation
            valid_time_ts = int(relation.getTupleTS(tup))
            valid_time_te = valid_time_ts + 1
            template = TEMPLATE_TIKZ_POINT
#            print(valid_time_ts)

    # Concatenate all non-temporal (non-meta) attributes as description above the line
    attribs = ""
    for key, value in enumerate(relation.getTupleB(tup)):
        attribs += r"\mathrm{%s}," % value

    if len(attribs) == 0:
        out = template + "{{${name}_{{{id}}}$}};\n"
    else:
        if relation.name == "":
            out = template + "{{$({attribs})$}};\n"
        else:
            out = template + "{{${name}_{{{id}}}=({attribs})$}};\n"

    if relation.ypos != -1:
        count = float(relation.getTupleYPOS(tup))

    return out.format(name=relation.name,
                      id=tuple_count,
                      ts=valid_time_ts,
                      te=valid_time_te,
                      count=count,
                      posx=float(valid_time_ts+valid_time_te) / 2,
                      posy=count - 0.2,
                      attribs=attribs.rstrip(','))

def format_tikz_timeline(cfg):
    """Prints a timeline in a standalone tikz figure"""
#    pos_numbers = 0
#    if 'inclusive' in cfg and cfg['inclusive']:
#        pos_numbers = 5
    pos_numbers = 5

    if 'step' in cfg and cfg['step']:
        return TEMPLATE_TIKZ_TIMELINE2.format(start=int(cfg['from']),
                                              end=int(cfg['to']),
                                              step=int(cfg['step']),
                                              desc=cfg['desc'],
                                              posno=pos_numbers)


    return TEMPLATE_TIKZ_TIMELINE.format(start=int(cfg['from']),
                                         end=int(cfg['to']),
                                         desc=cfg['desc'],
                                         posno=pos_numbers)

def raise_error(msg, hint=""):
    """Print an error message and a hint to solve the issue. The text is
    automatically indented behind "ERROR: " and "HINT : " strings."""
    if hint != "":
        hint = "HINT : " + hint
    raise ValueError("ERROR: " + os.path.basename(__file__) + ": " + msg, hint)

def raise_error_cfgline(key, msg):
    """Print an error message like raise_error, but for TIKZ: config, ...
    lines. """
    raise_error(
        "No config line with key '" + key + "' found!\n" + msg,
        "Define a configuration string of type 'config' and key '" + key + "'\n"
        "For example:\n"
        "-- TIKZ: config, " + key + ", value")

def pgsql_tokenizer(lines):
    """We parse the input lines with a simple state machine, and generate a
    token (i.e., 2-element list, with key and value) that we give back at each
    iteration"""

    input_type = INPUT_TYPE_POSTGRES
    value_sep = '|'

    state = STATE_FIRSTLINE
    for line in lines:

        line = line.lstrip()

        if state == STATE_FIRSTLINE:
            state = STATE_OUTSIDE
            match = re.search(r'--\s*TIKZ: TSV', line)
            if match:
                input_type = INPUT_TYPE_TSV
                value_sep = '\t'
                continue

        # Skip empty lines
        # This ends a table parsing, and returns to the STATE_OUTSIDE state
        if line.rstrip() == "":
            state = STATE_OUTSIDE
            continue

        # Skip SQL comments (except if they start with the keyword TIKZ)
        if line.startswith('--'):

            # We have found a SQL config line
            if state == STATE_OUTSIDE:
                yield ['COMMENT', line.lstrip("-- ").rstrip()]

            # If we have seen an header line already, this is a table
            # horizontal line which starts tuple lines, i.e., ----+----+-----
            if state == STATE_HEADER:
                state = STATE_TUPLES
            continue

        # Not skipped and currently in STATE_OUTSIDE state, hence it could be a
        # header line, or SQL command. Since we must have at least two temporal
        # columns, we can search for columns delimiters, i.e., |.
        if state == STATE_OUTSIDE:

            # PostgreSQL output: Search for table headers first, if not found, skip it...
            # TSV output: First line (not a comment), must be a table header...
            if input_type == INPUT_TYPE_POSTGRES:
                if None == re.search(r'\s*[^\|]+?\s*\|\s*[^\|]+?', line):
                    yield ['COMMAND', line.rstrip()]
                    continue

            state = STATE_HEADER
            headers = []
            for head in line.split(value_sep):
                headers.append(head.strip())

            yield ['HEADER', headers]
            if input_type == INPUT_TYPE_TSV:
                state = STATE_TUPLES
                continue

        # Not skipped and currently in a tuple state, therefore the next data
        # line must be another tuple, or tuple count, i.e., (3 rows)
        if state == STATE_TUPLES:

            # PostgreSQL: We skip tuple count rows at the end of each table. This ends a table block.
            match = re.search(r'\((\d+?)\s\w*\)', line)
            if match:
                state = STATE_OUTSIDE
                yield ['TUPLECOUNT', match.group(1)]
                continue

            values = []
            for value in line.split(value_sep):
                values.append(value.strip())

            yield ['TUPLE', values]

def pgsql_parser(text):
    """We parse the input lines with a simple state machine"""

    configs = []
    tables = []
    table_count = 0
    configs_count_relation = 0
    configs_count_timeline = 0

    for token in pgsql_tokenizer(text):

        # First, search for a TIKZ comment line, which looks as follows:
        # -TIKZ: name, config-list-comma-separated
        # Depending on "name" we get a different number of parameters in
        # "config-list-comma-separated". The last entry therein is either
        # a description or a caption, which can contain commas which will
        # be kept.
        if token[0] == 'COMMENT':
            match = re.search(r'TIKZ:\s*([a-z\-]+?)\s*,\s*(.*)+?', token[1])
            if match:
                comment_type = match.group(1)
                comment_body = match.group(2)

                if comment_type == 'config':
                    listitems = [comment_type] + re.split(r'\s*,\s*', comment_body, 1)
                    configs.append(dict(zip(['type', 'key', 'value'], listitems)))

                elif comment_type in ['relation', 'relation-table']:
                    listitems = [comment_type] + re.split(r'\s*,\s*', comment_body, 4)
                    if len(listitems) != 6:
                        raise_error("Not enough parameters for TIKZ relation or TIKZ relation-table given.\n" +
                                    "For example:\n--TIKZ: relation, R, ts, te, ypos, Description string\n" +
                                    "Instead the following was given: --" + token[1])

                    if configs_count_relation < table_count:
                        relation = tables[table_count]
                    else:
                        relation = Relation()
                        tables.append(relation)
                        configs_count_relation += 1

                    relation.name = listitems[1]
                    relation.tsname = listitems[2]
                    relation.tename = listitems[3]
                    relation.yposname = listitems[4]
                    relation.desc = listitems[5]

                    configs.append({'type' : listitems[0], 'relation' : relation})

                elif comment_type == 'timeline':
                    if configs_count_timeline == 1:
                        raise_error(
                            "More than one TIKZ timeline string found",
                            "Define a single configuration string for the " +
                            "timeline.\n For example:\n" +
                            "-- TIKZ: timeline, from, to, step, time line " +
                            "description")
                    else:
                        listitems = [comment_type] + re.split(r'\s*,\s*', comment_body, 3)
                        if len(listitems) != 5:
                            raise_error(
                                "Wrong TIKZ timeline string found: '%s'" % token[1],
                                "Define a correct configuration string for the " +
                                "timeline.\n For example: " +
                                "-- TIKZ: timeline, from, to, step, time line " +
                                "description")
                        configs_count_timeline += 1
                        configs.append(dict(zip(['type', 'from', 'to', 'step', 'desc'], listitems)))
        elif token[0] == 'HEADER':
            if configs_count_relation > table_count:
                relation = tables[table_count]
            else:
                relation = Relation()
                tables.append(relation)
                table_count += 1
            relation.setSchema(token[1])

        elif token[0] == 'TUPLE':
            relation = tables[table_count]
            relation.addTuple(token[1])

    if configs_count_relation == 0:
        raise_error(
            "No tables found! Is this a valid input file?")

    # The amount of relation config strings and table outputs must match!
    if configs_count_relation < len(tables):
        raise_error(
            "We do not have enough TIKZ relation config strings",
            "Define a configuration string for each table.\n" +
            "For example:\n" +
            "-- TIKZ: relation, table_name, ts, te, relation description")

    if configs_count_relation > len(tables):
        raise_error(
            "We do not have enough table outputs compared to the amount of " +
            "TIKZ relation config strings",
            "Either delete a configuration string for a table, or provide\n" +
            "an additional SQL-command to produce a table output.\n" +
            "For example:\n" +
            "-- TIKZ: relation, table_name, ts, te, relation description")

    # Add tables (with header and tuples) to the config dictionary
#    table_count = 0
#    for cfg in configs:
#        if cfg['type'] in ['relation', 'relation-table']:
#            relation = cfg['table'] = tables[table_count]
#            table_count += 1
#
#            relation.setMetaData(cfg['ts'], cfg['te'], cfg['ypos'])

    return configs

def format_tikz_figure(parse_result, cfg):
    """
    Draw a TIKZ figure with an optional timeline, tuple-lines for each tuple in
    all given tables, and description on the right-hand-side of each table.
    """

    # Count tuples above the timeline. We do this, because we need to count
    # backwards while creating lines above the timeline. However, it is not
    # necessary below, because there we count starting from 1, s.t., the
    # index 1 is always close to the timeline in the middle.
    count_above = 0
    for line in parse_result:
        if line['type'] == 'timeline':
            break

        if 'relation' in line:
            relation = line['relation']
            if relation.ypos != -1:
                m = 1.0
                ypos = relation.ypos
                for v in relation.values:
                    if m < float(v[ypos]):
                        m = float(v[ypos])
                count_above += m + 1
            else:
                count_above += relation.getLength() - 1

    posy = count_above
    out = ""

    xscale = list_get(cfg, 'xscale', 0.65)
    yscale = list_get(cfg, 'yscale', 0.4)

    for line in parse_result:

        # Only these configuration lines are allowed, skip all others...
        if line['type'] not in ['timeline', 'relation', 'relation-table']:
            continue

        # Print the timeline
        if line['type'] == 'timeline':
            out += format_tikz_timeline(line)
            posy = -2
            continue

        relation = line['relation']

        # Print description on the left-hand-side of each relation
        if relation.desc.strip() != "":
            out += format_tikz_desc(posy - (relation.getLength() - 1) / 2, relation.desc)


        # Print tuples of each table as lines from ts to te. The description of
        # each tuple is a list of explicit attributes (i.e., non-temporal
        # columns), and optionally a tuple identifier "relation_tuplecount"
        for tuple_count, tup in enumerate(relation.values, 1):
            out += format_tikz_tupleline(tup, line, tuple_count, posy)
            posy -= 1

    return TEMPLATE_TIKZ_PICTURE.format(content=out, xscale=xscale, yscale=yscale)

def format_latex_header(raw_data):
    """Prints a TEX comment header including a version, this app's name, and
    the input text."""
    return TEMPLATE_HEADER.format(
                appname=os.path.basename(__file__),
                appversion=__version__,
                input="".join("%% %s\n" % x
                              for x in raw_data.strip().split("\n")))

def format_latex_standalone(figure):
    """Creates a TIKZ standalone latex document"""
    return TEMPLATE_TIKZ_DOC.format(tikzpicture=figure)


def format_latex_table(line, label, table_type=1):
    """Print a single table from a relation-config-line"""

    if line['type'] not in ['relation', 'relation-table']:
        raise_error("Latex Print Table: Provided config-line has wrong " \
                        "type '%s' (type 'relation' expected)" % line['type'])

    relation = line['relation']

    # We skip the first element inside a table. It is the header.
    header = relation.getSchemaTemporal()
    tuples = relation.getTuplesTB()

    # Concatenate all non-temporal attributes as description above the line
    attribs = r" & ".join(header)
    rows = ""
    for row_count, row in enumerate(tuples, 1):
        rows += " " * 12 + "$%s_{%d}$ & %s \\\\\n" % (relation.name,
                                         row_count,
                                         r" & ".join(row))

    if table_type == 1:
        return TEMPLATE_LATEX_TABLE.format(
                caption=relation.desc,
                label=label,
                length=len(header) + 1,
                header_cfg="c" * len(header),
                header=attribs.rstrip(" &"),
                rows=rows.rstrip("\n"))

    if table_type == 2:
        return TEMPLATE_LATEX_TABLE2.format(
                    header_cfg="c" * len(header),
                    header=attribs.rstrip(" &"),
                    rows=rows.rstrip("\n"),
                    relation=relation.name)

    return TEMPLATE_LATEX_TABLETOP.format(
                header_cfg="c" * len(header),
                header=attribs.rstrip(" &"),
                rows=rows.rstrip("\n"),
                relation=relation.name)



def format_latex_figure_and_table(table_str, tikz_str, caption, label, subfigure_left, subfigure_right):
    """Prints a figure and a table side-by-side as sub-figures"""
    return TEMPLATE_LATEX_TIKZTABLE.format(table=table_str,
                                           tikzpicture=tikz_str,
                                           caption=caption,
                                           label=label,
                                           subfigureleft=subfigure_left,
                                           subfigureright=subfigure_right)

def format_latex_figure_and_table_top(table_str, tikz_str, caption, label, tablecaption, tablelabel, graphcaption, graphlabel):
    """Prints a figure and a table side-by-side as sub-figures"""
    return TEMPLATE_LATEX_TIKZTABLETOP.format(table=table_str,
                                           tikzpicture=tikz_str,
                                           caption=caption,
                                           label=label,
                                           tablecaption=tablecaption,
                                           tablelabel=tablelabel,
                                           graphcaption=graphcaption,
                                           graphlabel=graphlabel)

def list_get (l, idx, default):
    try:
        return l[idx]
    except:
        return default

# STATES of the tokenizer, which is implemented as a state machine...
STATE_FIRSTLINE = 0
STATE_OUTSIDE   = 1      # We have not found a table yet
STATE_HEADER    = 2      # We have found a table STATE_HEADER (attribute names)
STATE_TUPLES    = 3      # We have already parsed the table header, and are
                         # reading in tuples now

INPUT_TYPE_POSTGRES = 0
INPUT_TYPE_TSV      = 1

TEMPLATE_HEADER = r"""% This file has been automatically generated by...
%
% {appname} v{appversion} written by Peter Moser <pitiz29a@gmail.com>
% Source code can be found under: https://github.com/Piiit/pwScripts
%
% From input:
% _______________________________________________________________INPUT-START__
{input}% _______________________________________________________________INPUT-END____
"""

TEMPLATE_TIKZ_DOC = r"""
\documentclass{{standalone}}
\usepackage{{tikz}}
\usetikzlibrary{{
	arrows,
	decorations,
	positioning,
	shapes,
	fit,
	calc,
	matrix
}}
\begin{{document}}
    {tikzpicture}
\end{{document}}
"""

TEMPLATE_TIKZ_PICTURE = r"""
    \begin{{tikzpicture}}[xscale={xscale},yscale={yscale}]
    {content}
    \end{{tikzpicture}}
"""

# Prints the description of each found table on the left-hand-side of the
# tuple time lines in a standalone tikz figure
TEMPLATE_TIKZ_DESC = r"""
        % Description
        \node[align=left, font=\scriptsize] at (0,{pos}) {{{desc}}};
"""

# Regular timeline representation with a number on each step
TEMPLATE_TIKZ_TIMELINE = r"""
        % Time line
        \draw[->, line width = 0.9] ({start},0)--({end}+1,0);
        \foreach \t in {{{start},...,{end}}}
        {{
            \draw ($(\t cm,-1mm)+(0cm,0)$)--($(\t cm,1mm)+(0cm,0)$);
            \draw ($(\t {posno}mm,0.5mm)$) node[below,font=\scriptsize \bfseries]{{\t}};
        }}
        \draw ($({end}+1,0)+(3mm,-1mm)$) node[below,font=\bfseries]{{$\mathrm{{{desc}}}$}};
"""

# Time line with number at each {step}.
TEMPLATE_TIKZ_TIMELINE2 = r"""
        % Time line
        \draw[->, line width = 0.9] ({start},0)--({end}+1,0);
        \foreach \t in {{{start},...,{end}}}
        {{
            \draw ($(\t cm,-1mm)+(0cm,0)$)--($(\t cm,1mm)+(0cm,0)$);
            \pgfmathparse{{Mod(\t, {step}) == 0 ? 1 : 0}}
            \ifnum\pgfmathresult>0
            	  \draw ($(\t {posno}mm,0.5mm)$) node[below,font=\scriptsize \bfseries]{{\t}};
            \fi
        }}
        \draw ($({end}+1,0)+(3mm,-1mm)$) node[below,font=\bfseries]{{$\mathrm{{{desc}}}$}};
"""

TEMPLATE_TIKZ_TUPLE = r"""
        % Tuple {name}_{id}
        \draw[-] ({ts},{count})--({te},{count});
        \draw[-] ({posx},{posy}) node[above,font=\tiny]"""

TEMPLATE_TIKZ_POINT = r"""
        % Point {name}_{id}
        \draw ({ts}+0.5,{count}) node[cross] {{}};
        \draw[-] ({posx},{posy}) node[above,font=\tiny]"""


TEMPLATE_LATEX_TABLE = r"""
    \begin{{table}}
        \renewcommand{{\arraystretch}}{{1.3}}
        \caption{{{caption}}}
        \label{{tab:{label}}}
        \centering
        \begin{{tabular}}{{c|{header_cfg}|}}
            \cline{{2-{length}}}
            ~ & {header} \\
            \cline{{2-{length}}}
{rows}
            \cline{{2-{length}}}
        \end{{tabular}}
    \end{{table}}
"""

TEMPLATE_LATEX_TABLE2 = r"""
    \begin{{tabular}}{{|c|{header_cfg}|}}
        \hline
        \bfseries {relation} & {header} \\
        \hline
{rows}
        \hline
    \end{{tabular}}
"""

TEMPLATE_LATEX_TIKZTABLE = r"""
\begin{{figure}}[!ht]
    \centering
    \hfill
    \begin{{subfigure}}[c]{{{subfigureleft}\textwidth}}
{table}
    \end{{subfigure}}
    \hspace{{10pt}}
    \begin{{subfigure}}[c]{{{subfigureright}\textwidth}}
{tikzpicture}
    \end{{subfigure}}
    \caption{{{caption}}}
    \label{{fig:{label}}}
\end{{figure}}"""

TEMPLATE_LATEX_TABLETOP = r"""
    \begin{{tabular}}[t]{{|c|{header_cfg}|}}
        \hline
        \bfseries {relation} & {header} \\
        \hline
{rows}
        \hline
    \end{{tabular}}
"""

TEMPLATE_LATEX_TIKZTABLETOP = r"""
\begin{{figure}}[!ht]
    \centering
    \begin{{subfigure}}{{\textwidth}}
    \centering
{table}
    \caption{{{tablecaption}}}
    \label{{sfig:{tablelabel}}}
    \end{{subfigure}}

    \begin{{subfigure}}{{\textwidth}}
    \centering
{tikzpicture}
    \caption{{{graphcaption}}}
    \label{{sfig:{graphlabel}}}
    \end{{subfigure}}
    \caption{{{caption}}}
    \label{{fig:{label}}}
\end{{figure}}
"""

RELATION_TYPE_INTERVAL = 0
RELATION_TYPE_POINT    = 1

class Relation:
    def __init__(self):
        self.schema = []
        self.values = []
        self.tsid = -1
        self.teid = -1
        self.ypos = -1
        self.tsname = ""
        self.tename = ""
        self.yposname = ""
        self.name = ""
        self.relType = RELATION_TYPE_INTERVAL

    def setSchema(self, schema):
        self.schema = schema

    def addTuple(self, tup):
        if len(tup) == len(self.schema):
            self.values.append(tup)
        else:
            raise_error("Too many tuple columns for the actual schema: " + self.schema)

    def getTupleTS(self, tup):
        return tup[self.tsid]

    def getTupleTE(self, tup):
        return tup[self.teid]

    def getTupleYPOS(self, tup):
        return tup[self.ypos]

    def getTupleB(self, tup):
        result = []
        for i, a in enumerate(tup):
            if i == self.tsid or i == self.teid or i == self.ypos:
                continue
            result.append(a)
        return result

    def getTupleTB(self, tup):
        result = []
        for i, a in enumerate(tup):
            if i == self.ypos:
                continue
            result.append(a)
        return result

    def getTuplesTB(self):
        for tup in self.values:
            yield self.getTupleTB(tup)

    def getSchemaTemporal(self):
        result = []
        for i, a in enumerate(self.schema):
            if i == self.ypos:
                continue
            result.append(a)
        return result

    def getLength(self):
        return len(self.values)

    def getDefault(self, name, default):
        try:
            return self.get(name)
        except:
            return default

    def setMetaData(self, tsname, tename, yposname):
        # Find attribute numbers (i.e., column indexes) for temporal
        # attributes
        for attnum, column in enumerate(self.schema):
            if tsname == column:
                self.tsid = attnum
            elif tename == column:
                self.teid = attnum
            elif yposname == column:
                self.ypos = attnum

        # Only check for the first temporal attribute, if the second is missing,
        # it means that "ts" contains a range type.
        if self.tsid == -1:
            raise_error("Temporal attribute '%s' not found in table header %s" % (tsname, self.schema))


if __name__ == '__main__':
    main()
