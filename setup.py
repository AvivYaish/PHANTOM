from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='phantom',
    version='0.041',
    description='An efficient implementation of the PHANTOM block-DAG protocol.',
    url='https://github.cs.huji.ac.il/aviv-yaish/PHANTOM',
    author='Aviv Yaish',
    author_email='aviv.yaish@mail.huji.ac.il',
    packages=['phantom'],
    long_description=readme(),
    python_requires='>=3.6',
    install_requires=[
        'networkx',
        'numpy',
        'pathos',
        'jsonpickle',
        'matplotlib',   # for printing purposes
        'seaborn',      # for printing purposes
        'ordered_set',  # for printing purposes
        'simpy',        # for simulation purposes
        'pytest',       # for testing purposes
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
