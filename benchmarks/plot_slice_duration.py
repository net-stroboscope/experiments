import itertools

import graph_tools as lib

import matplotlib as mplt
import matplotlib.pyplot as plt

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

mplt.rcParams['text.usetex'] = True

list_diff = list()
slice_length = list()
save_times = list()
n_list = list()
n = 0
n_slice = 0
start = 0
end = 0
count = 0

filename = 'duration_50_times.txt'
with open(filename, 'r') as data_in:
    for i, line in enumerate(data_in):
        cells = line.strip().split('\t')

        if len(cells) != 5:
            continue

        if cells[2] == '60':
            temp_time = float(cells[0].split(' ')[3].split(':')[2])
            temp_data = cells[4]
            count += 1
            if count > 1 and start != 0:
                save_times.append([start, end])
                slice_length.append(end-start)
                n_list.append(n_slice)
                start = 0
                end = 0

        elif cells[2] == '110':
            n += 1
            count = 0
            list_diff.append(float(cells[1]))
            if start == 0:
                n_slice = 0
                start = float(cells[0].split(' ')[3].split(':')[2])
            n_slice += 1
            end = float(cells[0].split(' ')[3].split(':')[2])

to_plot = [list(), list(), list(), list(), list(), list(), list(), list(), list(), list(), list()]
num = 0
for value in slice_length:
    if value < 0:
        value += 60
    to_plot[num].append(value)
    num = (num + 1) % 11

fig, ax = lib.mk_plot('', 'Slice duration in ms', 'Pre-specified delay before \n automatic deactivation in ms')
bp = ax.boxplot(to_plot, patch_artist=True, showfliers=False)

color = 'lightblue'
contrast_color = 'dark%s' % color.replace('light', '')

for e in ['whiskers', 'means', 'medians', 'caps']:
    plt.setp(bp[e], color=contrast_color)
plt.setp(bp['whiskers'], linestyle='--', dashes=(6, 5))
plt.setp(bp['fliers'], markeredgecolor=color)
plt.setp(bp['boxes'], color=contrast_color)  # , hatch=hatch)
for patch in bp['boxes']:
    patch.set_facecolor('none')

ax.yaxis.grid(True, which='major')
ax.set_yticks([0.023, 0.026, 0.029, 0.032, 0.035])
ax.set_yticklabels([23, 26, 29, 32, 35])
ax.set_xticklabels([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
ax.set_ylim(0.022, 0.036)

ax.get_yaxis().set_tick_params(direction='in')
ax.get_xaxis().set_tick_params(direction='in')
ax.yaxis.set_ticks_position('both')
ax.xaxis.set_ticks_position('both')

#plt.show()
fig.savefig('slice_duration.pdf', format='pdf', dpi=500, bbox_inches='tight')
