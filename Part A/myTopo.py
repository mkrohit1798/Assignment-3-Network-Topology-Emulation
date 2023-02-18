from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.util import dumpNodeConnections
from mininet.node import OVSController


class LinuxRouter(Node):

    def config(self, **params): # enable forwarding
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self): # disable forwarding
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


class NetworkTopo(Topo):
    "A topology of 4 routers and 2 hosts"

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

def nodeDefaultPath(router, IPAddr, port): # function for configuring static routes to nodes
    mnet.get(router).cmd('ip route add default via ' + IPAddr + ' dev ' + port)

def enableNodeForwarding(node): # enabling nodes to forward packets
    mnet.get(node).cmd("sysctl net.ipv4.ip_forward=1")
    
def routerCMD(router, IPAddr, port): # function to assign Ip address to each node in the topology
    mnet.get(router).cmd('ip addr add ' + IPAddr + ' dev ' + port)      

def run():
    nodes = ['host_1', 'router_1', 'router_2', 'router_3', 'router_4', 'host_2']

    topo = NetworkTopo()
    global mnet
    mnet = Mininet(topo=topo, controller=OVSController)
    mnet.start()
    
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

    
    nodeDefaultPath('host_1', '152.0.1.2', 'host_1-eth0')
    nodeDefaultPath('host_2', '157.0.1.2', 'host_2-eth0')

    mnet.get('router_1').cmd('ip route add 156.0.0.0/16 via 154.0.1.2 dev router_1-eth2')
    nodeDefaultPath('router_1', '153.0.1.2', 'router_1-eth1')

    mnet.get('router_2').cmd('ip route add 152.0.0.0/16 via 153.0.1.1 dev router_2-eth0')
    mnet.get('router_2').cmd('ip route add 154.0.0.0/16 via 153.0.1.1 dev router_2-eth0')
    nodeDefaultPath('router_2', '155.0.1.2', 'router_2-eth1')

    mnet.get('router_3').cmd('ip route add 152.0.0.0/16 via 154.0.1.1 dev router_3-eth0')
    mnet.get('router_3').cmd('ip route add 153.0.0.0/16 via 154.0.1.1 dev router_3-eth0')
    nodeDefaultPath('router_3', '156.0.1.2', 'router_3-eth1')

    mnet.get('router_4').cmd('ip route add 154.0.0.0/16 via 156.0.1.1 dev router_4-eth2')
    nodeDefaultPath('router_4', '155.0.1.1', 'router_4-eth1')

    for n in nodes:
        info('*** Routing Table on %s\n' % n)
        info(mnet[n].cmd('route'))
    
    CLI(mnet)
    mnet.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
