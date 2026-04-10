# 广告投放 BI 系统设计说明（基于 merged_adjust_fb）

## 1. 文档目的

本方案用于指导搭建广告投放 BI 系统，覆盖以下内容：

- 指标参考（原生指标 + 衍生指标）
- 报表风格与图表参考
- 可执行数据库表结构（DDL）
- 与现有字段一一对应的 Power BI 建模与图表清单（按字段拖拽即可）

> 说明：你提到的文件名为 `merged_adjusts_fb.csv`，当前目录实际可见主文件为 `merged_adjust_fb.csv`（及带时间戳版本），本文按该结构设计。

---

## 2. 数据基础与字段清单

当前可用字段（以 `merged_adjust_fb_20260401152444.csv` 为准）：

- `day`
- `os_name`
- `country`
- `events`
- `campaign_id`
- `creative_id_network`
- `creative_network`
- `account_id`
- `ad_id`
- `ad_name`
- `spend`
- `installs`
- `revenue`
- `impressions_adjust`
- `clicks_adjust`
- `impressions`
- `clicks`
- `视频播放进度25%次数`
- `视频播放进度50%次数`
- `视频平均播放时长`

---

## 3. 指标参考（结合 BI 需求 PDF）

### 3.1 原生指标（直接来自源数据）

- 花费：`spend`
- 展示：`impressions`
- 点击：`clicks`
- 安装：`installs`
- 收入：`revenue`
- 视频25%播放次数：`视频播放进度25%次数`
- 视频50%播放次数：`视频播放进度50%次数`
- 视频平均播放时长：`视频平均播放时长`

### 3.2 衍生指标（建议在 Power BI 用 DAX 计算）

- CTR = `clicks / impressions`
- CPC = `spend / clicks`
- CPM = `spend / impressions * 1000`
- CPI = `spend / installs`
- CVR = `installs / clicks`
- ROAS = `revenue / spend`
- 25%进度完播率 = `视频播放进度25%次数 / impressions`
- 50%进度完播率 = `视频播放进度50%次数 / impressions`

### 3.3 暂缺指标（后续补数）

以下指标在当前单表中缺失，需补充 Adjust 事件明细或付费用户表后再建：

- 付费用户数、付费次数
- 0D/3D/7D/30D/累计 ROAS
- 0D/3D/7D/30D/累计 LTV
- ARPU、ARPPU
- 0D/3D/7D/30D/60D 留存

---

## 4. 报表风格与图表参考

### 4.1 面向优化师的广告报表（总览页）

- 顶部 KPI 卡：花费、展示、点击、安装、收入、ROAS、CTR、CPI
- 趋势图：按 `day` 展示花费/安装/收入趋势
- 漏斗图：展示 -> 点击 -> 安装
- 分布图：国家消耗占比、终端消耗占比
- 排行图：Campaign 消耗 TopN、素材消耗 TopN
- 明细表：支持按渠道/国家/Campaign/广告名称等维度自由切换

### 4.2 面向设计师的素材看板（分析页）

- 单素材周期收入折线图
- 周维度素材消耗环比柱状图
- 素材细分方向消耗占比饼图
- 素材细分方向素材数量饼图
- 素材细分方向消耗柱状图
- 新素材/次新素材/老素材消耗柱状图 + 占比饼图
- 设计师维度素材数量统计
- 设计师维度周期消耗统计

### 4.3 页面风格建议

- 背景：浅色（白/浅灰），突出主指标
- 颜色：花费（橙/红）、收入（绿）、安装（蓝），全局统一
- 字体：中文无衬线，数值右对齐，千分位显示
- 交互：统一顶部筛选器（日期、国家、终端、Campaign、素材）

---

## 5. 数据库表结构（DDL，可执行）

建议数据库：MySQL 8.x（字符集 `utf8mb4`）

