from typing import AbstractSet
from abc import abstractmethod

from phantom.dag import Block, DAG


class MaliciousDAG(DAG):
    """
    An interface for a malicious DAG.
    """

    # Note that probably different types of attacks need different methods.
    # As a design choice, the actual handling of the "DAG-side" of the attack is relegated
    # to the DAG, and not to the miner, as the current state of the attack can affect various
    # DAG functions, for example - the parents of the virtual block. In Addition, various
    # aspects of the attack might need information that is hidden from outside classes.

    @abstractmethod
    def get_virtual_block_parents(self, is_malicious: bool = False) -> AbstractSet[Block.GlobalID]:
        """
        :param is_malicious: True iff the requested parents are for the virtual malicious block.
        :return: a set containing the global ids of the parents of the virtual honest/malicious block.
        """
        pass

    @abstractmethod
    def did_attack_succeed(self) -> bool:
        """
        :return: True iff the current attack succeeded.
        """
        pass

    @abstractmethod
    def did_attack_fail(self) -> bool:
        """
        :return: True iff the current attack failed.
        """
        pass
