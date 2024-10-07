# 指定输入和输出文件路径
input_file = 'Author_sample.txt'
output_file = 'output.txt'

# 打开并读取文件内容
with open(input_file, 'r', encoding='utf-8') as file:
    content = file.readlines()

filter_lines = []
for line in content:
    if line.startswith('#pi') or line.startswith('#upi'):
        continue
    else:
        if line.startswith('#t'):
            updated_content = line.replace('#t', 'Research Interest:')
        elif line.startswith('#a'):
            updated_content = line.replace('#a', 'Affiliations:')
        elif line.startswith('#n'):
            updated_content = line.replace('#n', 'Name:')
        elif line.startswith('#pc'):
            updated_content = line.replace('#pc', 'The count of published papers:')
        elif line.startswith('#hi'):
            updated_content = line.replace('#hi', 'H-index:')
        elif line.startswith('#cn'):
            updated_content = line.replace('#cn', 'Citations:')
        elif line.startswith('#index'):
            updated_content = line
        else:
            updated_content = '\n'
        filter_lines.append(updated_content)

# 将替换后的内容写入新文件
with open(output_file, 'w', encoding='utf-8') as file:
    file.writelines(filter_lines)

print("所有'#t'已成功替换为'a'并保存到", output_file)
