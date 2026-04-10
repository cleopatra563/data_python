# Lark Agent 功能技术实现方案（可复用现有脚本）

**文档用途**：与《Lark Agent 功能清单（基于高频场景）》配套，说明各能力在工程上的落地方式；**飞书云文档友好**（标题 + 列表，无 Markdown 表格）。

**说明**：下文仅列出**函数名与文件路径**，**密钥、Webhook、app_token 等须继续放在环境变量或现有脚本配置中**，勿写入版本库或对外文档。

---

## 一、现有工程与 Agent 的分工

**当前管道（广告域）**

- `1_Adjust拉取.py`：Adjust 报表拉取、清洗、落 CSV。
- `2_FB拉取.py`：Facebook 广告 Insights 拉取、落 CSV。
- `3_表格合并.py`：Adjust 与 FB 按创意/广告 ID 与日期合并、去重、输出合并 CSV。
- `5_运行前四步main.py`：用 `load_module` 串联上述步骤，并在 Step3 内做简化版合并、Step4 写入多维表格。
- `4_写入飞书表格.py`：`get_tenant_access_token`、`write_to_bitable`，写入飞书多维表格。
- `7_图表展示_Lark.py`：复用 `4_写入飞书表格.py` 鉴权；`fetch_bitable_records`、`to_day_string`、`load_chart_data_from_lark` 从多维表格读数并汇总。
- `8_发送飞书群聊.py`：`get_bot_tenant_access_token`、`build_chart_image`、`upload_image_to_feishu`、`send_image_by_bot`，Webhook 发图到群。
- `10_FB监控.py`：花费监控与告警思路（可与「定时推送」共用 Webhook 或改为开放 API 发卡片）。

**Agent 新增部分（与上面对齐）**

- **数仓**：产品/策划问的「新增、留存」等以**数仓语义层或参数化 SQL**为准；现有 CSV 管道可继续服务**投放侧**日报，与数仓指标在文档中**写清两套口径**。
- **Lark**：对话与卡片复用「鉴权 + 发消息」能力；在现有 Webhook 发图基础上，可增加**消息卡片 JSON**（`msg_type: interactive`）或**开放平台发群消息 API**。

---

## 二、总体技术架构（推荐）

**分层**

1. **接入层**：Lark 事件（群聊 @机器人、长连接或 HTTP 回调）→ 你的服务（Flask/FastAPI 均可；`7_图表展示_Lark.py` 已使用 Flask，可同栈扩展）。
2. **意图层**：规则 + 小模型分类 → `查数` / `问口径与报表解释` / `拉数工单`。
3. **数据层（核心）**
   - **指标 API**：`query_metric(metric_id, dims, date_range)`，内部只执行**白名单** SQL 或调用指标服务；**定时任务与对话必须调用同一函数**（对齐《功能清单》1.4）。
   - **知识库**：指标说明、报表 FAQ 的向量检索（RAG），**不参与算数**，只出引用片段。
4. **触达层**：组装文本或卡片 → 调用飞书发送接口；定时任务走同一套组装函数。

**与现有代码的衔接点**

- **Token**：新建模块内封装 `get_token()`，内部直接调用现有 `4_写入飞书表格.py` 的 `get_tenant_access_token(app_id, app_secret)`，或调用 `8_发送飞书群聊.py` 的 `get_bot_tenant_access_token()`（二者需统一为**同一应用**的凭证，避免权限分裂）。
- **读多维表格**：对话里若需「和线上一致」的投放汇总，可复用 `7_图表展示_Lark.py` 的 `fetch_bitable_records` + `to_day_string` + 按 `day` 聚合逻辑（与 `load_chart_data_from_lark` 同源）。
- **写多维表格**：新数据仍用 `write_to_bitable(df, token)`；Agent 一般不直接写仓，只写「工单记录表」或已有 Base。

---

## 三、可复用函数清单（按文件）

### 3.1 `5_运行前四步main.py`

- **`load_module(filename, alias)`**：动态加载带数字/中文文件名的脚本；Agent 侧若要把「拉数脚本」当技能插件加载，可复用同一模式。
- **`run_step1`～`run_step4`**：编排范例；定时任务中「先跑管道再推送」可仿照顺序，改为调用你的 `query_metric` + `build_daily_card` + `send_*`。

### 3.2 `4_写入飞书表格.py`

- **`get_tenant_access_token(app_id, app_secret)`**：租户令牌，供多维表格写入、以及扩展为「发消息」「读记录」等开放 API。
- **`write_to_bitable(df, token)`**：批量写入记录；字段中的日期已按毫秒时间戳处理，Agent 推送结构化结果落地多维表格时可沿用。

