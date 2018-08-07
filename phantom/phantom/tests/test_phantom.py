import pytest
from itertools import product


class TestPHANTOM:
    """
    Test suite for the basic functionality of all phantom DAGs.
    """

    @pytest.mark.data_structure
    def test_constructor(self, dag):
        """
        Tests the constructor.
        """
        assert len(dag) == 0
        assert dag.get_virtual_block_parents() == set()

    @pytest.mark.data_structure
    def test_adding_genesis(self, dag, genesis):
        """
        Tests adding the genesis block.
        """
        dag.add(genesis)
        assert len(dag) == 1
        assert hash(genesis) in dag
        assert dag[hash(genesis)] == genesis
        assert dag.get_virtual_block_parents() == {hash(genesis)}

    @pytest.mark.data_structure
    def test_adding_multiple_blocks(self, dag, genesis, block1, block2, block3):
        """
        Creates a small phantom DAG and checks that adding multiple blocks works correctly.
        """
        dag.add(genesis)

        dag.add(block1)   # graph should look like this: 0 <- 1
        assert len(dag) == 2
        assert hash(block1) in dag
        assert dag[hash(block1)] == block1
        assert dag.get_virtual_block_parents() == {hash(block1)}

        dag.add(block2)   # graph should look like this: 0 <- 1, 2
        assert len(dag) == 3
        assert hash(block2) in dag
        assert dag[hash(block2)] == block2
        assert dag.get_virtual_block_parents() == {hash(block1), hash(block2)}

        dag.add(block3)   # graph should look like this: 0 <- 1, 2 <- 3
        assert len(dag) == 4
        assert hash(block3) in dag
        assert dag[hash(block3)] == block3
        assert dag.get_virtual_block_parents() == {hash(block3)}

    @staticmethod
    def assert_mapping(dag, correct_mapping):
        """
        Given a DAG, verifies that its mapping is identical to correct_mapping using a series of is_a_before_b queries.
        """
        for lid1, lid2 in product(correct_mapping, correct_mapping):
            gid1 = correct_mapping[lid1]
            gid2 = correct_mapping[lid2]
            if gid1 not in dag and gid2 not in dag:
                correct_result = None
            elif lid1 == lid2:
                correct_result = True
            else:
                correct_result = lid1 < lid2
            assert dag.is_a_before_b(gid1, gid2) is correct_result

    @pytest.mark.topological_order
    def test_topological_order_basic(self, dag, genesis, block1, block2, block3, block4):
        """
        Simple tests for the topological ordering on a small phantom DAG.
        """
        dag.set_k(4)

        TestPHANTOM.assert_mapping(dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2), 3: hash(block3),
                                         4: hash(block4)})

        dag.add(genesis)
        TestPHANTOM.assert_mapping(dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2), 3: hash(block3),
                                         4: hash(block4)})

        dag.add(block1)   # graph should look like this: 0 <- 1
        TestPHANTOM.assert_mapping(dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2), 3: hash(block3),
                                         4: hash(block4)})

        dag.add(block2)   # graph should look like this: 0 <- 1, 2
        TestPHANTOM.assert_mapping(dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2), 3: hash(block3),
                                         4: hash(block4)})

        dag.add(block3)   # graph should look like this: 0 <- 1, 2 <- 3
        TestPHANTOM.assert_mapping(dag, {0: hash(genesis), 1: hash(block1), 2: hash(block2), 3: hash(block3),
                                         4: hash(block4)})
