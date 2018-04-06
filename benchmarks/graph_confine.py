import logging
import itertools

from .bench_confinement import FIELDS
from .graph_keypoints import main, _mk_plot
from .graph_tools import (parse_args, substitute, boxplot, group_by, cdf,
                          set_colors_and_legend, mk_plot as lib_mk_plot,
                          series_bounds)

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


def _get_out_len(v):
    return int(v.get('output_len', -1))


def plot_runtime(series, title):
    series = series.copy()
    series.pop('Edge surrounding', None)
    fig, ax, minlen, maxlen, xticks = _mk_plot(series, '', 'Time [ms]',
                                               xlabel="Region size")
    measurements = group_by(series[series.keys()[0]], 'input_len').keys()
    xticks = map(lambda x: x if x in measurements else "", xticks)

    set_colors_and_legend(
        bp for bp in boxplot(ax, series, xticks,
                             lambda v: float(v.get('time', -1)) * 1000))

    ax.set_yscale("log")
    yticks = [.05, .1, 1, 5, 15, 50, 100]
    ax.set_ylim(ymin=yticks[0], ymax=1000)
    ax.set_yticks(yticks)
    ax.set_yticklabels(map(str, yticks))

    LOG.info("Built runtime graph for: %s", title)
    fig.tight_layout()
    return fig


def plot_reduction(series, title):
    fig, ax, minlen, maxlen, xticks = _mk_plot(
        series, title, 'Number of mirroring rule')

    set_colors_and_legend(
        bp for bp in boxplot(ax, series, xticks, _get_out_len))

    ax.set_ylim(ymin=1, ymax=series_bounds(series, 'output_len')[1] + 2)

    LOG.info("Built reduction graph for: %s", title)
    return fig


def plot_reduction_edges(series, title):
    series = series.copy()
    series.pop('Edge surrounding', None)

    fig, ax, minlen, maxlen, xticks = _mk_plot(
        series, title, 'Number of mirroring rule', 'edge_count',
        'Number of surrounding edges')

    ax.plot([0, int(xticks[-1])],
            # Y - 1 because we'll crop the y axis
            [int(xticks[0]) - 1, int(xticks[0]) + int(xticks[-1]) - 1],
            color='red')

    set_colors_and_legend(
        bp for bp in boxplot(
            ax, series, xticks, _get_out_len, 'edge_count'))

    ax.set_ylim(ymin=1, ymax=series_bounds(series, 'edge_count')[1] + 2)

    LOG.info("Built edge reduction graph for: %s", title)
    return fig


def plot_cdf_edges(series, title):
    series = series.copy()
    series.pop('Edge surrounding', None)

    fig, ax = lib_mk_plot('', 'Fraction of experiments', 'Optimization gain')
    xticks = list(xrange(0, 101, 10))

    set_colors_and_legend(bp for bp in cdf(ax, series, xticks))

    ax.set_ylim(ymin=0, ymax=1.0)
    ax.set_xticklabels(map(lambda x: '' if x[0] % 2 == 0 else str(x[1]),
                           enumerate(xticks)))

    LOG.info("Built CDF reduction graph for: %s", title)
    fig.tight_layout()
    return fig


if __name__ == '__main__':
    out_f, results = parse_args('Confinement graph generation',
                                    'confinement', FIELDS)
    substitute(results, 'function',
               find_confinement_edges='Edge surrounding',
               find_confinement_region='Node surrounding',
               find_confinement_relaxed='Minimal surrounding')
    it = iter(results)
    for edges, nodes, optimal in itertools.izip_longest(
            it, it, it, fillvalue=None):
        x = str(_get_out_len(edges))
        edges['edge_count'] = nodes['edge_count'] = optimal['edge_count'] = x
    for r in results:
        r['reduction_pc'] = 100 * (
            1 - float(r['output_len']) / float(r['edge_count']))
    if out_f is not None:
        main(out_f, results, (plot_runtime, plot_reduction,
                              plot_reduction_edges, plot_cdf_edges,))
