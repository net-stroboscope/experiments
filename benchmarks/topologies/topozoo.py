import logging
import os

import networkx as nx

from stroboscope.network_database import NetGraph
from . import sanitize_graph

LOG = logging.getLogger(__name__)


def get_topo(name):
    """Return the network graph for the named topology"""
    filename = os.path.join(os.path.dirname(__file__),
                            'topologyzoo',
                            '%s.gml' % name)
    logging.debug('Reading graph from %s', filename)
    content = nx.read_gml(filename, label='id')
    g = NetGraph()
    g.name = name
    for n in content:
        g.register_router(n)
    for u, v in content.edges_iter():
        g.register_link(u, v)
    return sanitize_graph(g)
