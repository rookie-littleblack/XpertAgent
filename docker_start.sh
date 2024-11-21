#!/bin/bash
VERSION=$(cat /code/VERSION)
echo ">>> [docker_start.sh] ==============================================================================="
echo ">>> [docker_start.sh] XpertAgent Service Startup Script"
echo ">>> [docker_start.sh] Version: $VERSION"
echo ">>> [docker_start.sh] Author : rookielittblack"
echo ">>> [docker_start.sh] Email  : rookielittblack@yeah.net"
echo ">>> [docker_start.sh] Desc   : This script initializes and starts the XpertAgent services in a Docker container"
echo ">>> [docker_start.sh] ==============================================================================="

# Exit immediately if a command exits with a non-zero status
set -e

# Start XpertAgent services
echo ">>> Starting XpertAgent services..."

# Initialize Conda for bash shell
# This is required to use conda commands in the script
echo ">>> Initializing Conda environment..."
source /root/anaconda3/etc/profile.d/conda.sh || {
    echo "ERROR: Failed to initialize Conda. Please check Anaconda installation."
    exit 1
}

# Activate the XpertAgent Conda environment
echo ">>> Activating 'xpertagent' environment..."
conda activate xpertagent || {
    echo "ERROR: Failed to activate 'xpertagent' environment."
    exit 1
}

# Debugging environment
echo ">>> Debugging Environment..."
echo "CUDA Version: $(nvcc --version)"
echo "Python Version: $(python --version)"
echo "PyTorch Version: $(python -c 'import torch; print(torch.__version__)')"
echo "CUDA Available: $(python -c 'import torch; print(torch.cuda.is_available())')"
echo "CUDA Device Count: $(python -c 'import torch; print(torch.cuda.device_count())')"

# Start the main gRPC service
# Note: if xmedocr is enabled, xocr will be automatically enabled!
echo ">>> Starting XpertAgent gRPC service..."
python -m xpertagent.services.xservice -t grpc -s xmedocr || {
    echo "ERROR: Failed to start gRPC service."
    exit 1
}