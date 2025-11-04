from setuptools import setup, find_packages

setup(
    name="app-sink-cli",
    version="1.0.0",
    description="CLI for App-Sink Kubernetes Abstraction Layer",
    author="App-Sink Team",
    packages=find_packages(),
    install_requires=[
        "click>=8.1.0",
        "requests>=2.31.0",
        "pyyaml>=6.0",
        "rich>=13.0.0",
        "tabulate>=0.9.0",
        "anthropic>=0.7.0",
        "gitpython>=3.1.0"
    ],
    entry_points={
        "console_scripts": [
            "app-sink=app_sink_cli.cli:cli",
        ],
    },
    python_requires=">=3.8",
)
