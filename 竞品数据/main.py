from 文件移动 import run as move_run
from 蔚蓝数据处理 import process_data

def main():
    # 1. 获取文件路径
    file_path = move_run()

    if not file_path:
        print("❌ 流程终止：没有找到文件")
        return

    # 2. 处理数据
    process_data(file_path)


if __name__ == "__main__":
    main()