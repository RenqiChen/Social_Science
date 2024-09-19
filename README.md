# Social-Science

Forker from [AgentScope](https://github.com/modelscope/agentscope).

We use Meta-Llama-3-8B-Instruct as local model.

salloc --gres=gpu:2 -p vip_gpu_ailab -A ai4agr

module load anaconda/2021.11

module load compilers/cuda/11.8

module load compilers/gcc/12.2.0

module load compilers/gcc/9.3.0

module load cudnn/8.4.0.27_cuda11.x

module load compilers/cuda/12.1

module load cudnn/8.8.1.3_cuda12.x 

module load 7z/22.01 

module load git-lfs/3.5.1

7z x data111.rar

export LD_PRELOAD=$LD_PRELOAD:/home/bingxing2/ailab/scxlab0066/.conda/envs/mamba_ssm_cp311/lib/libgomp.so.1