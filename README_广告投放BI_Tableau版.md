# 广告投放 BI 系统 README（Tableau 版本）

## 1. 文档目标

基于 `merged_adjust_fb.csv`（及同结构时间戳文件）搭建广告投放 BI，看板工具为 Tableau，数据库为 SQLite。  
本 README 提供可直接落地的内容：

1. 指标口径
2. 报表与图表参考
3. SQLite 表结构（DDL）
4. CSV 导入 SQLite 可执行命令（`.mode` / `.import`）
5. Tableau 建模与拖拽清单

---

## 2. 数据字段（当前可用）

源表字段：

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

## 3. 指标口径

### 3.1 原生指标

- 花费：`spend`
- 展示：`impressions`
- 点击：`clicks`
- 安装：`installs`
- 收入：`revenue`
- 25%播放次数：`视频播放进度25%次数`
- 50%播放次数：`视频播放进度50%次数`
- 平均播放时长：`视频平均播放时长`

### 3.2 衍生指标（Tableau 计算字段）

- CTR = `SUM([clicks]) / SUM([impressions])`
- CPC = `SUM([spend]) / SUM([clicks])`
- CPM = `SUM([spend]) / SUM([impressions]) * 1000`
- CPI = `SUM([spend]) / SUM([installs])`
- CVR = `SUM([installs]) / SUM([clicks])`
- ROAS = `SUM([revenue]) / SUM([spend])`
- 25%进度完播率 = `SUM([video_play_25]) / SUM([impressions])`
- 50%进度完播率 = `SUM([video_play_50]) / SUM([impressions])`

> 当前数据暂缺：付费用户数、付费次数、分日留存、0D/3D/7D/30D 收入明细。后续补充事件明细表后扩展。

---

## 4. 报表与图表参考

### 4.1 优化师总览页

- KPI：花费、展示、点击、安装、收入、CTR、CPI、ROAS
- 趋势折线：按 `stat_date` 展示花费/安装/收入
- 漏斗：展示 -> 点击 -> 安装
- 国家消耗占比：饼图
- Campaign 消耗排行：条形图
- 广告明细矩阵：广告名称 + 国家 + 核心指标

### 4.2 设计师素材页

- 单素材收入趋势折线
- 周维度素材消耗环比柱状
- 素材方向消耗占比饼图
- 素材数量统计（按素材方向/设计师）
- 新素材/次新素材/老素材消耗（柱状 + 占比）

---

## 5. SQLite 数据库结构（DDL）

建议数据库文件：`D:\WorkFlow\data_python\ad_bi.db`

```sql
-- 原始层：与 CSV 一一对应
CREATE TABLE IF NOT EXISTS ods_merged_adjust_fb (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  day_raw TEXT NOT NULL,
  os_name TEXT,
  country TEXT,
  events REAL DEFAULT 0,
  campaign_id_raw TEXT,
  creative_id_network_raw TEXT,
  creative_network TEXT,
  account_id_raw TEXT,
  ad_id_raw TEXT,
  ad_name TEXT,
  spend REAL DEFAULT 0,
  installs INTEGER DEFAULT 0,
  revenue REAL DEFAULT 0,
  impressions_adjust INTEGER DEFAULT 0,
  clicks_adjust INTEGER DEFAULT 0,
  impressions INTEGER DEFAULT 0,
  clicks INTEGER DEFAULT 0,
  video_play_25 INTEGER DEFAULT 0,
  video_play_50 INTEGER DEFAULT 0,
  video_avg_watch_seconds REAL DEFAULT 0,
  etl_loaded_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 分析层：Tableau 直连事实表
CREATE TABLE IF NOT EXISTS dwd_ad_daily_fact (
  fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
  stat_date TEXT NOT NULL,                   -- YYYY-MM-DD
  channel TEXT NOT NULL DEFAULT 'Meta',
  os_name TEXT,
  country TEXT,
  events REAL DEFAULT 0,
  campaign_id TEXT,
  creative_id_network TEXT,
  account_id TEXT,
  ad_id TEXT,
  creative_network TEXT,
  ad_name TEXT,
  spend REAL DEFAULT 0,
  installs INTEGER DEFAULT 0,
  revenue REAL DEFAULT 0,
  impressions_adjust INTEGER DEFAULT 0,
  clicks_adjust INTEGER DEFAULT 0,
  impressions INTEGER DEFAULT 0,
  clicks INTEGER DEFAULT 0,
  video_play_25 INTEGER DEFAULT 0,
  video_play_50 INTEGER DEFAULT 0,
  video_avg_watch_seconds REAL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_dwd_stat_date ON dwd_ad_daily_fact(stat_date);
CREATE INDEX IF NOT EXISTS idx_dwd_country ON dwd_ad_daily_fact(country);
CREATE INDEX IF NOT EXISTS idx_dwd_os_name ON dwd_ad_daily_fact(os_name);
CREATE INDEX IF NOT EXISTS idx_dwd_campaign_id ON dwd_ad_daily_fact(campaign_id);
CREATE INDEX IF NOT EXISTS idx_dwd_ad_id ON dwd_ad_daily_fact(ad_id);
```

