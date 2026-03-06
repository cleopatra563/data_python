import time
import pandas as pd

try:
    # 1. 加载数据
    file_path = 'orgin_data.xlsx'
    df = pd.read_excel(file_path,sheet_name = 'Sheet1', engine='openpyxl')

    # 2. 字段处理
    df['round_id_str'] = df['round_id'].astype(str)
    df['log_date'] = pd.to_datetime(df['log_date']).dt.strftime('%Y-%m-%d')

    event_map = {
        'main_stage_start': '1.战斗准备',
        'main_stage_end': '2.战斗结束'
    }
    df['阶段'] = df['event_name'].map(event_map)
    df['合成等级'] = df['合成等级'].fillna(0).astype(int)

    # 3. 数据透视
    # 按照 章节、关卡、回合、阶段 进行分组
    # 将 合成等级 作为列，对 sum_card_count 进行求和
    result = df.pivot_table(
        values='sum_card_count',
        index= ['user_type','log_date','章节','关卡','回合','阶段'],
        columns='合成等级',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    # 4. 优化列名显示
    level_cols = [c for c in result.columns if isinstance(c, (int, float))]
    new_col_names = {c: f'等级{int(c)}' for c in level_cols}
    result.rename(columns=new_col_names, inplace=True)

    # 5. 排序
    result = result.sort_values(
        ['user_type','log_date','章节','关卡','回合','阶段'],
        ascending = [True,True,True,True,True,False]
    )

    # 5.5 百分比转换
    percentage_cols = [col for col in result.columns if col.startswith('等级')]
    row_total = result[percentage_cols].sum(axis=1)
    # 将数值转为百分比（保留4位小数，方便后续显示）
    result[percentage_cols] = result[percentage_cols].div(row_total, axis=0).fillna(0)

    # 6. 打印输出结果（展示前10行）
    timestamp = time.strftime("%H%M%S")
    output_file = f'合成等级透视表_{timestamp}.xlsx'

    print(f"✅ 处理成功！最终文件已保存为: {output_file}")
    print("\n表格预览：")
    print("--- 章节/关卡/回合 合成等级分布统计 (sum_card_count) ---")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(result.head(10).to_string(index=False))

    # 如果需要导出到 Excel
    result.to_excel(output_file, index=False)

    #7. 流失VS留存用户趋势图
    # 调用画图脚本
    # from draw2 import plot_user_behavior
    #
    # # 场景 1: 分析 0209
    # path09 = plot_user_behavior(
    #     result,
    #     '2026-02-09',
    #     ['cbt1_0209_次日流失玩家', 'cbt1_0209_次日留存玩家']
    # )
    #
    # # 场景 2: 分析 0210
    # path10 = plot_user_behavior(
    #     result,
    #     '2026-02-10',
    #     ['cbt1_0210_次日流失玩家', 'cbt1_0210_次日留存玩家']
    # )
    #
    # if path09:
    #     print(f"分析完成，图表保存在: {path09}")

except Exception as e:
    print(f"❌处理失败，错误原因：{e}")