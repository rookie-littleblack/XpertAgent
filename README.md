# XpertAgent

XpertAgent is an open-source platform for building and deploying AI applications. It combines intelligent workflow orchestration, knowledge enhancement, and multi-agent collaboration in an intuitive interface, helping you transform ideas into production-ready solutions.

## Features

- 🤖 Intelligent reasoning and decision making
- 🛠️ Extensible tool system
- 💾 Vector-based memory management
- 📋 Task planning and execution
- 🔧 Easy configuration and customization

## Installation

- Clone the project from GitHub

```bash
git clone https://github.com/rookie-littleblack/XpertAgent.git
cd XpertAgent
```

- Configure the environment variables in the `.env` file

```bash
cp .env.example .env
vim .env
```

> For a basic using of XpertAgent, you only need to configure the `API configurations (Required)` in the `.env` file.

- Initiate the project

```bash
./init.sh --with-xocr
```

- Then, following the steps of the printed messages in the terminal to start the project, for example:

```bash
conda activate XXX  # Activate the environment
```

## Quick Start

```bash
python -m examples.test_simple_agent
```

## Contributing

Contributions are welcome!

## License

This project is licensed under the Apache License, Version 2.0.