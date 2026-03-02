import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import time

from data_clean import timestamp

# 全局样式设置
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid", font='SimHei')


def plot_user_behavior(df, target_date, user_types, output_dir='plots'):
    """
    对比流失与留存玩家合成等级占比分布
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. 筛选数据
    mask = (df['log_date'] == target_date) & (df['user_type'].isin(user_types))
    plot_df = df[mask].copy()

    if plot_df.empty:
        print(f"⚠️ [draw] 未找到 {target_date} 数据")
        return None

    # 2. 构造进度标签
    plot_df['进度'] = (plot_df['章节'] + "\n" + plot_df['关卡'] + "\n回" + plot_df['回合'].astype(str))

    # 3. 宽表转长表
    level_cols = [c for c in plot_df.columns if '等级' in str(c)]
    df_melted = plot_df.melt(
        id_vars=['user_type', '阶段', '进度'],
        value_vars=level_cols,
        var_name='合成等级',
        value_name='卡牌数量'
    )

    # 4. 【核心修改】消除绝对值差异：计算每个阶段/进度下，各等级的占比
    # 分组计算总数，然后合并回去计算百分比
    group_cols = ['user_type', '阶段', '进度']
    df_melted['该组总数'] = df_melted.groupby(group_cols)['卡牌数量'].transform('sum')

    # 避免除以0
    df_melted['百分比'] = (df_melted['卡牌数量'] / df_melted['该组总数']).fillna(0) * 100

    # 5. 绘图
    try:
        # 使用百分比作为 y 轴
        g = sns.catplot(
            data=df_melted,
            x='合成等级', y='百分比', hue='user_type',
            col='阶段', row='进度',
            kind='bar',
            height=4, aspect=2.5,
            sharey=True,  # 既然是百分比，建议统一 Y 轴看整体分布
            palette='Set2',
            margin_titles=True
        )

        # 6. 细节优化：X轴文字横向展示
        for ax in g.axes.flat:
            plt.setp(ax.get_xticklabels(), rotation=0, horizontalalignment='center')
            # 确保每个柱子下都有刻度
            ax.set_xticks(range(len(level_cols)))
            ax.set_xticklabels(level_cols)

        g.set_axis_labels("合成等级", "卡牌数量占比 (%)")
        g.set_titles(row_template="{row_name}", col_template="{col_name}")
        g.fig.suptitle(f'日期 {target_date}：留存/流失玩家合成等级【占比】分布对比', y=1.02, fontsize=16)

        plt.subplots_adjust(hspace=0.6)
        timestamp = time.strftime("%H%M%S")
        file_path = os.path.join(output_dir, f'dist_percent_{target_date}_{timestamp}.png')
        plt.savefig(file_path, bbox_inches='tight', dpi=100)
        plt.close()
        return file_path

    except Exception as e:
        print(f"❌ [draw] 绘图出错: {e}")
        return None