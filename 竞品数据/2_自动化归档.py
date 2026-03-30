import os
import shutil


def archive_pivot_files():
    target_folder = 'pivot_archive'

    # 如果文件夹不存在则创建
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
        print(f"创建文件夹: {target_folder}")

    files = [f for f in os.listdir('.') if os.path.isfile(f)]

    for file in files:
        # 匹配逻辑：以 pivot_data 开头，但不是原始的 pivot_data.csv
        if file.startswith('pivot_data') and file != 'pivot_data.csv':
            try:
                shutil.move(file, os.path.join(target_folder, file))
                print(f"已归档: {file}")
            except Exception as e:
                print(f"处理 {file} 时出错: {e}")


if __name__ == "__main__":
    archive_pivot_files()
    print("-" * 20)
    print("Pivot 数据归档完成！")