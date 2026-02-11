import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 1. 数据准备 (包含 CBT3 数据)
data = {
    '测试版本': ['CBT0', 'CBT1', 'CBT2', 'CBT3'],
    'X轴标签': ['v1.5.3', 'v1.6.0', 'v1.7.0', 'v1.8.0'],  # 对应的版本号
    'CPI': [0.93, 0.27, 0.20, 0.17],
    '次留': [17.65, 18.09, 29.21, 30.34],
    '7留': [2.22, 3.85, 9.34, 7.92],
    'CPI环比下降': [0, -70.97, -25.93, -15.00],
    '次留环比增长': [0, 2.49, 61.47, 3.87],
    '7留环比增长': [0, 73.42, 142.60, -15.20]
}

df = pd.DataFrame(data)

# 2. 设置绘图风格
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
plt.style.use('seaborn-v0_8-whitegrid')  # 使用更清晰的网格风格

# 3. 创建画布和双坐标轴
fig, ax1 = plt.subplots(figsize=(14, 8))

# 主坐标轴 (左侧): 用于显示留存率 (百分比)
ax1.set_xlabel('测试版本', fontsize=12)
ax1.set_ylabel('留存率 (%)', color='black', fontsize=12)
ax1.set_ylim(0, 35)  # Y轴范围对应图片中的 0% 到 35%
ax1.set_xticks(range(len(df)))
ax1.set_xticklabels(df['X轴标签'], fontsize=10)

# 次坐标轴 (右侧): 用于显示 CPI (美元)
ax2 = ax1.twinx()
ax2.set_ylabel('CPI ($)', color='orange', fontsize=12)
ax2.set_ylim(0, 1.0)  # Y轴范围对应图片中的 $0.00 到 $1.00

# 4. 绘制柱状图 (留存率)
bar_width = 0.35
x = np.arange(len(df))

# 次留 (浅蓝色)
bars1 = ax1.bar(x - bar_width / 2, df['次留'], bar_width, label='次留', color='#6495ED', alpha=0.8)
# 7留 (深蓝色)
bars2 = ax1.bar(x + bar_width / 2, df['7留'], bar_width, label='7留', color='#4169E1', alpha=0.8)

# 5. 绘制折线图 (CPI)
# CPI (橙色圆点线)
ax2.plot(x, df['CPI'], 'o-', color='orange', linewidth=2, markersize=8, label='CPI')


# 6. 添加数据标签
def add_labels(bars, values, offset=0.5):
    """在柱状图或折线图上添加标签"""
    for bar, val in zip(bars, values):
        height = bar.get_height() if hasattr(bar, 'get_height') else val
        ax1.text(bar.get_x() + bar.get_width() / 2, height + offset,
                 f'{val:.2f}%' if val != 0 else '',
                 ha='center', va='bottom', color='black', fontweight='bold', fontsize=9)


# 为柱状图添加数值标签
add_labels(bars1, df['次留'], 1)
add_labels(bars2, df['7留'], 0.5)

# 为 CPI 折线添加数值标签
for i, val in enumerate(df['CPI']):
    ax2.text(i, val + 0.03, f'${val:.2f}', ha='center', va='bottom',
             color='orange', fontweight='bold', fontsize=10)

# 7. 添加环比增长箭头和数据 (这是最核心的视觉元素)
# 注意：从第二个数据点开始绘制
for i in range(1, len(df)):
    # 计算位置
    x_pos = i
    y_pos_cpi = df['CPI'][i]
    y_pos_7d = df['7留'][i]

    # 1. CPI 环比变化 (橙色)
    # 箭头位置 (在 CPI 折线点的上方或下方)
    anno_y_cpi = y_pos_cpi + 0.08 if df['CPI环比下降'][i] < 0 else y_pos_cpi + 0.12
    color_cpi = 'red' if df['CPI环比下降'][i] < 0 else 'green'

    ax2.annotate(f"{df['CPI环比下降'][i]:.1f}%",
                 xy=(x_pos, y_pos_cpi),
                 xytext=(x_pos, anno_y_cpi),
                 color=color_cpi,
                 fontsize=10,
                 ha='center',
                 arrowprops=dict(arrowstyle="->", color=color_cpi, lw=1))

    # 2. 7留 环比变化 (蓝色)
    # 箭头位置 (在 7留 柱子的上方或下方)
    anno_y_7d = y_pos_7d + 1.5 if df['7留环比增长'][i] > 0 else y_pos_7d - 2
    color_7d = 'blue' if df['7留环比增长'][i] > 0 else 'red'

    ax1.annotate(f"{df['7留环比增长'][i]:.1f}%",
                 xy=(x_pos, y_pos_7d),
                 xytext=(x_pos, anno_y_7d),
                 color=color_7d,
                 fontsize=10,
                 ha='center',
                 arrowprops=dict(arrowstyle="->", color=color_7d, lw=1))

# 8. 添加图例和标题
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines + lines2, labels + labels2, loc='upper left', fontsize=10, frameon=True)

plt.title('Joyjoy 历测留存及 CPI 趋势分析', fontsize=16, pad=20)
plt.grid(True, axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
plt.show()