import logging
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
from .graph_tools import parse_args, save_graphs

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


def main(res):
    mpl.rcParams['figure.figsize'] = (10, 5)
    mpl.rcParams['text.usetex'] = True
    fig, ax = plt.subplots()
    ax.set_ylabel('Traffic Volume [Kb/s]')
    ax.set_xlabel('Time [s]')
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, linestyle='-', which='major', color='lightgrey',
                  alpha=.5)
    ax.xaxis.grid(True, linestyle='-', which='major', color='lightgrey',
                  alpha=.5)
    xticks = list(xrange(22))
    mirrored = {idx: i['mirrored'] for idx, i in enumerate(res)}
    mirrored[10.6] = mirrored[11]
    mirrored[10.625] = mirrored[11] = -200
    mirrored[11.25] = mirrored[12]
    mirrored[11.275] = mirrored[12] = -200
    mirrored_x = sorted(mirrored.iterkeys())
    mirrored = [mirrored[k] for k in mirrored_x]
    predicted = [i['predicted'] for i in res]
    sent = [i['sent'] for i in res]
    ax.plot([0, 32], [5000, 5000], color='darkgrey', linestyle='-', label='_nolegend_')
    ax.plot(sent, label='real', color='red', linestyle='-')
    ax.plot(mirrored_x, mirrored, label='mirrored', color='darkblue', linestyle='--')
    ax.plot(predicted, label='predicted', color='darkgreen', linestyle=':', drawstyle='steps-pre')

    ax.legend(loc='upper right')

    yticks = [50, 1000, 2000, 5000]
    ax.set_xlim(xmin=0, xmax=21)
    ax.set_xticks(xticks)
    ax.set_xticklabels(map(lambda x: str(x) if x in (1, 10, 12, 20, 0) else '',
                           xticks))
    ax.set_yticks(yticks)
    ax.set_yticklabels(map(str, yticks))
    ax.set_ylim(ymin=-500, ymax=11000)

    axins = inset_axes(ax, width='40%', height='20%', loc=2)
    axins.plot([0, 32], [5000, 5000], color='darkgrey', linestyle='-')
    axins.plot(mirrored_x, mirrored, linestyle='--', color='darkblue')
    axins.plot(sent, linestyle='-', color='red')

    axins.set(ylim=(4800, 5300), xlim=(11.22, 11.275))
    axins.set_yticks([5000])
    axins.set_yticklabels([''])
    axins.set_xticks([11.225, 11.25])
    axins.set_xticklabels(['11.225', '11.25'])
    axins.xaxis.grid(True, linestyle='-', which='major', color='lightgrey',
                  alpha=.5)
    for tick in axins.xaxis.get_major_ticks():
        tick.label.set_fontsize(18)

    mark_inset(ax, axins, loc1=1, loc2=4, fc="none", ec="0.5")

    LOG.info("Built budget graph")
    fig.tight_layout()
    return [fig]


if __name__ == '__main__':
    out_f, results = parse_args('Budget reaction analyzis', 'budget',
                                ['mirrored', 'predicted', 'sent'])
    idx = 0
    for i in results:
        i['slot'] = idx
        idx += 1
    save_graphs(out_f, main, results)
