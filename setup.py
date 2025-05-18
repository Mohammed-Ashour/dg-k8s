# setup.py
from setuptools import find_packages, setup

setup(
    name="dg_k8s",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-postgres",
        "dagster-k8s",
        "numpy",
        "pandas",
        "shapely",
        "geopandas",
    ],
    extras_require={
        "dev": [
            "dagit",
            "dagster-webserver",
            "ruff"
        ]
    },
)
