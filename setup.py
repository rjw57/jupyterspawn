from setuptools import setup, find_packages
setup(
    name="jupyterspawn",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        'docker-py', 'docopt',
    ],
    entry_points={
        'console_scripts': [
            'juspawn=jupyterspawn:main',
        ],
    },
)
