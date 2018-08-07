"""
A run script that runs the simulation multiple times with various parameters
and generates statistics regarding the success rate of the chosen attack.
"""
import os
import time
import numpy
import pickle
import itertools
import seaborn
import matplotlib.pyplot as pyplot

from statistics import variance
from pathos.multiprocessing import ProcessingPool as Pool
from scipy.stats import norm as normal_dist
from typing import Iterator, Dict, Any, Iterable, Tuple, List, Callable

from phantom.network_simulation import Simulation
from phantom.network_simulation.run_simulation import greedy_constructor_with_parameters, \
    competing_chain_constructor_with_parameters, generate_hash_rates

# Default path to save all result files
DEFAULT_RESULTS_PATH = os.path.join(os.getcwd(), "results")

# Default path to save all graph result files
DEFAULT_GRAPH_PATH = os.path.join(DEFAULT_RESULTS_PATH, "graphs")

# The type of a simulation parameter dictionary
SimulationParameterDictionary = Dict[str, Any]

# The number of processes to use
PROCESS_NUM = 8

# Minimal number of times to iterate on every combination of parameters
MIN_ITERATION_NUMBER = 100

# The maximal error for the attack success rate
MAX_ERROR = 0.05

# Default block size in bytes.
DEFAULT_BLOCK_SIZE = 1 << 20

# The default max neighbor num
DEFAULT_MAX_PEER_NUM = 8

# Dictionary keys for the various parameters
K_KEY = "k"
CONFIRMATION_DEPTH_KEY = "confirmation_depth"
MALICIOUS_HASH_RATIO_KEY = "malicious_hash_ratio"
NUMBER_OF_HONEST_MINERS_KEY = "number_of_honest_miners"
HONEST_HASH_RATES_KEY = "honest_hash_rates"
BLOCKS_PER_MINUTE_KEY = "blocks_per_minute"
SIMULATION_LENGTH_IN_MINUTES_KEY = "simulation_length_in_minutes"
MAXIMAL_DEPTH_DIFFERENCE_KEY = "maximal_depth_difference"
MALICIOUS_HASH_RATES_KEY = "malicious_hash_rates"
BLOCK_CREATION_RATE_KEY = "block_creation_rate"
PROPAGATION_DELAY_PARAMETER_KEY = "propagation_delay_parameter"
SECURITY_PARAMETER_KEY = "security_parameter"
SIMULATION_LENGTH_KEY = "simulation_length"
HONEST_DAG_INIT_KEY = "honest_dag_init"
MALICIOUS_DAG_INIT_KEY = "malicious_dag_init"
MEDIAN_SPEED_KEY = "median_speed"
MAX_BLOCK_SIZE_KEY = "max_block_size"
MAX_PEER_NUMBER_KEY = "max_peer_number"
FETCH_REQUESTED_BLOCKS_KEY = "fetch_requested_blocks"
BROADCAST_ADDED_BLOCKS_KEY = "broadcast_added_blocks"
NO_DELAY_FOR_MALICIOUS_MINERS_KEY = "no_delay_for_malicious_miners"
COMPLETELY_CONNECTED_MALICIOUS_MINERS_KEY = "completely_connected_malicious_miners"
SIMULATE_MINER_JOIN_LEAVE_KEY = "simulate_miner_join_leave"
HASH_RATE_PARAMETER_KEY = "hash_rate_parameter"
ENABLE_PRINTING_KEY = "enable_printing"
ENABLE_LOGGING_KEY = "enable_logging"
SAVE_SIMULATION_KEYS = "save_simulation"


