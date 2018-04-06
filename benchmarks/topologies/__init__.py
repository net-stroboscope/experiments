import logging
import random

import networkx as nx


LOG = logging.getLogger(__name__)


def sanitize_graph(g):
    """Make sure that g can be used for benchmarking."""
    LOG.debug('Sanitizing %s (%d nodes, %d edges)', g.name,
              g.number_of_nodes(), g.number_of_edges())
    g.remove_edges_from(g.selfloop_edges())
    LOG.debug('Removed selfloops: %d nodes, %d edges', g.number_of_nodes(),
              g.number_of_edges())
    connected_component = max(nx.strongly_connected_components(g), key=len)
    g.remove_nodes_from(set(g.nodes_iter()).difference(connected_component))
    LOG.debug('Kept only the largest strongly connected component: '
              '%d nodes, %d edges', g.number_of_nodes(), g.number_of_edges())
    g.build_spt()
    g.net_diameter = max(len(p[0])
                         for s, d in g.spt.iteritems()
                         for p in d.itervalues())
    egresses = random.sample(g.nodes(), int(len(g) * .3))
    LOG.debug('Registering egresses: %s', egresses)
    for e in egresses:
        g.register_egress(e)
    LOG.info('Built graph for %s (%d nodes, %d edges, diameter: %d)',
             g.name,
             g.number_of_nodes(),
             g.number_of_edges(),
             g.net_diameter)
    return g
