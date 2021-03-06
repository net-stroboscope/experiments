import gc
import os
import time
import csv
import logging


from stroboscope.algorithms.key_points import KPS_OPT

from .parse import (parse_commandline, parse_paths, parse_topo, init_parser,
                    build_graphs, build_paths)

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


FIELDS = ['function', 'time', 'input_len', 'output_len', 'egress_selection',
          'path_selection', 'graph', 'perturb', 'egress_cnt']


def parse_args():
    parser = init_parser(
        description='Key point sampling benchmarking suite',
        epilog='If multiple arguments are given for the same parameter, '
        'the benchmark will be run multiple times, combining the different '
        'possibilities of these arguments across groups.')
    parse_paths(parser)
    parse_topo(parser)
    args = parse_commandline(parser)
    return args, build_graphs(args)


def test(runid, f, g, path, writer, args):
    t = -time.clock()
    sampling = f(g, path)
    t += time.clock()
    outlen = len(sampling)
    res = {'function': f.__name__, 'time': t, 'input_len': len(path),
           'output_len': outlen, 'graph': g.name,
           'egress_selection': args.egress_selection,
           'path_selection': args.path_selection,
           'perturb': args.path_perturb,
           'egress_cnt': len(g.egresses)}
    LOG.info("Run %d: %s", runid, res)
    writer.writerow(res)


def main():
    args, graphs = parse_args()
    existed = os.path.exists(args.out)
    with open(args.out, 'a') as outfile:
        writer = csv.DictWriter(outfile, FIELDS)
        if not existed:
            writer.writeheader()
        runid = 0
        for g in graphs:
            for _ in xrange(args.repeat):
                pcount = 0
                for path in build_paths(g, args):
                    for f in KPS_OPT:
                        test(runid, f, g, path, writer, args)
                        runid += 1
                    pcount += 1
                    if pcount > args.max_path:
                        break
            gc.collect()
            gc.collect()


if __name__ == '__main__':
    main()
