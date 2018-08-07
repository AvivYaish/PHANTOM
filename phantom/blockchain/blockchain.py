import matplotlib.pyplot as plt
from phantom.dag import DAG
import networkx as nx
import copy


class Blockchain(DAG):
    """
    An implementation of the blockchain protocol.
    """

    # Dictionary key for the total number of blocks in the block's past
    _CHAIN_LENGTH_KEY = "chain_length"

    # Dictionary key for the block's data
    _BLOCK_DATA_KEY = "block_data"

    def __init__(self):
        super().__init__()
        self._G = nx.DiGraph()      # A nx directed graph object
        self._leaves = set()        # Set of all the leaves
        self._longest_chain_tip_gid = None
        self._longest_chain = set()

    def get_virtual_block_parents(self):
        if self._longest_chain_tip_gid is None:
            return set()
        return {self._longest_chain_tip_gid}

    def _get_longest_chain_tip(self, global_ids):
        """
        :param global_ids: a container of global ids of blocks in the DAG.
        :return: the global id of the block which is the tip of the longest chain.
        """
        if len(global_ids) == 0:
            return None

        # note that max finds the first tip which fulfills the requirements,
        # and because the tips are sorted according to their gids - it also finds the correct one
        # according to the tie breaking rule
        return max(sorted(global_ids), key=lambda gid: self._G.node[gid][Blockchain._CHAIN_LENGTH_KEY])

    def __contains__(self, global_id):
        return global_id in self._G

    def __getitem__(self, global_id):
        return self._G.node[global_id][self._BLOCK_DATA_KEY]

    def __iter__(self):
        return iter(self._G)

    def __len__(self):
        return len(self._G)

    def __str__(self):
        return str(self._G)

    def add(self, block):
        copy_gid = copy.deepcopy(hash(block))
        parent = self._get_longest_chain_tip(block.get_parents())   # O(1), as each block has only one parent
        chain_length = 1
        if parent is not None:
            chain_length += self._G.node[parent][Blockchain._CHAIN_LENGTH_KEY]

        # add the block to the DAG
        self._G.add_node(copy_gid)
        self._G.node[copy_gid][Blockchain._CHAIN_LENGTH_KEY] = chain_length
        self._G.node[copy_gid][Blockchain._BLOCK_DATA_KEY] = block
        if parent is not None:
            self._G.add_edge(copy_gid, parent)

        # update the leaves
        if parent is not None and parent in self._leaves:
            self._leaves.remove(parent)
        self._leaves.add(copy_gid)

        # update the longest chain if necessary
        self._update_longest_chain_incrementally(copy_gid, parent)

    def _update_longest_chain_incrementally(self, global_id, parent):
        """
        Updates the longest chain with the given block global id.
        """
        chain_length = self._G.node[global_id][Blockchain._CHAIN_LENGTH_KEY]
        if (self._longest_chain_tip_gid is None) or \
            (chain_length > self._G.node[self._longest_chain_tip_gid][Blockchain._CHAIN_LENGTH_KEY]) or \
            (chain_length == self._G.node[self._longest_chain_tip_gid][Blockchain._CHAIN_LENGTH_KEY] and
             global_id < self._longest_chain_tip_gid):

            previous_tip_gid = self._longest_chain_tip_gid
            self._longest_chain_tip_gid = global_id
            if parent == previous_tip_gid:
                self._longest_chain.add(global_id)
            else:
                chain_intersection_gid = None
                to_add = set()
                for gid, lid in self._chain_generator(global_id):
                    if gid in self._longest_chain:
                        chain_intersection_gid = gid
                        break
                    to_add.add(gid)
                for gid, lid in self._chain_generator(previous_tip_gid):
                    if gid == chain_intersection_gid:
                        break
                    self._longest_chain.remove(gid)
                self._longest_chain |= to_add

    def _chain_generator(self, tip_gid):
        """
        :return: generator for a chain starting with the given tip and going backwards.
        """
        gid = tip_gid
        if gid is None:
            return set()
        counter = self._G.node[gid][Blockchain._CHAIN_LENGTH_KEY] - 1

        while counter >= 0:
            yield gid, counter

            gid = self._get_longest_chain_tip(list(self._G.successors(gid)))
            counter -= 1

    def _get_chain(self, tip_gid=None):
        """
        :return: the longest chain as a set.
        """
        if tip_gid is None:
            tip_gid = self._longest_chain_tip_gid
        return {gid: lid for gid, lid in self._chain_generator(tip_gid)}

    def get_depth(self, global_id):
        if global_id not in self:
            return -float('inf')
        if global_id not in self._longest_chain:
            return 0
        return self._G.node[self._longest_chain_tip_gid][Blockchain._CHAIN_LENGTH_KEY] - \
            self._G.node[global_id][Blockchain._CHAIN_LENGTH_KEY]

    def is_a_before_b(self, a, b):
        a_in = a in self._longest_chain
        b_in = b in self._longest_chain
        if (not a_in) and (not b_in):
            return None
        if (not a_in) and b_in:
            return False
        if a_in and (not b_in):
            return True
        return self._G.node[a][Blockchain._CHAIN_LENGTH_KEY] <= self._G.node[b][Blockchain._CHAIN_LENGTH_KEY]

    def draw(self, emphasized_blocks=set(), with_labels=False):
        # could probably use phantom's draw here, but for design purposes I
        # don't want to move the common code to DAG/create an ancestor class/use some form of composition
        plt.figure()
        nx.draw_networkx(self._G,
                         pos=nx.spring_layout(self._G, k=10, iterations=10000),
                         node_color=['red' if gid not in self._get_chain() else 'blue'
                                     for gid in self._G.nodes()],
                         node_size=[500 if gid in emphasized_blocks else 250 for gid in self._G.nodes()],
                         with_labels=with_labels,
                         font_size=8)
        plt.show()
