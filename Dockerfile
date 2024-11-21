# Use NVIDIA CUDA base image for GPU support
FROM nvcr.io/nvidia/cuda:12.4.1-devel-ubuntu20.04

# Set maintainer information
LABEL maintainer="rookielittblack@yeah.net"
LABEL version="0.1.1"
LABEL description="XpertAgent - A flexible and powerful AI agent framework"

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory in the container
WORKDIR /code

# Set environment variables
# Add Anaconda to PATH
ENV PATH="/root/anaconda3/bin:$PATH"
# Add project root to Python path for module imports
ENV PYTHONPATH="/code:$PYTHONPATH"

# Set timezone to Shanghai
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    git \
    vim \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# # Download and install Anaconda
# RUN wget https://repo.anaconda.com/archive/Anaconda3-2023.09-0-Linux-x86_64.sh -O anaconda.sh && \
#     bash anaconda.sh -b -p /root/anaconda3 && \
#     rm anaconda.sh

# Install Git LFS
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
    apt-get install -y git-lfs && \
    git lfs install

# Download and install Miniconda instead of Anaconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh && \
    bash miniconda.sh -b -p /root/anaconda3 && \
    rm miniconda.sh

# Create necessary directories for data and logs
# models: store AI model weights and configurations
# logs: store application and service logs
RUN mkdir -p ./data/models ./data/logs

# Initialize conda and create a new environment
# 1. Initialize conda for bash shell
# 2. Create a new environment named 'xpertagent' with Python 3.10
# 3. Add conda activation to bashrc for interactive sessions
RUN /root/anaconda3/bin/conda init bash && \
    conda init bash && \
    conda create --name xpertagent python=3.10 -y && \
    echo "conda activate xpertagent" >> ~/.bashrc

# Copy project files to container
# This includes source code, configuration files, and scripts
COPY . .

# Install project dependencies
# 1. Activate conda environment
# 2. Install main project package in editable mode
# 3. Install OCR-specific dependencies
RUN /bin/bash -c "source /root/anaconda3/etc/profile.d/conda.sh && \
    conda activate xpertagent && \
    pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple --root-user-action=ignore && \
    pip install -e ./xpertagent/tools/xpert_ocr/vendor/got_ocr/GOT-OCR-2.0-master -i https://pypi.tuna.tsinghua.edu.cn/simple --root-user-action=ignore"

# Clone the model repository with Git LFS
RUN cd /code/data/models && \
    git clone https://www.modelscope.cn/stepfun-ai/GOT-OCR2_0.git

# Clear proxy settings after all installations are complete
ENV HTTP_PROXY=""
ENV HTTPS_PROXY=""
ENV http_proxy=""
ENV https_proxy=""

# Set GRPC environment variables
ENV GRPC_POLL_STRATEGY=epoll1
ENV GRPC_ENABLE_FORK_SUPPORT=0
ENV GRPC_TRACE=call_error

# Expose ports for different services
# 7833: Main service port for agent communication (http)
# 7834: Main service port for agent communication (grpc)
EXPOSE 7833 7834

# Start all services using the startup script
# This script should handle:
# 1. Environment activation
# 2. Starting the OCR service
# 3. Starting the main agent service
# 4. Starting any additional required services
CMD ["/bin/bash", "/code/docker_start.sh"]

# ##########################################################################
# ##########################################################################
# Note: To generate a Docker image, use:
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# docker build -t xpertagent:latest .
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# Or, use the following command to build the image with proxy settings:
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# docker build \
# --build-arg HTTP_PROXY=http://192.168.1.23:7890 \
# --build-arg HTTPS_PROXY=http://192.168.1.23:7890 \
# --build-arg http_proxy=http://192.168.1.23:7890 \
# --build-arg https_proxy=http://192.168.1.23:7890 \
# --network host \
# --add-host archive.ubuntu.com:127.0.0.1 \
# -t xpertagent:latest .
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# Note: When running the container, use:
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# docker run --name=xpertagent \
# -e PROJ_ENV=pre \
# --gpus=all \
# --privileged=true \
# --restart=always \
# --ipc=host \
# --pid=host \
# -v /usr/local/cuda:/usr/local/cuda \
# -v /etc/localtime:/etc/localtime:ro \
# -p 7933:7833 \
# -p 7934:7834 \
# xpertagent:latest
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# Note: if you encounter the error of network, you can create a network first:
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# docker network create xpertagent-network
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# then run the container with the network:
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# docker run --name=xpertagent \
# -e PROJ_ENV=pre \
# --gpus=all \
# --privileged=true \
# --restart=always \
# --ipc=host \
# --pid=host \
# --network=xpert-network \
# -v /usr/local/cuda:/usr/local/cuda \
# -v /etc/localtime:/etc/localtime:ro \
# -p 7933:7833 \
# -p 7934:7834 \
# xpertagent:latest
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# ##########################################################################
# ##########################################################################