from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).parent.absolute()


def parse_requirements(filename: str) -> list:
    """Load requirements from a pip requirements file.

    Args:
        filename: Path to the requirements text file.

    Returns: list of strings, one per line in the requirements.txt file.

    """

    with open(filename, encoding='utf-8') as file:
        lines = file.read().splitlines()
    return [line for line in lines if line and not line.startswith('#')]


setup(
    name='flex_package',
    version='0.0.1',
    description='Set of tools for obtaining information on when and where afvoertekorten are expected and for suggesting possible solutions using flex rides',
    author='DKS',
    packages=find_packages(where='.', exclude=['tests']),
    install_requires=parse_requirements(ROOT / 'requirements.txt'),
    extras_require={
        'dev': ['flake8', 'mypy', 'pylama', 'notebook'],
        'docs': ['sphinx_rtd_theme', 'sphinx', 'myst-parser', 'sphinx_math_dollar'],
        'tests': ['pytest', 'pytest-cov', 'tox'],
    },
)
