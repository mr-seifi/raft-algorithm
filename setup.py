from setuptools import find_packages, setup

setup(
    name="py-skylab",
    version="0.0.1",
    description="Skylab",
    license="MIT",
    packages=find_packages(exclude=["test"]),
    author="Amin Seifi",
    author_email="aminseiifi@gmail.com",
    keywords=[],
    entry_points={
        "console_scripts": [
            "skylab=skylab.main:main",
        ],
    },
    url="https://github.com/mr-seifi/skylab",
    install_requires=[],
    extras_require={},
)