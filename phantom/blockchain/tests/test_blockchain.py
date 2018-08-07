import pytest

from phantom.dag import Block
from phantom.blockchain import Blockchain


class TestBlockchain:
    """
    Test suite for the blockchain class.
    """

    @pytest.fixture(scope="module")
    def blockchain(self):
        return Blockchain()

    @pytest.fixture(scope="module")
    def genesis(self):
        return Block()

    def test_constructor(self, blockchain):
        """
        Tests the constructor.
        """
        assert len(blockchain._G) == 0
        assert blockchain._leaves == set()
        assert blockchain.get_virtual_block_parents() == set()
        assert blockchain._get_chain() == {}
        assert blockchain._longest_chain == set()

    def test_adding_genesis(self, blockchain, genesis):
        """
        Tests adding the genesis block.
        """
        assert blockchain.get_depth(hash(genesis)) == -float('inf')

        blockchain.add(genesis)
        assert hash(genesis) in blockchain
        assert blockchain[hash(genesis)] == genesis
        assert blockchain._leaves == {hash(genesis)}
        assert blockchain.get_virtual_block_parents() == {hash(genesis)}
        assert blockchain._G.node[hash(genesis)][Blockchain._CHAIN_LENGTH_KEY] == 1
        assert blockchain._get_chain() == {hash(genesis): 0}
        assert blockchain._longest_chain == {hash(genesis)}
        assert blockchain.get_depth(hash(genesis)) == 0

    @pytest.fixture(scope="module")
    def block1(self, genesis):
        # graph should look like this: 0 <- 1
        return Block(hash(genesis) + 1, {hash(genesis)})

    @pytest.fixture(scope="module")
    def block2(self, genesis, block1):
        # graph should look like this: 0 <- 2
        return Block(hash(block1) + 1, {hash(genesis)})

    @pytest.fixture(scope="module")
    def block3(self, block1, block2):
        # graph should look like this: 0 <- 1 <- 3
        return Block(hash(block2) + 1, {hash(block1)})

    @pytest.mark.data_structure
    def test_adding_multiple_blocks(self, blockchain, genesis, block1, block2, block3):
        """
        Creates a small blockchain and checks that adding multiple blocks works correctly.
        """
        assert blockchain.get_depth(hash(block1)) == -float('inf')
        assert blockchain.get_depth(hash(block2)) == -float('inf')
        assert blockchain.get_depth(hash(block3)) == -float('inf')

        blockchain.add(block1)
        # graph should look like this:
        # 0 <- 1
        assert hash(block1) in blockchain
        assert blockchain[hash(block1)] == block1
        assert blockchain._leaves == {hash(block1)}
        assert blockchain.get_virtual_block_parents() == {hash(block1)}
        assert blockchain._G.node[hash(genesis)][Blockchain._CHAIN_LENGTH_KEY] == 1
        assert blockchain._G.node[hash(block1)][Blockchain._CHAIN_LENGTH_KEY] == 2
        assert blockchain._get_chain() == {hash(genesis): 0, hash(block1): 1}
        assert blockchain._longest_chain == {hash(genesis), hash(block1)}
        assert blockchain.is_a_before_b(hash(genesis), hash(block1)) is True
        assert blockchain.get_depth(hash(genesis)) == 1
        assert blockchain.get_depth(hash(block1)) == 0
        assert blockchain.get_depth(hash(block2)) == -float('inf')
        assert blockchain.get_depth(hash(block3)) == -float('inf')

        blockchain.add(block2)
        # graph should look like this:
        # 0 <- 1
        # 0 <- 2
        assert hash(block2) in blockchain
        assert blockchain[hash(block2)] == block2
        assert blockchain._leaves == {hash(block1), hash(block2)}
        assert blockchain.get_virtual_block_parents() == {min(hash(block1), hash(block2))}
        assert blockchain._G.node[hash(genesis)][Blockchain._CHAIN_LENGTH_KEY] == 1
        assert blockchain._G.node[hash(block1)][Blockchain._CHAIN_LENGTH_KEY] == 2
        assert blockchain._G.node[hash(block2)][Blockchain._CHAIN_LENGTH_KEY] == 2
        assert blockchain._get_chain() == {hash(genesis): 0, hash(block1): 1}
        assert blockchain._longest_chain == {hash(genesis), hash(block1)}
        assert blockchain.is_a_before_b(hash(genesis), hash(block1)) is True
        assert blockchain.is_a_before_b(hash(block1), hash(block2)) is True
        assert blockchain.is_a_before_b(hash(genesis), hash(block2)) is True
        assert blockchain.get_depth(hash(genesis)) == 1
        assert blockchain.get_depth(hash(block1)) == 0
        assert blockchain.get_depth(hash(block2)) == 0
        assert blockchain.get_depth(hash(block3)) == -float('inf')

        blockchain.add(block3)
        # graph should look like this:
        # 0 <- 1 <- 3
        # 0 <- 2
        assert hash(block3) in blockchain
        assert blockchain[hash(block3)] == block3
        assert blockchain._leaves == {hash(block2), hash(block3)}
        assert blockchain.get_virtual_block_parents() == {hash(block3)}
        assert blockchain._G.node[hash(genesis)][Blockchain._CHAIN_LENGTH_KEY] == 1
        assert blockchain._G.node[hash(block1)][Blockchain._CHAIN_LENGTH_KEY] == 2
        assert blockchain._G.node[hash(block2)][Blockchain._CHAIN_LENGTH_KEY] == 2
        assert blockchain._G.node[hash(block3)][Blockchain._CHAIN_LENGTH_KEY] == 3
        assert blockchain._get_chain() == {hash(genesis): 0, hash(block1): 1, hash(block3): 2}
        assert blockchain._longest_chain == {hash(genesis), hash(block1), hash(block3)}
        assert blockchain.is_a_before_b(hash(genesis), hash(block1)) is True
        assert blockchain.is_a_before_b(hash(block1), hash(block2)) is True
        assert blockchain.is_a_before_b(hash(genesis), hash(block2)) is True
        assert blockchain.is_a_before_b(hash(block3), hash(block2)) is True
        assert blockchain.is_a_before_b(hash(genesis), hash(block3)) is True
        assert blockchain.get_depth(hash(genesis)) == 2
        assert blockchain.get_depth(hash(block1)) == 1
        assert blockchain.get_depth(hash(block2)) == 0
        assert blockchain.get_depth(hash(block3)) == 0

    @pytest.fixture(scope="module")
    def block4(self, block2, block3):
        # graph should look like this: 0 <- 2 <- 4
        return Block(hash(block3) + 1, {hash(block2)})

    @pytest.fixture(scope="module")
    def block5(self, block4):
        # graph should look like this: 0 <- 2 <- 4 <- 5
        return Block(hash(block4) + 1, {hash(block4)})

    @pytest.fixture(scope="module")
    def block6(self, block3, block5):
        # graph should look like this: 0 <- 1 <- 3 <- 6
        return Block(hash(block5) + 1, {hash(block3)})

    @pytest.mark.coloring
    def test_chain_selection(self, blockchain, genesis, block1, block2, block3, block4, block5, block6):
        """
        Tests chain selection on a small blockchain.
        Tests the topological sorting too on the way.
        """
        blockchain.add(block4)
        # gids:
        # 0 <- 1 <- 3
        # 0 <- 2 <- 4

        assert blockchain._leaves == {hash(block3), hash(block4)}
        assert blockchain._G.node[hash(genesis)][Blockchain._CHAIN_LENGTH_KEY] == 1
        assert blockchain._G.node[hash(block1)][Blockchain._CHAIN_LENGTH_KEY] == 2
        assert blockchain._G.node[hash(block2)][Blockchain._CHAIN_LENGTH_KEY] == 2
        assert blockchain._G.node[hash(block3)][Blockchain._CHAIN_LENGTH_KEY] == 3
        assert blockchain._G.node[hash(block4)][Blockchain._CHAIN_LENGTH_KEY] == 3
        assert blockchain._get_chain() == {hash(genesis): 0, hash(block1): 1, hash(block3): 2}
        assert blockchain._longest_chain == {hash(genesis), hash(block1), hash(block3)}

        blockchain.add(block5)
        # gids:
        # 0 <- 1 <- 3
        # 0 <- 2 <- 4 <- 5

        assert blockchain._leaves == {hash(block3), hash(block5)}
        assert blockchain._G.node[hash(genesis)][Blockchain._CHAIN_LENGTH_KEY] == 1
        assert blockchain._G.node[hash(block1)][Blockchain._CHAIN_LENGTH_KEY] == 2
        assert blockchain._G.node[hash(block2)][Blockchain._CHAIN_LENGTH_KEY] == 2
        assert blockchain._G.node[hash(block3)][Blockchain._CHAIN_LENGTH_KEY] == 3
        assert blockchain._G.node[hash(block4)][Blockchain._CHAIN_LENGTH_KEY] == 3
        assert blockchain._G.node[hash(block5)][Blockchain._CHAIN_LENGTH_KEY] == 4
        assert blockchain._get_chain() == {hash(genesis): 0, hash(block2): 1, hash(block4): 2, hash(block5): 3}
        assert blockchain._longest_chain == {hash(genesis), hash(block2), hash(block4), hash(block5)}

        blockchain.add(block6)
        # gids:
        # 0 <- 1 <- 3 <- 6
        # 0 <- 2 <- 4 <- 5

        assert blockchain._leaves == {hash(block5), hash(block6)}
        assert blockchain._G.node[hash(genesis)][Blockchain._CHAIN_LENGTH_KEY] == 1
        assert blockchain._G.node[hash(block1)][Blockchain._CHAIN_LENGTH_KEY] == 2
        assert blockchain._G.node[hash(block2)][Blockchain._CHAIN_LENGTH_KEY] == 2
        assert blockchain._G.node[hash(block3)][Blockchain._CHAIN_LENGTH_KEY] == 3
        assert blockchain._G.node[hash(block4)][Blockchain._CHAIN_LENGTH_KEY] == 3
        assert blockchain._G.node[hash(block5)][Blockchain._CHAIN_LENGTH_KEY] == 4
        assert blockchain._G.node[hash(block6)][Blockchain._CHAIN_LENGTH_KEY] == 4
        assert blockchain._get_chain() == {hash(genesis): 0, hash(block2): 1, hash(block4): 2, hash(block5): 3}
        assert blockchain._longest_chain == {hash(genesis), hash(block2), hash(block4), hash(block5)}

    @pytest.mark.topological_order
    def test_topological_order(self, blockchain, genesis, block1, block2, block3, block4, block5, block6):
        """
        Simple tests for the topological ordering on a small blockchain.
        """
        # gids:
        # 0 <- 1 <- 3 <- 6
        # 0 <- 2 <- 4 <- 5

        assert blockchain.is_a_before_b(hash(genesis), hash(genesis)) is True
        assert blockchain.is_a_before_b(hash(genesis), hash(block1)) is True
        assert blockchain.is_a_before_b(hash(genesis), hash(block2)) is True
        assert blockchain.is_a_before_b(hash(genesis), hash(block3)) is True
        assert blockchain.is_a_before_b(hash(genesis), hash(block4)) is True
        assert blockchain.is_a_before_b(hash(genesis), hash(block5)) is True
        assert blockchain.is_a_before_b(hash(genesis), hash(block6)) is True

        assert blockchain.is_a_before_b(hash(block1), hash(genesis)) is False
        assert blockchain.is_a_before_b(hash(block1), hash(block1)) is None
        assert blockchain.is_a_before_b(hash(block1), hash(block2)) is False
        assert blockchain.is_a_before_b(hash(block1), hash(block3)) is None
        assert blockchain.is_a_before_b(hash(block1), hash(block4)) is False
        assert blockchain.is_a_before_b(hash(block1), hash(block5)) is False
        assert blockchain.is_a_before_b(hash(block1), hash(block6)) is None

        assert blockchain.is_a_before_b(hash(block2), hash(block1)) is True
        assert blockchain.is_a_before_b(hash(block2), hash(block2)) is True
        assert blockchain.is_a_before_b(hash(block2), hash(block3)) is True
        assert blockchain.is_a_before_b(hash(block2), hash(block4)) is True
        assert blockchain.is_a_before_b(hash(block2), hash(block5)) is True
        assert blockchain.is_a_before_b(hash(block2), hash(block6)) is True
