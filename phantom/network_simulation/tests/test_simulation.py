import pytest

from typing import Callable, Iterable

from phantom.dag import Block, DAG, MaliciousDAG
from phantom.phantom import GreedyPHANTOM
from phantom.network_simulation import Simulation
from phantom.network_simulation.run_simulation import competing_chain_constructor_with_parameters


class TestSimulation:
    """
    Test suite for the Simulation class.
    """
    ALL_HASH_RATES = [[], [1], [2, 3, 4, 5.5]]
    POISSON_PARAMETERS = [1, 5]
    PROBABILITIES = [0, 0.5, 1]
    MIN_MINER_COUNTS = [1, 5]
    MAX_MINER_COUNTS = MIN_MINER_COUNTS + [float('inf')]
    BLOCK_SIZES = [1, round((1 << 20) / 3)]
    BOOLEAN_VALUES = [False, True]

    @pytest.mark.parametrize("honest_hash_rates", ALL_HASH_RATES)
    @pytest.mark.parametrize("malicious_hash_rates", ALL_HASH_RATES)
    @pytest.mark.parametrize("block_creation_rate", POISSON_PARAMETERS)
    @pytest.mark.parametrize("propagation_delay_parameter", POISSON_PARAMETERS)
    @pytest.mark.parametrize("security_parameter", PROBABILITIES)
    @pytest.mark.parametrize("simulation_length", [0, 100])
    @pytest.mark.parametrize("honest_dag_init", [GreedyPHANTOM])
    @pytest.mark.parametrize("malicious_dag_init", [competing_chain_constructor_with_parameters(1, 1),
                                                    competing_chain_constructor_with_parameters(8, 8),
                                                    ])
    @pytest.mark.parametrize("median_speed", BLOCK_SIZES)
    @pytest.mark.parametrize("max_block_size", BLOCK_SIZES)
    @pytest.mark.parametrize("max_peer_number", MAX_MINER_COUNTS)
    @pytest.mark.parametrize("fetch_requested_blocks", BOOLEAN_VALUES)
    @pytest.mark.parametrize("broadcast_added_blocks", BOOLEAN_VALUES)
    @pytest.mark.parametrize("no_delay_for_malicious_miners", BOOLEAN_VALUES)
    @pytest.mark.parametrize("completely_connected_malicious_miners", BOOLEAN_VALUES)
    @pytest.mark.parametrize("simulate_miner_join_leave", BOOLEAN_VALUES)
    @pytest.mark.parametrize("max_miner_count", MAX_MINER_COUNTS)
    @pytest.mark.parametrize("min_miner_count", MIN_MINER_COUNTS)
    @pytest.mark.parametrize("miner_join_rate", POISSON_PARAMETERS)
    @pytest.mark.parametrize("miner_leave_rate", POISSON_PARAMETERS)
    @pytest.mark.parametrize("hash_rate_parameter", POISSON_PARAMETERS)
    @pytest.mark.parametrize("malicious_miner_probability", PROBABILITIES)
    @pytest.mark.parametrize("printing", BOOLEAN_VALUES)
    @pytest.mark.parametrize("logging", BOOLEAN_VALUES)
    @pytest.mark.parametrize("save_simulation", BOOLEAN_VALUES)
    def test_sanity(self,
                    honest_hash_rates: Iterable[float],
                    malicious_hash_rates: Iterable[float],
                    block_creation_rate: int,
                    propagation_delay_parameter: int,
                    security_parameter: float,
                    simulation_length: int,
                    honest_dag_init: Callable[..., DAG],
                    malicious_dag_init: Callable[..., MaliciousDAG],
                    median_speed: Block.BlockSize,
                    max_block_size: Block.BlockSize,
                    max_peer_number: int,
                    fetch_requested_blocks: bool,
                    broadcast_added_blocks: bool,
                    no_delay_for_malicious_miners: bool,
                    completely_connected_malicious_miners: bool,
                    simulate_miner_join_leave: bool,
                    max_miner_count: float,
                    min_miner_count: int,
                    miner_join_rate: int,
                    miner_leave_rate: int,
                    hash_rate_parameter: int,
                    malicious_miner_probability: float,
                    printing: bool,
                    logging: bool,
                    save_simulation: bool):
        """
        Sanity tests for the simulation.
        """
        simulation = Simulation(honest_hash_rates=honest_hash_rates,
                                malicious_hash_rates=malicious_hash_rates,
                                block_creation_rate=block_creation_rate,
                                propagation_delay_parameter=propagation_delay_parameter,
                                security_parameter=security_parameter,
                                simulation_length=simulation_length,
                                honest_dag_init=honest_dag_init,
                                malicious_dag_init=malicious_dag_init,
                                median_speed=median_speed,
                                max_block_size=max_block_size,
                                max_peer_number=max_peer_number,
                                fetch_requested_blocks=fetch_requested_blocks,
                                broadcast_added_blocks=broadcast_added_blocks,
                                no_delay_for_malicious_miners=no_delay_for_malicious_miners,
                                completely_connected_malicious_miners=completely_connected_malicious_miners,
                                simulate_miner_join_leave=simulate_miner_join_leave,
                                max_miner_count=max_miner_count,
                                min_miner_count=min_miner_count,
                                miner_join_rate=miner_join_rate,
                                miner_leave_rate=miner_leave_rate,
                                hash_rate_parameter=hash_rate_parameter,
                                malicious_miner_probability=malicious_miner_probability,
                                enable_printing=printing,
                                enable_logging=logging,
                                save_simulation=save_simulation)
        simulation.run()
        assert True
