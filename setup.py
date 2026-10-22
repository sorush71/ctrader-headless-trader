from setuptools import setup, find_packages

setup(
    name="ctrader-headless-trader",
    version="1.0.0",
    description="Headless Python library for algorithmic trading on cTrader Open API without a GUI",
    author="Sorush",
    packages=find_packages(),
    install_requires=[
        "protobuf>=4.25.0",
        "websockets>=12.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
    ],
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
)
