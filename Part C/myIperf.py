from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, OVSController
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.util import dumpNodeConnections
from mininet.link import TCLink
from contextlib import contextmanager
import os
import time

class LinuxRouter(Node):

    @contextmanager
    def in_router_dir(self):
        working_directory = os.getcwd()
        self.cmd('cd %s' % self.name)
        yield
        self.cmd('cd %s' % working_directory)

    def config(self, **params): # enable forwarding and BIRD
        super(LinuxRouter, self).config(**params)

        self.cmd('sysctl net.ipv4.ip_forward=1')

        with self.in_router_dir():
            self.cmd('bird -l')

    def terminate(self): # terminate BIRD and disable forwarding
        self.cmd('sysctl net.ipv4.ip_forward=0')

        with self.in_router_dir():
            self.cmd('birdc -l down')

        super(LinuxRouter, self).terminate()


class NWTopology(Topo):
    "A topology of 4 routers and 2 hosts"

    def build(self, **_opts):
        router_1 = self.addNode('router_1', cls=LinuxRouter, ip='152.0.1.2/16')
        router_2 = self.addNode('router_2', cls=LinuxRouter, ip='153.0.1.2/16')
        router_3 = self.addNode('router_3', cls=LinuxRouter, ip='154.0.1.2/16')
        router_4 = self.addNode('router_4', cls=LinuxRouter, ip='157.0.1.2/16')

        host_1 = self.addHost('host_1', ip='152.0.1.1/16')
        host_2 = self.addHost('host_2', ip='157.0.1.1/16')

        self.addLink(host_1, router_1, bw=100, delay='30ms')
        self.addLink(host_2, router_4, bw=100, delay='30ms')
        
        self.addLink(router_1, router_2, bw=100, delay='30ms')
        self.addLink(router_1, router_3, bw=100, delay='30ms')
        self.addLink(router_2, router_4, bw=100, delay='30ms')
        self.addLink(router_3, router_4, bw=100, delay='30ms')

        


def run():
    topo = NWTopology()
    global mnet
    mnet = Mininet(topo=topo, link=TCLink)
    mnet.start()

    current_directory = os.getcwd()
    print(current_directory)

    info('** Dumping hosts connections\n')
    dumpNodeConnections(mnet.hosts)

    # enabling packet forwarding
    enableNodeForwarding("router_1")
    enableNodeForwarding("router_2")
    enableNodeForwarding("router_3")
    enableNodeForwarding("router_4")
    enableNodeForwarding("host_1")
    enableNodeForwarding("host_2")

    # assign IP addresses to routers
    routerCMD('router_1', '153.0.1.1/16', 'router_1-eth1')
    routerCMD('router_1', '154.0.1.1/16', 'router_1-eth2')
    routerCMD('router_2', '155.0.1.1/16', 'router_2-eth1')
    routerCMD('router_3', '156.0.1.1/16', 'router_3-eth1')
    routerCMD('router_4', '155.0.1.2/16', 'router_4-eth1')
    routerCMD('router_4', '156.0.1.2/16', 'router_4-eth2')

    

    hosts = ['host_1', 'host_2']
    for h in hosts:        
        mnet[h].cmd('cd '+ current_directory + '/' + h)
        mnet[h].cmd('bird -l')

    info('** Standby for 6 seconds for routing table update...**\n')
    time.sleep(6)

    # set delay for routers
    routerDelay('router_1', 'router_1-eth0')
    routerDelay('router_1', 'router_1-eth1')
    routerDelay('router_1', 'router_1-eth2')

    routerDelay('router_2', 'router_2-eth0')
    routerDelay('router_2', 'router_2-eth1')

    routerDelay('router_3', 'router_3-eth0')
    routerDelay('router_3', 'router_3-eth1')

    routerDelay('router_4', 'router_4-eth0')
    routerDelay('router_4', 'router_4-eth1')
    routerDelay('router_4', 'router_4-eth2')
    
    # Set burst limit for routers
    routerBurst('router_1', 'router_1-eth0')
    routerBurst('router_1', 'router_1-eth1')
    routerBurst('router_1', 'router_1-eth2')
    
    routerBurst('router_2', 'router_2-eth0')
    routerBurst('router_2', 'router_2-eth1')
    
    routerBurst('router_3', 'router_3-eth0')
    routerBurst('router_3', 'router_3-eth1')
    
    routerBurst('router_4', 'router_4-eth0')
    routerBurst('router_4', 'router_4-eth1')
    routerBurst('router_4', 'router_4-eth2')
    
    mnet.pingAll()

    info('\n')
    info('** Starting IPerf test with host_2 as server')
    mnet.get('host_2').cmd('iperf3 -s -D')

    info('** Starting IPerf test with host_1 as client')
    info('** Run the following commands in Mininet CLI:\n')
    
    info('host_1 iperf3 -c 157.0.1.1 -b 100m -w 10k -t 10\n')
    info('host_1 iperf3 -c 157.0.1.1 -b 100m -w 5m -t 10\n')
    info('host_1 iperf3 -c 157.0.1.1 -b 100m -w 25mb -t 10\n')

    CLI(mnet) # command line interface to enter the commands above

    for h in hosts:
        mnet[h].cmd('cd '+ current_directory + '/' + h)
        mnet[h].cmd('birdc -l down')
    mnet.stop()

def enableNodeForwarding(node): # enabling nodes to forward packets
    mnet.get(node).cmd("sysctl net.ipv4.ip_forward=1") 
    
def routerCMD(router, IPAddr, port): # function to assign Ip address to each node in the topology
    mnet.get(router).cmd('ip addr add ' + IPAddr + ' dev ' + port)
    
def routerBurst(router, port): # function to configure the burst limit for each router
    mnet.get(router).cmd('tc qdisc add dev ' + port + ' root tbf burst 1000000')
    
def routerDelay(router, port): # function to configure delay for each router
    mnet.get(router).cmd('tc qdisc add dev ' + port + ' root netem delay 30ms')

if __name__ == '__main__':
    setLogLevel('info')
    run()
