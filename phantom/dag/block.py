from collections.abc import Hashable
from typing import AbstractSet


class Block(Hashable):
    """
    An implementation of a generic block.
    Some terminology:
    Global ID of a block - the hash of the block.
    """
    GlobalID = int
    BlockSize = float

    def __init__(self, global_id: GlobalID = 0,
                 parents: AbstractSet[GlobalID] = frozenset(),
                 size: BlockSize = 0,
                 data: Hashable = None):
        """
        Initializes the block.
        :param global_id: the global id of the block.
        :param parents: the global ids of this block's parent blocks
        :param size: the size of the block.
        :param data: optional, additional data included in the block.
        """
        self._gid = global_id
        self._parents = parents
        self._size = size
        self._data = data

    def get_parents(self) -> AbstractSet[GlobalID]:
        """
        :return: the global ids of this block's parent blocks.
        """
        return self._parents

    def __hash__(self):
        return self._gid

    def __str__(self):
        return "Block: " + str(self._gid) + ", parents: " + ', '. join([str(parent) for parent in self._parents])

    def __sizeof__(self):
        return max(self._size - 24, 0)  # need to account for python's garbage collection overhead
