#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Ignoring warnings about "Used * or ** magic (star-args)"
# pylint: disable=W0142

# Author: Peter Moser <pitiz29a@gmail.com)

r"""TIKZ IMAGE GENERATOR FOR TIMELINE AND TEMPORAL TUPLES

Introduction
------------
Reads an PostgreSQL (psql --echo-all, see man-page of psql for further details)
output, and creates a standalone TIKZ tex-figure, or combined table/figure
LaTex file to be used with \input{filename}. To configure each output
table or timeline a SQL comment starting with "TIKZ:" must be provided. In
addition this script needs the following prerequisites for the input:
  1) There must be at least 2 columns for VALID TIME for each table
  2) Each relation must have a TIKZ config line as SQL comment (see below)
  3) A single timeline can be defined with "TIKZ: timeline, from, to, desc"
     This is optional.

We do not use some Python PostgreSQL libs here, because TEMPORAL OPERATORS are
not supported yet. Another reason is that we can create output files manually,
if we do not have a (TEMPORAL) POSTGRESQL instance running.


TIKZ-comment syntax
-------------------
First argument after "TIKZ: " is the type of drawing. The following lines
describe which types are supported:
  1) -- TIKZ: relation[-table], [abbrev], start column, end column, description
     If you put "relation-table" as drawing-type, a table and a diagram will be
     printed.
     The abbreviation is optional (it is used for tuple names). If you want to
     suppress it, do not forget to put the comma separator anyway.
  2) -- TIKZ: timeline, from, to, description
  3) -- TIKZ: config, key, value
     The key and value of this line is used for the combined table/figure
     picture, or for the standalone tikzpicture file. You can configure the
     label and caption of figures for instance.

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


For example
-----------
   -- TIKZ: relation, r, ts, te, Input relation r
   TABLE r;
    a | ts | te
   ---+----+----
    B |  1 |  7
    B |  3 |  9
    G |  8 | 10

   -- TIKZ: relation, s, ts, te, Input relation s
   SELECT * FROM s WHERE a='B';
    a | ts | te
   ---+----+----
    B |  2 |  5
    B |  3 |  4
    B |  7 |  9

   -- TIKZ: timeline, 0, 10, time

   -- You can refer to this figure with \ref{fig:input001}
   -- TIKZ: config, label, input001
   -- TIKZ: config, caption, Input relations \textbf{r} and \textbf{s}


Changelog
---------
  0.5
      - TIKZ-config lines are now key/value pairs
      - Additional config parameters to tweak the TEX output, i.e., subfigure
        column widths
  0.4.1
      - BUGFIX: captions are no longer truncated if a comma is found
  0.4
      - config line added to provide "label" and "caption" to LaTex
      - command line arguments (see usage output for details; i.e., --help)
  0.3
      - Parser becomes a generator (i.e., we use yield)
      - Parser simplified, returns only tokens to reuse it later for other
        projects
      - String formatting unified
  0.2
      - Reads configs from SQL comments with prefix "-- TIKZ"
      - Checks if TIKZ configs and data input matches
      - Different string formatting techniques tested (just for fun!)
      - Skips SQL commands
      - pylint errors and warnings fixed (most)
  0.1
      - Creates a standalone tikz picture from a PostgreSQL output
      - Skips comments and empty lines
      - Restriction: Hard-coded configuration
"""

import re
import os
import stat
import sys
import argparse

__version__ = "0.5"

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
        print __doc__
        parser.print_help()
        sys.exit(0)

    # No parse regular command line arguments
    args = parser.parse_args()

    # Stdin file stats to see if it is a pipe or redirection...
    mode = os.fstat(sys.stdin.fileno()).st_mode

    # Input files are explicitely given as a filename list
    if type(args.FILE) is file:
        input_file = args.FILE
        input_text = input_file.readlines()

    # We have a piped or redirected STDIN at disposal...
    elif stat.S_ISFIFO(mode) or stat.S_ISREG(mode):
        print "READING FROM STDIN\n"
        input_text = sys.stdin.readlines()

    # No stdin, no input files... shutdown!
    else:
        parser.error("No input files, nor stdin given (i.e., a dash).")

    try:
        parse_result = pgsql_parser(input_text)

        figure = ""
        table = ""
        cfg = {}

        if args.output_type in ['all', 'figure-standalone', 'figure-only']:
            figure = format_tikz_figure(parse_result)

        if args.output_type in ['all', 'table-only']:
            table_type = 1
            if args.output_type == 'all':
                table_type = 2

            for line in parse_result:
                if line['type'] == 'relation-table':
                    table += format_latex_table(line, "", table_type)
                if line['type'] == 'config':
                    cfg[line['key']] = line['value']

        # If we print the whole figure/table combination, we need a "label" and
        # "caption" below the two sub-figures.
        if args.output_type == 'all':
            if not cfg.has_key('label'):
                raise_error_cfgline(
                    'label',
                    "We do not know which 'label' to use for figures.")

            if not cfg.has_key('caption'):
                raise_error_cfgline(
                    'caption',
                    "We do not know which 'caption' to use for figures.")

        # TODO Create text first in memory, and write it at last. Otherwise, we
        # could get half-made output files, when an error has
        outfile = sys.stdout
        if args.output != None:
            if os.path.isfile(args.output):
                raise_error(
                    "File '%s' already exists! Exiting..." % args.output)
            outfile = open(args.output, 'w')

        outfile.write(format_latex_header("".join(input_text)))

        if args.output_type == 'all':

            # Subfigures have a left and right column with a certain width
            # If it is not configured explicitely, we will take these defaults:
            subfigure_left = 0.27
            subfigure_right = 0.63
            if cfg.has_key('subfigure-left'):
                subfigure_left = cfg['subfigure-left']
            if cfg.has_key('subfigure-right'):
                subfigure_right = cfg['subfigure-right']

            outfile.write(format_latex_figure_and_table(table,
                                      figure,
                                      cfg['caption'],
                                      cfg['label'],
                                      subfigure_left,
                                      subfigure_right))
        elif args.output_type == 'table-only':
            outfile.write(table)
        elif args.output_type == 'figure-only':
            outfile.write(figure)
        elif args.output_type == 'figure-standalone':
            outfile.write(format_latex_standalone(figure))
        else:
            raise_error(
                "Unknown output type specified")

    except ValueError as valerr:
        print "\n".join(valerr.args) + "\n"
        sys.exit(3)

