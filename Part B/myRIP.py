from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.util import dumpNodeConnections
from mininet.link import TCLink
from mininet.node import OVSController
from contextlib import contextmanager
import os
import time


class LinuxRouter(Node):

    @contextmanager
    def in_router_dir(self):
        working_dir = os.getcwd()
        self.cmd('cd %s' % self.name)
        yield
        self.cmd('cd %s' % working_dir)

    def config(self, **params): #method to enable BIRD and forwarding
        super(LinuxRouter, self).config(**params)

       
        self.cmd('sysctl net.ipv4.ip_forward=1')

        
        with self.in_router_dir():
            self.cmd('bird -l')

    def terminate(self): #method to disable forwarding and terminate BIRD
        self.cmd('sysctl net.ipv4.ip_forward=0')

        with self.in_router_dir():
            self.cmd('birdc -l down')

        super(LinuxRouter, self).terminate()





class NWTopology(Topo):

    def build(self, **_opts):
        
        router_1 = self.addNode('router_1', cls=LinuxRouter, ip='152.0.1.2/16')
        router_2 = self.addNode('router_2', cls=LinuxRouter, ip='153.0.1.2/16')
        router_3 = self.addNode('router_3', cls=LinuxRouter, ip='154.0.1.2/16')
        router_4 = self.addNode('router_4', cls=LinuxRouter, ip='157.0.1.2/16')

        
        host_1 = self.addHost('host_1', ip='152.0.1.1/16')
        host_2 = self.addHost('host_2', ip='157.0.1.1/16')

        
        self.addLink(host_1, router_1)
        self.addLink(host_2, router_4)
        
        self.addLink(router_1, router_2)
        self.addLink(router_1, router_3)
        self.addLink(router_2, router_4)
        self.addLink(router_3, router_4)

        

def run():
    topo = NWTopology()
    global mnet
    mnet = Mininet(topo=topo, link=TCLink)
    mnet.start()

    current_directory = os.getcwd()
    print(current_directory)
    
    info('** Dumping host connections\n')
    dumpNodeConnections(mnet.hosts)

    enableNodeForwarding("router_1")
    enableNodeForwarding("router_2")
    enableNodeForwarding("router_3")
    enableNodeForwarding("router_4")
    enableNodeForwarding("host_1")
    enableNodeForwarding("host_2")

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

    nodes = ['host_1', 'router_1', 'router_2', 'router_3', 'router_4', 'host_2']
    for node in nodes:
        info('*** Routing Table on %s\n' % node)
        info(mnet[node].cmd('route'))

    info('** Standby for 6 seconds for routing table update..\n')
    time.sleep(6)

    mnet.pingAll()
    CLI(mnet)

    for h in hosts:
        mnet[h].cmd('cd '+ current_directory + '/' + h)
        mnet[h].cmd('birdc -l down')
    mnet.stop()

def enableNodeForwarding(node): # enabling nodes to forward packets
    mnet.get(node).cmd("sysctl net.ipv4.ip_forward=1")
    
def routerCMD(router, IPAddr, port): # function to assign Ip address to each node in the topology
    mnet.get(router).cmd('ip addr add ' + IPAddr + ' dev ' + port)

if __name__ == '__main__':
    setLogLevel('info')
    run()
