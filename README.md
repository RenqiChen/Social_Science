# [Submitted to ICLR2025] <br> Crop Dataset and Benchmark.

## 👀 Introduction

This repository contains the code and data for our paper `Empowering and Assessing the Utility of Large Language Models in Crop Science`. 

We introduce CROP, which includes a novel instruction tuning dataset (Crop dataset) specifically designed to enhance LLMs’ professional capabilities in the crop science sector, along with a benchmark (Crop benchmark) that serves as a comprehensive evaluation of LLMs’ understanding of the domain knowledge. **To the best of our knowledge, Crop dataset is the first-ever instruction tuning dataset in the crop science domain. We anticipate that CROP will accelerate the adoption of LLMs in the domain of crop science, ultimately contributing to global food production.** 

Our project website is https://RenqiChen.github.io/The_Crop/.

## 💻 Training
### Environment

We tested our codebase with PyTorch 1.13.1 and CUDA 11.6. Please install the corresponding versions of PyTorch and CUDA based on your computational resources.

To install the required packages, run:
```bash
pip install -r requirements.txt.
```

#### Note
flash-attention need linux kernel higher than 5.5

### Setup

We use the [COIG-CQIA](https://github.com/paralym/COIG-CQIA) dataset as an additional general dataset in this work to aviod losing generalization capability, which consists of multi tasks chinese Instruction Fine-tuning

```bash
 --dataset ruozhiba
```

To use Crop data for fine-tuning models, download the Crop datasets to the './train/data' folder and revise the file 'dataset_info.json' file by adding the following annotation to the config file:
```json
  "crop_dataset": {
    "file_name": "crop dataset.json"
  }
```

Then, update the training command:

```bash
--dataset ruozhiba, crop_dataset
```

We recommend downloading the pre-trained model weights to the /train/model folder.
```
cd /train
mkdir model
```
then download a pretraining model:
[LLama3-8B](https://huggingface.co/meta-llama/Meta-Llama-3-8B) ,
[InternLM2-7B](https://huggingface.co/internlm/internlm2-7b) ,
[Qwen1.5-7B](https://huggingface.co/Qwen/Qwen1.5-7B) .

### Usage

To train local models using our dataset with LoRA, run:
```
CUDA_VISIBLE_DEVICES=0 python src/train_bash.py --stage sft --model_name_or_path ./train/model/Meta-Llama-3-8B  --do_train --dataset ruozhiba --finetuning_type lora  --lora_target q_proj,v_proj --output_dir /output --logging_steps 10 --save_steps 100 --num_train_epochs 4 --plot_loss --per_device_train_batch_size=4 --fp16 --template default --preprocessing_num_workers 1
```
This refined version should help you better understand and utilize the project. If you have any questions, feel free to reach out.

## 💡 Prompt

### Code

(1) The codes for the prompts of Crop dataset are released in ./Code/prompt.

Single-turn dialogue:

CQA: closed-book QA

OQA: open-book QA

EE: event extraction

NER: named entity recognition

Summary: summary

EN: English, CH: Chinese

Multi-turn dialogue:

EN: English, CH: Chinese

(2) The codes for the prompts of Crop benchmark are released in ./Code/benchmark.

### Usage

Take closed-book QA prompt as an example:

```
python prompt_cqa_en.py
```

Please note to replace the input/output folder path and API key.

## 🙏 Acknowledgements

This project is supported by Shanghai Artificial Intelligence Laboratory.

The multi-agent framework in this work is based on the [AgentScope](https://github.com/modelscope/agentscope).

## 📧 Contact

If you have any questions, please  contact at [chenrenqi@pjlab.org.cn, suhaoyang@pjlab.org.cn].

## ⚖ License

This repository is licensed under the [Apache-2.0 License](LICENSE).

## 📌 BibTeX & Citation

If you find this code useful, please consider citing our work:

```bibtex
Comming soon!
```

