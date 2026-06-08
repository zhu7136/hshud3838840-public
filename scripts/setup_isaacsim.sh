#!/usr/bin/env bash
# Exit on error, and print commands
set -ex

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR=$(dirname "$SCRIPT_DIR")

if ! command -v sudo &> /dev/null; then
  # in docker build sudo isn't avaiable, but its ok
  echo "Warning: sudo could not be found, you may need to run this script with sudo"
  function sudo { "$@"; }
  export -f sudo
fi

# Use CONDA_ENV_NAME if provided, otherwise default to "hssim"
CONDA_ENV_NAME=${CONDA_ENV_NAME:-hssim}
echo "conda environment name is set to: $CONDA_ENV_NAME"

# Create overall workspace
source ${SCRIPT_DIR}/source_common.sh
ENV_ROOT=$CONDA_ROOT/envs/$CONDA_ENV_NAME
SENTINEL_FILE=${WORKSPACE_DIR}/.env_setup_finished_$CONDA_ENV_NAME
echo "SENTINEL_FILE: $SENTINEL_FILE"

mkdir -p $WORKSPACE_DIR

if [[ ! -f $SENTINEL_FILE ]]; then
  # Install miniconda
  if [[ ! -d $CONDA_ROOT ]]; then
    mkdir -p $CONDA_ROOT
    curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o $CONDA_ROOT/miniconda.sh
    bash $CONDA_ROOT/miniconda.sh -b -u -p $CONDA_ROOT
    rm $CONDA_ROOT/miniconda.sh
  fi

  # Create the conda environment
  if [[ ! -d $ENV_ROOT ]]; then
    $CONDA_ROOT/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
    $CONDA_ROOT/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
    if [[ ! -f $CONDA_ROOT/bin/mamba ]]; then
      $CONDA_ROOT/bin/conda install -y mamba -c conda-forge -n base
    fi
    MAMBA_ROOT_PREFIX=$CONDA_ROOT $CONDA_ROOT/bin/mamba create -y -n $CONDA_ENV_NAME python=3.11 -c conda-forge --override-channels
  fi

  source $CONDA_ROOT/bin/activate $CONDA_ENV_NAME

  # Install ffmpeg for video encoding
  conda install -c conda-forge -y ffmpeg
  conda install -c conda-forge -y libiconv
  conda install -c conda-forge -y libglu

  # Below follows https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/pip_installation.html
  # Install IsaacSim
  pip install --upgrade pip
  # Install nvidia dependencies first with --no-deps to avoid network download
  pip install --no-deps /workspace/holosoma/nvidia_cudnn_cu12-9.7.1.26-py3-none-manylinux_2_27_x86_64.whl
  pip install --no-deps /workspace/holosoma/nvidia_cublas_cu12-12.8.3.14-py3-none-manylinux_2_27_x86_64.whl
  pip install --no-deps /workspace/holosoma/nvidia_cusolver_cu12-11.7.2.55-py3-none-manylinux_2_27_x86_64.whl
  pip install --no-deps /workspace/holosoma/nvidia_cusparse_cu12-12.5.7.53-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
  pip install --no-deps /workspace/holosoma/torch-2.7.0+cu128-cp311-cp311-manylinux_2_28_x86_64.whl
  pip install -U torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128

  # Install dependencies from PyPI first
  pip install pyperclip
  # Then install isaacsim from NVIDIA index only
  pip install "isaacsim[all,extscache]==5.1.0" --extra-index-url https://pypi.nvidia.com

  # Use IsaacLab from holosoma directory (pre-downloaded)
  if [[ -d /workspace/holosoma/IsaacLab ]] && [[ ! -d $WORKSPACE_DIR/IsaacLab ]]; then
    cp -a /workspace/holosoma/IsaacLab $WORKSPACE_DIR/IsaacLab
  fi
  if [[ ! -d $WORKSPACE_DIR/IsaacLab ]]; then
    echo "ERROR: IsaacLab not found."
    exit 1
  fi

  sudo apt install -y cmake build-essential
  cd $WORKSPACE_DIR/IsaacLab
  # setuptools 81 removes pkg_resoures, a dep needs that
  # see https://github.com/isaac-sim/IsaacLab/pull/4585
  pip install 'setuptools<81'
  echo 'setuptools<81' > build-constraints.txt
  export PIP_BUILD_CONSTRAINT="$(realpath build-constraints.txt)"
  # Fix upstream bug: should use flatdict 4.1.0 (https://github.com/isaac-sim/IsaacLab/issues/4576)
  sed -i 's/flatdict==4.0.1/flatdict==4.1.0/' source/isaaclab/setup.py
  # Pre-install rl-games locally to avoid git clone
  if [[ -d /workspace/holosoma/rl_games ]]; then
    pip install --no-deps -e /workspace/holosoma/rl_games
  fi
  # Patch isaaclab_rl to use local rl-games instead of git
  sed -i 's|"rl-games @ git+https://github.com/isaac-sim/rl_games.git@python3.11"|"rl-games"|' source/isaaclab_rl/setup.py
  # Patch isaaclab_mimic to remove robomimic git dependency (network issue in docker)
  sed -i 's|"robomimic@git+https://github.com/ARISE-Initiative/robomimic.git@v0.4.0"|"robomimic"|' source/isaaclab_mimic/setup.py
  # work-around for egl_probe cmake max version issue
  export CMAKE_POLICY_VERSION_MINIMUM=3.5
  export OMNI_KIT_ACCEPT_EULA=${OMNI_KIT_ACCEPT_EULA:-1}
  ./isaaclab.sh --install
  unset PIP_BUILD_CONSTRAINT

 # Install Holosoma (skip unitree/booster which require GitHub downloads)
  pip install -U pip
  pip install -e $ROOT_DIR/src/holosoma

  # Force upgrade wandb to override rl-games constraint
  pip install --upgrade 'wandb>=0.21.1'
  touch $SENTINEL_FILE
fi