def format_tikz_desc(pos, desc):
    """Prints the description of each found table on the left-hand-side of the
    tuple time lines in a standalone tikz figure"""
    return TEMPLATE_TIKZ_DESC.format(pos=pos,
                                     desc=desc)


def format_tikz_tupleline(tup, cfg, tuple_count, count):
    """Prints the tuple time lines in a standalone tikz figure"""
    if cfg['name'] == "":
        out = TEMPLATE_TIKZ_TUPLE + "{{$({attribs})$}};\n"
    else:
        out = TEMPLATE_TIKZ_TUPLE + "{{${name}_{{{id}}}=({attribs})$}};\n"

    valid_time_ts = int(tup[cfg['tsattnum']])
    valid_time_te = int(tup[cfg['teattnum']])

    # Concatenate all non-temporal attributes as description above the line
    attribs = ""
    for key, value in enumerate(tup):
        if key not in [cfg['tsattnum'], cfg['teattnum']]:
            attribs += r"\mathrm{%s}," % value

    return out.format(name=cfg['name'],
                      id=tuple_count,
                      ts=valid_time_ts,
                      te=valid_time_te,
                      count=count,
                      posx=float(valid_time_ts+valid_time_te) / 2,
                      posy=count - 0.2,
                      attribs=attribs.rstrip(','))

def format_tikz_timeline(cfg):
    """Prints a timeline in a standalone tikz figure"""
    return TEMPLATE_TIKZ_TIMELINE.format(start=int(cfg['from']),
                                         end=int(cfg['to']),
                                         desc=cfg['desc'])

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

    state = STATE_OUTSIDE
    for line in lines:

        line = line.lstrip()

        # Skip empty lines
        # This ends a table parsing, and returns to the STATE_OUTSIDE state
        if line.rstrip() == "":
            if state != STATE_OUTSIDE:
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

            # Search for table headers, if none found, skip it...
            if None == re.search(r'\s*[^\|]+?\s*\|\s*[^\|]+?', line):
                yield ['COMMAND', line.rstrip()]
                continue

            state = STATE_HEADER
            headers = []
            for head in line.split('|'):
                headers.append(head.strip())

            yield ['HEADER', headers]

        # Not skipped and currently in a tuple state, therefore the next data
        # line must be another tuple, or tuple count, i.e., (3 rows)
        if state == STATE_TUPLES:

            # We skip tuple count rows at the end of each table. This ends
            # a table block.
            match = re.search(r'\((\d+?)\srows\)', line)
            if match:
                state = STATE_OUTSIDE
                yield ['TUPLECOUNT', match.group(1)]
                continue

            values = []
            for value in line.split('|'):
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
                    listitems = [comment_type] + re.split(r'\s*,\s*',
                                                          comment_body, 1)
                    configs.append(
                        dict(zip(['type',
                                  'key',
                                  'value'], listitems)))
                elif comment_type in ['relation', 'relation-table']:
                    listitems = [comment_type] + re.split(r'\s*,\s*',
                                                          comment_body, 3)
                    configs_count_relation += 1
                    configs.append(
                        dict(zip(['type',
                                  'name',
                                  'ts',
                                  'te',
                                  'desc'], listitems)))
                elif comment_type == 'timeline':
                    if configs_count_timeline == 1:
                        raise_error(
                            "More than one TIKZ timeline string found",
                            "Define a single configuration string for the " +
                            "timeline.\n For example:\n" +
                            "-- TIKZ: timeline, from, to, time line " +
                            "description")
                    else:
                        listitems = [comment_type] + re.split(r'\s*,\s*',
                                                              comment_body, 2)
                        configs_count_timeline += 1
                        configs.append(
                            dict(zip(['type',
                                      'from',
                                      'to',
                                      'desc'], listitems)))
        elif token[0] == 'HEADER':
            tables.append([token[1]])
            table_count = len(tables) - 1
        elif token[0] == 'TUPLE':
            tables[table_count].append(token[1])

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
    table_count = 0
    for cfg in configs:
        if cfg['type'] in ['relation', 'relation-table']:
            cfg['table'] = tables[table_count]
            table_count += 1

            # Find attribute numbers (i.e., column indexes) for temporal
            # attributes
            for attnum, column in enumerate(cfg['table'][0]):
                if cfg['ts'] == column:
                    cfg['tsattnum'] = attnum
                elif cfg['te'] == column:
                    cfg['teattnum'] = attnum

            # One or both temporal attributes are non-existent. Raise an error.
            if not cfg.has_key('tsattnum') or not cfg.has_key('teattnum'):
                raise_error(
                    "Temporal attribute '%s' or '%s' not found in table " \
                    "header %s" % (cfg['ts'], cfg['te'], cfg['table'][0]))

    return configs