### 3.3 `7_图表展示_Lark.py`

- **`load_feishu_writer_module()`**：加载 `4_写入飞书表格.py`，复用 `app_id`、`APP_TOKEN`、`TABLE_ID`。
- **`fetch_bitable_records(token, app_token, table_id)`**：分页拉全表；可做「对照查询」数据源之一。
- **`to_day_string(value)`**：飞书日期字段转 `YYYY-MM-DD`；任何从 Base 读出的日期列都应经此函数再聚合。
- **`load_chart_data_from_lark()`**：按日汇总 `installs`、`spend`、`clicks`；**定时卡片里「投放侧曲线/汇总」**可直接调用或抽成 `aggregate_ad_metrics(df)` 复用。

### 3.4 `8_发送飞书群聊.py`

- **`get_bot_tenant_access_token()`**：机器人应用换 token（需应用已开机器人能力）。
- **`build_chart_image(csv_file, chart_file)`**：从合并 CSV 按日聚合画图；定时推送可继续发图，或把聚合结果改为卡片里的数字。
- **`upload_image_to_feishu(token, image_path)`**：得 `image_key`；与发消息 API 组合使用。
- **`send_image_by_bot(webhook_url, image_key)`**：Webhook 发图；**扩展**：增加一个 `send_text_by_bot` / `send_card_by_bot`（新写函数，payload 结构见飞书机器人文档），用于纯文字与卡片。

### 3.5 `3_表格合并.py`

- **`get_latest_file(pattern)`**：取最新 `adjust_report_*.csv`、`fb_ad_data_*.csv`、`merged_adjust_fb_*.csv`；定时任务若仍基于本地文件，可复用。
- **`normalize_id(value)`**：创意/广告 ID 归一化；合并、去重键一致性问题可继续用。
- **合并与去重逻辑**：`merge` + `match_prio` 排序 + `drop_duplicates`；若 Agent 侧做「本地 CSV 对照」，勿重复造轮子，应 import 或抽成公共模块 `merge_adjust_fb(df_adjust, df_fb)`。

### 3.6 `1_Adjust拉取.py` / `2_FB拉取.py`

- **`init_api`、`get_adjust_campaign_data`、`process_data`、`save_to_csv`**（Adjust）。
- **`init_api`、`get_fb_campaign_data`、`save_to_csv`**（FB）。
- **用途**：定时任务「先更新投放数据再推卡片」时直接调用；与数仓无关的**投放明细**仍走此链路。

### 3.7 `10_FB监控.py`

- **`init_api`（FB）**、花费拉取与阈值判断思路；可与「超预算告警」类定时推送共用，向同一 Webhook 或群发卡片。

---

## 四、分场景实现要点（与功能清单一一对应）

### 4.1 场景 1：产品/策划问数（新增、留存等）

**目标**：自然语言 → 槽位 → `query_metric`（数仓），返回文本或卡片。

**复用**

- 飞书侧：**无直接复用数仓**；仅复用 `get_tenant_access_token` 用于后续「写反馈表」「发消息」。
- 编排：可参考 `5_运行前四步main.py` 的 `load_module` 模式，把「指标查询」做成独立模块 `metrics_service.py`（新建）。

**新建（必做）**

- **`query_metric(metric_id, dimensions, start, end)`**：内部映射到受控 SQL 或 HTTP；禁止拼接自由 SQL。
- **`parse_intent(text) -> {intent, slots}`**：规则 + LLM，输出标准化槽位。
- **Lark 入站**：新建路由接收事件，调用 `parse_intent` → `query_metric` → 格式化回复。

**与现有投放管道关系**

- 若问题为「投放花费/安装/点击」，可二选一：**数仓同口径**（推荐与报表一致）或 **临时读合并 CSV / Base**（复用 `load_chart_data_from_lark`），须在回复中标注数据来源。

### 4.2 场景 2：对报表数据有疑问、需解释

**目标**：文档解释 + 可选「同口径再算一遍」。

**复用**

- **RAG**：独立文档库，与现有脚本无代码复用；可选把飞书云文档导出为 Markdown 再入库。
- **对照查询（与投放表一致）**：`fetch_bitable_records` + `to_day_string` + 与 `load_chart_data_from_lark` 相同的 groupby 逻辑，对单指标、单时间段做对比。
- **数据新鲜度**：在配置或数仓元数据中维护 `last_partition`，回复模板固定字符串即可。

