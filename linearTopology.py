#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import UserSwitch, OVSKernelSwitch, Controller, RemoteController
from mininet.topo import Topo
from mininet.log import lg
from mininet.util import irange, quietRun
from mininet.link import TCLink
from functools import partial
from mininet.cli import CLI

import sys
flush = sys.stdout.flush

class LinearTestTopo( Topo ):
    "Topology for a string of N hosts and N-1 switches."

    def __init__( self, N, **params ):

        # Initialize topology
        Topo.__init__( self, **params )

        # Create switches and hosts
        hosts = [ self.addHost( 'h%s' % h )
                  for h in irange( 1, N ) ]
        switches = [ self.addSwitch( 's%s' % s )
                     for s in irange( 1, N - 1 ) ]

        # Wire up switches
        last = None
        for switch in switches:
            if last:
                self.addLink( last, switch )
            last = switch

        # Wire up hosts
        self.addLink( hosts[ 0 ], switches[ 0 ] )
        for host, switch in zip( hosts[ 1: ], switches ):
            self.addLink( host, switch )


def linearBandwidthTest( lengths ):

    "Check bandwidth at various lengths along a switch chain."

    results = {}
    switchCount = max( lengths )
    hostCount = switchCount + 1

    switches = { 'reference user': UserSwitch,
                 'Open vSwitch kernel': OVSKernelSwitch }

    # UserSwitch is horribly slow with recent kernels.
    # We can reinstate it once its performance is fixed
    del switches[ 'reference user' ]

    topo = LinearTestTopo( hostCount )

    # Select TCP Reno
    output = quietRun( 'sysctl -w net.ipv4.tcp_congestion_control=reno' )
    assert 'reno' in output

    for datapath in switches.keys():
        print "*** testing", datapath, "datapath"
        Switch = switches[ datapath ]
        results[ datapath ] = []
        link = partial( TCLink, delay='1ms' )
        net = Mininet( topo=topo, switch=Switch,
                       controller=RemoteController, waitConnected=True,
                       link=link )
        net.start()
        print "*** testing basic connectivity"
        for n in lengths:
	    print "*** first ping***"
            net.pingFull( [ net.hosts[ 0 ], net.hosts[ n ] ] )
	    print "*** second ping***"
	    net.pingFull( [ net.hosts[ 0 ], net.hosts[ n ] ] )
        print "*** testing bandwidth"
        for n in lengths:
	    print "***h1 -> h"+str(n)
            src, dst = net.hosts[ 0 ], net.hosts[ n ]
            # Try to prime the pump to reduce PACKET_INs during test
            # since the reference controller is reactive
            #src.cmd( 'telnet', dst.IP(), '5001' )
            print "testing", src.name, "<->", dst.name,
            bandwidth = net.iperf( [ src, dst ], seconds=10 )
            print bandwidth
            flush()
            #results[ datapath ] += [ ( n, bandwidth ) ]
	    print "***h1 -> h2"
            src, dst = net.hosts[ 0 ], net.hosts[ 1 ]
            # Try to prime the pump to reduce PACKET_INs during test
            # since the reference controller is reactive
            #src.cmd( 'telnet', dst.IP(), '5001' )
            print "testing", src.name, "<->", dst.name,
            bandwidth = net.iperf( [ src, dst ], seconds=10 )
            print bandwidth
            flush()
            #results[ datapath ] += [ ( n, bandwidth ) ]
	print "Starting a web server on h1 host: python -m SimpleHTTPServer 80 >& /tmp/http.log &"
	#print net.hosts[ 0 ].cmd('ping -c 2', net.hosts[ 1 ].IP())
	print net.hosts[ 0 ].cmd( 'python -m SimpleHTTPServer 80 >& /tmp/http.log &' )
	print "Http Request from h2 to h1: h2 wget h1"
	#print net.hosts[ 1 ].cmd( 'wget http://10.0.0.1') 
	CLI(net)        
	net.stop()
    '''
    for datapath in switches.keys():
        print
        print "*** Linear network results for", datapath, "datapath:"
        print
        result = results[ datapath ]
        print "SwitchCount\tiperf Results"
        for switchCount, bandwidth in result:
            print switchCount, '\t\t',
            print bandwidth[ 0 ], 'server, ', bandwidth[ 1 ], 'client'
        print
    print
    '''

if __name__ == '__main__':
    lg.setLogLevel( 'info' )
    #sizes = [ 1, 10, 20, 40, 60, 80, 100 ]
    sizes = [ 27]
    print "*** Running Linear Topology", sizes
    linearBandwidthTest( sizes  )
