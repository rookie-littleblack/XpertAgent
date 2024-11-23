#!/bin/bash

# Required files
VER_FILE="./VERSION"
ENV_FILE=".env"

# Check required files
if [[ ! -f "${VER_FILE}" || ! -f "${ENV_FILE}" ]]; then
    echo "ERROR: Required files ('${VER_FILE}' and '${ENV_FILE}') not found!"
    exit 1
fi

# Read environment variables from .env file
read_env_var() {
    local var_name=$1
    local value=""
    
    # Use grep to find the variable and extract its value
    value=$(grep "^${var_name}=" "$ENV_FILE" | cut -d '=' -f2-)
    
    # Remove possible quotes
    value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
    
    if [ -z "$value" ]; then
        echo "ERROR: Variable $var_name not found in .env file"
        exit 1
    fi
    
    echo "$value"
}

# Check if the path is an absolute path
check_absolute_path() {
    local path=$1
    if [[ "$path" != /* ]]; then
        echo "ERROR: $path is not an absolute path"
        exit 1
    fi
}

# Check if the path exists
check_path_exists() {
    local path=$1
    if [ ! -d "$path" ]; then
        echo "ERROR: Path $path does not exist"
        exit 1
    fi
}

# Check models path
LOCAL_MODELS_PATH=$(read_env_var "LOCAL_MODELS_PATH")
check_absolute_path "${LOCAL_MODELS_PATH}"
check_path_exists "${LOCAL_MODELS_PATH}"

# Get project environment
PROJ_ENV=$(read_env_var "PROJ_ENV")
### Current supported values: dev, pre, prod
if [[ "${PROJ_ENV}" != "dev" && "${PROJ_ENV}" != "pre" && "${PROJ_ENV}" != "prod" ]]; then
    echo "ERROR: Invalid project environment: '${PROJ_ENV}', supported values: dev, pre, prod"
    exit 1
fi

# Get version
VERSION=$(cat ${VER_FILE})

# Build Docker image
docker build -t xpertagent:${VERSION} .

# Build Docker image with proxy:
# docker build \
# --build-arg HTTP_PROXY=http://192.168.XX.XX:XXX \
# --build-arg HTTPS_PROXY=http://192.168.XX.XX:XXX \
# --build-arg http_proxy=http://192.168.XX.XX:XXX \
# --build-arg https_proxy=http://192.168.XX.XX:XXX \
# --network host \
# --add-host archive.ubuntu.com:127.0.0.1 \
# -t xpertagent:${VERSION} .

# Create network if not exists
if ! docker network ls | grep -q "xpertagent-network"; then
    docker network create xpertagent-network
fi

# Run Docker container
docker run --name=xpertagent \
-e PROJ_ENV=${PROJ_ENV} \
--gpus=all \
--privileged=true \
--restart=always \
--ipc=host \
--pid=host \
--network=xpertagent-network \
-v /usr/local/cuda:/usr/local/cuda \
-v /etc/localtime:/etc/localtime:ro \
-v ${LOCAL_MODELS_PATH}:/code/data/models \
-p 7833:7833 \
-p 7834:7834 \
xpertagent:${VERSION}