**新建**

- **`retrieve_docs(query)`**：向量检索 + 引用片段。
- **`explain_with_citations(answer, citations)`**：组装回复，要求带出处。

### 4.3 场景 3：具体拉数需求

**目标**：口语 → 结构化字段 → 工单或多维表格一行；复杂需求不自动跑数。

**复用**

- **`write_to_bitable`**：若工单落在 Base「拉数需求表」，把 LLM 抽取的字段写成一条 record。
- **`5_运行前四步main` 中的管道**：仅当需求命中**已有模板**（如指定维度的合并 CSV）时，在服务端显式调用 `run_step1`～`run_step3` 或单独封装的安全函数；**禁止**把用户自然语言直接拼进 SQL。

**新建**

- **`fill_ticket_template(nl_text) -> dict`**：结构化输出。
- **`classify_complexity(text) -> simple|template|need_human`**：分流。

---

## 五、定时推送卡片（技术落点）

**推荐实现**

1. **调度**：Windows 任务计划程序 / 服务器 cron / Airflow，定时执行 Python。
2. **数据**：优先调用 **`query_metric`（数仓）** 与业务约定一致；投放侧可继续先跑 `5_运行前四步main` 或子集再推。
3. **渲染**：用 Jinja2 或字符串模板生成飞书**交互卡片** JSON（标题、字段区、备注、跳转 BI 链接）。
4. **发送**：
   - **方案 A**：扩展 `8_发送飞书群聊.py`，新增基于同一 `tenant_access_token` 的 **open-apis 群消息**（需机器人在群内，权限与 Webhook 文档一致）。
   - **方案 B**：短期保留 Webhook，使用 `msg_type: post` 或富文本发「伪卡片」；后续再切卡片。

**复用**

- 聚合与作图：`build_chart_image` 仍可用于「一图一报」；与卡片并行不冲突。
- Token：`get_bot_tenant_access_token` 或 `get_tenant_access_token`，与对话共用应用。

---

## 六、对话问答（技术落点）

**推荐实现**

1. Lark 开放平台创建应用：开启**机器人**，订阅 **im.message.receive_v1**（或等价事件），配置请求网址到你的服务。
2. 服务内：验签 → 解析文本 → `parse_intent` → 分支调用 `query_metric` / `retrieve_docs` / `fill_ticket_template`。
3. 回复：`reply_message` API 发文本或卡片（与定时任务共用 `build_card_payload` 函数）。

**复用**

- Flask 已在 `7_图表展示_Lark.py` 使用；可增加路由 `/lark/events` 专接事件（注意与现有 `/` 仪表盘分离）。

---

## 七、工程化与风控（摘要）

- **同一指标、同一函数**：定时与对话共用 `query_metric` 或共用 `load_chart_data_from_lark`（仅投放域），避免口径分裂。
- **审计日志**：记录 `user_id、群_id、metric_id、SQL 模板编号、时间`，不落用户级明细到日志。
- **限流**：群聊入口对单用户 QPS 做简单限制。
- **密钥**：全部走环境变量或飞书应用后台，**不写死在 Agent 新代码中**（现有脚本中的硬编码建议在后续迭代中逐步迁出）。

---

## 八、建议的新增文件（命名供参考）

以下为逻辑拆分，便于与现有脚本并存：

- `metrics_service.py`：`query_metric`、数仓连接（与业务数仓对接）。
- `lark_agent_server.py`：事件回调、意图路由、调用上述服务。
- `card_templates.py`：日报/周报卡片 JSON 模板。
- `ticket_formatter.py`：拉数需求结构化工单字段。
- `rag_retriever.py`：指标词典与报表 FAQ 检索（可选）。

**公共抽取（可选重构）**

- 将 `7_图表展示_Lark.py` 中的 `fetch_bitable_records`、`to_day_string`、聚合逻辑抽到 `feishu_bitable_utils.py`，供仪表盘、Agent、定时任务共同 import，避免三处复制。

---

## 九、与《功能清单》的追踪关系

- **场景 1**：对应本文第四节 4.1、第五节、第六节；复用第三节 Token 与可选 Base 读数。
- **场景 2**：对应第四节 4.2；读 Base 用 3.3 所列函数。
- **场景 3**：对应第四节 4.3；写工单用 `write_to_bitable` 或工单 API。
- **定时 + 对话一致**：第二节数据层 + 第五节与第六节的发送函数共用。

---

**版本说明**：本文档随仓库内脚本函数名更新；若重命名脚本，请同步修改第三节中的文件名与函数名。
