from setuptools import setup, find_packages

setup(
    name="xpertagent",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "chromadb>=0.4.0",
        "pydantic>=2.0.0",
        "python-dotenv>=0.19.0",
        "httptools>=0.6.4",
        "latex2mathml>=3.77.0",
        "pipdeptree>=2.23.4",
        "socksio>=1.0.0",
        "uvloop>=0.21.0",
        "watchfiles>=0.24.0",
        "wavedrom>=2.0.3.post3",
        "websockets>=14.1",
        "wheel>=0.44.0",
        "pymongo>=4.10.1"
    ],
    package_dir={
        'GOT': 'xpertagent/tools/xpert_ocr/vendor/got_ocr/GOT-OCR-2.0-master'
    },
    author="rookielittblack",
    author_email="rookielittleblack@yeah.net",
    description="XpertAgent, a flexible and powerful AI agent framework",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/rookie-littleblack/XpertAgent",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License 2.0",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)