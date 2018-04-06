import os
import logging

from stroboscope.network_database import NetGraph

from . import sanitize_graph

LOG = logging.getLogger(__name__)


def get_topo(name):
    """Return the network graph for the named topology"""
    filename = os.path.join(os.path.dirname(__file__),
                            'rocketfuel',
                            'as%s' % name)
    LOG.debug('Reading graph from %s', filename)
    g = NetGraph()
    g.name = name
    try:
        with open(filename, 'r') as f:
            for line in f.readlines():
                u, v, c = _to_weighted_edge(line)
                g.register_link(u, v, cost=c)
    except IOError as e:
        LOG.error('Could not open the rocketfuel topology for AS %s: %s',
                  name, e)
        return None
    for n in g:
        g.register_router(n)
    return sanitize_graph(g)


def _to_weighted_edge(x):
    u, v, c = x.strip(' \r\t\n').split(' ')
    return u, v, int(float(c))