---

## 6. CSV 导入 SQLite（可执行命令）

### 6.1 打开数据库

```powershell
sqlite3 D:\WorkFlow\data_python\ad_bi.db
```

### 6.2 每次自动使用最新 `merged_adjust_fb*.csv` 导入临时表

```powershell
$dbPath = "D:\WorkFlow\data_python\ad_bi.db"
$csvDir = "D:\WorkFlow\data_python\广告数据拉取"
$latestCsv = Get-ChildItem -Path $csvDir -File -Filter "merged_adjust_fb*.csv" |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

if (-not $latestCsv) { throw "未找到 merged_adjust_fb*.csv" }

$csvPath = $latestCsv.FullName.Replace('\', '/')
$sql = @"
.mode csv
.headers on
DROP TABLE IF EXISTS stg_merged_adjust_fb;
.import "$csvPath" stg_merged_adjust_fb
"@

$tmpSql = Join-Path $env:TEMP "sqlite_import_latest.sql"
Set-Content -Path $tmpSql -Value $sql -Encoding UTF8
sqlite3 $dbPath ".read $tmpSql"
Write-Host "已导入最新文件: $($latestCsv.FullName)"
```

### 6.3 写入 ODS 表

```sql
INSERT INTO ods_merged_adjust_fb (
  day_raw, os_name, country, events,
  campaign_id_raw, creative_id_network_raw, creative_network,
  account_id_raw, ad_id_raw, ad_name,
  spend, installs, revenue, impressions_adjust, clicks_adjust,
  impressions, clicks, video_play_25, video_play_50, video_avg_watch_seconds
)
SELECT
  day,
  os_name,
  country,
  events,
  campaign_id,
  creative_id_network,
  creative_network,
  account_id,
  ad_id,
  ad_name,
  spend,
  installs,
  revenue,
  impressions_adjust,
  clicks_adjust,
  impressions,
  clicks,
  "视频播放进度25%次数",
  "视频播放进度50%次数",
  "视频平均播放时长"
FROM stg_merged_adjust_fb;
```

### 6.4 ODS -> DWD

