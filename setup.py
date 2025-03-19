from setuptools import setup

setup(
    name="trdl",
    version="0.1.0",
    description="Trade Republic Portfolio Downloader",
    author="angt",
    url="https://github.com/angt/trdl",
    py_modules=["trdl"],
    install_requires=["requests", "websocket-client"],
    entry_points={"console_scripts": ["trdl = trdl:main"]},
    python_requires=">=3.6",
)
