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
#检测csv编码
def detect_csv():
    import chardet
    with open('蔚蓝每日双端数据 (5).csv','rb') as f:
        result = chardet.detect(f.read())
    csv_encoding = result['encoding']
    print(f'csv_encoding:{csv_encoding}')

# 获取主表和副表
import pandas as pd
path = '蔚蓝每日双端数据.xlsx'
orgin_data = pd.read_excel(path,sheet_name = '蔚蓝每日双端数据',header = 0)
print(orgin_data.head())
##日期格式化 年-月-日
orgin_data['日期'] = pd.to_datetime(orgin_data['日期']).dt.strftime('%Y-%m-%d')
orgin_data['日期'] = pd.to_datetime().dt.strftime()

'''
data_column = '日期'
if date_colmn in .columns



'''

downloadData = orgin_data[['日期','下载量']]
print(downloadData.head())

path_sub = '蔚蓝每日双端数据 (5).csv'
sub_data = pd.read_csv(path_sub,encoding= 'utf-16',sep = '	') #检测编码，使用分隔符
##日期格式化 年-月-日
data_column = '日期'
if data_column in sub_data.columns:
    sub_data[data_column] = pd.to_datetime(sub_data[data_column]).dt.strftime('%Y-%m-%d')

# 两表去重
merged_data = pd.concat([orgin_data,sub_data],ignore_index = True) #重置索引
print(f'merged:{merged_data}')
output_file_path = 'merged_data.csv'
merged_data.to_csv(output_file_path, index=False, encoding='utf-8-sig') #不写入索引，utf-8编码，正确显示中文

#处理时间格式



# 数据透视表




#数据透视表导出




# 定义主函数
# def main():
#     detect_csv()
#
#
#
# # 测试用例
# if __name__ == '__main__':
#     main()