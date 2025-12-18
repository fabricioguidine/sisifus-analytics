"""Setup script for the project"""

from setuptools import setup, find_packages

setup(
    name="sisifus-analytics",
    version="1.0.0",
    description="Job application email parser and analytics tool",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "pytest>=7.4.0",
        "tqdm>=4.66.0",
        "plotly>=5.17.0",
        "pandas>=2.1.0",
        "python-dotenv>=1.0.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
    ],
    python_requires=">=3.8",
)


