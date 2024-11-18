from setuptools import setup, find_packages

setup(
    name="xpertagent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "chromadb>=0.4.0",
        "pydantic>=2.0.0",
        "python-dotenv>=0.19.0"
    ],
    author="rookielittblack",
    author_email="rookielittleblack@yeah.net",
    description="XpertAgent, a flexible and powerful AI agent framework",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/rookie-littleblack/XpertAgent",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)