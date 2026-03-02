
import pandas as pd
import time

# 1.加载数据
file_path = 'orgin_data.xlsx'
df = pd.read_excel(file_path,sheet_name = 'Sheet1')
# print(df['round_id'])

# 2.基础字段处理
# 基础字段处理
df['round_id_str'] = df['round_id'].astype(str)
df['log_date'] = pd.to_datetime(df['log_date']).dt.strftime('%Y-%m-%d')

# 阶段映射
event_map = {'main_stage_start':'战斗准备','main_stage_end':'战斗结束'}
df['阶段'] = df['event_name'].map(event_map)
df['合成等级'] = df['合成等级'].fillna(0).astype(int)
# print(df)
# print(df.columns)

# 3.计算人均数量
# 按维度汇总【总数量】和【去重人数】
group_cols = ['user_type','log_date','章节','关卡','回合','阶段']
pivot_sum = df.pivot_table(
    index = group_cols,
    columns = '合成等级',
    values = '对应数量',
    aggfunc = 'sum',
    fill_value = 0
)

# 计算人均：总量 / 人数
# user_count = df.groupby(group_cols)['role_num'].nunique()
# pivot_avg = pivot_sum.div(user_count,axis = 0).reset_index()

# 4.格式美化
cols = list(pivot_sum.columns)
for i in range(len(group_cols), len(cols)):
    cols[i] = f"{int(cols[i])}级总数"
pivot_sum.columns = cols

# 5.排序
pivot_sum = pivot_sum.sort_values(
    ['user_type','log_date','章节','关卡','回合','阶段'],
    ascending = [True,True,True,True,True,False]

)

# 6.导出结果
timestamp = time.strftime("%H%M%S")
output_file = f'合成等级总量分布统计_{timestamp}.xlsx'

try:
    pivot_sum.to_excel(output_file, index=False)
    print(f"✅ 处理成功！最终文件已保存为: {output_file}")
    print("\n表格预览：")
    print(pivot_sum.head())
except PermissionError:
    print("❌ 错误：文件被占用，请关闭 Excel 后重试。")
print(pivot_sum.tail())