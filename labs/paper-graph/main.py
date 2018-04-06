#!/usr/bin/python2
"""Graph definition/instantiation, we directly extract it from the tests."""
import os
import argparse
import time
import subprocess as sp


from mininet.node import Host
from mininet.log import lg as MNLOG

from ipmininet.iptopo import IPTopo
from ipmininet.ipnet import IPNet
from ipmininet.cli import IPCLI
from ipmininet.topologydb import TopologyDB
from ipmininet.router.config import SSHd, OSPF, RouterConfig
import ipmininet.router.config.sshd as ssh

from stroboscope.tests.conftest import _paper_graph

MNLOG.setLogLevel('debug')

COLLECTOR_EXE = os.path.join(os.path.dirname(__file__), 'collector.py')
COLLECTOR_ID = 'collector'
TOPO_DB = 'net.db'
REQ_FILE = '/tmp/stroboscope_paper_lab.req'
FLOW_COUNT = 10
SRC_EXE = os.path.join(os.path.dirname(__file__), 'source.py')


class _CLI(IPCLI):
    def do_start_collector(self, line=''):
        """Start the Stroboscope collector."""
        cltr = self.mn[COLLECTOR_ID]
        cltr.start_collector(fn=cltr.cmd)


class _PaperGraph(IPTopo):
    """Setup the graph presented in the paper."""
    def __init__(self, *a, **kw):
        self.egresses = []
        super(_PaperGraph, self).__init__(*a, **kw)

    def build(self, *args, **kw):
        """The graph is as described in the paper.

        See 'Stroboscope: Declarative network Monitoring on a Budget',
        in proc. NSDI'18, fig 2a"""
        g = _paper_graph()
        config = (RouterConfig, {'daemons': [SSHd, OSPF]})
        for r in g.nodes_iter():
            self.addRouter(r, config=config)
        for e in g.egresses:
            self.egresses.append(e)
            self.g.node[e]['egress'] = True
        for u, v in g.edges_iter():
            self.addLink(u, v)
        self.addLink('U', self.addNode(COLLECTOR_ID, cls=_Collector))
        self.addLink('A', self.addNode('source', cls=_Source))
        self.addLink('D', self.addNode('sink', cls=_Sink))
        super(_PaperGraph, self).build(*args, **kw)


class _Collector(Host):
    """Start up our custom collector instance."""

    def __init__(self, *a, **kw):
        super(_Collector, self).__init__(*a, **kw)
        self.collector = None

    def start_collector(self, fn=None):
        """Start the collector instance."""
        if not fn:
            fn = self.popen
        self.collector = fn('python', COLLECTOR_EXE,
                            '--db', TOPO_DB,
                            '--name', COLLECTOR_ID,
                            '--req', REQ_FILE,
                            '--ssh-key', ssh.KEYFILE,
                            stdout=None, stderr=None)

    def terminate(self):
        if self.collector:
            try:
                self.collector.terminate()
            except OSError:
                pass
            self.collector = None


class _Source(Host):
    """Start up a process that will generate traffic."""

    def __init__(self, *a, **kw):
        super(_Source, self).__init__(*a, **kw)
        self.src = None

    def start_src(self, dst, origin, flow_count=50):
        """Start flooding the dest prefix."""
        self.src = self.popen('python', SRC_EXE,
                              '--dst', dst,
                              '--origin', origin,
                              '--count', str(flow_count),
                              stdout=None, stderr=None)

    def terminate(self):
        if self.src:
            try:
                self.src.terminate()
            except OSError:
                pass
            self.src = None


class _Sink(Host):

    def filter_source(self, origin):
        """Start dropping packets coming from the source."""
        self.cmd('iptables', '-A', 'INPUT', '-s', origin, '-j', 'DROP')


class HashPolicySetter(object):
    """Adapts the fib_multipath_hash_policy settings in newer kernel"""

    SYSCTL_KEY = 'fib_multipath_hash_policy'

    def __init__(self):
        """Store old sysctl value"""
        try:
            self.old_val = sp.check_output(['sysctl', self.SYSCTL_KEY])
        except sp.CalledProcessError:
            self.old_val = None

    def set_policy(self, val):
        """Change the sysctl policy value."""
        try:
            sp.call(['sysctl', '%s=%s' % (self.SYSCTL_KEY, val)])
        except sp.CalledProcessError:
            pass

    def __enter__(self):
        """ and set hashing to L4-aware."""
        self.set_policy('1')

    def __exit__(self, *a):
        self.restore()

    def restore(self):
        """Restore the sysctl value."""
        if self.old_val is not None:
            self.set_policy(self.old_val)
            self.old_val = None

    def __del__(self):
        self.restore()


def _main(autostart=False):
    graph = _PaperGraph()
    net = IPNet(topo=graph, use_v6=False)
    net.start()
    db = TopologyDB(net=net)
    for e in net.topo.egresses:
        db._network[e]['is_egress'] = True
    db.save(TOPO_DB)
    sink = net['sink']
    source = net['source']
    sink_addr = sink.IP()
    src_addr = source.IP()
    MNLOG.debug('Source is at ', src_addr, 'sink is at ', sink_addr, '\n')
    with open(REQ_FILE, 'w') as f:
        f.write('MIRROR {sink} ON [A B C D]\n'
                'CONFINE {sink} ON [A B L C D]\n'
                'USING {cnt} M DURING 500ms'.format(sink=sink_addr,
                                                    cnt=FLOW_COUNT))
    MNLOG.info('Starting sink')
    sink.filter_source(src_addr)
    MNLOG.info('Starting source')
    source.start_src(sink_addr, src_addr, FLOW_COUNT)
    time.sleep(5)
    if autostart:
        MNLOG.info('Starting collector')
        net[COLLECTOR_ID].start_collector()
    _CLI(net)
    net.stop()
    if os.path.exists(REQ_FILE):
        os.unlink(REQ_FILE)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--autostart', default=False, action='store_true',
                        help='Autostart the collector')
    args = parser.parse_args()
    with HashPolicySetter():
        _main(autostart=args.autostart)
