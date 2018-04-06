"""
This modules define heuristics used on the graph for the benchmarks.

i.e. egresses locations.
"""
import random
import abc
import itertools
import logging

import networkx as nx

LOG = logging.getLogger(__name__)


class Heuristic(object):
    @classmethod
    def heuristics(cls):
        return {klass.KEY: klass() for klass in cls.__subclasses__()}


# Egress seelection heuristics


class Egresses(Heuristic):
    __metaclass__ = abc.ABCMeta

    def __call__(self, graph, **kw):
        _egresses = self.egresses_for(graph, **kw)
        LOG.info('Registering egresses: %s', _egresses)
        for e in _egresses:
            graph.register_egress(e)

    @abc.abstractmethod
    def egresses_for(self, g, **kw):
        """Return the set of egresses to use on the given graph
        :param g: The graph on which egresses should be defined"""


class LowDegressEgresses(Egresses):
    """Egresses are nodes whose out degree is greater or equal to a given
    threshold"""

    KEY = 'low_degree'

    @staticmethod
    def egresses_for(g, degree=2, percentage=.25, **kw):
        egresses = [n for n, d in g.out_degree_iter() if d <= degree]
        if len(egresses) > len(g) * percentage:
            return RandomEgresses.egresses_for(g, percentage=percentage,
                                               n=egresses)
        return egresses


class RandomEgresses(Egresses):
    """Egresses are randomly selected on the graph"""

    KEY = 'random'

    @staticmethod
    def egresses_for(g, percentage=.25, n=None, **kw):
        nodes = g.nodes() if not n else n
        return random.sample(nodes, int(percentage * len(nodes)))


# Path selection heristics


class Path(Heuristic):
    __metaclass__ = abc.ABCMeta

    def __call__(self, g, **kw):
        egresses = g.egresses
        if not egresses:
            __e = random.choice(g.nodes())
            egresses = [__e, __e]
        for u, v in itertools.combinations(g.egresses, 2):
            for p in self.path(g, src=u, dst=v, **kw):
                if len(p) > 2 and len(p) <= kw.get('maxlen', 20):
                    yield p

    @abc.abstractmethod
    def path(self, g, src, dst, maxlen=None):
        """Return a set of paths on the given graph
        :param g: The graph on which paths should be defined
        :param src: restrict the paths to those starting at src
        :param dst: restrict the paths to those ending at dst
        :param maxlen: (opt) the maximal length of the path"""


class ShortestPath(Path):
    """Paths are following the shortest path on the graph"""

    KEY = 'spt'

    @staticmethod
    def path(g, src, dst, **kw):
        return g.spt[src][dst]


class PerturbedSPT(Path):
    """Path follow up to %% of the spt"""

    KEY = 'perturb'

    @staticmethod
    def path(g, src, dst, perturb=None, maxlen=None, **kw):
        nlen = int(len(g.spt[src][dst][0]) * (1 + perturb))
        if nlen > maxlen:
            return []
        return RandomPath.path(g, src, dst, maxlen=nlen)


class RandomPath(Path):
    """Find a random path between two point"""

    KEY = 'random'

    @staticmethod
    def path(g, src, dst, maxlen=None, **kw):
        return nx.all_simple_paths(g, src, dst, cutoff=maxlen)


class Region(Path):
    """Define a cluster of nodes containing two points"""

    KEY = 'region'

    @staticmethod
    def path(g, src, dst, maxlen=None, region_count=None, **kw):
        for _ in xrange(region_count):
            region = set(g.spt[src][dst][0])
            r_nodes = set(itertools.chain.from_iterable(
                g.neighbors_iter(n) for n in region)).difference(region)
            while len(region) < maxlen and r_nodes:
                n = random.choice(list(r_nodes))
                r_nodes.remove(n)
                region.add(n)
                r_nodes.update(nei for nei in g.neighbors_iter(n)
                               if nei not in region)
            yield region


class Island(Path):
    """Define a random cluster"""

    KEY = 'island'

    @staticmethod
    def path(g, src, dst, maxlen=None, region_count=None, **kw):
        for _ in xrange(region_count):
            region = set([random.choice(g.nodes())])
            left = region.copy()
            explored = set()
            while len(region) < maxlen and len(region) < len(g) and left:
                n = left.pop()
                nei = set(g.neighbors_iter(n))
                region.update(nei)
                explored.add(n)
                left.update(nei.difference(explored))
            yield region