```sql
CREATE DATABASE IF NOT EXISTS ad_bi
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE ad_bi;

-- 1) 原始层（ODS）
CREATE TABLE IF NOT EXISTS ods_merged_adjust_fb (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  day_raw VARCHAR(32) NOT NULL COMMENT '原始日期字符串',
  os_name VARCHAR(32) NULL,
  country VARCHAR(32) NULL,
  events DECIMAL(18,6) DEFAULT 0,
  campaign_id_raw VARCHAR(64) NULL,
  creative_id_network_raw VARCHAR(64) NULL,
  creative_network VARCHAR(255) NULL,
  account_id_raw VARCHAR(64) NULL,
  ad_id_raw VARCHAR(64) NULL,
  ad_name VARCHAR(255) NULL,
  spend DECIMAL(18,6) DEFAULT 0,
  installs BIGINT DEFAULT 0,
  revenue DECIMAL(18,6) DEFAULT 0,
  impressions_adjust BIGINT DEFAULT 0,
  clicks_adjust BIGINT DEFAULT 0,
  impressions BIGINT DEFAULT 0,
  clicks BIGINT DEFAULT 0,
  video_play_25 BIGINT DEFAULT 0 COMMENT '视频播放进度25%次数',
  video_play_50 BIGINT DEFAULT 0 COMMENT '视频播放进度50%次数',
  video_avg_watch_seconds DECIMAL(18,6) DEFAULT 0 COMMENT '视频平均播放时长',
  etl_loaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2) 事实层（DWD）
CREATE TABLE IF NOT EXISTS dwd_ad_daily_fact (
  fact_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  stat_date DATE NOT NULL,
  channel VARCHAR(32) NOT NULL DEFAULT 'Meta',
  os_name VARCHAR(32) NULL,
  country VARCHAR(32) NULL,
  events DECIMAL(18,6) DEFAULT 0,

  campaign_id VARCHAR(64) NULL,
  creative_id_network VARCHAR(64) NULL,
  account_id VARCHAR(64) NULL,
  ad_id VARCHAR(64) NULL,
  creative_network VARCHAR(255) NULL,
  ad_name VARCHAR(255) NULL,

  spend DECIMAL(18,6) DEFAULT 0,
  installs BIGINT DEFAULT 0,
  revenue DECIMAL(18,6) DEFAULT 0,
  impressions_adjust BIGINT DEFAULT 0,
  clicks_adjust BIGINT DEFAULT 0,
  impressions BIGINT DEFAULT 0,
  clicks BIGINT DEFAULT 0,
  video_play_25 BIGINT DEFAULT 0,
  video_play_50 BIGINT DEFAULT 0,
  video_avg_watch_seconds DECIMAL(18,6) DEFAULT 0,

  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_stat_date (stat_date),
  KEY idx_country (country),
  KEY idx_os_name (os_name),
  KEY idx_campaign_id (campaign_id),
  KEY idx_ad_id (ad_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3) ODS -> DWD 装载示例
INSERT INTO dwd_ad_daily_fact (
  stat_date, channel, os_name, country, events,
  campaign_id, creative_id_network, account_id, ad_id, creative_network, ad_name,
  spend, installs, revenue, impressions_adjust, clicks_adjust, impressions, clicks,
  video_play_25, video_play_50, video_avg_watch_seconds
)
SELECT
  STR_TO_DATE(REPLACE(day_raw, '/', '-'), '%Y-%m-%d') AS stat_date,
  'Meta' AS channel,
  os_name,
  country,
  COALESCE(events, 0),
  REPLACE(REPLACE(campaign_id_raw, '="', ''), '"', '') AS campaign_id,
  REPLACE(REPLACE(creative_id_network_raw, '="', ''), '"', '') AS creative_id_network,
  REPLACE(REPLACE(account_id_raw, '="', ''), '"', '') AS account_id,
  REPLACE(REPLACE(ad_id_raw, '="', ''), '"', '') AS ad_id,
  creative_network,
  ad_name,
  COALESCE(spend, 0),
  COALESCE(installs, 0),
  COALESCE(revenue, 0),
  COALESCE(impressions_adjust, 0),
  COALESCE(clicks_adjust, 0),
  COALESCE(impressions, 0),
  COALESCE(clicks, 0),
  COALESCE(video_play_25, 0),
  COALESCE(video_play_50, 0),
  COALESCE(video_avg_watch_seconds, 0)
FROM ods_merged_adjust_fb
WHERE STR_TO_DATE(REPLACE(day_raw, '/', '-'), '%Y-%m-%d') IS NOT NULL;
```