def format_tikz_figure(parse_result):
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
        count_above += len(line['table']) - 1

    posy = count_above
    out = ""

    for line in parse_result:

        # Only these configuration lines are allowed, skip all others...
        if line['type'] not in ['timeline', 'relation', 'relation-table']:
            continue

        # Print the timeline
        if line['type'] == 'timeline':
            out += format_tikz_timeline(line)
            posy = -2
            continue

        # Print description on the left-hand-side of each relation
        if line['desc'].strip() != "":
            out += format_tikz_desc(posy - (len(line['table']) - 1) / 2,
                                   line['desc'])

        # We skip the first element inside a table. It is the header.
        table = line['table'][1:]

        # Print tuples of each table as lines from ts to te. The description of
        # each tuple is a list of explicit attributes (i.e., non-temporal
        # columns), and optionally a tuple identifier "relation_tuplecount"
        for tuple_count, tup in enumerate(table, 1):
            out += format_tikz_tupleline(tup, line, tuple_count, posy)
            posy -= 1

    return TEMPLATE_TIKZ_PICTURE.format(content=out)

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

    # We skip the first element inside a table. It is the header.
    tuples = line['table'][1:]
    header = line['table'][0]

    # Concatenate all non-temporal attributes as description above the line
    attribs = r" & ".join(header)
    rows = ""
    for row_count, row in enumerate(tuples, 1):
        rows += " " * 12 + "$%s_{%d}$ & %s \\\\\n" % (line['name'],
                                         row_count,
                                         r" & ".join(row))

    if table_type == 1:
        return TEMPLATE_LATEX_TABLE.format(
                caption=line['desc'],
                label=label,
                length=len(header) + 1,
                header_cfg="c" * len(header),
                header=attribs.rstrip(" &"),
                rows=rows.rstrip("\n"))

    return TEMPLATE_LATEX_TABLE2.format(
                header_cfg="c" * len(header),
                header=attribs.rstrip(" &"),
                rows=rows.rstrip("\n"),
                relation=line['name'])


def format_latex_figure_and_table(table_str,
                                  tikz_str,
                                  caption,
                                  label,
                                  subfigure_left,
                                  subfigure_right):
    """Prints a figure and a table side-by-side as sub-figures"""
    return TEMPLATE_LATEX_TIKZTABLE.format(table=table_str,
                                           tikzpicture=tikz_str,
                                           caption=caption,
                                           label=label,
                                           subfigureleft=subfigure_left,
                                           subfigureright=subfigure_right)

# STATES of the tokenizer, which is implemented as a state machine...
STATE_OUTSIDE = 0        # We have not found a table yet
STATE_HEADER = 1         # We have found a table STATE_HEADER (attribute names)
STATE_TUPLES = 2         # We have already parsed the table header, and are
                         # reading in tuples now

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
    \begin{{tikzpicture}}[xscale=0.65,yscale=0.4]
    {content}
    \end{{tikzpicture}}
"""

# Prints the description of each found table on the left-hand-side of the
# tuple time lines in a standalone tikz figure
TEMPLATE_TIKZ_DESC = r"""
        % Description
        \node[align=left, font=\scriptsize] at (0,{pos}) {{{desc}}};
"""

TEMPLATE_TIKZ_TIMELINE = r"""
        % Time line
        \draw[->, line width = 0.9] ({start},0)--({end}+1,0);
        \foreach \t in {{{start},...,{end}}}
        {{
            \draw ($(\t cm,-1mm)+(0cm,0)$)--($(\t cm,1mm)+(0cm,0)$);
            \draw ($(\t cm,0.5mm)$) node[below,font=\scriptsize \bfseries]{{\t}};
        }}
        \draw ($({end}+1,0)+(3mm,-1mm)$) node[below,font=\bfseries]{{$\mathrm{{{desc}}}$}};
"""

TEMPLATE_TIKZ_TUPLE = r"""
        % Tuple {name}_{id}
        \draw[-] ({ts},{count})--({te},{count});
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

if __name__ == '__main__':
    main()
