import uuid
import sys
from collections import deque
from typing import Iterable, Union, Set

import networkx as nx
import numpy as np

from phantom.network_simulation.network import Network
from phantom.dag import Block, DAG


class Miner:
    """
    A miner on the network.
    """
    # A type for the miner name
    Name = str

    # Data key for the blocks in _block_queue
    _BLOCK_DATA_KEY = "to_add_block_data"

    def __init__(self,
                 name: Name,
                 dag: DAG,
                 max_peer_num: float,
                 block_size: Block.BlockSize,
                 fetch_requested_blocks: bool = False,
                 broadcast_added_blocks: bool = False):
        """
        Initializes the miner.
        :param name: the name of the miner.
        :param dag: the DAG the miner uses.
        :param max_peer_num: the miner's maximal number of peers.
        :param block_size: the maximal block size, in bytes.
        :param fetch_requested_blocks: True if the miner should fetch blocks requested from it that it doesn't have.
        :param broadcast_added_blocks: True if the miner should broadcast all blocks that it adds to its DAG.
        """
        self._name = name
        self._dag = dag
        self._max_peer_num = max_peer_num
        self._block_size = block_size
        self._fetch_requested_blocks = fetch_requested_blocks
        self._broadcast_added_blocks = broadcast_added_blocks

        self._block_queue = nx.DiGraph()  # a queue of blocks that are waiting to be added to the miner's DAG
        self._mined_blocks_gids: Set[Block.GlobalID] = set()
        self._network = None

    def set_network(self, network: Network):
        """
        Sets the miner's network.
        """
        self._network = network

    def __contains__(self, global_id: Block.GlobalID) -> bool:
        """
        :return: True iff the block with the given global id is in the miner's DAG
        """
        return global_id in self._dag

    def send_block(self, recipient_name: Name, global_id: Block.GlobalID):
        """
        If the block with the given global id exists in this miner's DAG, sends it to the miner with the given name
        If doesn't have the block, fetches it according to the miner's behavior.
        """
        if global_id in self._dag:
            self._network.send_block(self._name, recipient_name, self._dag[global_id])
        elif self._fetch_requested_blocks:
            self._fetch_block(global_id)

    def _broadcast_block(self, block):
        """
        Broadcasts the given block to all the network.
        """
        self._network.broadcast_block(self._name, block)

    def _fetch_block(self, block_gid):
        """
        Fetches the block with the given global id from the network.
        """
        self._network.fetch_block(self._name, block_gid)
        self._block_queue.add_node(block_gid)
        self._block_queue.node[block_gid][Miner._BLOCK_DATA_KEY] = None

    def _add_to_block_queue(self, block):
        """
        Adds the given block to the block queue, if necessary.
        :return: True iff the block was added to the queue.
        """
        missing_parent = False
        for parent_gid in block.get_parents():
            if parent_gid not in self._dag:
                missing_parent = True
                if parent_gid not in self._block_queue:
                    self._fetch_block(parent_gid)
                self._block_queue.add_edge(hash(block), parent_gid)

        if missing_parent:
            self._block_queue.node[hash(block)][Miner._BLOCK_DATA_KEY] = block
            return True

        return False

    def _basic_block_add(self, block):
        """
        Adds the given block without checking if its parents are present.
        """
        self._dag.add(block)
        if self._broadcast_added_blocks:
            self._broadcast_block(block)

    def _cascade_block_addition(self, block):
        """
        :param block:
        :return:
        """
        self._block_queue.node[hash(block)][Miner._BLOCK_DATA_KEY] = block
        addition_queue = deque([hash(block)])
        while addition_queue:
            cur_block_gid = addition_queue.popleft()
            if cur_block_gid not in self._block_queue:
                continue
            cur_block = self._block_queue.node[cur_block_gid][Miner._BLOCK_DATA_KEY]
            if cur_block is not None and np.bitwise_and.reduce([parent_gid in self._dag
                                                                for parent_gid in cur_block.get_parents()]):
                addition_queue.extend(self._block_queue.predecessors(hash(cur_block)))
                self._block_queue.remove_node(hash(cur_block))
                self._basic_block_add(cur_block)

    def _is_valid(self, block):
        """
        :return: True iff the block is valid according to the rules followed by the miner.
        """
        return sys.getsizeof(block) <= self._block_size

    def add_block(self, block: Block) -> bool:
        """
        Adds a given block to the miner's dag.
        :return: True iff adding the block was successful.
        """
        if not self._is_valid(block):
            return False

        if hash(block) in self._dag:
            return True

        if self._add_to_block_queue(block):
            return False

        if hash(block) in self._block_queue:
            self._cascade_block_addition(block)
        else:
            self._basic_block_add(block)

        return True

    def mine_block(self) -> Union[Block, None]:
        """
        :return: the mined block or None if mining was unsuccessful.
        """
        gid = hash(uuid.uuid4().int)
        block = Block(global_id=gid,
                      parents=self._dag.get_virtual_block_parents().copy(),
                      size=self._block_size,  # assume for the simulation's purposes that blocks are maximal
                      data=self._name)  # use the data field to hold the miner's name for better logs
        if not self.add_block(block):
            return None
        if not self._broadcast_added_blocks:
            # The block will be broadcast by _basic_block_add
            self._broadcast_block(block)
        self._mined_blocks_gids.add(gid)
        return block

    def discover_peers(self):
        """
        Adds peers up to the maximal defined amount.
        """
        self.add_peers(self._network.discover_peers(self._name, self._max_peer_num))

    def add_peers(self, peers: Iterable[Name]):
        """
        Adds the given miners as peers to this miner.
        """
        self._network.add_peers(self._name, peers)

    def remove_peers(self, peers: Iterable[Name]):
        """
        Unpeers the given miners from this miner.
        """
        self._network.remove_peers(self._name, peers)

    def get_depth(self, global_id: Block.GlobalID) -> int:
        """
        :return: the depth in the "main" sub-DAG of the block with the given global id if it exists in the miner's DAG.
        """
        return self._dag.get_depth(global_id)

    def draw_dag(self, with_labels: bool = False):
        """
        Draws the DAG of the miner.
        The bigger blocks are the ones mined by the miner.
        :param with_labels: prints node labels iff True.
        """
        self._dag.draw(self._mined_blocks_gids, with_labels)

    def get_name(self) -> Name:
        """
        :return: the name of the miner.
        """
        return self._name

    def get_mined_blocks(self) -> Set:
        """
        :return: a set of all the blocks mined by this Miner.
        """
        return self._mined_blocks_gids

    def __str__(self):
        """
        :return: a string representation of the miner.
        """
        return ', '.join([
            "miner: " + self._name,
            "DAG type: " + type(self._dag).__name__,
            "max block size: " + str(self._block_size),
            "max peer number: " + str(self._max_peer_num),
            "fetches requested blocks: " + str(self._fetch_requested_blocks),
            "broadcasts added blocks: " + str(self._broadcast_added_blocks)
        ])
