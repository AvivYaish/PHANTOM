import os
import sys
import copy
import random
import logging
import jsonpickle
from time import strftime

import numpy
import simpy
import simpy.util

from phantom.dag import Block, DAG, MaliciousDAG
from .miner import Miner, MaliciousMiner
from .network import Network

from typing import Callable, Iterable


class Simulation:
    """
    The main network_simulation event loop.
    """

    # Default path to save all result files
    _DEFAULT_RESULTS_PATH = os.path.join(os.getcwd(), "results")

    # Default path for the log files
    _DEFAULT_LOG_PATH = os.path.join(_DEFAULT_RESULTS_PATH, "logs")

    # Suffix for log files
    _LOG_FILE_SUFFIX = ".log"

    # Default path for the simulation files
    _DEFAULT_SIMULATION_PATH = os.path.join(_DEFAULT_RESULTS_PATH, "simulation")

    # Suffix for simulation files
    _SIMULATION_FILE_SUFFIX = ".json"

    def __init__(self,
                 honest_hash_rates: Iterable[float],
                 malicious_hash_rates: Iterable[float],
                 block_creation_rate: int,
                 propagation_delay_parameter: int,
                 security_parameter: float,
                 simulation_length: int,
                 honest_dag_init: Callable[..., DAG],
                 malicious_dag_init: Callable[..., MaliciousDAG],
                 median_speed: Block.BlockSize = 1 << 20,
                 max_block_size: Block.BlockSize = 1 << 20,
                 max_peer_number: float = 5,
                 fetch_requested_blocks: bool = False,
                 broadcast_added_blocks: bool = False,
                 no_delay_for_malicious_miners: bool = True,
                 completely_connected_malicious_miners: bool = True,
                 simulate_miner_join_leave: bool = False,
                 max_miner_count: float = float('inf'),
                 min_miner_count: int = 1,
                 miner_join_rate: int = 1000,
                 miner_leave_rate: int = 1000,
                 hash_rate_parameter: int = 2,
                 malicious_miner_probability: float = 0.1,
                 enable_printing: bool = False,
                 enable_logging: bool = False,
                 save_simulation: bool = False):
        """
        Initializes the simulation.
        :param honest_hash_rates: a list of hash-rates that defines the initial hash distribution among honest miners.
        :param malicious_hash_rates: a list of hash-rates that defines the initial hash distribution among malicious
        miners.
        :param block_creation_rate: the parameter defining the Poisson block generation process,
        called lambda in the phantom paper. Measured in seconds.
        :param propagation_delay_parameter: the upper bound on the propagation delay,
        also called Dmax in the paper. Measured in seconds.
        :param security_parameter: the security parameter called delta in the paper. It is a probability.
        :param simulation_length: the simulation length in seconds (simulated seconds, not actual real world ones!)
        :param honest_dag_init: the constructor to be used when creating honest DAGs.
        :param malicious_dag_init: the constructor to be used when creating malicious DAGs.
        :param median_speed: the median inter-Miner connection speed, in MB/s.
        :param max_block_size: the maximal block size to be used by the miners.
        :param max_peer_number: the maximal number of peers for miners on the network.
        :param fetch_requested_blocks: True if the miners on the network should fetch blocks requested from them
        that they don't have.
        :param broadcast_added_blocks: True if the miners on the network should broadcast every block they add.
        :param no_delay_for_malicious_miners: True if malicious miners should have no network delay.
        :param completely_connected_malicious_miners: True if malicious miners should be connected to every node on the
        network. Note that this only affects blocks that the malicious miners wants to send.
        :param simulate_miner_join_leave: True if the simulation should add/remove miners on the fly.
        :param max_miner_count: the maximal number of miners to be simulated.
        :param min_miner_count: the minimal number of miners to be simulated.
        :param miner_join_rate: the rate at which the simulation should add miners to the network.
        :param miner_leave_rate: the rate at which the simulation should remove miners from the network.
        :param hash_rate_parameter: the parameter for the hash-rate distribution among newly added miners.
        :param malicious_miner_probability: the probability with which the simulation should pick a malicious miner as
        the miner to add to the simulation.
        :param enable_printing: True if the simulation should print the logs on the screen.
        :param enable_logging: True if the simulation should save the logs to a file.
        :param save_simulation: True if a copy of the simulation object should be saved to a file.
        """
        self._logging = enable_logging
        self._save_simulation = save_simulation

        self._honest_hash_rates = honest_hash_rates
        self._malicious_hash_rates = malicious_hash_rates

        self._no_delay_for_malicious_miners = no_delay_for_malicious_miners
        self._completely_connected_malicious_miners = completely_connected_malicious_miners
        self._propagation_delay_parameter = propagation_delay_parameter
        self._security_parameter = security_parameter
        self._block_creation_rate = block_creation_rate
        self._simulation_length = simulation_length

        # To be honest, median speed doesn't really matter as the parameter can be "tucked into"
        # the propagation delay parameter, but it is useful for unit conversion - by dividing block
        # sizes that are in MBs by a median speed which is in MB/s, we get delay in seconds.
        self._median_speed = median_speed
        self._max_block_size = max_block_size

        self._max_peer_number = max_peer_number
        self._fetch_requested_blocks = fetch_requested_blocks
        self._broadcast_added_blocks = broadcast_added_blocks

        self._miner_count = 0
        self._simulate_miner_join_leave = simulate_miner_join_leave
        self._max_miner_count = max_miner_count
        self._min_miner_count = min_miner_count
        self._miner_join_rate = miner_join_rate
        self._miner_leave_rate = miner_leave_rate
        self._hash_rate_parameter = hash_rate_parameter
        self._malicious_miner_probability = malicious_miner_probability

        self._honest_dag_init = honest_dag_init
        self._malicious_dag_init = malicious_dag_init

        self._env = simpy.Environment()
        self._attack_success_event = self._env.event()

        if enable_printing or enable_logging:
            logging_handlers = []
            if enable_logging:
                os.makedirs(self._DEFAULT_LOG_PATH, exist_ok=True)
                logging_handlers.append(
                    logging.FileHandler(
                        os.path.join(self._DEFAULT_LOG_PATH, self._get_filename() + self._LOG_FILE_SUFFIX), mode='w+'))
            if enable_printing:
                logging_handlers.append(logging.StreamHandler(stream=sys.stdout))

            logging.basicConfig(level=logging.INFO, format='%(message)s', handlers=logging_handlers)

        self._network = Network(self._propagation_delay_parameter, self._median_speed,
                                self._no_delay_for_malicious_miners, self._completely_connected_malicious_miners,
                                self._honest_dag_init(), self)
        for hash_rate in honest_hash_rates:
            self._add_miner(hash_rate=hash_rate,
                            discover_peers=False,
                            is_malicious=False)
        for hash_rate in malicious_hash_rates:
            self._add_miner(hash_rate=hash_rate,
                            discover_peers=False,
                            is_malicious=True)
        # Let the miners discover peers only after adding them all
        for miner_name in self._network:
            self._network[miner_name].discover_peers()

    def _log(self, text: str):
        """
        Logs the given text with the network_simulation's current timestamp.
        """
        logging.info("Time: " + str(self._env.now) + ", " + text)

    def _block_generator_process(self) -> simpy.Event:
        """
        Generates blocks at a poisson rate with miners picked according to the hash-rate distribution.
        """
        while True:
            if len(self._network) > 0:
                miner = self._network.get_random_miner(according_to_hash_rate=True)
                block = miner.mine_block()
                self._log(str(miner.get_name()) + " mined " + str(block))
            else:
                self._log("no miners left to mine blocks.")

            yield self._env.timeout(numpy.random.poisson(self._block_creation_rate))

    def _add_miner(self,
                   hash_rate: float,
                   discover_peers: bool = True,
                   is_malicious: bool= False) -> Miner:
        """
        Generates a miner according to the given parameter, adds it to the simulation and returns it.
        """
        self._miner_count += 1

        if is_malicious:
            miner_name = "M"
            dag_init = self._malicious_dag_init
            miner_init = MaliciousMiner
        else:
            miner_name = "H"
            dag_init = self._honest_dag_init
            miner_init = Miner
        miner_name += str(self._miner_count)

        miner = miner_init(miner_name, dag_init(), self._max_peer_number, self._max_block_size,
                           self._fetch_requested_blocks, self._broadcast_added_blocks)
        self._network.add_miner(miner=miner,
                                hash_rate=hash_rate,
                                is_malicious=is_malicious,
                                discover_peers=discover_peers)
        return miner

    def _miner_adder_process(self) -> simpy.Event:
        """
        Adds miners at a poisson rate.
        """
        while len(self._network) < self._max_miner_count:
            miner = self._add_miner(hash_rate=numpy.random.poisson(self._hash_rate_parameter),
                                    discover_peers=True,
                                    is_malicious=random.random() < self._malicious_miner_probability)
            self._log("added: " + str(miner))

            yield self._env.timeout(numpy.random.poisson(self._miner_join_rate))

    def _miner_remover_process(self) -> simpy.Event:
        """
        Removes miners at a poisson rate.
        """
        while True:
            if len(self._network) > self._min_miner_count:
                miner = self._network.get_random_miner(according_to_hash_rate=False)
                self._network.remove_miner(miner.get_name())
                self._log("removed: " + str(miner))
            else:
                self._log("no miner to remove")

            yield self._env.timeout(numpy.random.poisson(self._miner_leave_rate))

    def _check_if_block_needed(self, sender_name: Miner.Name, receiver_name: Miner.Name, gid: Block.GlobalID) -> bool:
        """
        :return: True iff the sending of the block with the given global id is possible and needed.
        """
        # The miners by default try to send blocks to a peer, even if a peer already has them.
        # This behavior that can thrash the event queue with unneeded events - events that take negligible
        # time in the "real world" slow down the simulation considerably and unnecessarily.
        # This function is used in order to prevent this from happening.
        sender = self._network[sender_name]
        receiver = self._network[receiver_name]
        return (sender is not None and gid in sender) and (receiver is not None and gid not in receiver)

    def send_block(self, sender_name: Miner.Name, receiver_name: Miner.Name, block: Block, delay_time: float):
        """
        Adds the given block to the miner after the given delay time (given in simulation time-steps).
        """

        def send_block_process(env):
            if self._check_if_block_needed(sender_name, receiver_name, hash(block)):
                receiver = self._network[receiver_name]
                self._log("sending " + str(hash(block)) + " from " + sender_name + " to " + receiver_name)
                receiver.add_block(copy.deepcopy(block))
            yield env.timeout(0)

        # if the sending is still needed, add an event for it
        if self._check_if_block_needed(sender_name, receiver_name, hash(block)):
            if delay_time <= 0:
                delay_time = 0.0001
            simpy.util.start_delayed(self._env, send_block_process(self._env), delay_time)

    def draw_network(self, with_labels: bool = False):
        """
        Draws the network topology.
        """
        self._network.draw_network(with_labels)

    def draw_dag(self, miner_name: Miner.Name = None, with_labels: bool = False):
        """
        Draws the DAG of the given miner name (or of of the total network DAG if no name was specified).
        """
        if miner_name:
            self._network[miner_name].draw_dag(with_labels)
        else:
            self._network.draw_total_network_dag(with_labels)

    def run(self) -> bool:
        """
        Runs the network_simulation.
        :return: True iff the attack succeeded.
        """
        self._log(str(self) + "\nSimulation start!")
        self._env.process(self._block_generator_process())
        if self._simulate_miner_join_leave:
            self._env.process(self._miner_adder_process())
            self._env.process(self._miner_remover_process())

        self._env.run(until=simpy.events.AnyOf(self._env, [self._attack_success_event,
                                                           self._env.timeout(self._simulation_length)]))

        return self.end()

    def attack_success(self):
        if not self._attack_success_event.triggered:
            self._attack_success_event.succeed()
            self._log("attack succeeded")

    def end(self) -> bool:
        """
        Ends the simulation.
        :return: True iff the attack succeeded.
        """
        if not self._attack_success_event.triggered:
            self._log("attack failed")

        self._log("simulation ended")
        self._log(str(self._network))

        # self.draw_network()
        # self.draw_dag("M6")

        if self._save_simulation:
            self.save()

        return self._attack_success_event.triggered

    def __str__(self):
        """
        :return: a string representation of the simulation.
        """
        simulation_params = "Simulation is run with the following parameters: \n" + \
                            "Simulation length: " + str(self._simulation_length) + "\n" + \
                            "Block generation rate: " + str(self._block_creation_rate)
        return simulation_params + "\nUsing the following network configuration: " + str(self._network)

    def _get_filename(self) -> str:
        """
        :return: the name representing this Simulation.
        """
        return '_'.join([
            strftime("%Y%m%d-%H%M%S"),
            str(self._honest_hash_rates),
            str(self._malicious_hash_rates),
            str(self._block_creation_rate),
            str(self._propagation_delay_parameter),
            str(self._security_parameter),
            str(self._simulation_length),
            str(self._median_speed),
            str(self._max_block_size),
            str(self._fetch_requested_blocks),
            str(self._broadcast_added_blocks),
            str(self._no_delay_for_malicious_miners),
            str(self._completely_connected_malicious_miners),
        ])

    def save(self, path: os.PathLike = None):
        """
        Saves the current simulation to the given path in a file named:
        time_parameters_attackStatus
        Note: the event queue isn't saved!
        """
        if path is None:
            path = self._DEFAULT_SIMULATION_PATH

        temp_env = self._env
        self._env = None
        temp_attack_success_event = self._attack_success_event
        self._attack_success_event = None

        json = jsonpickle.encode(self)

        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "simulation_" + self._get_filename() + self._SIMULATION_FILE_SUFFIX), "w+") as f:
            f.write(json)

        self._env = temp_env
        self._attack_success_event = temp_attack_success_event
        return json

    @classmethod
    def load(cls, filename: os.PathLike):
        """
        Loads the simulation saved in the given file.
        """
        # Note: ._env and ._attack_success_event are reset.
        with open(filename, "r") as f:
            simulation = jsonpickle.decode(f.read())
            simulation._env = simpy.Environment()
            simulation._attack_success_event = simulation._env.event()
            return simulation
