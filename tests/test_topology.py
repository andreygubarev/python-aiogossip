from aiogossip.topology import Topology


def test_topology_initialization():
    topology = Topology()
    assert topology.nodes == []


def test_topology_set():
    topology = Topology()
    peers = [("localhost", 8000), ("localhost", 8001)]
    topology.set(peers)
    assert topology.nodes == peers


def test_topology_add():
    topology = Topology()
    peer = ("localhost", 8000)
    topology.add(peer)
    assert peer in topology.nodes


def test_topology_remove():
    topology = Topology()
    peer = ("localhost", 8000)
    topology.add(peer)
    topology.remove(peer)
    assert peer not in topology.nodes


def test_topology_get():
    topology = Topology()
    peers = [("localhost", 8000), ("localhost", 8001)]
    topology.set(peers)
    assert topology.get() == peers


def test_topology_len():
    topology = Topology()
    peers = [("localhost", 8000), ("localhost", 8001)]
    topology.set(peers)
    assert len(topology) == 2


def test_topology_contains():
    topology = Topology()
    peer = ("localhost", 8000)
    topology.add(peer)
    assert peer in topology


def test_topology_iter():
    topology = Topology()
    peers = [("localhost", 8000), ("localhost", 8001)]
    topology.set(peers)
    for peer in topology:
        assert peer in peers


def test_topology_get_sample():
    topology = Topology()
    peers = [("localhost", 8000), ("localhost", 8001), ("localhost", 8002)]
    topology.set(peers)
    sample = topology.get(sample=2)
    assert len(sample) == 2
    for peer in sample:
        assert peer in peers
