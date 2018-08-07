from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='lazy_set',
    version='1.4.6',
    description='A collection that tries to imitate a "lazy" difference and union of sets.',
    url='https://github.com/AvivYaish/LazySet',
    author='Aviv Yaish',
    author_email='aviv.yaish@mail.huji.ac.il',
    packages=['lazy_set'],
    long_description=readme(),
    python_requires='>=3.6',
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
