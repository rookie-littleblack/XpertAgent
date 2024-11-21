#!/bin/bash
echo ">>> [init.sh] ======================================================"
echo ">>> [init.sh] XpertAgent, a flexible and powerful AI agent framework"
echo ">>> [init.sh] Author: rookielittblack"
echo ">>> [init.sh] Email : rookielittblack@yeah.net"
echo ">>> [init.sh] ======================================================"

# Check if running in project root directory
if [[ ! -d "./xpertagent" || ! -f "./setup.py" ]]; then
    echo ">>> [init.sh] Please run this script in the project root directory"
    exit 1
fi

# Default value for OCR installation
install_ocr=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-xocr)
            install_ocr=true
            shift # Remove --with-xocr from processing
            ;;
        -h|--help)
            echo "Usage: $0 [--with-xocr]"
            echo "Options:"
            echo "  --with-xocr   Install XpertOCR tool and its dependencies"
            echo "  -h, --help    Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Start initialization
echo ">>> [init.sh] Starting initialization..."

# Create virtual environment
env_name="test_xpertagent_$(date +%Y%m%d%H%M)"
echo ">>> [init.sh] Creating virtual environment: '$env_name'..."
conda create -n $env_name python=3.10 -y

# Get conda installation path
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"

# Activate environment
echo ">>> [init.sh] Activating environment '$env_name'..."
conda activate $env_name

# Verify environment and python path
current_env=$(conda info --envs | grep '*' | awk '{print $1}')
python_path=$(which python)
echo ">>> [init.sh] Using Python from: $python_path"
if [[ "$current_env" != "$env_name" || ! "$python_path" =~ "$env_name" ]]; then
    echo ">>> [init.sh] ERROR: Failed to activate environment '$env_name'"
    echo ">>> [init.sh] Current environment: $current_env"
    echo ">>> [init.sh] Python path: $python_path"
    exit 1
fi

# Install main dependencies
echo ">>> [init.sh] Installing main package dependencies into environment '$env_name'..."
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install OCR if requested
if [ "$install_ocr" = true ]; then
    echo ">>> [init.sh] Installing XpertOCR tool..."
    
    # Create necessary directories
    mkdir -p ./data/models
    mkdir -p ./data/logs
    
    # Install OCR dependencies
    pip install -e ./xpertagent/tools/xpert_ocr/vendor/got_ocr/GOT-OCR-2.0-master -i https://pypi.tuna.tsinghua.edu.cn/simple
    
    # Download model weights if not exists
    if [ ! -d "./data/models/GOT-OCR2_0" ]; then
        echo ">>> [init.sh] Downloading OCR model weights..."
        git clone https://www.modelscope.cn/stepfun-ai/GOT-OCR2_0.git ./data/models/GOT-OCR2_0
    fi
    
    # Start OCR service
    echo ">>> [init.sh] Starting OCR service..."
    nohup python ./xpertagent/tools/xpert_ocr/xocr_service.py >> ./data/logs/xpert_ocr_service.log 2>&1 &
    
    # Log completion
    echo ">>> [init.sh] XpertOCR installation completed!"
fi

echo ">>> [init.sh] Initialization completed! Environment name: '$env_name'!"
echo ">>> [init.sh] Next steps:"
echo ">>> [init.sh] 1. Update .env file"
echo ">>> [init.sh] 2. Run 'conda activate $env_name' to activate the environment"
echo ">>> [init.sh] 3. Run 'python -m examples.test_simple_agent' to test the agent"
if [ "$install_ocr" = true ]; then
    echo ">>> [init.sh] 4. Run 'python -m xpertagent.services.xservice -t http -s xocr' to start the XOCR service"
    echo ">>> [init.sh] 5. Run 'python -m examples.test_xocr_tool' to test the XpertOCR tool (if this running failed, please check the log file './data/logs/xpert_ocr_service.log' to make sure the XOCR service is running properly)"
fi
echo ">>> [init.sh] ======================================================"

# __END__