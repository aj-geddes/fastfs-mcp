#!/usr/bin/env python3
"""
FastFS-MCP setup script.
"""

from setuptools import setup, find_packages

setup(
    name="fastfs-mcp",
    version="1.0.0",
    description="FastFS MCP with PyGit2 integration",
    author="FastFS Team",
    packages=find_packages(),
    install_requires=[
        "fastmcp==2.8.0",
        "PyJWT==2.8.0",
        "cryptography==41.0.4",
        "pygit2==1.13.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
