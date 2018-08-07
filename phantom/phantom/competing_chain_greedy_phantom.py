from typing import Set, AbstractSet
from collections import deque

from phantom.dag import Block, MaliciousDAG
from .greedy_phantom import GreedyPHANTOM


class CompetingChainGreedyPHANTOM(GreedyPHANTOM, MaliciousDAG):
    """
    A variant of the greedy phantom that allows a miner to mine a competing coloring chain.
    """

    # A block is confirmed if it is in the blue past of a block in the main coloring chain that
    # has at least X blue past (picked by the user))
    # publish the parallel chain when you see that the order is changed (success) or when you see that it is too
    # deep to be changed
    def __init__(self, k: int = None, confirmation_depth: int = 5, maximal_depth_difference: int = 5):
        super().__init__(k)

        # A copy of the honest sub-DAG of the current DAG
        self._honest_dag = GreedyPHANTOM(k)

        # The global id of hte bluest honest node
        self._bluest_honest_block_gid = None

        # The global id of the competing chains tip
        self._competing_chain_tip_gid = None

        # The global id of the currently attacked block
        self._currently_attacked_block_gid = None

        # The global id of the first block parallel to the currently attacked block
        self._first_parallel_block_gid = None

        # A set of the gids of the antipast blocks of the competing chain's tip
        self._competing_chain_tip_antipast = set()

        # The parents of the virtual çompeting chain's tip
        self._virtual_competing_chain_block_parents = set()

        # When a block's blue future is at least this amount, the block is considered to be confirmed
        self._confirmation_depth = confirmation_depth

        # Restart the attack when the blue past of the selfish tip is lagging by this amount
        self._maximal_depth_difference = maximal_depth_difference

        # A deque of all the global ids of the malicious blocks that are yet to be added to the honest DAG
        self._malicious_blocks_to_add_to_honest_dag = deque()

    def _get_competing_chain_tip_parents(self, tip_global_id: Block.GlobalID, tip_antipast: Set[Block.GlobalID],
                                         initial_parents: AbstractSet[Block.GlobalID]):
        """
        :return: a set of the bottom-most (closest to the leaves) blocks that don't overshadow the given selfish tip.
        """
        selfish_virtual_block_parents = set(initial_parents)
        visited = set(initial_parents)
        queue = deque()
        queue.extend(self.get_virtual_block_parents())
        while queue:
            gid = queue.popleft()
            if gid in visited or gid not in tip_antipast:
                continue
            visited.add(gid)

            if self._is_a_bluer_than_b(tip_global_id, gid):
                selfish_virtual_block_parents.add(gid)

                # removes all ancestors
                ancestor_queue = deque()
                ancestor_queue.extend(self._G.successors(gid))
                while ancestor_queue:
                    ancestor_gid = ancestor_queue.popleft()
                    if ancestor_gid not in tip_antipast:
                        continue
                    visited.add(ancestor_gid)
                    selfish_virtual_block_parents.discard(ancestor_gid)
                    ancestor_queue.extend(self._G.successors(ancestor_gid))
            else:
                queue.extend(self._G.predecessors(gid))

        return selfish_virtual_block_parents

    def did_attack_fail(self) -> bool:
        return (self._first_parallel_block_gid is None) or (self._currently_attacked_block_gid is None)

    def _add_malicious_blocks_to_honest_dag(self):
        """
        Adds the malicious blocks to the honest DAG.
        """
        while self._malicious_blocks_to_add_to_honest_dag:
            self._honest_dag.add(self[self._malicious_blocks_to_add_to_honest_dag.popleft()])

    def add(self, block: Block, is_malicious: bool = False):
        super().add(block)

        global_id = hash(block)
        if is_malicious:
            self._malicious_blocks_to_add_to_honest_dag.append(global_id)

            if self.did_attack_fail():
                self._first_parallel_block_gid = global_id

            # The malicious attack generates a chain, so the new tip is the current block
            self._competing_chain_tip_gid = global_id
            self._competing_chain_tip_antipast -= self._G.node[global_id][self._BLUE_DIFF_PAST_ORDER_KEY].keys()
            self._competing_chain_tip_antipast -= self._G.node[global_id][self._RED_DIFF_PAST_ORDER_KEY].keys()

            # Because we are under the assumption that a selfish miner has zero network latency and the
            # simulation design, the assumption is that no new blocks are mined between the moment a new
            # selfish block is mined and the moment it is added to the DAG
            self._virtual_competing_chain_block_parents = \
                self._get_competing_chain_tip_parents(global_id,
                                                      self._competing_chain_tip_antipast,
                                                      block.get_parents())
        else:
            # Add malicious blocks to the honest DAG as soon as possible
            if self.did_attack_fail():
                self._add_malicious_blocks_to_honest_dag()

            # This is possible because this is a competing chain attack,
            # where the honest chain doesn't include any malicious blocks
            self._honest_dag.add(block)

        if self.did_attack_succeed():
            self._add_malicious_blocks_to_honest_dag()

        if not self.did_attack_fail():
            # need to update the data structure only if in the middle of a (seemingly) successful attack
            self._competing_chain_tip_antipast.add(global_id)
            if global_id == self._competing_chain_tip_gid or \
                    self._is_a_bluer_than_b(self._competing_chain_tip_gid, global_id):
                self._virtual_competing_chain_block_parents -= block.get_parents()
                self._virtual_competing_chain_block_parents.add(global_id)
            elif not self._is_attack_viable():
                self._stop_attack()

    def _stop_attack(self):
        """
        Ends the current attack.
        """
        self._add_malicious_blocks_to_honest_dag()
        self._competing_chain_tip_gid = None
        self._first_parallel_block_gid = None

    def _restart_attack(self):
        """
        Starts a new attack.
        """
        self._stop_attack()
        self._competing_chain_tip_antipast = set(self._honest_dag._antipast)
        self._currently_attacked_block_gid = self._honest_dag._coloring_tip_gid
        self._virtual_competing_chain_block_parents = \
            self._get_competing_chain_tip_parents(self._currently_attacked_block_gid,
                                                  self._competing_chain_tip_antipast,
                                                  self[self._honest_dag._coloring_tip_gid].get_parents())

    def _is_attack_viable(self) -> bool:
        if self.did_attack_fail():
            # The previous attack failed, so there is no attack currently,
            # meaning that a new attack is viable.
            return True

        # An attack is viable iff the blue history difference between the honest and selfish tips is lower than the
        # maximal gap that the user defined
        return (self._G.node[self._coloring_tip_gid][self._BLUE_NUMBER_KEY] -
                self._G.node[self._competing_chain_tip_gid][self._BLUE_NUMBER_KEY]) <= self._maximal_depth_difference

    def get_virtual_block_parents(self, is_malicious: bool = False) -> AbstractSet[Block.GlobalID]:
        if (not is_malicious) or (len(self) <= 1):
            return super().get_virtual_block_parents()
        if self.did_attack_fail():
            self._restart_attack()
        return self._virtual_competing_chain_block_parents

    def did_attack_succeed(self) -> bool:
        if self.did_attack_fail():
            return False

        return (self.get_depth(self._first_parallel_block_gid) >= self._confirmation_depth) and \
               (self._honest_dag.get_depth(self._currently_attacked_block_gid) >= self._confirmation_depth) and \
            self.is_a_before_b(self._first_parallel_block_gid, self._currently_attacked_block_gid)

    def set_k(self, k: int):
        """
        :param k: the maximal anticone size for the blue blocks.
        """
        self._set_parameters({'k': k,
                              'confirmation_depth': self._confirmation_depth,
                              'maximal_depth_difference': self._maximal_depth_difference})
