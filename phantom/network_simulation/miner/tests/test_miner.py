import uuid
import pytest

from phantom.dag import Block
from phantom.phantom import GreedyPHANTOM, CompetingChainGreedyPHANTOM
from phantom.network_simulation import Miner, MaliciousMiner, Network


MINER = 'miner'
MALICIOUS_MINER = 'malicious_miner'


def pytest_generate_tests(metafunc):
    if MINER in metafunc.fixturenames:
        metafunc.parametrize(MINER, [MINER, MALICIOUS_MINER], indirect=True)


@pytest.fixture(scope="module")
def miner(request):
    if request.param == MINER:
        miner = Miner(Network.get_random_ip(), GreedyPHANTOM(), TestMiner.DEFAULT_MAX_NEIGHBOR_NUM, 1 << 20)
    elif request.param == MALICIOUS_MINER:
        miner = MaliciousMiner(Network.get_random_ip(), CompetingChainGreedyPHANTOM(), float('inf'), 1 << 20)
    else:
        raise ValueError("invalid internal test config")
    Network(total_network_dag=GreedyPHANTOM()).add_miner(miner, 0)
    return miner


@pytest.fixture(scope="module")
def genesis():
    return Block()


class TestMiner:
    """
    Test suite for the miner class.
    """

    # The default max neighbor num
    DEFAULT_MAX_NEIGHBOR_NUM = 5

    def test_init(self, miner):
        """
        Tests adding the genesis block.
        """
        assert len(miner._network) == 1
        assert miner._network[miner.get_name()] == miner

    def test_adding_genesis(self, miner, genesis):
        """
        Tests adding the genesis block.
        """
        assert hash(genesis) in miner

    def test_mining_block(self, miner, genesis):
        """
        Tests mining a block.
        """
        block = miner.mine_block()

        assert block is not None
        assert hash(block) in miner
        assert block.get_parents() == {hash(genesis)}

        assert hash(block) in miner._network._total_network_dag
        assert miner._network._total_network_dag[hash(block)] == block

    def test_blocks_with_missing_parents(self, miner, genesis):
        """
        Tests adding a fork with missing parents.
        """
        # Creating a fork that looks like this:
        # 0 <- 1 <- 2 <- 3
        # 0 <- 1 <- 4 <- 5
        block1 = Block(uuid.uuid4().int, {hash(genesis)})
        block2 = Block(uuid.uuid4().int, {hash(block1)})
        block3 = Block(uuid.uuid4().int, {hash(block2)})
        block4 = Block(uuid.uuid4().int, {hash(block1)})
        block5 = Block(uuid.uuid4().int, {hash(block4)})

        # Add the blocks in the following order:
        # 3 (and then the miner will fetch 2)
        # 4 (and then the miner will fetch 1)
        # 5
        # 1 (and then the miner will add 4, 5)
        # 2 (and then the miner will add 3)

        assert miner.add_block(block3) is False
        assert hash(block3) not in miner

        assert miner.add_block(block4) is False
        assert hash(block4) not in miner

        assert miner.add_block(block5) is False
        assert hash(block5) not in miner

        assert miner.add_block(block1) is True
        assert hash(block1) in miner

        assert hash(block4) in miner
        assert hash(block5) in miner
        assert hash(block2) not in miner
        assert hash(block3) not in miner

        assert miner.add_block(block2) is True
        assert hash(block2) in miner
        assert hash(block3) in miner
