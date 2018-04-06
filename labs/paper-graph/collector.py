#!/bin/python2
"""Entry point to start a Stroboscope collector."""
import argparse
import logging
import itertools

from stroboscope import join
from stroboscope.collector import Collector
from stroboscope.measurement_processor import MeasurementProcessor

from ipmininet.topologydb import TopologyDB


logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)


class Analyzer(MeasurementProcessor):
    """
    Compute loss rates and load-balancing occurences for all MIRROR queries.
    """

    def process(self, locations, queries, traffic_slices):
        for q in queries:
            lost = 0
            load_balanced = 0
            try:
                src, dst = q.path_endpoints()
            except AttributeError:
                continue  # This is a confine query
            matches = {}  # Record matches for the query
            for pkt in traffic_slices[src]:
                # Check that its DA fits the query prefix
                if pkt.dst not in q.prefix:
                    continue
                seen = {}  # record the location where a packet has been seen
                # We have a packet for this query, find all matching locations
                prev_ttl = pkt.ttl
                prev_loc = src
                for loc, dist in q.locations:
                    if loc == src:
                        continue
                    try:
                        # Get the copy (see the __eq__ overload)
                        copy = traffic_slices[traffic_slices[loc].index(pkt)]
                        # Check TTL condition
                        decrease = prev_ttl - copy.ttl
                        if decrease != dist:
                            LOG.warning('TTL mismatch for %s: saw a decrease'
                                        ' of %d from %d to %d (expected %d)',
                                        q, decrease, prev_loc, loc, dist)
                        prev_ttl = copy.ttl
                        prev_loc = loc
                        # register the match
                        seen[loc] = copy
                    except ValueError:
                        seen[loc] = None
                matches[pkt] = seen
                if seen[dst] is None:
                    lost += 1
                else:  # Packet seen at both ends
                    if len(seen) + 1 < len(q.locations):
                        load_balanced += 1  # Disappeared then reappeared
            LOG.info('Statistics for %s on %s: entered=%d, exited=%d, lost=%d,'
                     ' load-balanced=%d', q.name, q.subregions, len(matches),
                     len(matches) - lost - load_balanced, lost, load_balanced)


def _complete_graph(db, net, collector_name):
    g = net.graph
    # Register all routers/egresses
    for node, prop in db.iteritems():
        if prop.get('is_egress', False):
            g.register_egress(node)
        elif node != collector_name:
            g.register_router(node)
    # Brute-force to identify all links
    for u, v in itertools.combinations(db.keys(), 2):
        if v not in db[u]:
            continue
        base = db[u][v]
        # Extract link properties
        uv_prop = {g.ADDRESS_KEY: base['ip'].split('/')[0],
                   g.IFNAME_KEY: base['name']}
        base = db[v][u]
        vu_prop = {g.ADDRESS_KEY: base['ip'].split('/')[0],
                   g.IFNAME_KEY: base['name']}
        g.register_link(u, v, uv_prop=uv_prop, vu_prop=vu_prop)
    net.update_router_addresses()


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Start a Stroboscope collector")
    parser.add_argument('--db', default=None, required=True,
                        help='The network topology db to fetch addresses from')
    parser.add_argument('--name', default=None, required=True,
                        help='The collector node name')
    parser.add_argument('--req', default=None, required=True,
                        help='Requirements file name')
    parser.add_argument('--ssh-key', default=None, required=True,
                        help='SSH key to use to log into routers')
    return parser


def _parse_args(parser):
    return parser.parse_args()


def _main():
    args = _parse_args(_build_parser())
    db = TopologyDB(db=args.db)
    collector_itf = db._network[args.name]['interfaces'][0]
    collect_address = db._network[args.name][collector_itf]['ip'].split('/')[0]
    c = Collector(measurement_processor=Analyzer(),
                  ssh_keypath=args.ssh_key, ssh_username='root',
                  phys_dst=collect_address)
    _complete_graph(db._network, c.net, args.name)
    c.load_requirements(args.req)
    join()


if __name__ == '__main__':
    _main()
