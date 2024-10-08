# [Submitted to ICLR2025] <br> Two Heads Are Better Than One: A Multi-Agent System Has the Potential to Improve Scientific Idea Generation.

## 👀 Introduction

This repository contains the code for our paper `Two Heads Are Better Than One: A Multi-Agent System Has the Potential to Improve Scientific Idea Generation`. 

- To the best of our knowledge, we propose the first multi-agent system for conducting scientific collaborations in an end-to-end pipeline from team organization to novel scientific idea generation. Furthermore, the real data is utilized for role-play and the objective evaluation of final outputs.

- We conduct extensive evaluations to investigate VirSci in terms of the team settings and the novelty of generated scientific ideas. The results demonstrate that multi-agent collaboration can improve the quality of the outcomes, surpassing the SOTA single-agent method.

- The simulation results align with the important findings in Science of Science, such as fresh teams tend to create more innovative research, showcasing the potential of VirSci as a powerful tool for future research in this field.

Our project website is [https://renqichen.github.io/Social_Science/](https://renqichen.github.io/Social_Science/).

## 💡 Run
### Environment

We tested our codebase with PyTorch 2.3.1 and CUDA 12.1. Please install the corresponding versions of PyTorch and CUDA based on your computational resources.

To install the required packages, run:
```bash
pip install -r requirements.txt.
```

### Setup

Our prepocessed dataset is publicly available at https://drive.google.com/drive/folders/1ZwWMBQ5oK-l4VuzMa60GbMND0g2EIxIu?usp=sharing.

Then, update the training command:

```bash
--dataset ruozhiba, crop_dataset
```

### Usage

Take closed-book QA prompt as an example:

```
python run.py
```

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

