# PHANTOM (GhostDAG)

Presented here is an efficient implementation of the PHANTOM block-DAG protocol.

This package includes:
- An interface for block-DAGs.
- Various implementations of the PHANTOM block-DAG protocol:
    - a brute force optimal coloring implementation
    - a greedy approximating coloring implementation
- A simulation framework to test out block-DAGs adhering the the aforementioned interface. Almost every parameter is modifiable: network topology, average network delay, hash-rate distribution, etc'.
- An implementation of a chain-diversion attack against the PHANTOM protocol.

### Installation
There are two methods of installation:
- Download the repository and run: 

        cd PHANTOM
        pip install .

- Download the repository and run: 

        cd PHANTOM
        python setup.py install  

### Usage
There are two ways to run the simulation:
1. Using run_simulation.py to run a single simulation:
        
        cd PHANTOM
        python -m phantom.network_simulation.run_simulation

2. Using analyze_attack_success_rate.py to run multiple simulations on various combinations of run-time parameters to 
to analyze the success rate of a given attack on given block-DAG protocols.
        
        cd PHANTOM
        python -m phantom.network_simulation.analyze_attack_success_rate

All parameters relevant for each run method are contained in the run script and can easily be changed.
