import itertools as itrt
from collections import deque
from ordered_set import OrderedSet
from typing import Iterator, AbstractSet, Dict

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

import networkx as nx
import numpy as np

from phantom.dag import DAG, Block


class PHANTOM(DAG):
    """
    An implementation of the DAG for the SPECTRE 2 protocol.
    """

    # Dictionary key for the block of each block
    _BLOCK_DATA_KEY = "block_data"

    # Dictionary key for the local id of each block
    _LID_KEY = 'lid'

    # Dictionary key for the blue anticone of each block
    _BAC_KEY = 'blue_anticone'

    # The local id of the genesis.
    _GENESIS_LID = 0

    def __init__(self, k: int = None):
        super().__init__()

        self._G = nx.DiGraph()      # A nx directed graph object
        self._leaves = set()        # Set of all the leaves (in essence, the parents of the virtual block)
        self._coloring = set()      # Set of all the blue blocks according to the virtual block
        self._genesis_gid = None    # The global id of the genesis block

        # k is received as a parameter because the network delay and security parameters
        # can change over time, and because the DAG is only a container - the Miner is the
        # one that should care about these parameters, the PHANTOM DAG only cares about k.
        if k is None:
            k = self.calculate_k()

        self._k = k                 # the maximal blue anticone size for a blue block

    def __contains__(self, global_id: Block.GlobalID) -> bool:
        return global_id in self._G

    def __getitem__(self, global_id: Block.GlobalID) -> Block:
        return self._G.node[global_id][self._BLOCK_DATA_KEY]

    def __iter__(self) -> Iterator[Block.GlobalID]:
        return iter(self._G)

    def __len__(self) -> int:
        return len(self._G)

    def __str__(self) -> str:
        return str(list(self._G.edges()))

    def __get_past(self, global_id: Block.GlobalID):
        """
        :param global_id: global id of a block in the DAG.
        :return: the past of the block with the given global id.
        """
        return nx.descendants(self._G, global_id)

    def __get_future(self, global_id: Block.GlobalID):
        """
        :param global_id: global id of a block in the DAG.
        :return: the future of the block with the given global id.
        """
        return nx.ancestors(self._G, global_id)

    def __get_anticone(self, global_id: Block.GlobalID):
        """
        :param global_id: global id of a block in the DAG.
        :return: the anticone of the block with the given global id.
        """
        block_cone = {global_id}.union(self.__get_past(global_id), self.__get_future(global_id))
        return set(self._G.nodes()).difference(block_cone)

    def get_virtual_block_parents(self) -> AbstractSet[Block.GlobalID]:
        return self._leaves

    def add(self, block: Block):
        global_id = hash(block)
        parents = block.get_parents()

        # add the block to the phantom
        self._G.add_node(global_id)
        self._G.node[global_id][self._BLOCK_DATA_KEY] = block
        for parent in parents:
            self._G.add_edge(global_id, parent)

        # update the leaves
        self._leaves -= parents
        self._leaves.add(global_id)

        # update the coloring of the graph and everything related (the blue anticones and the topological order too)
        self._update_coloring_incrementally(global_id)
        self._update_topological_order_incrementally(global_id)

    def _update_coloring_incrementally(self, global_id: Block.GlobalID):
        """
        Updates the coloring of the phantom.
        The coloring is a maximal subset of the blocks V' such that for each v in V': |anticone(v, coloring)| <= k.
        :param global_id: the block to add to the coloring. Must be in the DAG.
        """
        def powerset(iterable):
            """powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"""
            s = list(iterable)
            return itrt.chain.from_iterable(itrt.combinations(s, r) for r in range(len(s) + 1))

        k = self._k

        def compute_blue_anticones(anticone_dict, coloring):
            """ Returns the blue anticones if the coloring is valid (
            for each v in coloring: |anticone(v, coloring)| <= k),
            else returns None. """
            blue_bacs = dict()
            for cur_block, anticone in anticone_dict.items():
                blue_bacs[cur_block] = anticone.intersection(coloring)
                if cur_block in coloring and len(blue_bacs[cur_block]) > k:
                    return None
            return blue_bacs

        # calculate the regular anticones
        anticones = dict()
        for block in self._G.nodes():
            anticones[block] = self.__get_anticone(block)

        # this is the brute force approach:
        # go over all colorings, and find the maximal valid one.
        max_coloring = set()
        max_coloring_bac = dict()

        for cur_coloring in powerset(self._G.nodes()):
            cur_coloring = set(cur_coloring)
            cur_coloring_bac = compute_blue_anticones(anticones, cur_coloring)

            if cur_coloring_bac is not None and len(cur_coloring) > len(max_coloring):
                max_coloring = cur_coloring
                max_coloring_bac = cur_coloring_bac

        self._coloring = max_coloring

        # update the blue anticones according to the new coloring
        for block, blue_anticone in max_coloring_bac.items():
            self._G.node[block][self._BAC_KEY] = blue_anticone

    @staticmethod
    def calculate_k(propagation_delay_parameter: float = 60, security_parameter: float = 0.1):
        """
        :param propagation_delay_parameter: the upper bound on the propagation delay, measured in seconds.
        :param security_parameter: the DAG's security parameter, it is a probability.
        :return: the parameter k as defined in the phantom paper.
        """
        # TODO: calculate k
        return 4

    def _set_parameters(self, parameters: Dict):
        """
        Sets all the given parameters.
        """
        new_dag = type(self)(**parameters)
        for global_id in self:
            new_dag.add(self[global_id])

        self.__dict__ = new_dag.__dict__

    def set_k(self, k: int):
        """
        :param k: the maximal anticone size for the blue blocks.
        """
        self._set_parameters({'k': k})

    def _is_blue(self, global_id: Block.GlobalID) -> bool:
        """
        :param global_id: global id of a block in the DAG.
        :return: True iff the block with the given global id is blue.
        """
        return global_id in self._coloring

    def _get_coloring(self):
        """
        :return: the global ids of all the blue blocks in the DAG.
        """
        return self._coloring

    def _update_topological_order_incrementally(self, global_id: Block.GlobalID):
        """
        Updates the topological order of the DAG.
        :param global_id: the global id of the newly added block.
        """
        class TopologicalOrderer:
            """
            Given a phantom, this class can output a topological order on each subset of the phantom.
            """

            def __init__(self, graph, coloring):
                """
                Initializes the topological orderer.
                :param graph: the graph to order.
                :param coloring: the coloring of G.
                """
                self._ordered = set()
                self._G = graph
                self._coloring = coloring

            def get_topological_order(self, leaves):
                """
                :param leaves: leaves of a phantom.
                :return: a list sorted according to a topological order on the input leaves and their ancestors.
                """
                cur_order = []
                leaves = leaves - self._ordered
                if len(leaves) == 0:
                    return cur_order

                blue_leaves_set = leaves.intersection(self._coloring)
                for leaf in sorted(blue_leaves_set) + sorted(leaves - blue_leaves_set):
                    self._ordered.add(leaf)
                    cur_leaf_order = self.get_topological_order(set(self._G.successors(leaf)))
                    cur_leaf_order.append(leaf)
                    cur_order.extend(cur_leaf_order)

                return cur_order

        new_order = TopologicalOrderer(self._G, self._coloring).get_topological_order(self._leaves)
        self._genesis_gid = next(iter(new_order), None)
        for new_lid, cur_gid in enumerate(new_order):
            self._G.node[cur_gid][self._LID_KEY] = new_lid

    def _get_local_id(self, global_id: Block.GlobalID) -> float:
        """
        :return: the local id of the block with the given global id.
        """
        return self._G.node[global_id][self._LID_KEY]

    def is_a_before_b(self, a: Block.GlobalID, b: Block.GlobalID):
        has_a = a in self
        has_b = b in self
        if not has_a and not has_b:
            return None
        if has_a and not has_b:
            return True
        if not has_a and has_b:
            return False
        return self._get_local_id(a) <= self._get_local_id(b)

    def get_depth(self, global_id: Block.GlobalID) -> float:
        # The notion of depth is the same for brute-force phantom as it is for the greedy phantom.
        # But, as the run-time complexity is so high, when the DAG is complex enough to actually query about a block's
        # depth, it will probably take too long to actually color the DAG and calculate the depth.
        return -float('inf')

    def _get_genesis_global_id(self) -> Block.GlobalID:
        """
        :return: the global id of the genesis block.
        """
        return self._genesis_gid

    def _get_draw_color(self, global_id: Block.GlobalID):
        """
        :param global_id: the global id of the block to be drawn.
        :return: a string of the color to use when drawing the block with the given global id
        """
        pass

    def draw(self, emphasized_blocks=set(), with_labels=False):
        def dag_layout(digraph, genesis_global_id: Block.GlobalID):
            """
            :param digraph: a networkx DiGraph.
            :param genesis_global_id: the block that should be the leftmost.
            :return: generates a layout positioning dictionary for the given DiGraph such that the block with the
            genesis global ID is the first (leftmost) block.
            """
            cur_height = 0
            blocks_left_in_cur_height = 1
            blocks_left_in_next_height = 0

            height_to_blocks = {cur_height: OrderedSet()}  # a mapping from height to all the blocks of that height
            blocks_to_height = {}   # a mapping between each block and its height

            block_queue = deque([genesis_global_id])
            while block_queue:
                block = block_queue.popleft()
                if block in blocks_to_height:
                    height_to_blocks[blocks_to_height[block]].remove(block)
                blocks_to_height[block] = cur_height
                height_to_blocks[cur_height].add(block)
                blocks_left_in_cur_height -= 1

                for child_gid in digraph.predecessors(block):
                    block_queue.append(child_gid)
                    blocks_left_in_next_height += 1

                if blocks_left_in_cur_height == 0:
                    cur_height += 1
                    height_to_blocks[cur_height] = OrderedSet()
                    blocks_left_in_cur_height = blocks_left_in_next_height
                    blocks_left_in_next_height = 0

            pos = {}  # the position dictionary for matplotlib's draw function
            for height, blocks in height_to_blocks.items():
                blocks_left_in_cur_height = len(blocks)
                cur_y = (blocks_left_in_cur_height - 1) / 2
                y_step_length = 1
                if blocks_left_in_cur_height != 1 and blocks_left_in_cur_height % 2 != 0:
                    y_step_length = 2 * (cur_y + 0.5) / blocks_left_in_cur_height
                for block in blocks:
                    pos[block] = np.asarray([height, cur_y])
                    cur_y -= y_step_length

            return pos

        plt.figure()

        genesis_color = 'orange'
        main_chain_color = 'blue'
        off_main_chain_color = 'red'

        if len(self) > 0:
            genesis_gid = self._get_genesis_global_id()
            block_colors = [genesis_color if gid == genesis_gid else
                            (main_chain_color if self._is_blue(gid) else off_main_chain_color)
                            for gid in self._G.nodes()]
            block_sizes = [750 if gid in emphasized_blocks else 250 for gid in self._G.nodes()]
            nx.draw_networkx(self._G,
                             pos=dag_layout(self._G, genesis_gid),
                             node_size=block_sizes,
                             node_color=block_colors,
                             with_labels=with_labels)

        genesis_patch = mpatches.Patch(color=genesis_color, label='Genesis block')
        main_chain_patch = mpatches.Patch(color=main_chain_color, label='Blocks on the main chain')
        off_main_chain_patch = mpatches.Patch(color=off_main_chain_color, label='Blocks off the main chain')
        plt.legend(handles=[genesis_patch, main_chain_patch, off_main_chain_patch])
        plt.show()
