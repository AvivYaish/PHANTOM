from lazy_set import LazySet
from ordered_set import OrderedSet
from collections import deque, ChainMap, namedtuple
from typing import Iterable, Iterator, AbstractSet, Collection, Dict, Union, List, Tuple

from .phantom import PHANTOM
from phantom.dag import Block


class GreedyPHANTOM(PHANTOM):
    """
    A greedy implementation of the DAG for the phantom protocol.
    """
    # The type for the order values
    OrderValue = Union[int, None]

    # The type for order dictionaries
    OrderDict = Dict[Block.GlobalID, OrderValue]

    # A data structure for chains such that the total number of blue blocks added by each consecutive block is <= k.
    # global_ids is a set of all chain blocks, minimal_height is the height of the earliest chain block.
    KChain = namedtuple('KChain', ['global_ids', 'minimal_height'])

    # Dictionary key for the order on the blue blocks in the past of the block that the
    # block added to the coloring.
    _BLUE_DIFF_PAST_ORDER_KEY = 'blue_diff_order'

    # Dictionary key for the order on the red blocks in the past of the block that the
    # block added to the coloring.
    _RED_DIFF_PAST_ORDER_KEY = 'red_diff_order'

    # Dictionary key for the index of the current block (self) in its own topological ordering.
    _SELF_ORDER_INDEX_KEY = 'self_order_index'

    # Dictionary key for the height of the block in the DAG.
    _HEIGHT_KEY = 'height_key'

    # Dictionary key for the total number of blue blocks in the block's past.
    _BLUE_NUMBER_KEY = 'blue_blocks_number'

    # Dictionary key for the global id of the parent from which the coloring is inherited.
    _COLORING_PARENT_KEY = 'coloring_parent'

    def __init__(self, k: int = None):
        super().__init__(k)

        self._coloring_tip_gid = None  # The gid of the tip of the coloring chain
        self._coloring_chain = set()   # A set of the coloring chain
        self._k_chain = self.KChain(set(), float('inf'))  # The "main" k-chain

        # The various data structures to hold the coloring and ordering of the DAG
        self._blue_past_order = ChainMap()
        self._red_past_order = ChainMap()

        # The antipast is in essence the diffpast between the virtual block and its coloring parent,
        # who is simply the coloring tip of the entire DAG.
        self._blue_antipast_order = dict()
        self._red_antipast_order = dict()
        self._uncolored_unordered_antipast = LazySet()

        # Some unifying data structures to make coloring and ordering easier
        self._past_order = ChainMap(self._blue_past_order, self._red_past_order)
        self._antipast_order = ChainMap(self._blue_antipast_order, self._red_antipast_order)
        self._antipast = ChainMap(self._antipast_order).keys() | self._uncolored_unordered_antipast
        self._coloring_order = ChainMap(self._blue_past_order, self._blue_antipast_order)

        # The coloring is in essence the virtual block's coloring of the entire DAG
        self._coloring = self._coloring_order.keys()

        # The mapping is in essence the virtual block's ordering of the entire DAG
        self._mapping = ChainMap(self._past_order, self._antipast_order)

    def _clear_antipast_order(self):
        """
        Clears the various data structures that hold the antipast order.
        """
        self._blue_antipast_order = dict()
        self._red_antipast_order = dict()

        # Update the antipast order with the new dictionaries
        self._antipast_order.maps.pop()
        self._antipast_order.maps.pop()
        self._antipast_order.maps.append(self._blue_antipast_order)
        self._antipast_order.maps.append(self._red_antipast_order)

        # Update the coloring order with the new dictionaries
        self._coloring_order.maps.pop()
        self._coloring_order.maps.append(self._blue_antipast_order)

    def _is_blue(self, global_id: Block.GlobalID) -> bool:
        self._update_antipast_coloring()
        return super()._is_blue(global_id)

    def _get_coloring(self) -> AbstractSet[Block.GlobalID]:
        self._update_antipast_coloring()
        return super()._get_coloring()

    def _get_local_id(self, global_id: Block.GlobalID) -> float:
        if (self._mapping.get(global_id, None) is None) or self._uncolored_unordered_antipast:
            self._update_antipast_coloring()
            self._update_topological_order_in_dicts(self._blue_antipast_order, self._red_antipast_order, self._leaves,
                                                    self._coloring_tip_gid)

        local_id = self._mapping.get(global_id, None)
        if local_id is None:
            local_id = float('inf')

        return local_id

    def _get_extreme_blue(self, global_ids: Collection[Block.GlobalID], bluest: bool = False) -> Block.GlobalID:
        """
        :return: the "extreme" (either max/min) block in the DAG according to its number of blue past blocks.
        """
        if len(global_ids) == 0:
            return None

        if bluest:
            func = max
        else:
            func = min

        # note that max/min finds the first parent with the maximal/minimal amount of blue blocks in its history,
        # and because the parents are sorted according to their gids - it also finds the correct one
        # according to the tie breaking rule
        return func(sorted(global_ids), key=lambda gid: self._G.node[gid][self._BLUE_NUMBER_KEY])

    def _get_bluest(self, global_ids: Collection[Block.GlobalID]) -> Block.GlobalID:
        """
        :param global_ids: a collection of global ids of blocks in the DAG.
        :return: the global id of the block with the largest blue history.
        """
        return self._get_extreme_blue(global_ids, True)

    def _coloring_chain_generator(self, tip_global_id: Block.GlobalID) -> Iterator[int]:
        """
        A generator for the coloring chain ending with the given tip.
        """
        cur_gid = tip_global_id
        while cur_gid is not None:
            yield cur_gid
            cur_gid = self._G.node[cur_gid][self._COLORING_PARENT_KEY]

    def _local_tip_to_global_tip_generator(self, local_tip_global_id: Block.GlobalID) -> \
            Tuple[Block.GlobalID, bool, bool]:
        """
        Walks on the local tip's chain until it intersects the main coloring chain,
        and then goes from the tip of the main coloring chain until the intersection again.
        """
        CurrentChainBlock = namedtuple('CurrentChainBlock',
                                       ['global_id', 'is_main_coloring_chain', 'is_intersection'])
        intersection_gid = None
        for cur_chain_gid in self._coloring_chain_generator(local_tip_global_id):
            if cur_chain_gid in self._coloring_chain:
                intersection_gid = cur_chain_gid
                yield CurrentChainBlock(intersection_gid, True, True)
                break

            yield CurrentChainBlock(cur_chain_gid, False, False)

        for cur_chain_gid in self._coloring_chain_generator(self._coloring_tip_gid):
            if cur_chain_gid == intersection_gid:
                break

            yield CurrentChainBlock(cur_chain_gid, True, False)

    def _get_coloring_chain(self, global_id: Block.GlobalID, length: float = float("inf")) -> LazySet:
        """
        :param global_id: the global id of the last block of the chain. Block must be in the DAG.
        :param length: optional, a cutoff for the number of blocks in the chain.
        :return: a LazySet of the global ids of blocks in the coloring chain of the given global id.
        The coloring chain is simply a chain ending with a block, such that for each block, the block before him
        in the chain is his "coloring parent".
        """
        infinite_length = length == float("inf")
        main_chain_intersection_gid = None
        base_set = set()
        positive_fork = set()
        negative_fork = set()
        count = 0

        for cur_gid in self._coloring_chain_generator(global_id):
            if count >= length + 1:
                break

            # Note that for complete coloring chains it is enough to find the first coloring ancestor block
            # that is in the main coloring chain - continuing past this point is pointless
            if cur_gid in self._coloring_chain and infinite_length:
                main_chain_intersection_gid = cur_gid
                break

            positive_fork.add(cur_gid)
            count += 1

        if infinite_length and (main_chain_intersection_gid is not None):
            base_set = self._coloring_chain
            for cur_gid in self._coloring_chain_generator(self._coloring_tip_gid):
                if cur_gid == main_chain_intersection_gid:
                    break
                negative_fork.add(cur_gid)
                count += 1

        return LazySet(base_set, [negative_fork], [positive_fork])

    def _coloring_rule_2(self, k_chain: KChain, global_id: Block.GlobalID) -> bool:
        """
        :param k_chain: the chain to color the block according to.
        :param global_id: the block to test whether is blue or not.
        :return: True iff the block with the given global id is blue according to the second coloring rule.
        """
        for cur_chain_block_gid in self._coloring_chain_generator(global_id):
            if self._G.node[cur_chain_block_gid][self._HEIGHT_KEY] < k_chain.minimal_height:
                return False
            if cur_chain_block_gid in k_chain.global_ids:
                return True
        return False

    def _coloring_rule_3(self, k_chain: KChain, global_id: Block.GlobalID) -> bool:
        """
        :param k_chain: the chain to color the block according to.
        :param global_id: the block to test whether is blue or not.
        :return: True iff the block with the given global id is blue according to the third coloring rule.
        """
        depth = 0
        for cur_chain_block_gid in self._coloring_chain_generator(global_id):
            if (self._G.node[cur_chain_block_gid][self._HEIGHT_KEY] < k_chain.minimal_height) or (depth > self._k):
                return False
            if cur_chain_block_gid in k_chain.global_ids:
                return True
            depth += len(self._G.node[cur_chain_block_gid][self._BLUE_DIFF_PAST_ORDER_KEY])
        return False

    def _color_block(self, blue_order: OrderDict, red_order: OrderDict,
                     k_chain: KChain, global_id: Block.GlobalID):
        """
        Colors (assigns to the correct ordering dictionary) the block with the given global id
        according to the coloring rule.
        """
        if self._coloring_rule_2(k_chain, global_id):
            blue_order[global_id] = None
        else:
            red_order[global_id] = None

    def _get_k_chain(self, global_id: Block.GlobalID) -> KChain:
        """
        :return: the k-chain that the block with the given global id is the tip of.
        """
        chain_blocks = set()
        minimal_height = float('inf')
        blue_count = 0

        for cur_chain_block_gid in self._coloring_chain_generator(global_id):
            if blue_count > self._k:
                break

            chain_blocks.add(cur_chain_block_gid)
            minimal_height = self._G.node[cur_chain_block_gid][self._HEIGHT_KEY]
            blue_count += len(self._G.node[cur_chain_block_gid][self._BLUE_DIFF_PAST_ORDER_KEY])

        return self.KChain(chain_blocks, minimal_height)

    def _update_diff_coloring_of_block(self, global_id: Block.GlobalID):
        """
        Updates the diff coloring data of the block with the given global id.
        :param global_id: the global id of the block to update the diff coloring for. Must be in the DAG.
        """
        blue_diff_past_order = {}
        red_diff_past_order = {}
        k_chain = self._get_k_chain(global_id)
        parent_antipast = self._get_antipast(self._G.node[global_id][self._COLORING_PARENT_KEY])

        # Go over diff past and color all the blocks there according to the newly added block's coloring chain.
        # Note that because a block considers itself part of its antipast, it won't include itself in its coloring!
        # This doesn't make any difference whatsoever - it just subtracts 1 from all the blue past counts
        diff_past_queue = deque(self._G.successors(global_id))
        while diff_past_queue:
            block_to_color_gid = diff_past_queue.popleft()
            if (block_to_color_gid in blue_diff_past_order) or (block_to_color_gid in red_diff_past_order) or \
                    (block_to_color_gid not in parent_antipast):
                continue

            diff_past_queue.extendleft(self._G.successors(block_to_color_gid))
            self._color_block(blue_diff_past_order, red_diff_past_order, k_chain, block_to_color_gid)

        # update the coloring block with the details of his coloring
        self._G.node[global_id][self._BLUE_DIFF_PAST_ORDER_KEY] = blue_diff_past_order
        self._G.node[global_id][self._RED_DIFF_PAST_ORDER_KEY] = red_diff_past_order
        self._G.node[global_id][self._BLUE_NUMBER_KEY] += \
            len(self._G.node[global_id][self._BLUE_DIFF_PAST_ORDER_KEY])

    def _is_a_bluer_than_b(self, a: Block.GlobalID, b: Block.GlobalID) -> bool:
        """
        :return: True iff the global id a is "bluer" than b
        """
        a_blue_number = self._G.node[a][self._BLUE_NUMBER_KEY]
        b_blue_number = self._G.node[b][self._BLUE_NUMBER_KEY]
        return a_blue_number > b_blue_number or a_blue_number == b_blue_number and a < b

    def _is_max_coloring_tip(self, global_id: Block.GlobalID) -> bool:
        """
        :return: True iff the given global id is of the block that is the max coloring tip of the DAG.
        """
        if self._coloring_tip_gid is None:
            return True
        return self._is_a_bluer_than_b(global_id, self._coloring_tip_gid)

    def _get_past(self, global_id: Block.GlobalID) -> AbstractSet[Block.GlobalID]:
        """
        :return: the past of the block with the given global id.
        """
        if global_id is None:
            return set()

        positive_chain, negative_chain = ChainMap(), ChainMap()
        for cur_chain_gid, is_main_coloring_chain, is_intersection in \
                self._local_tip_to_global_tip_generator(global_id):
            if is_intersection:
                continue
            if not is_main_coloring_chain:
                append_to = positive_chain.maps
            else:
                append_to = negative_chain.maps
            append_to.append(self._G.node[cur_chain_gid][self._BLUE_DIFF_PAST_ORDER_KEY])
            append_to.append(self._G.node[cur_chain_gid][self._RED_DIFF_PAST_ORDER_KEY])

        return LazySet(base_set=self._past_order.keys(), negative_sets=[negative_chain.keys()],
                       positive_sets=[positive_chain.keys()])

    def _get_antipast(self, global_id: Block.GlobalID) -> AbstractSet[Block.GlobalID]:
        """
        :return: the antipast of the block with the given global id.
        """
        if global_id is None:
            return self._mapping.keys()

        if global_id == self._coloring_tip_gid:
            return self._antipast

        positive_sets, negative_sets = [], []
        for cur_chain_gid, is_main_coloring_chain, is_intersection in \
                self._local_tip_to_global_tip_generator(global_id):
            if not is_main_coloring_chain or is_intersection:
                append_to = negative_sets
            else:
                append_to = positive_sets
            append_to.append(self._G.node[cur_chain_gid][self._BLUE_DIFF_PAST_ORDER_KEY].keys())
            append_to.append(self._G.node[cur_chain_gid][self._RED_DIFF_PAST_ORDER_KEY].keys())

        antipast = LazySet(base_set=self._antipast, positive_sets=positive_sets)
        for negative_set in negative_sets:
            antipast.lazy_difference_update(negative_set)

        # See the remark on antipast usage in _update_past_coloring_according_to
        # antipast.flatten()

        return antipast

    def _update_past_coloring_according_to(self, new_tip_gid: Block.GlobalID):
        """
        Updates the max DAG coloring of all the blocks in the past of new tip.
        :param new_tip_gid: the new max coloring tip to color the DAG according to.
        """
        self._uncolored_unordered_antipast.lazy_update(self._blue_antipast_order.keys())
        self._uncolored_unordered_antipast.lazy_update(self._red_antipast_order.keys())
        self._clear_antipast_order()

        # Add the tips to the antipast
        self._uncolored_unordered_antipast.add(new_tip_gid)
        if (self._coloring_tip_gid is not None) and (self._coloring_tip_gid in self._blue_antipast_order):
            self._uncolored_unordered_antipast.add(self._coloring_tip_gid)

        blue_diff_past_orderings = []
        red_diff_past_orderings = []
        for cur_chain_gid, is_main_coloring_chain, is_intersection in \
                self._local_tip_to_global_tip_generator(new_tip_gid):
            if is_intersection:
                # The intersection is common for both the old coloring chain and the new one,
                # so there is no reason to make any modifications
                continue
            if is_main_coloring_chain:
                self._coloring_chain.remove(cur_chain_gid)
                self._uncolored_unordered_antipast.lazy_update(self._blue_past_order.maps.pop().keys())
                self._uncolored_unordered_antipast.lazy_update(self._red_past_order.maps.pop().keys())
            else:
                self._coloring_chain.add(cur_chain_gid)
                blue_diff_past_orderings.append(self._G.node[cur_chain_gid][self._BLUE_DIFF_PAST_ORDER_KEY])
                red_diff_past_orderings.append(self._G.node[cur_chain_gid][self._RED_DIFF_PAST_ORDER_KEY])

        for blue_diff_past_order, red_diff_past_order in zip(blue_diff_past_orderings, red_diff_past_orderings):
            self._blue_past_order.maps.append(blue_diff_past_order)
            self._red_past_order.maps.append(red_diff_past_order)

            self._uncolored_unordered_antipast.lazy_difference_update(blue_diff_past_order.keys())
            self._uncolored_unordered_antipast.lazy_difference_update(red_diff_past_order.keys())

        self._coloring_tip_gid = new_tip_gid

        # Full disclosure: depending on the use-cases, using a non flat LazySet here can be either good or bad:
        # Commenting out the line below will cause changing the max coloring to take O(# of blocks on the path from
        # the old coloring tip to the new one) instead of O(total # of blocks in all the diffpasts of the blocks on the
        # path from the old coloring tip to the new one), but will cause coloring the diff-past of any new block to
        # potentially take much longer (# of sets in _uncolored_unordered_antipast, which in theory has no limit unless
        # the antipast was ordered/colored).
        self._uncolored_unordered_antipast.flatten(modify=True)

    def _update_antipast_coloring(self):
        """
        Updates the coloring of the antipast of the new coloring tip.
        """
        # Note that for most intents and purposes, there is no reason to actually color the
        # antipast, it is only useful when being queried on order of blocks in the antipast,
        # but again that is also irrelevant for almost all uses.
        for global_id in self._uncolored_unordered_antipast:
            self._color_block(self._blue_antipast_order, self._red_antipast_order, self._k_chain, global_id)
        self._uncolored_unordered_antipast.clear()

    def _update_max_coloring(self, global_id: Block.GlobalID):
        """
        Updates the max coloring of the DAG with the block with the given global id.
        :param global_id: the global id of the block to update the coloring with. Must be in the DAG.
        :return: True iff the block is the new coloring tip.
        """
        if self._is_max_coloring_tip(global_id):
            self._update_past_coloring_according_to(global_id)
            self._k_chain = self._get_k_chain(global_id)
            if self._get_genesis_global_id() not in self._coloring_chain:
                self._genesis_gid = self._get_extreme_blue(self._coloring_chain, bluest=False)

    def _update_coloring_incrementally(self, global_id: Block.GlobalID):
        # Update block's coloring data
        parents = self._G.node[global_id][self._BLOCK_DATA_KEY].get_parents()
        self._G.node[global_id][self._SELF_ORDER_INDEX_KEY] = None
        self._G.node[global_id][self._COLORING_PARENT_KEY] = \
            self._get_bluest(parents)
        self._G.node[global_id][self._BLUE_DIFF_PAST_ORDER_KEY] = set()
        self._G.node[global_id][self._RED_DIFF_PAST_ORDER_KEY] = set()

        if self._G.node[global_id][self._COLORING_PARENT_KEY] is not None:
            self._G.node[global_id][self._HEIGHT_KEY] = \
                max(self._G.node[parent][self._HEIGHT_KEY] for parent in parents) + 1
            self._G.node[global_id][self._BLUE_NUMBER_KEY] = \
                self._G.node[self._G.node[global_id][self._COLORING_PARENT_KEY]][self._BLUE_NUMBER_KEY]
        else:
            self._G.node[global_id][self._HEIGHT_KEY] = 0
            self._G.node[global_id][self._BLUE_NUMBER_KEY] = 0

        # Update the virtual block's view of the current block
        self._uncolored_unordered_antipast.add(global_id)

        self._update_diff_coloring_of_block(global_id)
        self._update_max_coloring(global_id)

    def _calculate_topological_order(self, coloring_parent_gid: Block.GlobalID, leaves: AbstractSet[Block.GlobalID],
                                     coloring: AbstractSet[Block.GlobalID], unordered: AbstractSet[Block.GlobalID]) \
            -> Iterable[Block.GlobalID]:
        """
        :param coloring_parent_gid: the coloring parent of the sub-DAG to order.
        :param leaves: leaves of the sub-DAG to order.
        :param coloring: the coloring of the sub-DAG to order.
        :param unordered: all the unordered blocks in the sub-DAG to order.
        :return: an iterable sorted according to a topological order on the input leaves and their ancestors.
        """
        def sort_blocks(last_block_gid: Block.GlobalID,
                        later_blocks: AbstractSet[Block.GlobalID],
                        to_sort: AbstractSet,
                        unsorted: AbstractSet[Block.GlobalID]) -> \
                List[Block.GlobalID]:
            """
            :return: a reversely sorted list of the blocks in to_sort.
            """
            remaining_gids = (to_sort - {last_block_gid}) & unsorted

            # Sort the blue blocks
            blue_gids_set = remaining_gids & later_blocks
            blue_gids_list = sorted(blue_gids_set, reverse=True)

            # Sort the red blocks
            red_gids_list = sorted(remaining_gids - blue_gids_set, reverse=True)

            # last_block is the coloring parent
            if last_block_gid is not None:
                blue_gids_list.append(last_block_gid)
            return red_gids_list + blue_gids_list

        to_order = list(sort_blocks(coloring_parent_gid, coloring, leaves, unordered))
        ordered = OrderedSet()
        while to_order:
            cur_gid = to_order.pop()
            if cur_gid in ordered:
                continue

            cur_parents = set(self._G.successors(cur_gid)) & unordered
            if cur_parents <= ordered:
                ordered.append(cur_gid)
            else:
                to_order.append(cur_gid)
                to_order.extend(sort_blocks(self._G.node[cur_gid][self._COLORING_PARENT_KEY], coloring, cur_parents,
                                            unordered))

        return ordered

    def _update_topological_order_in_dicts(self, blue_dict: OrderDict, red_dict: OrderDict,
                                           leaves: AbstractSet[Block.GlobalID], coloring_parent_gid: Block.GlobalID):
        """
        Updates the topological order of the blocks contained in the given dictionaries.
        :param blue_dict: the dictionary that holds all blue blocks to be ordered.
        :param red_dict: the dictionary that holds all red blocks to be ordered.
        :param leaves: leaves of the sub-DAG to order.
        :param coloring_parent_gid: the coloring parent of the sub-DAG to order.
        """

        if (coloring_parent_gid is not None) and \
                (self._G.node[coloring_parent_gid][self._SELF_ORDER_INDEX_KEY] is not None):
            starting_index = self._G.node[coloring_parent_gid][self._SELF_ORDER_INDEX_KEY]
        else:
            starting_index = 0
        for new_lid, cur_gid in enumerate(self._calculate_topological_order(coloring_parent_gid, leaves,
                                                                            blue_dict.keys(),
                                                                            ChainMap(blue_dict, red_dict).keys())):
            new_lid = new_lid + starting_index
            if cur_gid in blue_dict:
                blue_dict[cur_gid] = new_lid
            else:
                red_dict[cur_gid] = new_lid

    def _update_self_order_index(self, global_id: Block.GlobalID):
        """
        Updates the order index of the block with the given global id according to its own topological order.
        """
        # Uses the invariant that the coloring parent's diffpast and self order index are correct,
        # and that for each block, its coloring parent is always the first in the topological ordering of its
        # diff past (anything behind it is in the diffpast of the coloring parent, and thus definitely not in the
        # diffpast of the block itself)
        self._G.node[global_id][self._SELF_ORDER_INDEX_KEY] = \
            len(self._G.node[global_id][self._BLUE_DIFF_PAST_ORDER_KEY]) + \
            len(self._G.node[global_id][self._RED_DIFF_PAST_ORDER_KEY])
        coloring_parent_gid = self._G.node[global_id][self._COLORING_PARENT_KEY]
        if coloring_parent_gid is not None and \
                self._G.node[coloring_parent_gid][self._SELF_ORDER_INDEX_KEY] is not None:
            self._G.node[global_id][self._SELF_ORDER_INDEX_KEY] += \
                self._G.node[coloring_parent_gid][self._SELF_ORDER_INDEX_KEY]

    def _update_topological_order_incrementally(self, global_id: Block.GlobalID):
        """
        Updates the topological order of the DAG.
        """
        # Update the topological order of the diffpast
        self._update_topological_order_in_dicts(self._G.node[global_id][self._BLUE_DIFF_PAST_ORDER_KEY],
                                                self._G.node[global_id][self._RED_DIFF_PAST_ORDER_KEY],
                                                self[global_id].get_parents(),
                                                self._G.node[global_id][self._COLORING_PARENT_KEY])
        self._update_self_order_index(global_id)

    def get_depth(self, global_id: Block.GlobalID) -> float:
        # The notion of depth is defined to be the number of blue blocks added to the "main chain" after
        # the first main chain block that colored blue the block with global id global_id.
        if global_id not in self:
            return -float('inf')

        if global_id in self._antipast:
            return 0

        depth = 1
        for cur_gid in self._coloring_chain_generator(self._coloring_tip_gid):
            if global_id in self._G.node[cur_gid][self._RED_DIFF_PAST_ORDER_KEY]:
                return 0
            if global_id in self._G.node[cur_gid][self._BLUE_DIFF_PAST_ORDER_KEY]:
                return depth
            depth += len(self._G.node[cur_gid][self._BLUE_DIFF_PAST_ORDER_KEY])

        return 0