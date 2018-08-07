import pytest

from phantom.phantom import PHANTOM
from .test_phantom import TestPHANTOM


@pytest.fixture
def brute_force_dag():
    dag = PHANTOM()
    dag.set_k(4)
    return dag


class TestBruteForceColoring:
    """
    Test suite for the brute force coloring and all related tasks of the phantom class.
    """

    @pytest.mark.coloring
    def test_coloring_basic(self, brute_force_dag, genesis, block1, block2, block3):
        """
        Tests coloring a small phantom DAG.
        """
        assert brute_force_dag._get_coloring() == set()

        brute_force_dag.add(genesis)
        assert brute_force_dag._get_coloring() == set(brute_force_dag._G.nodes())
        assert brute_force_dag._G.node[hash(genesis)][PHANTOM._BAC_KEY] == set()

        brute_force_dag.add(block1)
        assert brute_force_dag._get_coloring() == set(brute_force_dag._G.nodes())
        assert brute_force_dag._G.node[hash(genesis)][PHANTOM._BAC_KEY] == set()
        assert brute_force_dag._G.node[hash(block1)][PHANTOM._BAC_KEY] == set()

        brute_force_dag.add(block2)
        assert brute_force_dag._get_coloring() == set(brute_force_dag._G.nodes())
        assert brute_force_dag._G.node[hash(genesis)][PHANTOM._BAC_KEY] == set()
        assert brute_force_dag._G.node[hash(block1)][PHANTOM._BAC_KEY] == {hash(block2)}
        assert brute_force_dag._G.node[hash(block2)][PHANTOM._BAC_KEY] == {hash(block1)}

        brute_force_dag.add(block3)
        assert brute_force_dag._get_coloring() == set(brute_force_dag._G.nodes())
        assert brute_force_dag._G.node[hash(genesis)][PHANTOM._BAC_KEY] == set()
        assert brute_force_dag._G.node[hash(block1)][PHANTOM._BAC_KEY] == {hash(block2)}
        assert brute_force_dag._G.node[hash(block2)][PHANTOM._BAC_KEY] == {hash(block1)}
        assert brute_force_dag._G.node[hash(block3)][PHANTOM._BAC_KEY] == set()

    @pytest.mark.coloring
    def test_coloring_advanced(self, brute_force_dag, genesis, block1, block2, block3, block4, block5, block6, block7,
                               block8, block9):
        """
        Tests coloring a big  phantom DAG.
        """
        brute_force_dag.add(genesis)
        brute_force_dag.add(block1)
        brute_force_dag.add(block2)
        brute_force_dag.add(block3)

        # gids: 0 <- 1, 2 <- 3
        # gids: 0 <- 4
        brute_force_dag.add(block4)

        # gids: 0 <- 1, 2 <- 3
        # gids: 0 <- 4 <- 5
        brute_force_dag.add(block5)

        # gids: 0 <- 1, 2 <- 3
        # gids: 0 <- 4 <- 5 <- 6
        brute_force_dag.add(block6)

        # test colorings for various K values
        brute_force_dag.set_k(0)
        # gids: {0, 4, 5, 6}
        assert brute_force_dag._get_coloring() == {hash(genesis), hash(block4), hash(block5), hash(block6)}

        brute_force_dag.set_k(1)
        # gids: {0, 1, 2, 3}
        assert brute_force_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3)}

        brute_force_dag.set_k(2)
        # gids: {0, 1, 3, 4, 5}
        assert brute_force_dag._get_coloring() == {hash(genesis), hash(block1), hash(block3), hash(block4),
                                                   hash(block5)}

        brute_force_dag.set_k(3)
        # gids: {0, 1, 2, 3, 4, 5}
        assert brute_force_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                   hash(block4), hash(block5)}

        brute_force_dag.set_k(4)
        # gids: {0, 1, 2, 3, 4, 5, 6}
        assert brute_force_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                   hash(block4), hash(block5), hash(block6)}

        # gids: 0 <- 1, 2 <- 3 <- 7
        # gids: 0 <- 4 <- 5 <- 6
        brute_force_dag.add(block7)

        # gids: 0 <- 1, 2 <- 3 <- 7 <- 8
        # gids: 0 <- 4 <- 5 <- 6
        brute_force_dag.add(block8)

        # gids: 0 <- 1, 2 <- 3 <- 7 <- 8 <- 9
        # gids: 0 <- 4 <- 5 <- 6
        brute_force_dag.add(block9)

        # test colorings for various K values
        brute_force_dag.set_k(0)
        # gids: {0, 1, 3, 7, 8, 9}
        assert brute_force_dag._get_coloring() == {hash(genesis), hash(block1), hash(block3), hash(block7),
                                                   hash(block8), hash(block9)}

        brute_force_dag.set_k(1)
        # gids: {0, 1, 2, 3, 7, 8, 9}
        assert brute_force_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                   hash(block7), hash(block8), hash(block9)}

        brute_force_dag.set_k(2)
        # gids: {0, 1, 2, 3, 7, 8, 9}
        assert brute_force_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                   hash(block7), hash(block8), hash(block9)}

        brute_force_dag.set_k(3)
        # gids: {0, 1, 2, 3, 7, 8, 9}
        assert brute_force_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                   hash(block7), hash(block8), hash(block9)}

        brute_force_dag.set_k(4)
        # gids: {0, 1, 2, 3, 4, 5, 6, 7}
        assert brute_force_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                   hash(block4), hash(block5), hash(block6), hash(block7)}

        brute_force_dag.set_k(5)
        # gids: {0, 1, 2, 3, 4, 5, 6, 7, 8}
        assert brute_force_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                   hash(block4), hash(block5), hash(block6), hash(block7), hash(block8)}

        brute_force_dag.set_k(6)
        # gids: {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
        assert brute_force_dag._get_coloring() == {hash(genesis), hash(block1), hash(block2), hash(block3),
                                                   hash(block4), hash(block5), hash(block6), hash(block7), hash(block8),
                                                   hash(block9)}

    @pytest.mark.topological_order
    def test_topological_order_advanced(self, brute_force_dag, genesis, block1, block2, block3, block4, block5, block6):
        """
        Advanced tests for the topological ordering on a small phantom DAG.
        """
        brute_force_dag.add(genesis)
        brute_force_dag.add(block1)
        brute_force_dag.add(block2)
        brute_force_dag.add(block3)

        # gids: 0 <- 1, 2 <- 3
        # gids: 0 <- 4
        brute_force_dag.add(block4)
        TestPHANTOM.assert_mapping(brute_force_dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2),
                                                     3: hash(block3), 4: hash(block4), 5: hash(block5),
                                                     6: hash(block6)})

        # gids: 0 <- 1, 2 <- 3
        # gids: 0 <- 4 <- 5
        brute_force_dag.add(block5)
        TestPHANTOM.assert_mapping(brute_force_dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2),
                                                     3: hash(block3), 4: hash(block4), 5: hash(block5),
                                                     6: hash(block6)})

        # gids: 0 <- 1, 2 <- 3
        # gids: 0 <- 4 <- 5 <- 6
        brute_force_dag.add(block6)

        # test colorings for various K values
        brute_force_dag.set_k(0)
        # gids: {0, 4, 5, 6}, lids: {0, 1, 2, 3}

        TestPHANTOM.assert_mapping(brute_force_dag, {0: hash(genesis), 4: hash(block1), 5: hash(block2),
                                                     6: hash(block3), 1: hash(block4), 2: hash(block5),
                                                     3: hash(block6)})

        brute_force_dag.set_k(1)
        # gids: {0, 1, 2, 3}, lids: {0, 1, 2, 3}
        TestPHANTOM.assert_mapping(brute_force_dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2),
                                                     3: hash(block3), 4: hash(block4), 5: hash(block5),
                                                     6: hash(block6)})

        brute_force_dag.set_k(2)
        # gids: {0, 1, 3, 4, 5}, lids: {0, 1, 3, 4, 5}
        TestPHANTOM.assert_mapping(brute_force_dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2),
                                                     3: hash(block3), 4: hash(block4), 5: hash(block5),
                                                     6: hash(block6)})

        brute_force_dag.set_k(3)
        # gids: {0, 1, 2, 3, 4, 5}, lids: {0, 1, 2, 3, 4, 5}
        TestPHANTOM.assert_mapping(brute_force_dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2),
                                                     3: hash(block3), 4: hash(block4), 5: hash(block5),
                                                     6: hash(block6)})

        brute_force_dag.set_k(4)
        # gids: {0, 1, 2, 3, 4, 5, 6}, lids: {0, 1, 2, 3, 4, 5, 6}
        TestPHANTOM.assert_mapping(brute_force_dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2),
                                                     3: hash(block3), 4: hash(block4), 5: hash(block5),
                                                     6: hash(block6)})
