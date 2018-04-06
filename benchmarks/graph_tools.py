import csv
import math
import collections
import itertools
import operator
import os
import sys
import subprocess
import argparse
import logging

import matplotlib as mplt
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.backends.backend_pdf as mpdf

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


COLORS = [('lightblue', '///'), ('red', 'ooo'), ('lightgreen', '\\\\\\'), ]


mplt.rcParams.update({'font.size': 24, 'lines.linewidth': 4,
                      'boxplot.boxprops.linewidth': 2})
mplt.rcParams['text.usetex'] = True


class filter_by(object):
    """An utility class to filter data according to some of its values
    :kw: a dictionnary of field names and functions to apply on those
         fields. If all function return True, then the row matches"""

    def __init__(self, **kw):
        self.restrict = kw

    def matches(self, row):
        for k, v in self.restrict.iteritems():
            try:
                if not v(row[k]):
                    return False
            except KeyError:
                return False
        return True

    def __call__(self, data):
        for row in data:
            if self.matches(row):
                yield row


def group_by(data, key):
    keyfunc = operator.itemgetter(key)
    sorted_data = sorted(data, key=keyfunc)
    return {k: list(g) for k, g in itertools.groupby(sorted_data, keyfunc)}


def substitute(data, key, **values):
    for row in data:
        try:
            old_val = row[key]
            row[key] = values[old_val]
        except KeyError:
            pass


def read_results(filename, fields):
    with open(filename) as f:
        reader = csv.DictReader(f, fieldnames=fields)
        results = [r for r in reader]
    k = fields[0]
    if results and results[0][k] == k:
        LOG.info('Deleting header')
        del results[0]
    LOG.info('Read %d records from %s', len(results), filename)
    return results


def series_bounds(series, groupkey='input_len'):
    maxlen = 0
    minlen = 40
    for data in series.itervalues():
        __len = map(int, group_by(data, groupkey).iterkeys())
        maxlen = max(max(__len), maxlen)
        minlen = min(min(__len), minlen)
    return minlen, maxlen


def xticks_for_bounds(minlen, maxlen):
    return [str(x) for x in xrange(minlen, maxlen + 1)]


def mk_plot(title, ylabel, xlabel='Input path length'):
    fig, ax = plt.subplots()
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, linestyle='-', which='major', color='lightgrey',
                  alpha=.5)
    return fig, ax


def boxplot(ax, series, xticks, keyfunc, groupkey='input_len', fliers=False):
    for function, data in series.iteritems():
        by_input_len = group_by(data, groupkey)
        # Fill missing values if any
        for k in xticks:
            if k not in by_input_len:
                by_input_len[k] = [{}]
        bp = ax.boxplot([[keyfunc(v) for v in by_input_len[k]]
                         for k in xticks],
                        patch_artist=True,
                        showfliers=fliers)
        yield (bp, function, ax)
    set_xlabels(ax, xticks)


def cdf(ax, series, xticks, groupkey='reduction_pc', decreasing=True):
    for function, data in series.iteritems():
        item_pc = 1.0 / len(data)
        reductions = sorted(x[groupkey] for x in data)
        by_input_len = collections.defaultdict(int)
        for x in reductions:
            by_input_len[x] += item_pc
        cumsum = []
        acc = 0.0
        by_len = sorted(by_input_len.iterkeys())
        for k in by_len:
            acc += by_input_len[k]
            cumsum.append(1.0 - acc if decreasing else acc)
        p = ax.plot(by_len, cumsum, drawstyle='steps-post')
        yield (p, function, ax)
    set_xlabels(ax, xticks)


def set_xlabels(ax, ticks, max_ticks=12):
    lticks = len(ticks)
    if lticks > max_ticks:
        steps = int(math.ceil(lticks / max_ticks - 2))
        xticks = [ticks[i]
                  if i % steps == 0 or i == 0 or i == lticks - 1 else ""
                  for i in xrange(lticks)]
    else:
        xticks = ticks
    ax.set_xticklabels(xticks)


def set_colors_and_legend(plots, display_legend=True, loc='upper center'):
    legend = []
    for (plot, function, ax), (color, hatch) in zip(plots, COLORS):
        contrast_color = 'dark%s' % color.replace('light', '')
        if isinstance(plot, list):
            for p in plot:
                plt.setp(p, color=contrast_color)
        else:
            for e in ['whiskers', 'means', 'medians', 'caps']:
                plt.setp(plot[e], color=contrast_color)
            plt.setp(plot['fliers'], markeredgecolor=contrast_color)
            plt.setp(plot['boxes'], color=contrast_color)  # , hatch=hatch)
            for patch in plot['boxes']:
                patch.set_facecolor('none')
        legend.append((color, function, hatch, contrast_color))
    if display_legend:
        ax.legend(loc=loc, handles=[
            mpatches.Patch(facecolor=ccolor, edgecolor=ccolor,  # hatch=hatch,
                           label=f) for color, f, hatch, ccolor in legend])


def open_pdf(f):
    if os.environ.get('VIEWER', None) == '--no-viewer':
        return
    LOG.info('Trying to open %s with the default reader ...', f)
    try:
        if sys.platform.startswith('darwin'):
            subprocess.call(('open', f))
        elif os.name == 'nt':
            os.startfile(f)
        elif os.name == 'posix':
            subprocess.call(('xdg-open', f))
    except Exception:
        LOG.error('Failed!')


def save_graphs(out_filename, gen_graphs, *args, **kw):
    LOG.info("Saving graphs to: %s", out_filename)
    with mpdf.PdfPages(out_filename) as outfile:
        for fig in gen_graphs(*args, **kw):
            outfile.savefig(fig)
            plt.close(fig)
    open_pdf(out_filename)


def parse_args(title, suffix, csv_fields=None):
    parser = argparse.ArgumentParser(title)
    parser.add_argument('file', help="The path to a csv file containing"
                        " the results such as one generated by\n"
                        "`python -m millefeuille.bench.bench_%s --out FILE" %
                        suffix)
    args = parser.parse_args()
    out_name = '%s_graph_%s.pdf' % (args.file.replace('.csv', ''), suffix)
    try:
        results = read_results(args.file, csv_fields)
        return out_name, results
    except (IOError, OSError) as e:
        LOG.exception(e)
        return None, None
