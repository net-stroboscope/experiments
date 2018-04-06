import itertools
import logging

from .bench_ilp import FIELDS
from .graph_keypoints import _mk_plot
from .graph_tools import (boxplot, set_colors_and_legend, cdf, parse_args,
                          mk_plot as lib_mk_plot, substitute, save_graphs,
                          group_by)


LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


def plot_runtime(series):
    fig, ax, minlen, maxlen, xticks = _mk_plot(series, '', 'Time [s]',
                                               xlabel="Input query count",
                                               groupkey='query_count')
    xticks = set()
    for s in series.itervalues():
        xticks.update(r['query_count'] for r in s)
    xticks = map(str, sorted(map(int, xticks)))

    set_colors_and_legend(
        bp for bp in boxplot(ax, series, xticks,
                             lambda v: float(v.get('time', -1)),
                             groupkey='query_count', fliers=True))

    ax.set_yscale("log")
    yticks = [.0001, .001, .01, 1, 10, 100, 1000]
    ax.set_ylim(ymin=yticks[0], ymax=yticks[-1] * 100)
    ax.set_yticks(yticks)
    ax.set_yticklabels(map(str, yticks))

    LOG.info("Built runtime graph")
    fig.tight_layout()
    return fig


def plot_gain(series):
    series = series.copy()
    series.pop('Approximation', None)

    fig, ax = lib_mk_plot('', 'Fraction of experiments', 'Optimization gain')
    xticks = list(xrange(0, 101, 10))

    set_colors_and_legend((bp for bp in cdf(ax, series, xticks,
                                            groupkey='gain')),
                          display_legend=False)

    ax.set_ylim(ymin=0, ymax=1.0)

    LOG.info("Built CDF reduction graph")
    fig.tight_layout()
    return fig


def main(results):
    return [plot_runtime(results), plot_gain(results)]


if __name__ == '__main__':
    out_f, results = parse_args('ILP scheduling performance',
                                'ilp', FIELDS)
    substitute(results, 'function', approximation='Approximation',
               optimized='Optimized')

    i = 1
    while i < len(results):
        app, opt = results[i - 1], results[i]
        if opt['function'] == 'Approximation':
            app['baseline'] = app['total_allocs']
            i += 1
            continue
        app['baseline'] = opt['baseline'] = app['total_allocs']
        i += 2
    if results[-1]['function'] == 'Approximation':
        results.pop()
    maxgain = 0
    for r in results:
        r['gain'] = 100 * ((float(r['total_allocs']) - float(r['baseline'])) /
                           float(r['total_allocs']))
        maxgain = max(maxgain, r['gain'])
    print 'maxgain is:', maxgain
    if out_f is not None:
        save_graphs(out_f, main, group_by(results, key='function'))
