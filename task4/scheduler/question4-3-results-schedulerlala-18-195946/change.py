def adjust_data(input_file, output_file):
    with open(input_file, 'r') as f:
        lines = f.readlines()

    modified_lines = []
    for line in lines:
        if line.strip().startswith("read"):
            modified_lines.append(line)
            previous_line = line
        else:
            # 如果不是以 "read" 开头的行，则将数据挪到上一行的末尾
            previous_line = previous_line.strip() + " " + line.strip() + "\n"
            modified_lines[-1] = previous_line

    with open(output_file, 'w') as f:
        f.writelines(modified_lines)

# 输入文件名和输出文件名
input_file = "1.txt"
output_file = "2.txt"

# 调用函数进行调整
adjust_data(input_file, output_file)

print("调整完成！")
