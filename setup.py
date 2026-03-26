from setuptools import setup

setup(
    name="nyc-ped-analysis",
    version="0.1.0",
    packages=["nycwalks"],
    install_requires=[
        "scikit-learn==1.3.1",
        "numpy>=1.24,<2",
        "pandas>=2.0",
        "geopandas>=0.14",
        "requests>=2.28",
        "shapely>=2.0",
        "matplotlib>=3.7",
    ],
    python_requires=">=3.9",
)
