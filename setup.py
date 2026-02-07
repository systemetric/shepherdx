from setuptools import setup

setup(
    name="shepherdx",
    version="0.1.0",
    packages=["shepherdx"],

    install_requires = [
        "aiomqtt>=2.4.0",
        "asyncio>=4.0.0",
        "coloredlogs>=15.0.1",
        "fastapi>=0.124.4",
        "mock-gpio>=0.1.10",
        "pillow>=12.1.0",
        "pydantic>=2.12.5",
        "python-multipart>=0.0.20",
        "uvicorn>=0.38.0",
        "websockets>=16.0",
    ],

    author="Nathan Gill",
    author_email="nathan.j.gill@outlook.com",
)
