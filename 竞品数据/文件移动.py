import os
import shutil
import datetime

# 获取用户的下载目录
download_dir = os.path.expanduser('~') + '\\Downloads'

# 目标目录
target_dir = 'D:\\WorkFlow\\data_python\\竞品数据'

# 文件关键词（改这里）
file_keyword = '蔚蓝每日双端数据'
file_ext = '.csv'

# 确保目标目录存在
if not os.path.exists(target_dir):
    os.makedirs(target_dir)
def run():
    # 查找下载目录中所有符合条件的文件
    matching_files = []
    for root, dirs, files in os.walk(download_dir):
        for file in files:
            # ✅ 改成“包含匹配”
            if file_keyword in file and file.endswith(file_ext):
                file_path = os.path.join(root, file)
                matching_files.append((file_path, os.path.getmtime(file_path)))

    if not matching_files:
        print(f"未找到包含关键词的文件: {file_keyword}")
    else:
        # 按修改时间排序，获取最新的文件
        matching_files.sort(key=lambda x: x[1], reverse=True)
        latest_file = matching_files[0][0]
        print(f"找到最新文件: {latest_file}")

        # 取原始文件名（不是固定名）
        original_name = os.path.basename(latest_file)
        target_file = os.path.join(target_dir, original_name)

        # 检查目标文件是否存在
        if os.path.exists(target_file):
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            name, ext = os.path.splitext(original_name)
            new_file_name = f"{name}_{timestamp}{ext}"
            target_file = os.path.join(target_dir, new_file_name)
            print(f"文件已存在，使用新文件名: {new_file_name}")

        # 复制文件
        shutil.copy2(latest_file, target_file)
        print(f"文件已复制到: {target_file}")
        return target_file

# 允许单独运行测试
if __name__ == '__main__':
    run()