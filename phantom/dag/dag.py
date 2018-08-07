from typing import AbstractSet, Iterator
from collections.abc import Collection
from abc import abstractmethod

from phantom.dag import Block


class DAG(Collection):
    """
    An interface for a DAG based blockchain.
    Some terminology:
    Virtual block - a block that an "honest" miner would add to the top of the current DAG.
    Topological order of the DAG - the ordering of the blocks amongst themselves as seen by DAG. This is used to answer
    questions like "Did block a come before block y?"
    Local ID of a block - the numerical index of the block according to the DAG's topological order, starting 0 for the
    "first" block and |V| for the "last" block.
    """

    @abstractmethod
    def __init__(self):
        """
        Initializes the DAG.
        """
        pass

    @abstractmethod
    def __contains__(self, global_id: Block.GlobalID):
        """
        :return: True iff the block with the given global id is in the DAG
        """
        pass

    @abstractmethod
    def __getitem__(self, global_id: Block.GlobalID) -> Block:
        """
        :return: the data of the block with the given global id if it exists in the DAG.
        """
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[Block]:
        """
        :return: an iterator on the DAG's blocks.
        """
        pass

    @abstractmethod
    def __len__(self):
        """
        :return: the number of blocks in the DAG.
        """
        pass

    @abstractmethod
    def __str__(self):
        """
        :return: a string representation of the DAG.
        """
        pass

    @abstractmethod
    def get_virtual_block_parents(self) -> AbstractSet[Block.GlobalID]:
        """
        :return: a set containing the global ids of the parents of the virtual block.
        """
        # This function is a part of the DAG's interface as an "honest" design choice -
        # honest miners should use a DAG protocol as a black box, not knowing and not being able
        # to change anything.
        # Conceptually, it will probably be better to separate the DAG itself (who should take
        # care of the "coloring" and ordering of blocks) from any mining-relevant activity
        # (for example, deciding which blocks should be the ancestors of the to-be-mined block)
        pass

    @abstractmethod
    def add(self, block: Block):
        """
        Adds the given block to the DAG.
        """
        pass

    @abstractmethod
    def is_a_before_b(self, a: Block.GlobalID, b: Block.GlobalID) -> bool:
        """
        :param a: global id of a block.
        :param b: global id of a block.
        :return: None if both blocks aren't in the DAG.
        Otherwise, True iff the block with global id a is before the block
        with global id b according to the DAG's ordering.
        """
        pass

    @abstractmethod
    def get_depth(self, global_id: Block.GlobalID) -> int:
        """
        :return: the depth in the "main" sub-DAG of the block with the given global id if it exists in the DAG.
        """
        pass

    @abstractmethod
    def draw(self, emphasized_blocks: AbstractSet = frozenset(), with_labels: bool = False):
        """
        Draws the DAG as a graph.
        :param emphasized_blocks: a set of global ids of blocks that should be drawn in a bigger size,
        for emphasis, if they exist in the DAG.
        :param with_labels: prints node global ids iff True.
        """
        pass
