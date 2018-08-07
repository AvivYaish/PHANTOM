import pytest

from phantom.dag import Block
from phantom.phantom import CompetingChainGreedyPHANTOM


@pytest.fixture
def competing_chain_greedy_dag():
    competing_chain_greedy_dag = CompetingChainGreedyPHANTOM(confirmation_depth=1, maximal_depth_difference=1)
    competing_chain_greedy_dag.set_k(4)
    return competing_chain_greedy_dag


class TestCompetingChainGreedyPHANTOM:
    """
    Test suite for the CompetingChainGreedyPHANTOM class.
    """

    @pytest.mark.data_structure
    def test_constructor(self, competing_chain_greedy_dag):
        """
        Tests the constructor.
        """
        assert competing_chain_greedy_dag._currently_attacked_block_gid is None
        assert competing_chain_greedy_dag._first_parallel_block_gid is None
        assert competing_chain_greedy_dag._competing_chain_tip_gid is None
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == set()
        assert not competing_chain_greedy_dag.did_attack_succeed()

        assert competing_chain_greedy_dag.get_virtual_block_parents(is_malicious=True) == set()
        assert competing_chain_greedy_dag._currently_attacked_block_gid is None
        assert competing_chain_greedy_dag._first_parallel_block_gid is None
        assert competing_chain_greedy_dag._competing_chain_tip_gid is None
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == set()
        assert not competing_chain_greedy_dag.did_attack_succeed()

    @pytest.mark.data_structure
    def test_adding_genesis(self, competing_chain_greedy_dag, genesis):
        """
        Tests adding the genesis block.
        """
        competing_chain_greedy_dag.add(genesis)
        assert competing_chain_greedy_dag._currently_attacked_block_gid is None
        assert competing_chain_greedy_dag._competing_chain_tip_gid is None
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == set()
        assert not competing_chain_greedy_dag.did_attack_succeed()

        assert competing_chain_greedy_dag.get_virtual_block_parents(is_malicious=True) == {hash(genesis)}
        assert competing_chain_greedy_dag._currently_attacked_block_gid is None
        assert competing_chain_greedy_dag._competing_chain_tip_gid is None
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == set()
        assert not competing_chain_greedy_dag.did_attack_succeed()

    @pytest.mark.data_structure
    def test_competing_chain_only(self, competing_chain_greedy_dag, genesis, block4, block5, block6):
        """
        Tests creating a selfish chain on top of the genesis block.
        """
        competing_chain_greedy_dag.add(genesis)

        competing_chain_greedy_dag.add(block4, is_malicious=True)
        assert competing_chain_greedy_dag._currently_attacked_block_gid is None
        assert competing_chain_greedy_dag._competing_chain_tip_gid == hash(block4)
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == set()
        assert not competing_chain_greedy_dag.did_attack_succeed()

        # the virtual malicious block's parent should be the genesis block, because the only other block in the DAG
        # is the tip that was added maliciously. You need something to attack!
        assert competing_chain_greedy_dag.get_virtual_block_parents(is_malicious=True) == {hash(genesis)}
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block4)
        assert competing_chain_greedy_dag._competing_chain_tip_gid is None
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block4)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

        competing_chain_greedy_dag.add(block5, is_malicious=True)
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block4)
        assert competing_chain_greedy_dag._competing_chain_tip_gid == hash(block5)
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block5)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

        assert competing_chain_greedy_dag.get_virtual_block_parents(is_malicious=True) == {hash(block5)}
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block4)
        assert competing_chain_greedy_dag._competing_chain_tip_gid == hash(block5)
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block5)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

        competing_chain_greedy_dag.add(block6, is_malicious=True)
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block4)
        assert competing_chain_greedy_dag._competing_chain_tip_gid == hash(block6)
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block6)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

        assert competing_chain_greedy_dag.get_virtual_block_parents(is_malicious=True) == {hash(block6)}
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block4)
        assert competing_chain_greedy_dag._competing_chain_tip_gid == hash(block6)
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block6)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

    @pytest.mark.data_structure
    def test_attack_restart(self, competing_chain_greedy_dag, genesis, block1, block2, block3, block4):
        """
        Tests restarting a futile attack.
        """
        competing_chain_greedy_dag.add(genesis)

        # gids: 0 <- 4
        competing_chain_greedy_dag.add(block4, is_malicious=True)

        # gids: 0 <- 1
        # gids: 0 <- 4
        competing_chain_greedy_dag.add(block1)
        assert competing_chain_greedy_dag._currently_attacked_block_gid is None
        assert competing_chain_greedy_dag._competing_chain_tip_gid == hash(block4)
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == set()
        assert not competing_chain_greedy_dag.did_attack_succeed()

        # attack should be started only now
        assert competing_chain_greedy_dag.get_virtual_block_parents(is_malicious=True) == {hash(genesis), hash(block4)}
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block1)
        assert competing_chain_greedy_dag._competing_chain_tip_gid is None
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block1), hash(block4)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

        # gids: 0 <- 1, 2
        # gids: 0 <- 4
        competing_chain_greedy_dag.add(block2)
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block1)
        assert competing_chain_greedy_dag._competing_chain_tip_gid is None
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block1), hash(block4)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

        assert competing_chain_greedy_dag.get_virtual_block_parents(is_malicious=True) == {hash(genesis), hash(block2),
                                                                                           hash(block4)}
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block1)
        assert competing_chain_greedy_dag._competing_chain_tip_gid is None
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block1), hash(block2), hash(block4)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

        # gids: 0 <- 1, 2 <- 3
        # gids: 0 <- 4
        competing_chain_greedy_dag.add(block3)
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block1)
        assert competing_chain_greedy_dag._competing_chain_tip_gid is None
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block1), hash(block2), hash(block4)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

        assert competing_chain_greedy_dag.get_virtual_block_parents(is_malicious=True) == {hash(block1), hash(block2),
                                                                                           hash(block4)}
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block3)
        assert competing_chain_greedy_dag._competing_chain_tip_gid is None
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block3), hash(block4)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

    @pytest.mark.data_structure
    def test_complex_attack(self, competing_chain_greedy_dag, genesis, block1, block2, block3):
        """
        Tests a complex attack scenario.
        """
        competing_chain_greedy_dag.add(genesis)

        # gids: 0 <- 1
        competing_chain_greedy_dag.add(block1)

        # gids: 0 <- 1
        # gids: 0 <- 4
        block4 = Block(4, competing_chain_greedy_dag.get_virtual_block_parents(is_malicious=True))
        competing_chain_greedy_dag.add(block4, is_malicious=True)
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block1)
        assert competing_chain_greedy_dag._competing_chain_tip_gid == hash(block4)
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block1), hash(block4)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

        assert competing_chain_greedy_dag.get_virtual_block_parents(is_malicious=True) == {hash(block4)}
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block1)
        assert competing_chain_greedy_dag._competing_chain_tip_gid == hash(block4)
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block1), hash(block4)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

        # gids: 0 <- 1, 2
        # gids: 0 <- 4
        competing_chain_greedy_dag.add(block2)
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block1)
        assert competing_chain_greedy_dag._competing_chain_tip_gid == hash(block4)
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block1), hash(block2), hash(block4)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

        assert competing_chain_greedy_dag.get_virtual_block_parents(is_malicious=True) == {hash(block4)}
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block1)
        assert competing_chain_greedy_dag._competing_chain_tip_gid == hash(block4)
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block1), hash(block2), hash(block4)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

        # gids: 0 <- 1, 2
        # gids: 0 <- 4 <- 5
        block5 = Block(5, competing_chain_greedy_dag.get_virtual_block_parents(is_malicious=True))
        competing_chain_greedy_dag.add(block5, is_malicious=True)
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block1)
        assert competing_chain_greedy_dag._competing_chain_tip_gid == hash(block5)
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block1), hash(block2), hash(block5)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

        assert competing_chain_greedy_dag.get_virtual_block_parents(is_malicious=True) == {hash(block1), hash(block2),
                                                                                           hash(block5)}
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block1)
        assert competing_chain_greedy_dag._competing_chain_tip_gid == hash(block5)
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block1), hash(block2), hash(block5)}
        assert not competing_chain_greedy_dag.did_attack_succeed()  # block1 is still unconfirmed

        # gids: 0 <- 1, 2 <- 3
        # gids: 0 <- 4 <- 5
        competing_chain_greedy_dag.add(block3)
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block1)
        assert competing_chain_greedy_dag._competing_chain_tip_gid == hash(block5)
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block1), hash(block2), hash(block3),
                                                                            hash(block5)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

        assert competing_chain_greedy_dag.get_virtual_block_parents(is_malicious=True) == {hash(block1), hash(block2),
                                                                                           hash(block5)}
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block1)
        assert competing_chain_greedy_dag._competing_chain_tip_gid == hash(block5)
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block1), hash(block2), hash(block3),
                                                                            hash(block5)}
        assert not competing_chain_greedy_dag.did_attack_succeed()

        # gids: 0 <- 1, 2 <- 3
        # gids: 0 <- 1, 2 <- 6
        # gids: 0 <- 4 <- 5 <- 6
        block6 = Block(6, competing_chain_greedy_dag.get_virtual_block_parents(is_malicious=True))
        competing_chain_greedy_dag.add(block6, is_malicious=True)
        assert competing_chain_greedy_dag._currently_attacked_block_gid == hash(block1)
        assert competing_chain_greedy_dag._competing_chain_tip_gid == hash(block6)
        assert competing_chain_greedy_dag._competing_chain_tip_antipast == {hash(block3), hash(block6)}
        assert competing_chain_greedy_dag.did_attack_succeed()