---

## 6. Power BI 建模与图表清单（字段一一对应）

### 6.1 模型建议（最小可用）

- 事实表：`dwd_ad_daily_fact`
- 日期维表：`dim_date`
- 关系：`dwd_ad_daily_fact[stat_date]` -> `dim_date[Date]`

### 6.2 字段映射（源字段 -> Power BI 角色）

- 时间维度：`day` -> `stat_date`
- 终端维度：`os_name`
- 国家维度：`country`
- 广告系列：`campaign_id`
- 广告ID：`ad_id`
- 素材ID：`creative_id_network`
- 素材名称：`ad_name` / `creative_network`
- 花费指标：`spend`
- 展示指标：`impressions`
- 点击指标：`clicks`
- 安装指标：`installs`
- 收入指标：`revenue`
- 视频指标：`视频播放进度25%次数`、`视频播放进度50%次数`、`视频平均播放时长`

### 6.3 可拖拽图表清单（按对象）

1. KPI 卡片
  - 值：`SUM(spend)`、`SUM(installs)`、`SUM(revenue)`、`CTR`、`CPI`、`ROAS`
2. 趋势折线图
  - X轴：`dim_date[Date]`
  - Y轴：`SUM(spend)`、`SUM(installs)`、`SUM(revenue)`
3. 国家消耗排行（条形图）
  - 类别：`country`
  - 值：`SUM(spend)`
4. Campaign 消耗排行（条形图）
  - 类别：`campaign_id`
  - 值：`SUM(spend)`
  - 提示：`CTR`、`CPI`、`ROAS`
5. 素材表现矩阵
  - 行：`ad_name`
  - 列：`country`
  - 值：`SUM(spend)`、`SUM(installs)`、`CPI`、`ROAS`
6. 视频表现图（柱状图）
  - 类别：`ad_name`
  - 值：`25%进度完播率`、`50%进度完播率`

---

## 7. 推荐 DAX 度量（可直接复制）

```DAX
Spend = SUM('dwd_ad_daily_fact'[spend])
Impressions = SUM('dwd_ad_daily_fact'[impressions])
Clicks = SUM('dwd_ad_daily_fact'[clicks])
Installs = SUM('dwd_ad_daily_fact'[installs])
Revenue = SUM('dwd_ad_daily_fact'[revenue])

CTR = DIVIDE([Clicks], [Impressions])
CPC = DIVIDE([Spend], [Clicks])
CPM = DIVIDE([Spend] * 1000, [Impressions])
CPI = DIVIDE([Spend], [Installs])
CVR = DIVIDE([Installs], [Clicks])
ROAS = DIVIDE([Revenue], [Spend])

Video25 = SUM('dwd_ad_daily_fact'[video_play_25])
Video50 = SUM('dwd_ad_daily_fact'[video_play_50])
VideoAvgWatch = AVERAGE('dwd_ad_daily_fact'[video_avg_watch_seconds])
Video25Rate = DIVIDE([Video25], [Impressions])
Video50Rate = DIVIDE([Video50], [Impressions])
```

---

## 8. 实施顺序建议

1. 先把 CSV 入库到 `ods_merged_adjust_fb`
2. 执行装载 SQL 进入 `dwd_ad_daily_fact`
3. Power BI 连接 DWD 表并建立日期维表
4. 先完成优化师总览页，再扩展设计师素材页
5. 后续补齐付费用户/留存明细后，新增 LTV 与留存体系指标

