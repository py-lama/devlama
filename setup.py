from setuptools import setup

# This file is kept minimal as most configuration is in pyproject.toml
# It's only here for backward compatibility with older pip versions

setup(
    # Package metadata and dependencies are specified in pyproject.toml
    packages=['devlama'],
    package_data={
        'devlama': ['py.typed'],
    },
    include_package_data=True,
)
