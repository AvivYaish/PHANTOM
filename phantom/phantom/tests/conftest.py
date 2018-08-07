"""
The tests configuration file, contains several important fixtures.
"""

import pytest

from phantom.dag import Block
from phantom.phantom import PHANTOM, GreedyPHANTOM, CompetingChainGreedyPHANTOM


# DAG types
DAG = 'dag'
BRUTE_FORCE = 'brute_force'
GREEDY = 'greedy_dag'
COMPETING_CHAIN_GREEDY = 'competing_chain_greedy'


def pytest_generate_tests(metafunc):
    if DAG in metafunc.fixturenames:
        metafunc.parametrize(DAG, [BRUTE_FORCE, GREEDY, COMPETING_CHAIN_GREEDY], indirect=True)
    if GREEDY in metafunc.fixturenames:
        metafunc.parametrize(GREEDY, [GREEDY, COMPETING_CHAIN_GREEDY], indirect=True)


@pytest.fixture
def dag(request):
    if request.param == BRUTE_FORCE:
        dag = PHANTOM()
    elif request.param == GREEDY:
        dag = GreedyPHANTOM()
    elif request.param == COMPETING_CHAIN_GREEDY:
        dag = CompetingChainGreedyPHANTOM()
    else:
        raise ValueError("invalid internal test config")
    dag.set_k(4)
    return dag


@pytest.fixture
def greedy_dag(request):
    if request.param == GREEDY:
        greedy_dag = GreedyPHANTOM()
    elif request.param == COMPETING_CHAIN_GREEDY:
        greedy_dag = CompetingChainGreedyPHANTOM()
    else:
        raise ValueError("invalid internal test config")
    greedy_dag.set_k(4)
    return greedy_dag


@pytest.fixture(scope="module")
def genesis():
    return Block()


@pytest.fixture(scope="module")
def block1(genesis):
    # graph should look like this: 0 <- 1
    return Block(hash(genesis) + 1, {hash(genesis)})


@pytest.fixture(scope="module")
def block2(genesis, block1):
    # graph should look like this: 0 <- 2
    return Block(hash(block1) + 1, {hash(genesis)})


@pytest.fixture(scope="module")
def block3(block1, block2):
    # graph should look like this: 1, 2 <- 3
    return Block(hash(block2) + 1, {hash(block1), hash(block2)})


@pytest.fixture(scope="module")
def block4(genesis, block3):
    # graph should look like this: 0 <- 4
    return Block(hash(block3) + 1, {hash(genesis)})


@pytest.fixture(scope="module")
def block5(block4):
    # graph should look like this: 4 <- 5
    return Block(hash(block4) + 1, {hash(block4)})


@pytest.fixture(scope="module")
def block6(block5):
    # graph should look like this: 5 <- 6
    return Block(hash(block5) + 1, {hash(block5)})


@pytest.fixture(scope="module")
def block7(block3, block6):
    # graph should look like this: 3 <- 7
    return Block(hash(block6) + 1, {hash(block3)})


@pytest.fixture(scope="module")
def block8(block7):
    # graph should look like this: 7 <- 8
    return Block(hash(block7) + 1, {hash(block7)})


@pytest.fixture(scope="module")
def block9(block8):
    # graph should look like this: 8 <- 9
    return Block(hash(block8) + 1, {hash(block8)})
