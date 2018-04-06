import logging
from .bench_keypoints import FIELDS
from .graph_tools import (parse_args, series_bounds, mk_plot, cdf, group_by,
                          xticks_for_bounds, set_colors_and_legend, boxplot,
                          save_graphs, filter_by)


LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


def _mk_plot(series, title, ylabel, groupkey='input_len',
             xlabel='Input path length'):
    minlen, maxlen = series_bounds(series, groupkey=groupkey)
    xticks = xticks_for_bounds(minlen, maxlen)
    fig, ax = mk_plot(title, ylabel, xlabel=xlabel)
    return fig, ax, minlen, maxlen, xticks


def plot_runtime(series, title):
    fig, ax, minlen, maxlen, xticks = _mk_plot(series, '', 'Time [ms]')

    # ax.plot([-1, maxlen + 1], [1000, 1000], color='red')

    set_colors_and_legend(
        (bp for bp in boxplot(ax, series, xticks,
                              lambda v: float(v.get('time', -1)) * 1000)),
        False)

    ax.set_yscale("log")
    ax.set_ylim(ymin=.01, ymax=1000)
    yticks = [.01, .1, 1, 10, 100, 200, 1000]
    ax.set_yticks(yticks)
    ax.set_yticklabels(map(str, yticks))
    ax.set_xticklabels(map(lambda x: '' if int(x) % 2 == 0 else str(x),
                           xticks))

    LOG.info("Built runtime graph for: %s", title)
    fig.tight_layout()
    return fig


def plot_reduction(series, title):
    fig, ax, minlen, maxlen, xticks = _mk_plot(
        series, title, 'Number of mirroring rules')

    ax.plot([0, maxlen + 1], [2, maxlen + 3], color='red')
    ax.plot([0, maxlen + 1], [2, 2], color='grey')

    set_colors_and_legend(
        bp for bp in boxplot(ax, series, xticks,
                             lambda v: int(v.get('output_len', -1))))

    ax.set_yticks([2, 4, 6, 8, 10, 15, 20])
    ax.set_ylim(ymin=1, ymax=maxlen)

    LOG.info("Built reduction graph for: %s", title)
    return fig


def plot_cdf(series, title):
    fig, ax = mk_plot('', 'Fraction of experiments', 'Optimization gain')
    xticks = list(xrange(0, 101, 10))

    set_colors_and_legend((bp for bp in cdf(ax, series, xticks)),
                              False)

    ax.set_ylim(ymin=0, ymax=1)
    ax.set_xticklabels(map(lambda x: '' if x[0] % 2 == 0 else str(x[1]),
                           enumerate(xticks)))

    LOG.info("Built CDF reduction graph for: %s", title)
    fig.tight_layout()
    return fig


def gen_graphs(by_topos, func_list):
    for topo, _data in by_topos.iteritems():
        pselect = group_by(_data, 'path_selection')
        perturb = group_by(pselect.pop('perturb', []), 'perturb')
        for func in func_list:
            for level, data in perturb.iteritems():
                yield func(group_by(data, 'function'),
                           'graph: %s, paths selection: perturb(%d%%)' % (
                           topo, int(float(level) * 100)))
            for selection, data in pselect.iteritems():
                yield func(group_by(data, 'function'),
                           'graph: %s, paths selection: %s' %
                           (topo, selection))


def main(out_filename, results, func_list):
    by_topos = group_by(results, 'graph')
    LOG.info('Analyzing results over %d graphs', len(by_topos))
    by_topos['*'] = results
    save_graphs(out_filename, gen_graphs, by_topos, func_list)


if __name__ == '__main__':
    out_f, results = parse_args('Keypoints graph generation',
                                    'keypoints', FIELDS)
    results = filter_by(function=lambda x: x == 'find_key_points')(results)
    results = list(filter_by(input_len=lambda x: int(x) <= 15)(results))
    for r in results:
        r['reduction_pc'] = 100 * (
            1 - float(r['output_len']) / float(r['input_len']))
    if out_f is not None:
        main(out_f, results, (plot_runtime,plot_cdf))  # plot_reduction
