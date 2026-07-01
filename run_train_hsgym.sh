#!/bin/bash
export PATH=/root/.holosoma_deps/miniconda3/envs/hsgym/bin:$PATH
export LD_LIBRARY_PATH=/root/.holosoma_deps/miniconda3/envs/hsgym/lib/python3.8/site-packages/nvidia/cublas/lib:/root/.holosoma_deps/miniconda3/envs/hsgym/lib/python3.8/site-packages/nvidia/cuda_runtime/lib:/root/.holosoma_deps/miniconda3/envs/hsgym/lib/python3.8/site-packages/nvidia/cudnn/lib:/root/.holosoma_deps/miniconda3/envs/hsgym/lib/python3.8/site-packages/nvidia/cusolver/lib:/root/.holosoma_deps/miniconda3/envs/hsgym/lib/python3.8/site-packages/nvidia/cusparse/lib:/root/.holosoma_deps/miniconda3/envs/hsgym/lib:$LD_LIBRARY_PATH
exec /root/.holosoma_deps/miniconda3/envs/hsgym/bin/python -m holosoma.train_agent "$@"
