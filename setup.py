from setuptools import find_packages
from setuptools import setup

setup(
    name="pychatgpt",
    version="0.0.1",
    license="MIT",
    author="Shoppon",
    author_email="shopppon@gmail.com",
    description="Pychatgpt is a python package for chatting with GPT-3.",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=["revChatGPT", "GPTserver"],
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    entry_points={
        "console_scripts": [
            "pychatgpt-api = cmds.api:main",
        ]
    },
)
