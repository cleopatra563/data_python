import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import time

# 设置全局样式
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid", font='SimHei')


def plot_user_behavior(df, target_date, user_types, output_dir='plots'):
    """
    对比流失与留存玩家在特定日期的合成等级分布
    :param df: 原始透视表数据 (DataFrame)
    :param target_date: 日期字符串，如 '2026-02-09'
    :param user_types: 玩家类型列表
    :param output_dir: 图片保存目录
    """
    # 1. 确保目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 2. 筛选数据
    mask = (df['log_date'] == target_date) & (df['user_type'].isin(user_types))
    plot_df = df[mask].copy()

    if plot_df.empty:
        print(f"⚠️ [draw] 未找到 {target_date} 匹配 {user_types} 的数据")
        return None

    # 3. 构造进度标签 (章节-关卡-回合)
    plot_df['进度'] = (plot_df['章节'].astype(str) + "\n" +
                       plot_df['关卡'].astype(str) + "\n回" +
                       plot_df['回合'].astype(str))

    # 4. 宽表转长表 (处理 等级1, 等级2... 列)
    level_cols = [c for c in plot_df.columns if '等级' in str(c)]
    df_melted = plot_df.melt(
        id_vars=['user_type', '阶段', '进度'],
        value_vars=level_cols,
        var_name='合成等级',
        value_name='卡牌数量'
    )

    # 5. 使用 Seaborn 绘图
    # col: 阶段 (准备/结束), row: 进度 (关卡/回合), hue: 玩家类型 (留存/流失)
    try:
        g = sns.catplot(
            data=df_melted,
            x='合成等级', y='卡牌数量', hue='user_type',
            col='阶段', row='进度',
            kind='bar',
            height=3, aspect=3,
            sharey=False,
            palette='husl',
            margin_titles=True
        )

        g.set_axis_labels("合成等级", "数量")
        g.set_titles(row_template="{row_name}", col_template="{col_name}")
        g.fig.suptitle(f'分析日期：{target_date} 合成分布对比', y=1.02, fontsize=16)

        plt.subplots_adjust(hspace=0.5)

        # 6. 保存图片
        timestamp = time.strftime("%H%M%S")
        file_path = os.path.join(output_dir, f'analysis_{target_date}_{timestamp}.png')
        plt.savefig(file_path, bbox_inches='tight', dpi=100)
        plt.close()  # 释放内存，防止在循环调用时内存溢出
        return file_path

    except Exception as e:
        print(f"❌ [draw] 绘图出错: {e}")
        return None