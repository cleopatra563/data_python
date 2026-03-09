"""
1、读取本地文件(根据文件)
2、按照文件名增加一列
3、合并多个文件
4、输出结果
"""
import pandas as pd
import time
import glob
import os

def merge_csv_files():
    try:
        #1.读取本地文件
        filelist = glob.glob('*_次日*用户.csv')
        if not filelist:
            print(f"❌未找到匹配的CSV文件，请检查文件路径和名称。")
            return

        all_data = []
        for file in filelist:
            try: #处理编码问题
                df = pd.read_csv(file,encoding='utf-8')
            except:
                df = pd.read_csv(file,encoding = 'gbk')
            # 增加一列
            df['来源'] = os.path.basename(file).replace('.csv','')
            all_data.append(df)

        #2.合并多个文件
        result = pd.concat(all_data,ignore_index=True)

        #3.输出合并结果
        timestamp = time.strftime('%H%M%S')
        output_file = f'合成后文件_{timestamp}.csv'
        result.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"✅处理完成！共合并{len(filelist)}个文件，📂最终文件已保存为：{output_file}")
        print("\n---表格预览(前10行)---")
        print(result.head(10))

    except Exception as e:
        print(f"❌处理失败，错误原因：{e}")


if __name__ == '__main__':
    merge_csv_index = merge_csv_files()
