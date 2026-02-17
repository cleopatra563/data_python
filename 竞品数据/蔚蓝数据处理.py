"""
处理步骤
1、获取最新数据
    ST下载
2、文件合并并去重
    表1[sheet_name] = '蔚蓝每日双端数据'
3、制作数据透视表
    行 = 日期
    列 = 国家+平台
    求和项 = 下载量和收入
4、制作的透视表导出
"""
import pandas as pd
#检测csv编码
csv_file = '蔚蓝每日双端数据 (6).csv'

def detect_csv(): # csv编码检查
    import chardet
    with open(csv_file,'rb') as f:
        result = chardet.detect(f.read())
    csv_encoding = result['encoding']
    print(f'csv_encoding:{csv_encoding}')

def merge_pivot(): #数据处理
    # 获取主表和副表
    path = '蔚蓝每日双端数据.xlsx'
    origin_data = pd.read_excel(path,sheet_name = '蔚蓝每日双端数据',header = 0)
    sub_data = pd.read_csv(csv_file,encoding= 'utf-16',sep = '	') #检测编码，使用分隔符
    print(origin_data.head())

    # 日期格式化 年-月-日
    origin_data['日期'] = pd.to_datetime(origin_data['日期']).dt.strftime('%Y-%m-%d')
    sub_data['日期'] = pd.to_datetime(sub_data['日期']).dt.strftime('%Y-%m-%d')

    '''
    # 抽象化
    data_column = '日期'
    if data_column in origin_data.columns:
        pd.to_datetime(origin_data[data_column]).dt.strftime('%Y-%m-%d')
    '''

    # 两表去重
    merged_data = pd.concat([origin_data,sub_data],ignore_index = True) #重置索引
    print(f'merged:{merged_data}')
    output_mergeFile_path = 'merged_data.csv'
    merged_data.to_csv(output_mergeFile_path, index=False, encoding='utf-8-sig') #不写入索引，utf-8编码，正确显示中文

    # 数据透视表
    pivot_data = pd.pivot_table(
        merged_data
        ,values = ['下载量','收入']
        ,index = ['日期']
        ,columns = ['国家','平台']
        ,aggfunc = {'下载量':'sum','收入':'sum'}
        ,fill_value = 0 # 填充缺失值
    )
    pivot_data.reset_index(inplace=True) # 复位日期索引，成为普通列

    #数据透视表导出
    output_pivotFile_path = 'pivot_data.csv'
    pivot_data.to_csv(output_pivotFile_path,index=False,encoding = 'utf-8-sig')

# 定义主函数
def main():
    merge_pivot()

# 测试用例
if __name__ == '__main__':
    main()