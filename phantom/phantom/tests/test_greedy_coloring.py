import pytest
import networkx

from itertools import chain
from random import randint, sample

from typing import AbstractSet, List
from networkx import DiGraph
from .test_phantom import TestPHANTOM
from phantom.dag import Block
from phantom.phantom import GreedyPHANTOM


class TestGreedyColoring:
    """
    Test suite for the coloring and all related tasks of the GreedyPHANTOM class.
    Note that the tests run on the MaliciousGreedyPHANTOM class too.
    """

    # The number of times to run the random tests
    RANDOM_TESTS_RUN_NUMBER = 1

    @staticmethod
    def assert_coloring(greedy_dag, correct_coloring):
        """
        Asserts that the given coloring holds in the given DAG using _is_blue.
        """
        for global_id in greedy_dag:
            assert greedy_dag._is_blue(global_id) == (global_id in correct_coloring)

    @pytest.mark.coloring
    def test_coloring_basic(self, greedy_dag, genesis, block1, block2, block3):
        """
        Tests the data structure handles coloring a small DAG correctly.
        """
        assert greedy_dag._genesis_gid is None
        assert greedy_dag._coloring_tip_gid is None
        assert greedy_dag._coloring_chain == set()
        assert greedy_dag._k_chain == (set(), float('inf'))
        TestGreedyColoring.assert_coloring(greedy_dag, set())
        assert greedy_dag._get_coloring() == set()
        assert greedy_dag._antipast == set()
        assert greedy_dag.get_depth(hash(genesis)) == -float('inf')
        assert greedy_dag.get_depth(hash(block1)) == -float('inf')
        assert greedy_dag.get_depth(hash(block2)) == -float('inf')
        assert greedy_dag.get_depth(hash(block3)) == -float('inf')

        greedy_dag.add(genesis)
        assert greedy_dag._genesis_gid == hash(genesis)
        assert greedy_dag._coloring_tip_gid == hash(genesis)
        assert greedy_dag._coloring_chain == {hash(genesis)}
        assert greedy_dag._k_chain == ({hash(genesis)}, 0)
        TestGreedyColoring.assert_coloring(greedy_dag, set(greedy_dag._G.nodes()))
        assert greedy_dag._get_coloring() == set(greedy_dag._G.nodes())
        assert greedy_dag._antipast == {hash(genesis)}
        assert greedy_dag._G.node[hash(genesis)][GreedyPHANTOM._HEIGHT_KEY] == 0
        assert greedy_dag._G.node[hash(genesis)][GreedyPHANTOM._BLUE_NUMBER_KEY] == 0
        assert greedy_dag._G.node[hash(genesis)][GreedyPHANTOM._BLUE_DIFF_PAST_ORDER_KEY].keys() == set()
        assert greedy_dag._G.node[hash(genesis)][GreedyPHANTOM._RED_DIFF_PAST_ORDER_KEY].keys() == set()
        assert greedy_dag._G.node[hash(genesis)][GreedyPHANTOM._COLORING_PARENT_KEY] is None
        assert greedy_dag.get_depth(hash(genesis)) == 0
        assert greedy_dag.get_depth(hash(block1)) == -float('inf')
        assert greedy_dag.get_depth(hash(block2)) == -float('inf')
        assert greedy_dag.get_depth(hash(block3)) == -float('inf')

        greedy_dag.add(block1)
        assert greedy_dag._genesis_gid == hash(genesis)
        assert greedy_dag._coloring_tip_gid == hash(block1)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1)}
        assert greedy_dag._k_chain == ({hash(genesis), hash(block1)}, 0)
        TestGreedyColoring.assert_coloring(greedy_dag, set(greedy_dag._G.nodes()))
        assert greedy_dag._get_coloring() == set(greedy_dag._G.nodes())
        assert greedy_dag._antipast == {hash(block1)}
        assert greedy_dag._G.node[hash(block1)][GreedyPHANTOM._HEIGHT_KEY] == 1
        assert greedy_dag._G.node[hash(block1)][GreedyPHANTOM._BLUE_NUMBER_KEY] == 1
        assert greedy_dag._G.node[hash(block1)][GreedyPHANTOM._BLUE_DIFF_PAST_ORDER_KEY].keys() == {hash(genesis)}
        assert greedy_dag._G.node[hash(block1)][GreedyPHANTOM._RED_DIFF_PAST_ORDER_KEY].keys() == set()
        assert greedy_dag._G.node[hash(block1)][GreedyPHANTOM._COLORING_PARENT_KEY] == hash(genesis)
        assert greedy_dag.get_depth(hash(genesis)) == 1
        assert greedy_dag.get_depth(hash(block1)) == 0
        assert greedy_dag.get_depth(hash(block2)) == -float('inf')
        assert greedy_dag.get_depth(hash(block3)) == -float('inf')

        greedy_dag.add(block2)
        assert greedy_dag._genesis_gid == hash(genesis)
        assert greedy_dag._coloring_tip_gid == hash(block1)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1)}
        assert greedy_dag._k_chain == ({hash(genesis), hash(block1)}, 0)
        TestGreedyColoring.assert_coloring(greedy_dag, set(greedy_dag._G.nodes()))
        assert greedy_dag._get_coloring() == set(greedy_dag._G.nodes())
        assert greedy_dag._antipast == {hash(block1), hash(block2)}
        assert greedy_dag._G.node[hash(block2)][GreedyPHANTOM._HEIGHT_KEY] == 1
        assert greedy_dag._G.node[hash(block2)][GreedyPHANTOM._BLUE_NUMBER_KEY] == 1
        assert greedy_dag._G.node[hash(block2)][GreedyPHANTOM._BLUE_DIFF_PAST_ORDER_KEY].keys() == {hash(genesis)}
        assert greedy_dag._G.node[hash(block2)][GreedyPHANTOM._RED_DIFF_PAST_ORDER_KEY].keys() == set()
        assert greedy_dag._G.node[hash(block2)][GreedyPHANTOM._COLORING_PARENT_KEY] == hash(genesis)
        assert greedy_dag.get_depth(hash(genesis)) == 1
        assert greedy_dag.get_depth(hash(block1)) == 0
        assert greedy_dag.get_depth(hash(block2)) == 0
        assert greedy_dag.get_depth(hash(block3)) == -float('inf')

        greedy_dag.add(block3)
        assert greedy_dag._genesis_gid == hash(genesis)
        assert greedy_dag._coloring_tip_gid == hash(block3)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3)}
        assert greedy_dag._k_chain == ({hash(genesis), hash(block1), hash(block3)}, 0)
        TestGreedyColoring.assert_coloring(greedy_dag, set(greedy_dag._G.nodes()))
        assert greedy_dag._get_coloring() == set(greedy_dag._G.nodes())
        assert greedy_dag._antipast == {hash(block3)}
        assert greedy_dag._G.node[hash(block3)][GreedyPHANTOM._HEIGHT_KEY] == 2
        assert greedy_dag._G.node[hash(block3)][GreedyPHANTOM._BLUE_NUMBER_KEY] == 3
        assert greedy_dag._G.node[hash(block3)][GreedyPHANTOM._BLUE_DIFF_PAST_ORDER_KEY].keys() == {hash(block1),
                                                                                                    hash(block2)}
        assert greedy_dag._G.node[hash(block3)][GreedyPHANTOM._RED_DIFF_PAST_ORDER_KEY].keys() == set()
        assert greedy_dag._G.node[hash(block3)][GreedyPHANTOM._COLORING_PARENT_KEY] == hash(block1)
        assert greedy_dag.get_depth(hash(genesis)) == 3
        assert greedy_dag.get_depth(hash(block1)) == 1
        assert greedy_dag.get_depth(hash(block2)) == 1
        assert greedy_dag.get_depth(hash(block3)) == 0

    @pytest.mark.coloring
    def test_coloring_advanced(self, greedy_dag, genesis, block1, block2, block3, block4, block5, block6, block7,
                               block8, block9):
        """
        Tests coloring a big DAG.
        """
        greedy_dag.add(genesis)
        greedy_dag.add(block1)
        greedy_dag.add(block2)
        greedy_dag.add(block3)

        # gids: 0 <- 1, 2 <- 3
        # gids: 0 <- 4
        greedy_dag.add(block4)
        assert greedy_dag._k_chain == ({hash(genesis), hash(block1), hash(block3)}, 0)

        # gids: 0 <- 1, 2 <- 3
        # gids: 0 <- 4 <- 5
        greedy_dag.add(block5)
        assert greedy_dag._k_chain == ({hash(genesis), hash(block1), hash(block3)}, 0)

        # gids: 0 <- 1, 2 <- 3
        # gids: 0 <- 4 <- 5 <- 6
        greedy_dag.add(block6)
        assert greedy_dag._k_chain == ({hash(genesis), hash(block1), hash(block3)}, 0)

        # test colorings for various K values
        greedy_dag.set_k(0)
        assert greedy_dag._coloring_tip_gid == hash(block6)
        assert greedy_dag._k_chain == ({hash(block6)}, 3)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block4), hash(block5), hash(block6)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block4), hash(block5), hash(block6)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block4), hash(block5), hash(block6)})

        greedy_dag.set_k(1)
        assert greedy_dag._coloring_tip_gid == hash(block3)
        assert greedy_dag._k_chain == ({hash(block3)}, 2)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3)})

        greedy_dag.set_k(2)
        assert greedy_dag._coloring_tip_gid == hash(block3)
        assert greedy_dag._k_chain == ({hash(block1), hash(block3)}, 1)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3)})

        greedy_dag.set_k(3)
        assert greedy_dag._coloring_tip_gid == hash(block3)
        assert greedy_dag._k_chain == ({hash(genesis), hash(block1), hash(block3)}, 0)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3), hash(block4),
                                              hash(block5), hash(block6)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                        hash(block4), hash(block5), hash(block6)})

        greedy_dag.set_k(4)
        assert greedy_dag._coloring_tip_gid == hash(block3)
        assert greedy_dag._k_chain == ({hash(genesis), hash(block1), hash(block3)}, 0)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3), hash(block4),
                                              hash(block5), hash(block6)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                        hash(block4), hash(block5), hash(block6)})

        # gids: 0 <- 1, 2 <- 3 <- 7
        # gids: 0 <- 4 <- 5 <- 6
        greedy_dag.add(block7)
        assert greedy_dag._k_chain == ({hash(genesis), hash(block1), hash(block3), hash(block7)}, 0)

        # gids: 0 <- 1, 2 <- 3 <- 7 <- 8
        # gids: 0 <- 4 <- 5 <- 6
        greedy_dag.add(block8)
        assert greedy_dag._k_chain == ({hash(block1), hash(block3), hash(block7), hash(block8)}, 1)

        # gids: 0 <- 1, 2 <- 3 <- 7 <- 8 <- 9
        # gids: 0 <- 4 <- 5 <- 6
        greedy_dag.add(block9)
        assert greedy_dag._k_chain == ({hash(block3), hash(block7), hash(block8), hash(block9)}, 2)

        # test colorings for various K values
        greedy_dag.set_k(0)
        assert greedy_dag._coloring_tip_gid == hash(block9)
        assert greedy_dag._k_chain == ({hash(block9)}, 5)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block8),
                                              hash(block9)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block8),
                                              hash(block9)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block3), hash(block7),
                                                        hash(block8), hash(block9)})

        greedy_dag.set_k(1)
        assert greedy_dag._coloring_tip_gid == hash(block9)
        assert greedy_dag._k_chain == ({hash(block8), hash(block9)}, 4)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block8),
                                              hash(block9)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                              hash(block7), hash(block8), hash(block9)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                        hash(block7), hash(block8), hash(block9)})

        greedy_dag.set_k(2)
        assert greedy_dag._coloring_tip_gid == hash(block9)
        assert greedy_dag._k_chain == ({hash(block7), hash(block8), hash(block9)}, 3)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block8),
                                              hash(block9)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                              hash(block7), hash(block8), hash(block9)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                        hash(block7), hash(block8), hash(block9)})

        greedy_dag.set_k(3)
        assert greedy_dag._coloring_tip_gid == hash(block9)
        assert greedy_dag._k_chain == ({hash(block3), hash(block7), hash(block8), hash(block9)}, 2)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block8),
                                              hash(block9)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                              hash(block7), hash(block8), hash(block9)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                        hash(block7), hash(block8), hash(block9)})

        greedy_dag.set_k(4)
        assert greedy_dag._coloring_tip_gid == hash(block9)
        assert greedy_dag._k_chain == ({hash(block3), hash(block7), hash(block8), hash(block9)}, 2)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block8),
                                              hash(block9)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                              hash(block7), hash(block8), hash(block9)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                        hash(block7), hash(block8), hash(block9)})

        greedy_dag.set_k(5)
        assert greedy_dag._coloring_tip_gid == hash(block9)
        assert greedy_dag._k_chain == ({hash(block1), hash(block3), hash(block7), hash(block8), hash(block9)}, 1)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block8),
                                              hash(block9)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                              hash(block7), hash(block8), hash(block9)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                        hash(block7), hash(block8), hash(block9)})

        greedy_dag.set_k(6)
        assert greedy_dag._coloring_tip_gid == hash(block9)
        assert greedy_dag._k_chain == ({hash(genesis), hash(block1), hash(block3), hash(block7), hash(block8),
                                        hash(block9)}, 0)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block8),
                                              hash(block9)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3), hash(block4),
                                              hash(block5), hash(block6), hash(block7), hash(block8), hash(block9)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                        hash(block4), hash(block5), hash(block6), hash(block7),
                                                        hash(block8), hash(block9)})

        # gids: 0 <- 1, 2 <- 3 <- 7 <- 8 <- 9
        # gids: 0 <- 1, 2 <- 3 <- 7 <- 10
        # gids: 0 <- 4 <- 5 <- 6 <- 10
        block10 = Block(10, {hash(block6), hash(block7)})
        greedy_dag.add(block10)

        greedy_dag.set_k(0)
        assert greedy_dag._coloring_tip_gid == hash(block9)
        assert greedy_dag._k_chain == ({hash(block9)}, 5)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block8),
                                              hash(block9)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block8),
                                              hash(block9)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block3), hash(block7),
                                                        hash(block8), hash(block9)})

        greedy_dag.set_k(1)
        assert greedy_dag._coloring_tip_gid == hash(block9)
        assert greedy_dag._k_chain == ({hash(block8), hash(block9)}, 4)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block8),
                                              hash(block9)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                              hash(block7), hash(block8), hash(block9)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                        hash(block7), hash(block8), hash(block9)})

        greedy_dag.set_k(2)
        assert greedy_dag._coloring_tip_gid == hash(block9)
        assert greedy_dag._k_chain == ({hash(block7), hash(block8), hash(block9)}, 3)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block8),
                                              hash(block9)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                              hash(block7), hash(block8), hash(block9), hash(block10)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                        hash(block7), hash(block8), hash(block9), hash(block10)})

        greedy_dag.set_k(3)
        assert greedy_dag._coloring_tip_gid == hash(block9)
        assert greedy_dag._k_chain == ({hash(block3), hash(block7), hash(block8), hash(block9)}, 2)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block8),
                                              hash(block9)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                              hash(block7), hash(block8), hash(block9), hash(block10)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                        hash(block7), hash(block8), hash(block9), hash(block10)})

        greedy_dag.set_k(4)
        assert greedy_dag._coloring_tip_gid == hash(block10)
        assert greedy_dag._k_chain == ({hash(block7), hash(block10)}, 3)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block10)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                              hash(block4), hash(block5), hash(block6), hash(block7),
                                              hash(block8), hash(block9), hash(block10)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                        hash(block4), hash(block5), hash(block6), hash(block7),
                                                        hash(block8), hash(block9), hash(block10)})

        greedy_dag.set_k(5)
        assert greedy_dag._coloring_tip_gid == hash(block10)
        assert greedy_dag._k_chain == ({hash(block3), hash(block7), hash(block10)}, 2)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block10)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                              hash(block4), hash(block5), hash(block6), hash(block7),
                                              hash(block8), hash(block9), hash(block10)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                        hash(block4), hash(block5), hash(block6), hash(block7),
                                                        hash(block8), hash(block9), hash(block10)})

        greedy_dag.set_k(6)
        assert greedy_dag._coloring_tip_gid == hash(block10)
        assert greedy_dag._k_chain == ({hash(block3), hash(block7), hash(block10)}, 2)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block10)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                              hash(block4), hash(block5), hash(block6), hash(block7),
                                              hash(block8), hash(block9), hash(block10)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                        hash(block4), hash(block5), hash(block6), hash(block7),
                                                        hash(block8), hash(block9), hash(block10)})

        greedy_dag.set_k(7)
        assert greedy_dag._coloring_tip_gid == hash(block10)
        assert greedy_dag._k_chain == ({hash(block1), hash(block3), hash(block7), hash(block10)}, 1)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block10)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                              hash(block4), hash(block5), hash(block6), hash(block7),
                                              hash(block8), hash(block9), hash(block10)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                        hash(block4), hash(block5), hash(block6), hash(block7),
                                                        hash(block8), hash(block9), hash(block10)})

        greedy_dag.set_k(8)
        assert greedy_dag._coloring_tip_gid == hash(block10)
        assert greedy_dag._k_chain == ({hash(genesis), hash(block1), hash(block3), hash(block7), hash(block10)}, 0)
        assert greedy_dag._coloring_chain == {hash(genesis), hash(block1), hash(block3), hash(block7), hash(block10)}
        assert greedy_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                              hash(block4), hash(block5), hash(block6), hash(block7),
                                              hash(block8), hash(block9), hash(block10)}
        TestGreedyColoring.assert_coloring(greedy_dag, {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                        hash(block4), hash(block5), hash(block6), hash(block7),
                                                        hash(block8), hash(block9), hash(block10)})

    @pytest.mark.topological_order
    def test_topological_order_advanced(self, greedy_dag, genesis, block1, block2, block3, block4, block5, block6):
        """
        Advanced tests for the topological ordering on a small phantom DAG.
        """
        greedy_dag.add(genesis)
        greedy_dag.add(block1)
        greedy_dag.add(block2)
        greedy_dag.add(block3)

        # gids: 0 <- 1, 2 <- 3
        # gids: 0 <- 4
        greedy_dag.add(block4)
        TestPHANTOM.assert_mapping(greedy_dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2), 3: hash(block3),
                                                4: hash(block4), 5: hash(block5), 6: hash(block6)})

        # gids: 0 <- 1, 2 <- 3
        # gids: 0 <- 4 <- 5
        greedy_dag.add(block5)
        TestPHANTOM.assert_mapping(greedy_dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2), 3: hash(block3),
                                                4: hash(block4), 5: hash(block5), 6: hash(block6)})

        # gids: 0 <- 1, 2 <- 3
        # gids: 0 <- 4 <- 5 <- 6
        greedy_dag.add(block6)
        TestPHANTOM.assert_mapping(greedy_dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2), 3: hash(block3),
                                                4: hash(block4), 5: hash(block5), 6: hash(block6)})

        # test colorings for various K values
        greedy_dag.set_k(0)
        # gids: {0, 4, 5, 6}, lids: {0, 1, 2, 3}
        TestPHANTOM.assert_mapping(greedy_dag, {0: hash(genesis), 4: hash(block1), 5: hash(block2), 6: hash(block3),
                                                1: hash(block4), 2: hash(block5), 3: hash(block6)})

        greedy_dag.set_k(1)
        # gids: {0, 1, 2, 3, 4}, lids: {0, 1, 2, 3, 4}
        TestPHANTOM.assert_mapping(greedy_dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2), 3: hash(block3),
                                                4: hash(block4), 5: hash(block5), 6: hash(block6)})

        greedy_dag.set_k(2)
        # gids: {0, 1, 2, 3, 4, 5}, lids: {0, 1, 2, 3, 4, 5}
        TestPHANTOM.assert_mapping(greedy_dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2), 3: hash(block3),
                                                4: hash(block4), 5: hash(block5), 6: hash(block6)})

        greedy_dag.set_k(3)
        # gids: {0, 1, 2, 3, 4, 5, 6}, lids: {0, 1, 2, 3, 4, 5, 6}
        TestPHANTOM.assert_mapping(greedy_dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2), 3: hash(block3),
                                                4: hash(block4), 5: hash(block5), 6: hash(block6)})

        greedy_dag.set_k(4)
        # gids: {0, 1, 2, 3, 4, 5, 6}, lids: {0, 1, 2, 3, 4, 5, 6}
        TestPHANTOM.assert_mapping(greedy_dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2), 3: hash(block3),
                                                4: hash(block4), 5: hash(block5), 6: hash(block6)})

    @staticmethod
    def random_block_generator(genesis, initial_leaf_number, block_number):
        """
        Randomly generates blocks according to the given parameters.
        """
        max_initial_leaf_number = initial_leaf_number
        max_block_number = block_number

        all_blocks = set()
        all_blocks.add(hash(genesis))
        leaves = set()
        block_counter = 1
        yield genesis

        while block_counter <= max_block_number:
            if block_counter <= max_initial_leaf_number + 1:
                parents = {hash(genesis)}
            else:
                parents = frozenset(sample(leaves, randint(1, max(1, round(len(leaves) / 5)))))
            cur_block = Block(block_counter, parents)

            leaves -= cur_block.get_parents()
            leaves.add(hash(cur_block))
            all_blocks.add(hash(cur_block))
            block_counter += 1
            yield cur_block

    @staticmethod
    def get_topological_orderer(graph: DiGraph, coloring: AbstractSet[Block.GlobalID],
                                unordered: AbstractSet[Block.GlobalID]) -> "TopologicalOrderer":
        """
        :param graph: the graph to order.
        :param coloring: the coloring of the sub-DAG to order.
        :param unordered: all the unordered blocks in the sub-DAG to order.
        :return: a topological orderer for the sub-DAG.
        """

        class TopologicalOrderer:
            """
            Given a DAG, this class can output a topological order on each subset of the DAG.
            """

            def __init__(self, graph: DiGraph, coloring: AbstractSet[Block.GlobalID],
                         unordered: AbstractSet[Block.GlobalID]):
                """
                Initializes the topological orderer.
                :param graph: the graph to order.
                :param coloring: the coloring of the graph.
                :param unordered: the blocks to order.
                """
                self._ordered = set()
                self._unordered = unordered
                self._G = graph
                self._coloring = coloring

            def get_topological_order(self, leaves: AbstractSet[Block.GlobalID], coloring_parent_gid: Block.GlobalID) \
                    -> List[Block.GlobalID]:
                """
                :param coloring_parent_gid: the coloring parent of the sub-DAG to order.
                :param leaves: leaves of the sub-DAG to order.
                :return: an list sorted according to a topological order on the input leaves and their ancestors.
                """
                leaves = leaves - self._ordered
                leaves &= self._unordered
                cur_order = []
                if len(leaves) == 0:
                    return cur_order

                leaves -= {coloring_parent_gid}
                blue_leaves_set = leaves & self._coloring
                blue_leaves = sorted(blue_leaves_set)
                red_leaves = sorted(leaves - blue_leaves_set)

                coloring_parent_list = []
                if (coloring_parent_gid is not None) and (coloring_parent_gid not in self._ordered):
                    coloring_parent_list.append(coloring_parent_gid)
                for leaf in chain(coloring_parent_list, blue_leaves, red_leaves):
                    self._ordered.add(leaf)
                    cur_leaf_order = \
                        self.get_topological_order(set(self._G.successors(leaf)),
                                                   self._G.node[leaf][GreedyPHANTOM._COLORING_PARENT_KEY])
                    cur_leaf_order.append(leaf)
                    cur_order.extend(cur_leaf_order)

                return cur_order

        return TopologicalOrderer(graph, coloring, unordered)

    RANDOM_TESTS_RANGE = list(range(RANDOM_TESTS_RUN_NUMBER))

    @pytest.mark.parametrize("k", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    @pytest.mark.parametrize("run_number", RANDOM_TESTS_RANGE)
    @pytest.mark.topological_order
    def test_topological_order_randomly(self, greedy_dag, genesis, k, run_number):
        """
        Tests the topological order on randomly generated blocks.
        """
        greedy_dag.set_k(k)
        for block in TestGreedyColoring.random_block_generator(genesis=genesis,
                                                               initial_leaf_number=7,
                                                               block_number=40):
            greedy_dag.add(block)
            mapping_list = TestGreedyColoring.get_topological_orderer(greedy_dag._G, greedy_dag._get_coloring(),
                                                                      set(greedy_dag)).get_topological_order(
                greedy_dag.get_virtual_block_parents(), greedy_dag._coloring_tip_gid)
            TestPHANTOM.assert_mapping(greedy_dag, {new_lid: cur_gid for new_lid, cur_gid in enumerate(mapping_list)})

    @pytest.mark.parametrize("run_number", RANDOM_TESTS_RANGE)
    @pytest.mark.data_structure
    def test_antipast_calculation(self, greedy_dag, genesis, run_number):
        """
        Tests the antipast calculation on randomly generated blocks.
        """
        for block in TestGreedyColoring.random_block_generator(genesis=genesis,
                                                               initial_leaf_number=10,
                                                               block_number=130):
            greedy_dag.add(block)
            for global_id in greedy_dag:
                correct_antipast = set(greedy_dag._G.nodes()).difference(networkx.descendants(greedy_dag._G, global_id))
                actual_antipast = greedy_dag._get_antipast(global_id)
                assert actual_antipast == correct_antipast

    @pytest.mark.parametrize("run_number", RANDOM_TESTS_RANGE)
    @pytest.mark.data_structure
    def test_past_calculation(self, greedy_dag, genesis, run_number):
        """
        Tests the past calculation on randomly generated blocks.
        """
        for block in TestGreedyColoring.random_block_generator(genesis=genesis,
                                                               initial_leaf_number=10,
                                                               block_number=130):
            greedy_dag.add(block)
            for global_id in greedy_dag:
                assert greedy_dag._get_past(global_id) == set(networkx.descendants(greedy_dag._G, global_id))
