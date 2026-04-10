# 带序号脚本说明（1~8）

## 系统概览

本说明文档仅覆盖 `广告数据拉取` 目录下序号 **1~8** 的脚本。  
整体流程是：**拉取 Adjust/FB 数据 -> 表格合并 -> 写入飞书 -> 可视化展示 -> 群聊发送图表**。

## 目录结构（仅 1~8）

```text
data_python/
└─ 广告数据拉取/
   ├─ 1_Adjust拉取.py
   ├─ 2_FB拉取.py
   ├─ 3_表格合并.py
   ├─ 4_写入飞书表格.py
   ├─ 5_运行前四步main.py
   ├─ 6_图表展示_本地.py
   ├─ 7_图表展示_Lark.py
   └─ 8_发送飞书群聊.py
```

## 脚本用途总览

| 脚本 | 主要用途 | 输入 | 输出 |
|---|---|---|---|
| `1_Adjust拉取.py` | 拉取 Adjust 报表并做字段拆分 | Adjust API | `adjust_report_*.csv` |
| `2_FB拉取.py` | 拉取 FB 广告级数据 | FB Marketing API | `fb_ad_data_*.csv` |
| `3_表格合并.py` | 对齐 ID 后进行合并 | 1/2 步 CSV | `merged_adjust_fb_*.csv` |
| `4_写入飞书表格.py` | 批量写入飞书多维表格 | `merged_adjust_fb.csv` | 飞书记录 |
| `5_运行前四步main.py` | 串行调度 1~4 步 | 前四个脚本 | 一次性执行结果 |
| `6_图表展示_本地.py` | 本地 CSV 仪表盘展示 | `merged_adjust_fb.csv` | 本地网页（5000） |
| `7_图表展示_Lark.py` | 飞书数据仪表盘展示 | 飞书多维表格 API | 本地网页（5001） |
| `8_发送飞书群聊.py` | 图表生成并发到飞书群 | `merged_adjust_fb.csv` + 飞书机器人 | 群聊图片消息 |

---

## 逐个脚本说明（实现逻辑 + 函数用途）

## 1）`广告数据拉取/1_Adjust拉取.py`

**实现逻辑**
- 先组装 Adjust API 请求头和参数。
- 请求返回 CSV 后转为 DataFrame。
- 清洗数据并从 `campaign` 字段拆出结构化列（如 `campaign_id`）。
- 保存为 `adjust_report_日期.csv`。

**函数用途**
- `init_api()`：初始化请求头和查询参数。
- `get_adjust_campaign_data(headers, params)`：请求 Adjust 接口并解析 CSV。
- `process_data(df)`：去重、拆分 campaign 字段、补充分析列。
- `save_to_csv(df)`：保存到本地 CSV。
- `main()`：主执行入口。

## 2）`广告数据拉取/2_FB拉取.py`

**实现逻辑**
- 从环境变量读取 FB 鉴权参数并初始化 SDK。
- 按广告层级拉取花费、展示、点击、视频播放指标。
- 对 ID 列做字符串化，避免后续合并错位。
- 保存为 `fb_ad_data_日期.csv`。

**函数用途**
- `init_api()`：初始化 Facebook Ads API。
- `get_fb_campaign_data()`：循环账户拉取数据并拼接 DataFrame。
- `get_action_value(actions)`（内部函数）：提取 action 指标数值。
- `save_to_csv(df)`：保存到本地 CSV。
- `main()`：主执行入口（含异常处理）。

## 3）`广告数据拉取/3_表格合并.py`

**实现逻辑**
- 自动找到最新 Adjust/FB CSV 文件。
- 统一关键 ID 格式（含科学计数法、Excel 文本格式兼容）。
- 按 `creative_id_network + day` 对应 `ad_id + date` 左连接。
- 清洗空值并输出核心字段，导出 `merged_adjust_fb_时间戳.csv`。

**函数用途**
- `get_latest_file(pattern)`：按模式选最新文件。
- `normalize_id(value)`：统一 ID 格式。
- `main()`：读取、清洗、合并、导出完整流程。

## 4）`广告数据拉取/4_写入飞书表格.py`

**实现逻辑**
- 获取飞书 `tenant_access_token`。
- 将 DataFrame 转换成飞书记录结构。
- 日期字段转毫秒时间戳，分批（100 条）写入飞书多维表格。

**函数用途**
- `get_tenant_access_token(app_id, app_secret)`：获取飞书鉴权 token。
- `write_to_bitable(df, token)`：批量写入多维表格。
- `mock_data()`：测试数据构造（示例函数）。

## 5）`广告数据拉取/5_运行前四步main.py`

**实现逻辑**
- 使用动态加载方式导入 1~4 脚本（适配中文/数字文件名）。
- 按步骤执行：Adjust 拉取 -> FB 拉取 -> 合并 -> 飞书写入。
- 每一步独立异常处理，失败即停止，便于排查问题。

**函数用途**
- `load_module(filename, alias)`：动态导入模块。
- `step_banner(n, title)`：打印步骤标题。
- `run_step1()`：执行 Adjust 拉取。
- `run_step2()`：执行 FB 拉取。
- `run_step3()`：执行数据合并。
- `run_step4(df)`：执行飞书写入。
- `main()`：总调度入口。

## 6）`广告数据拉取/6_图表展示_本地.py`

**实现逻辑**
- 从本地 `merged_adjust_fb.csv` 读取数据。
- 按日期聚合 `installs / spend / clicks`。
- 用 Flask 返回 ECharts 页面进行可视化展示。

**函数用途**
- `load_chart_data()`：读取并聚合图表数据。
- `dashboard()`：首页路由，渲染仪表盘页面。

## 7）`广告数据拉取/7_图表展示_Lark.py`

**实现逻辑**
- 复用 `4_写入飞书表格.py` 的飞书配置和鉴权。
- 分页拉取飞书多维表格记录。
- 标准化日期并按天汇总后，用 Flask + ECharts 展示。

**函数用途**
- `load_feishu_writer_module()`：动态加载飞书写入脚本。
- `fetch_bitable_records(token, app_token, table_id)`：分页拉取飞书记录。
- `to_day_string(value)`：统一日期格式。
- `load_chart_data_from_lark()`：拉取并聚合图表数据。
- `dashboard()`：页面路由。

## 8）`广告数据拉取/8_发送飞书群聊.py`

**实现逻辑**
- 获取机器人应用 token。
- 从 merged CSV 按日期聚合后生成图表图片。
- 上传图片到飞书，拿到 `image_key`。
- 通过机器人 webhook 发送到群聊。

**函数用途**
- `get_bot_tenant_access_token()`：机器人 token 获取。
- `build_chart_image(csv_file, chart_file)`：图表生成与保存。
- `upload_image_to_feishu(token, image_path)`：上传图片，返回 `image_key`。
- `send_image_by_bot(webhook_url, image_key)`：向群聊发图片消息。
- `main()`：主执行入口。

---

## 推荐执行顺序

1. 执行数据链路：`5_运行前四步main.py`
2. 查看本地图表：`6_图表展示_本地.py`
3. 查看飞书图表：`7_图表展示_Lark.py`
4. 群内发送图表：`8_发送飞书群聊.py`