def generate_simulation_parameters(parameters_to_update: SimulationParameterDictionary) -> \
        SimulationParameterDictionary:
    """
    :return: a {param_name: param_value} dict that can be passed as a parameter to the Simulation constructor.
    """
    k = parameters_to_update.get(K_KEY, 4)
    confirmation_depth = parameters_to_update.get(CONFIRMATION_DEPTH_KEY, 5)

    # the percentage of all computing power that the malicious miner should have
    malicious_hash_ratio = parameters_to_update.get(MALICIOUS_HASH_RATIO_KEY, 0.41)
    number_of_honest_miners = parameters_to_update.get(NUMBER_OF_HONEST_MINERS_KEY, 100)
    blocks_per_minute = parameters_to_update.get(BLOCKS_PER_MINUTE_KEY, 1)
    hash_rate_parameter = parameters_to_update.get(HASH_RATE_PARAMETER_KEY, 5)
    simulation_length_in_minutes = parameters_to_update.get(SIMULATION_LENGTH_IN_MINUTES_KEY, 500)

    block_creation_rate = blocks_per_minute * 60

    # The simulation will be long enough to allow at least 3 attacks (actually much more, because the maximal
    # depth difference for the malicious miner is at most 1/2 of the confirmation depth)
    simulation_length = max(simulation_length_in_minutes * 60, confirmation_depth * 3 * 60 / blocks_per_minute)

    # Generate the hash-rates for all miners
    honest_hash_rates, malicious_hash_rates = generate_hash_rates(hash_rate_parameter, number_of_honest_miners,
                                                                  malicious_hash_ratio)

    # The malicious miner will give up on the attack if he believes his hash-rate is inadequate
    maximal_depth_difference = parameters_to_update.get(MAXIMAL_DEPTH_DIFFERENCE_KEY,
                                                        round(confirmation_depth * malicious_hash_ratio) + 1)

    simulation_parameters = {
        HONEST_HASH_RATES_KEY: honest_hash_rates,
        MALICIOUS_HASH_RATES_KEY: malicious_hash_rates,
        BLOCK_CREATION_RATE_KEY: block_creation_rate,
        PROPAGATION_DELAY_PARAMETER_KEY: 30,
        SECURITY_PARAMETER_KEY: 0.1,
        SIMULATION_LENGTH_KEY: simulation_length,
        HONEST_DAG_INIT_KEY: greedy_constructor_with_parameters(k=k),
        MALICIOUS_DAG_INIT_KEY: competing_chain_constructor_with_parameters(
            k=k,
            confirmation_depth=confirmation_depth,
            maximal_depth_difference=maximal_depth_difference),
        MEDIAN_SPEED_KEY: DEFAULT_BLOCK_SIZE / 2,
        MAX_BLOCK_SIZE_KEY: DEFAULT_BLOCK_SIZE,
        MAX_PEER_NUMBER_KEY: DEFAULT_MAX_PEER_NUM,
        FETCH_REQUESTED_BLOCKS_KEY: False,
        BROADCAST_ADDED_BLOCKS_KEY: True,
        NO_DELAY_FOR_MALICIOUS_MINERS_KEY: True,
        COMPLETELY_CONNECTED_MALICIOUS_MINERS_KEY: True,
        SIMULATE_MINER_JOIN_LEAVE_KEY: False,
        HASH_RATE_PARAMETER_KEY: hash_rate_parameter,
        ENABLE_PRINTING_KEY: False,
        ENABLE_LOGGING_KEY: False,
        SAVE_SIMULATION_KEYS: False
    }

    for parameter_name, parameter_value in parameters_to_update.items():
        if parameter_name in simulation_parameters:
            simulation_parameters[parameter_name] = parameter_value

    return simulation_parameters


def parameter_iterator(parameters_to_iterate_on: SimulationParameterDictionary) -> \
        Iterator[SimulationParameterDictionary]:
    """
    Iterates on all possible combinations of the given parameters dictionary.
    """
    parameter_names_list = []
    parameter_values_list = []
    for parameter_name, parameter_values in parameters_to_iterate_on.items():
        parameter_names_list.append(parameter_name)
        parameter_values_list.append(parameter_values)

    for current_parameter_list in itertools.product(*parameter_values_list):
        yield {parameter_names_list[current_parameter_name_idx]: current_parameter
               for current_parameter_name_idx, current_parameter
               in enumerate(current_parameter_list)}


def calculate_iteration_number(results: List[bool], max_error: float = MAX_ERROR) -> int:
    """
    :return: given the results of the simulations for a given set of parameters so far, returns the minimal required
    number of simulations such that the mean of the results has a max error of max_error.
    """
    if len(results) < MIN_ITERATION_NUMBER:
        return MIN_ITERATION_NUMBER

    qunatile = normal_dist.ppf(1 - (max_error / 2))
    return round(variance(results) * ((qunatile / max_error) ** 2))


def run_simulation_with_params(parameters_dict: SimulationParameterDictionary, max_error: float = MAX_ERROR) -> float:
    """
    :return: the attack success rate when run with the given parameters such that the mean of the results has a max
    error of max_error.
    """
    results = []
    attack_success_rate = 0
    while len(results) < calculate_iteration_number(results, max_error):
        print(str(calculate_iteration_number(results, max_error) - len(results)) +
              " simulations left for: " + str(parameters_dict) + ". Attack success rate so far: " +
              str(attack_success_rate))

        # Note that the honest hash rates change for each simulation iteration, even with the same parameters
        simulation = Simulation(**generate_simulation_parameters(parameters_dict))
        results.append(simulation.run())
        attack_success_rate = numpy.mean(results)
    print("All simulations finished running for parameters: " + str(parameters_dict) +
          ". The attack success rate is: " + str(attack_success_rate))
    return float(attack_success_rate)


