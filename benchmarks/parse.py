"""
Common definition to parse the command line.
"""
import random
import itertools
import argparse
import logging

from .heuristics import Path, Egresses
from .topologies.rf import get_topo as rf
from .topologies.topozoo import get_topo as zoo

from stroboscope.requirements import Budget


LOG = logging.getLogger(__name__)

RF_TOPOS = [
    '1221',
    '1239',
    '1755',
    '3257',
    '3967',
    '6461'
]

ZOO_TOPOS = [
    'Cogentco',
    'Kdl'
]

EGRESSES = Egresses.heuristics()
PATH = Path.heuristics()


def init_parser(description='', epilog='', default_timeout=30):
    parser = argparse.ArgumentParser(description=description,
                                     epilog=epilog)
    genprm = parser.add_argument_group('Execution parameters')
    genprm.add_argument('--enable-debug', help='Enable DEBUG log',
                        action='store_true', default=False)
    genprm.add_argument('--seed', help='Specify the random seed to use',
                        default=123456789, type=int)
    genprm.add_argument('--out', help='The filename where the benchmark '
                        'results will be saved', default='benchmark',
                        type=str)
    genprm.add_argument('--max-exec-time', help='The maximal execution time'
                        'of a test run', type=float,
                        default=default_timeout)
    genprm.add_argument('--repeat', help='Repeat each experiment a number of '
                        'time', default=1, type=int)
    return parser


def parse_commandline(parser):
    args = parser.parse_args()
    if not args.enable_debug:
        logging.disable(logging.DEBUG)
    LOG.info('Seeding specification generator with: %s', args.seed)
    random.seed(args.seed)
    return args


def parse_paths(parser):
    paths = parser.add_argument_group('Path selection')
    paths.add_argument('--max-path', help='The maximal number of paths per '
                       'run', type=int, default=50)
    paths.add_argument('--max-len', help='The maximal requirement path'
                       'lengths', type=int, default=20)
    paths.add_argument('--path-perturb', help='The perturbution from the SPT '
                       'as a percententage', type=float, default=.2)
    paths.add_argument('--egress-percentage', help='The maximal percentage of '
                       'egresses', type=float, default=.20)
    paths.add_argument('--egress-degree', help='The maximal out degre of'
                       'egresses', type=int, default=2)
    paths.add_argument('--region-count', help='The number of regions to '
                       'define', type=int, default=10)
    paths.add_argument('--egress-selection',
                       help='Egresses selection heuristic',
                       default='low_degree',
                       choices=EGRESSES.keys())
    paths.add_argument('--path-selection',
                       help='Paths selection heuristic',
                       default='perturb',
                       choices=PATH.keys())


def build_paths(graph, args):
    EGRESSES[args.egress_selection](graph, percentage=args.egress_percentage,
                                    degree=args.egress_degree)
    return PATH[args.path_selection](graph, maxlen=args.max_len,
                                     region_count=args.region_count,
                                     perturb=args.path_perturb)


def parse_topo(parser):
    topos = parser.add_argument_group('Topology sources')
    topos.add_argument('-z', '--zoo', help='Specify one or more topology '
                       'names from the topology zoo (the filenames in '
                       'topologies/topologyzoo without the extension)',
                       nargs='*', default=ZOO_TOPOS)
    topos.add_argument('-r', '--rocketfuel', help='Similar to -z but for the '
                       'rocketfuel topologies (see topologies/rocketfuel)',
                       nargs='*', default=RF_TOPOS)


def build_graphs(args):
    """Build a set of graphs from the topology zoo and/or the rocketfuel
    topology set"""
    rf_topos = args.rocketfuel
    zoo_topos = args.zoo
    LOG.debug('Building graphs rf:%s, zoo:%s', rf_topos, zoo_topos)
    graphs = filter(None, (zoo(n) for n in zoo_topos))
    graphs.extend(itertools.ifilter(None, (rf(n) for n in rf_topos)))
    graphs.sort(key=len)
    return graphs


def parse_budget(parser):
    budget = parser.add_argument_group('Budget parameter')
    budget.add_argument('--gap', help='The MIP GAP allowed from the optimal',
                        default=.05, type=float)
    budget.add_argument('--timeslots', help='The timeslot count',
                        default=150, type=int)
    budget.add_argument('--using', help='The budget ratio wrt. mean query '
                        'demands', default=2, type=float)


def build_budget(args):
    budget = Budget(mip_gap=args.gap, max_ilp_run=args.max_exec_time)
    budget.max_slots = args.timeslots
    budget.using = args.demand_ratio_avg * args.using
    return budget


def parse_queries(parser):
    cnt_queries = parser.add_argument_group('Query counts')
    cnt_queries.add_argument('--query-count', help='The number of queries to '
                             'generate', default=150, type=int)
    cnt_queries.add_argument('--active-ratio', help='The ratio of pure active '
                             'queries', default=.5, type=float)
    cnt_queries.add_argument('--passive-ratio', help='The ratio of pure '
                             'passive queries', default=.5, type=float)
    cnt_queries.add_argument('--demand-ratio-avg', help='The average flow'
                             'demands', type=float, default=100)
    cnt_queries.add_argument('--demand-ratio-stdev', help='The associated '
                             'stdev for the demands',
                             default=25, type=float)


def build_queries(budget, args):
    class MockQuery(object):
        ID = 0

        def __init__(self, has_cost=True):
            self.index = MockQuery.ID
            MockQuery.ID += 1
            self.cost = (max(0.001, random.normalvariate(
                            args.demand_ratio_avg, args.demand_ratio_stdev))
                         if has_cost else 0)
            self.weight = 1

        def __hash__(self):
            return hash(self.index)

        def __repr__(self):
            return 'Q%d' % self.index
        __str__ = __repr__

    budget.using = args.demand_ratio_avg * args.using
    queries = [MockQuery() for _ in
               xrange(int(args.active_ratio * args.query_count))]
    queries.extend([MockQuery(False) for _ in
                    xrange(int(args.passive_ratio * args.query_count))])
    return queries
