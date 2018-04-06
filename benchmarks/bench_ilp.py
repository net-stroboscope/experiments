import os
import csv
import time
import logging

import stroboscope.algorithms.schedule as ilp

from .utils import mean_stdev
from .parse import (init_parser, parse_budget, parse_queries,
                    parse_commandline, build_queries, build_budget)

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


FIELDS = ['time', 'budget_avg', 'budget_stdev', 'query_count', 'active',
          'passive', 'slots_avg', 'slots_stdev', 'gap', 'total_alloc',
          'slots', 'usage_avg', 'usage_stdev', 'function',
          'min_alloc_count']


def parse_args():
    parser = init_parser(
        description='ILP benchmarking suite',
        epilog='This benchmark is designed to run a single instance of the'
        'ILP at a time, in order to mimize the side-effects of the gc, ...',
        default_timeout=240)
    parse_budget(parser)
    parse_queries(parser)
    parser.add_argument('--restrict', help='restrict to the chosen ILP algo',
                        choices=ilp.FUNCS.keys(), default=ilp.FUNCS.keys(),
                        nargs='*')
    args = parse_commandline(parser)
    return (args, args.restrict)


def test(f, queries, budget, writer, args):
    try:
        LOG.info('Trying solver: %s', f)
        runtime = -time.clock()
        schedule = ilp.balance_and_schedule(queries, budget, f)
        runtime += time.clock()
        if not schedule:
            LOG.error('Empty schedule and no exception thrown ?')
            return
        _sched = {}
        for slot in schedule:
            for q in slot:
                try:
                    _sched[q] += 1
                except KeyError:
                    _sched[q] = 1
        avg_slots, stdev_slots = mean_stdev(_sched.values())
        res = {'time': runtime,
               'total_alloc': sum(len(slot) for slot in schedule),
               'min_alloc_count': min(_sched.itervalues()),
               'budget_avg': args.demand_ratio_avg,
               'budget_stdev': args.demand_ratio_stdev,
               'query_count': len(queries),
               'active': args.active_ratio,
               'passive': args.passive_ratio,
               'slots_avg': avg_slots,
               'slots_stdev': stdev_slots,
               'gap': args.gap, 'slots': len(schedule),
               'function': f}
        LOG.info(res)
        writer.writerow(res)
    except ilp.NoSchedule as e:
        LOG.error("%s could not compute a schedule for %s: %s", f, args, e)


def main():
    args, funcs = parse_args()
    existed = os.path.exists(args.out)
    with open(args.out, 'a') as outfile:
        writer = csv.DictWriter(outfile, FIELDS)
        if not existed:
            writer.writeheader()
        budget = build_budget(args)
        queries = build_queries(budget, args)
        LOG.info("Built %d queries with %s and %d slots", len(queries),
                 str(budget).replace('\n', '').replace('   ', ''),
                 budget.max_slots)
        for _ in xrange(args.repeat):
            for f in funcs:
                test(f, queries, budget, writer, args)


if __name__ == '__main__':
    main()