def analyze_results(parameters_to_iterate_on: SimulationParameterDictionary,
                    all_parameter_combinations: Iterable[SimulationParameterDictionary],
                    results: List[float],
                    show_plots: bool = True,
                    save_plots: bool = True):
    """
    Analyzes the results as functions of the various parameters.
    """
    for parameter_name in parameters_to_iterate_on.keys():
        parameters_leave_one_out = parameters_to_iterate_on.copy()
        parameters_leave_one_out.pop(parameter_name)
        all_leave_one_out = list(parameter_iterator(parameters_leave_one_out))

        color_cycler = itertools.cycle(numpy.linspace(0, 1, len(all_leave_one_out)))
        style_cycler = itertools.cycle(["-", "--", "-.", ":"])
        marker_cycler = itertools.cycle(["o", "^", "<", ">", "v", ".", "*", "x", "D", "d"])
        fig = pyplot.figure()
        ax = pyplot.axes()
        header = "Attack success rate as a function of " + parameter_name
        ax.set_title(header)
        ax.set_xlabel(parameter_name)
        ax.set_ylabel("Attack success rate")

        for current_parameters in all_leave_one_out:
            relevant_results = [results[index] for index, possible_parameters in enumerate(all_parameter_combinations)
                                if current_parameters.items() <= possible_parameters.items()]
            parameters_text = ', '.join(cur_param_name + "=" + str(cur_param_value)
                                        for cur_param_name, cur_param_value
                                        in current_parameters.items())

            print(header + ", " + parameters_text + ": " + str(relevant_results))
            pyplot.plot(parameters_to_iterate_on[parameter_name], relevant_results,
                        color=pyplot.cm.tab10(next(color_cycler)),
                        marker=next(marker_cycler),
                        linestyle=next(style_cycler),
                        label=parameters_text)

        pyplot.legend()
        pyplot.tight_layout()
        if save_plots:
            os.makedirs(DEFAULT_GRAPH_PATH, exist_ok=True)
            filename = os.path.join(DEFAULT_GRAPH_PATH, header + "_" + str(time.strftime("%Y%m%d-%H%M%S")))
            pyplot.savefig(os.path.join(filename + ".svg"), bbox_inches='tight')
            with open(filename + '.pickle', 'wb') as plot_pickle:
                pickle.dump(fig, plot_pickle)

    if show_plots:
        pyplot.show()


# For every parameter you wish to analyze that attack success rate on,
# add a {"param_name": iterable_of_possible_param_values} key: value pair
# to the parameters_to_iterate_on dictionary.
DEFAULT_PARAMETERS_TO_ITERATE_ON = {
    K_KEY: list(range(4, 7)),
    CONFIRMATION_DEPTH_KEY: list(range(50, 250 + 1, 50)),
    MALICIOUS_HASH_RATIO_KEY: list(numpy.arange(0.35, 0.5 + 0.01, 0.05)),
}


def run_analysis(parameters_to_iterate_on: SimulationParameterDictionary = None,
                 max_error: float = MAX_ERROR,
                 process_num: int = PROCESS_NUM,
                 show_plots: bool = False,
                 save_plots: bool = True) -> \
        Iterable[Tuple[SimulationParameterDictionary, float]]:
    """
    Analyzes the attack success rate on all combinations of the given Simulation parameters such that the mean of each
    result has a max error of max_error.
    :return: an iterable of (SimulationParameterDictionary, attack success rate with given parameters) tuples.
    """
    start = time.time()
    if parameters_to_iterate_on is None:
        parameters_to_iterate_on = DEFAULT_PARAMETERS_TO_ITERATE_ON

    all_parameter_combinations = list(parameter_iterator(parameters_to_iterate_on))
    print("Starting attack success analysis with parameters: " + str(parameters_to_iterate_on) +
          ", there are " + str(len(all_parameter_combinations)) + " parameter combinations. " +
          "Max error is: " + str(max_error))

    def simulation_run_func(max_error) -> Callable:
        def return_simulation_run_func(parameters_dict):
            return run_simulation_with_params(parameters_dict, max_error)
        return return_simulation_run_func

    process_pool = Pool(process_num)
    results = process_pool.map(simulation_run_func(max_error), all_parameter_combinations)
    process_pool.close()
    process_pool.join()
    print("Run time in seconds: " + str(time.time() - start))

    parameters_results_zipped = list(zip(all_parameter_combinations, results))
    print("The parameters and results are: \n" + str(parameters_results_zipped))

    analyze_results(parameters_to_iterate_on, all_parameter_combinations, results, show_plots, save_plots)

    return parameters_results_zipped


if __name__ == '__main__':
    run_analysis()
