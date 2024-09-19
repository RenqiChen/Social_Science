from sci_platform import Platform
from scientist_utils import read_txt_files_as_dict

epochs = 5
platform_example = Platform()
platform_example.running(epochs)

# paper_folder_path = "/home/bingxing2/ailab/group/ai4agr/crq/SciSci/papers"  # 替换为实际的文件夹路径
# paper_dicts = read_txt_files_as_dict(paper_folder_path)