```sql
INSERT INTO dwd_ad_daily_fact (
  stat_date, channel, os_name, country, events,
  campaign_id, creative_id_network, account_id, ad_id, creative_network, ad_name,
  spend, installs, revenue, impressions_adjust, clicks_adjust, impressions, clicks,
  video_play_25, video_play_50, video_avg_watch_seconds
)
SELECT
  date(replace(day_raw, '/', '-')) AS stat_date,
  'Meta' AS channel,
  os_name,
  country,
  ifnull(events, 0),
  replace(replace(campaign_id_raw, '="', ''), '"', '') AS campaign_id,
  replace(replace(creative_id_network_raw, '="', ''), '"', '') AS creative_id_network,
  replace(replace(account_id_raw, '="', ''), '"', '') AS account_id,
  replace(replace(ad_id_raw, '="', ''), '"', '') AS ad_id,
  creative_network,
  ad_name,
  ifnull(spend, 0),
  ifnull(installs, 0),
  ifnull(revenue, 0),
  ifnull(impressions_adjust, 0),
  ifnull(clicks_adjust, 0),
  ifnull(impressions, 0),
  ifnull(clicks, 0),
  ifnull(video_play_25, 0),
  ifnull(video_play_50, 0),
  ifnull(video_avg_watch_seconds, 0)
FROM ods_merged_adjust_fb
WHERE date(replace(day_raw, '/', '-')) IS NOT NULL;
```

---

## 7. Tableau 建模与拖拽清单

### 7.1 数据源

- 连接 SQLite：`ad_bi.db`
- 主表：`dwd_ad_daily_fact`
- `stat_date` 设置为日期类型

### 7.2 维度（Dimensions）

- `stat_date`
- `channel`
- `os_name`
- `country`
- `campaign_id`
- `ad_id`
- `creative_id_network`
- `ad_name`
- `creative_network`

### 7.3 度量（Measures）

- `spend`
- `impressions`
- `clicks`
- `installs`
- `revenue`
- `video_play_25`
- `video_play_50`
- `video_avg_watch_seconds`
- `impressions_adjust`
- `clicks_adjust`
- `events`

### 7.4 Tableau 计算字段

`CTR`
```tableau
IF SUM([impressions]) = 0 THEN 0
ELSE SUM([clicks]) / SUM([impressions])
END
```

`CPC`
```tableau
IF SUM([clicks]) = 0 THEN 0
ELSE SUM([spend]) / SUM([clicks])
END
```

`CPM`
```tableau
IF SUM([impressions]) = 0 THEN 0
ELSE SUM([spend]) / SUM([impressions]) * 1000
END
```

`CPI`
```tableau
IF SUM([installs]) = 0 THEN 0
ELSE SUM([spend]) / SUM([installs])
END
```

`CVR`
```tableau
IF SUM([clicks]) = 0 THEN 0
ELSE SUM([installs]) / SUM([clicks])
END
```

`ROAS`
```tableau
IF SUM([spend]) = 0 THEN 0
ELSE SUM([revenue]) / SUM([spend])
END
```

`视频25完播率`
```tableau
IF SUM([impressions]) = 0 THEN 0
ELSE SUM([video_play_25]) / SUM([impressions])
END
```

`视频50完播率`
```tableau
IF SUM([impressions]) = 0 THEN 0
ELSE SUM([video_play_50]) / SUM([impressions])
END
```

### 7.5 图表拖拽清单

1. KPI：`SUM(spend)`、`SUM(installs)`、`SUM(revenue)`、`CTR`、`CPI`、`ROAS`
2. 趋势折线：`Columns=stat_date`，`Rows=SUM(spend)/SUM(installs)/SUM(revenue)`
3. 国家排行：`Rows=country`，`Columns=SUM(spend)`
4. Campaign 排行：`Rows=campaign_id`，`Columns=SUM(spend)`，Tooltip 增加 `CTR/CPI/ROAS`
5. 素材矩阵：行 `ad_name`，列 `country`，值 `spend/installs/CPI/ROAS`
6. 视频图：类别 `ad_name`，值 `视频25完播率/视频50完播率`

---

## 8. 飞书云文档使用建议

- 直接复制本 README 到飞书文档即可，结构已按飞书阅读习惯拆分
- 建议在飞书中将第 5~7 章设置为折叠块，便于评审
- 对外展示时可保留第 1~4 章；技术落地保留全部章节

