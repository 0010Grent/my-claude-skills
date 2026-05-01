# Claude Code 技能库索引与选型指南

> 本仓库共收录 180 个 skill（截至 2026-05-01）。其中 ECC 官方 132 个，社区 12 个，第三方/个人 27 个，自定义 3 个，医疗领域 4 个，个人贡献 1 个。

---

## 一、不知道怎么选？先用这四个专用技能

| 技能 | 触发场景 | 核心能力 |
|------|---------|---------|
| **find-skills** | "怎么做到 X？" / "有没有 XX 的 skill？" | 搜索公共技能市场 skills.sh，按安装量、来源可信度推荐，支持一键安装 |
| **ant-find-skills** | 蚂蚁内部场景找不到技能时 | 搜索蚂蚁内部 @antskill 市场，支持中英文搜索 |
| **skill-stocktake** | 清理、审计已有技能质量 | 快速扫描或全面清点，给出 Keep / Improve / Update / Retire / Merge  verdict |
| **workspace-surface-audit** | 刚进入新仓库 / 换了电脑 | 审计当前环境（技能、MCP、规则、代理），推荐最匹配的能力组合 |

**选择优先级：** 先问 `find-skills`（或 `ant-find-skills`）→ 再用需要的能力 → 定期用 `skill-stocktake` 清理。

---

## 二、技能分类速查

### 2.1 AI / Agent 工程（16 个）
面向 AI 系统建设、多智能体编排和成本优化。

- **agent-eval** — 多 Agent 横向评测（Claude Code / Aider / Codex 等）
- **agent-harness-construction** — 设计和优化 Agent 的行动空间、工具定义
- **agentic-engineering** — eval-first 执行、任务分解、成本感知模型路由
- **autonomous-agent-harness** — 将 Claude Code 变成完全自主的 Agent 系统（定时任务、持久记忆、任务队列）
- **autonomous-loops** — 自主循环架构（简单流水线到 RFC 多 Agent DAG）
- **continuous-agent-loop** — 带质量门、评测和恢复控制的持续 Agent 循环
- **continuous-learning** — 自动从会话提取可复用模式并保存为技能
- **continuous-learning-v2** — Instinct 学习系统（带置信度评分，v2.1 支持项目隔离）
- **cost-aware-llm-pipeline** — LLM API 成本优化（模型路由、预算追踪、缓存）
- **dmux-workflows** — 用 dmux 并行编排多 Agent 会话
- **enterprise-agent-ops** — 长生命周期 Agent 负载的运维、可观测性和安全边界
- **eval-harness** — Claude Code 会话的正式评测框架（EDD）
- **gan-style-harness** — GAN 式生成-评测 Agent 框架
- **ralphinho-rfc-pipeline** — RFC 驱动多 Agent DAG 执行（质量门、合并队列）
- **team-builder** — 交互式团队组建与并行调度
- **ai-regression-testing** — AI 辅助开发的回归测试策略

### 2.2 语言特定开发（42 个）
每个技术栈通常都有 `*-patterns`（编码规范）和 `*-testing`（测试策略），部分还有 `*-security`（安全）和 `*-verification`（发布前检查环）。

| 语言/框架 | 编码规范 | 测试 | 安全 | 验证 |
|-----------|---------|------|------|------|
| Python | python-patterns, pytorch-patterns | python-testing | — | — |
| Go | golang-patterns | golang-testing | — | — |
| Rust | rust-patterns | rust-testing | — | — |
| Kotlin | kotlin-patterns, kotlin-coroutines-flows, kotlin-exposed-patterns, kotlin-ktor-patterns, compose-multiplatform-patterns | kotlin-testing | — | — |
| Java / Spring Boot | java-coding-standards, springboot-patterns, jpa-patterns | springboot-tdd | springboot-security | springboot-verification |
| .NET | dotnet-patterns | csharp-testing | — | — |
| C++ | cpp-coding-standards | cpp-testing | — | — |
| PHP / Laravel | laravel-patterns, laravel-plugin-discovery | laravel-tdd | laravel-security | laravel-verification |
| Perl | perl-patterns | perl-testing | perl-security | — |
| Dart / Flutter | dart-flutter-patterns | flutter-dart-code-review | — | — |
| TypeScript / JS | coding-standards | — | — | — |
| Android | android-clean-architecture | — | — | — |

**使用方式：** 进入对应技术栈项目时，Claude Code 会自动加载相关 pattern 和 testing 技能（若已安装到项目级目录）。

### 2.3 Web 前端（9 个）
- **frontend-patterns** — React / Next.js / 状态管理 / 性能优化
- **nextjs-turbopack** — Next.js 16+ 与 Turbopack
- **nuxt4-patterns** — Nuxt 4 SSR 安全与性能
- **nestjs-patterns** — NestJS 后端架构
- **design-system** — 生成或审计设计系统
- **liquid-glass-design** — iOS 26 Liquid Glass 设计系统
- **swiftui-patterns** — SwiftUI 架构与状态管理
- **remotion-video-creation** — Remotion 视频创作最佳实践
- **frontend-slides** — HTML 演示文稿 / PPT 转换

### 2.4 后端 / DevOps / 数据库（8 个）
- **backend-patterns** — Node.js / Express / Next.js API 架构
- **api-design** — REST API 设计（分页、过滤、错误响应、限流）
- **deployment-patterns** — CI/CD、健康检查、回滚策略
- **docker-patterns** — Docker Compose、容器安全、网络、卷策略
- **database-migrations** — 零停机迁移（PostgreSQL / MySQL / Prisma / Drizzle 等）
- **postgres-patterns** — PostgreSQL 查询优化、索引、安全
- **clickhouse-io** — ClickHouse 分析型数据库
- **bun-runtime** — Bun 运行时替代 Node

### 2.5 测试 / TDD / 质量（11 个）
- **tdd** — 红-绿-重构 TDD 循环
- **tdd-workflow** — 强制 80%+ 覆盖率的 TDD 流程（单元/集成/E2E）
- **e2e-testing** — Playwright E2E 测试
- **browser-qa** — 浏览器自动化视觉/交互验证
- **benchmark** — 性能基线与回归检测
- **canary-watch** — 部署后 URL 回归监控
- **verification-loop** — Claude Code 会话综合验证系统
- **django-tdd** / **django-verification** — Django 专属
- **plankton-code-quality** — 保存时自动格式化/修复

### 2.6 安全（8 个）
- **security-review** — 通用安全审查清单（认证、输入处理、密钥、API）
- **security-scan** — 扫描 `.claude/` 配置漏洞
- **safety-guard** — 生产环境/自主 Agent 的破坏性操作防护
- **django-security** / **springboot-security** / **laravel-security** / **perl-security** — 框架专属
- **opensource-pipeline** — 开源发布前的脱敏与安全检查

### 2.7 内容 / 创作 / 媒体（11 个）
- **article-writing** — 长文写作（博客、教程、新闻稿）
- **brand-voice** — 从真实样本提取写作风格并复用
- **content-engine** — 跨平台内容系统（X / LinkedIn / TikTok / YouTube / Newsletter）
- **crosspost** — 多平台内容分发
- **x-api** — X/Twitter API 集成
- **fal-ai-media** — fal.ai 统一媒体生成（图/视频/音频）
- **video-editing** — AI 视频剪辑（FFmpeg / Remotion / Descript）
- **manim-video** — Manim 动画解释器
- **videodb** — 视频/音频的摄取、理解、编辑与生成
- **ui-demo** — Playwright 录制 WebM 演示视频
- **frontend-slides** — HTML 幻灯片

### 2.8 商业 / 运营 / 市场 / 人际（8 个）
- **market-research** — 市场调研、竞品分析、投融资情报
- **investor-materials** — 融资材料（Pitch Deck、Memo、财务模型）
- **investor-outreach** — 投资人冷启动邮件、跟进
- **lead-intelligence** — AI 线索评分与渠道触达
- **connections-optimizer** — X / LinkedIn 社交网络整理与增长
- **social-graph-ranker** — 社交图排名引擎（桥接发现、缺口分析）
- **customer-billing-ops** — Stripe 客户订阅/退款/流失处理
- **product-lens** — 产品诊断：验证"为什么"再做

### 2.9 诊断 / 调试 / 研究（7 个）
- **diagnose** — 系统化 bug 诊断循环（复现→最小化→假设→修复→回归）
- **click-path-audit** — 按钮全链路状态追踪（排查功能互抵的隐蔽 bug）
- **deep-research** — 多源深度研究（firecrawl + exa MCP）
- **exa-search** — Exa 神经网络搜索
- **search-first** — 编码前先搜索现有工具/库/模式
- **iterative-retrieval** — 渐进式上下文检索（解决子 Agent 上下文不足）
- **documentation-lookup** — 通过 Context7 MCP 获取最新文档

### 2.10 工作流 / 生产力 / 工程管理（14 个）
- **git-workflow** — 分支策略、合并 vs Rebase、冲突解决
- **commit** — 提交辅助
- **github-push** — 一键上传本地项目到 GitHub 私有仓库
- **to-issues** — 将计划拆分为 issue（tracer-bullet 切片）
- **to-prd** — 将对话上下文转为 PRD 并发布到 issue 跟踪器
- **triage** — issue 状态机分流
- **project-flow-ops** — GitHub 与 Linear 的执行流协调
- **architecture-decision-records** — 自动捕获架构决策为 ADR
- **codebase-onboarding** — 陌生仓库分析与快速上手
- **prompt-optimizer** — 提示词优化
- **strategic-compact** — 逻辑间隔手动压缩上下文
- **context-budget** — 上下文 token 消耗审计
- **nanoclaw-repl** — ECC 零依赖 REPL
- **data-scraper-agent** — GitHub Actions 数据抓取 Agent

### 2.11 医疗健康（4 个）
来源：Health1 Super Speciality Hospitals
- **healthcare-cdss-patterns** — 临床决策支持系统
- **healthcare-emr-patterns** — 电子病历系统
- **healthcare-eval-harness** — 患者安全评测
- **healthcare-phi-compliance** — 健康信息隐私合规矩

### 2.12 物流 / 供应链 / 质检（7 个）
- **customs-trade-compliance** — 海关贸易合规
- **carrier-relationship-management** — 承运商关系管理
- **inventory-demand-planning** — 库存需求规划
- **logistics-exception-management** — 物流异常管理
- **returns-reverse-logistics** — 退货逆向物流
- **production-scheduling** — 生产排程
- **quality-nonconformance** — 质量不合格处理

### 2.13 Ant 内部 / 定制化（7 个）
- **aistudio-connect-diagnosis** — AIStudio 直连诊断
- **dataphin** — Dataphin (MaxCompute/ODPS) 数据开发
- **wohu-knowledge-base** — 外部知识库获取
- **eve-oc-eval** / **eve-debugger** / **eve-auto-eval** — EVE 平台评测与调试
- **ant-find-skills** — 蚂蚁内部技能市场搜索

### 2.14 其他 / 通用 / 基础设施（15 个）
- **mcp-server-patterns** — 用 Node/TypeScript 构建 MCP 服务器
- **content-hash-cache-pattern** — SHA-256 内容哈希缓存
- **regex-vs-llm-structured-text** — 正则 vs LLM 的结构化文本解析决策框架
- **improve-codebase-architecture** — 基于 CONTEXT.md 和 ADR 寻找架构深化机会
- **rules-distill** — 从技能提取跨领域原则并转为规则
- **skill-comply** — 验证技能、规则、代理定义是否被实际遵循
- **repo-scan** — 跨技术栈源码资产审计
- **ck** — 项目级持久化记忆
- **claude-devfleet** — Claude DevFleet 多 Agent 编排
- **agent-payment-x402** — Agent 支付（x402 协议）
- **openclaw-persona-forge** — 人格锻造
- **token-budget-advisor** — Token 预算建议
- **write-a-skill** — 创建新技能的结构化指南
- **zoom-out** — 获取更高层级视角
- **blueprint** — 项目蓝图

### 2.15 自定义 / 个人（3 个）
- **CV-create** — 互联网大厂简历优化（STAR 法则，AI 产品/金融方向）
- **github-push** — 一键推送本地项目到 GitHub
- **llm-pipeline-scaffold** — LLM 批量流水线脚手架（断点续传、自动提示优化）

---

## 三、选型决策建议

### 场景映射表

| 你的问题 | 推荐技能 |
|---------|---------|
| "有没有做 XX 的 skill？" | **find-skills** / **ant-find-skills** |
| 刚进入一个新项目，完全陌生 | **codebase-onboarding** + **workspace-surface-audit** |
| 写代码前想确认最佳实践 | `*-patterns`（对应语言）+ **search-first** |
| 每次编码后觉得质量不稳 | **tdd-workflow** + **verification-loop** |
| 遇到了诡异 bug，函数都没错但整体错了 | **diagnose** + **click-path-audit** |
| 要发版前做最终检查 | `*-verification`（对应框架）+ **security-review** |
| 要做视频/演示/内容 | **ui-demo** / **frontend-slides** / **video-editing** / **fal-ai-media** |
| 想减少 AI 调用成本 | **cost-aware-llm-pipeline** + **context-budget** |
| 技能太多想清理 | **skill-stocktake** |
| 想写自己的 skill | **write-a-skill** |

### 技术栈速查

- **全栈 TS/JS Web：** frontend-patterns + backend-patterns + nextjs-turbopack + tdd-workflow + security-review
- **Python 数据/后端：** python-patterns + python-testing + postgres-patterns + api-design
- **Java 企业后端：** springboot-patterns + springboot-tdd + springboot-security + jpa-patterns
- **移动开发：** android-clean-architecture + dart-flutter-patterns / swiftui-patterns + compose-multiplatform-patterns
- **AI 应用开发：** claude-api + agentic-engineering + mcp-server-patterns + cost-aware-llm-pipeline
- **医疗系统：** healthcare-* 系列
- **物流系统：** customs-trade-compliance + logistics-exception-management + carrier-relationship-management

---

## 四、技能来源质量标准

| 来源 | 信任级别 | 说明 |
|------|---------|------|
| **ECC** | 高 | 官方维护，与 Claude Code 版本同步更新 |
| **community** | 中高 | 社区审核通过，有 Stars 门槛 |
| **custom** | 自评 | 你自己写的，质量取决于维护力度 |
| **third-party** | 需甄别 | 使用前检查最近更新时间、GitHub Stars、作者可信度 |
| **Health1** | 领域权威 | 医疗行业专用，由真实医院贡献 |

---

## 五、安装与同步

```bash
# 安装单个技能（公共市场）
npx skills add <owner/repo@skill> -g -y

# 安装蚂蚁内部技能
tnpm i -g @antskill/<skill-name>

# 更新所有技能
npx skills update

# 审计质量
/skill-stocktake          # 快速扫描
/skill-stocktake full     # 全面清点

# 项目级 skills（仅对当前项目生效）
npx skills add <owner/repo@skill> -y
```

### 跨设备同步建议

1. **技能元数据** — 将本仓库 `my-claude-skills` 通过 Git 同步，保留 `skills/` 和 `.skills-manifest.json`。
2. **个人规则** — 同步 `~/.claude/rules/` 和 `~/.claude/CLAUDE.md`。
3. **配置** — 同步 `~/.claude/settings.json`。
4. **记忆** — `~/.claude/memory/` 按需同步。

不要在仓库中提交包含密钥的 `.skills-manifest.json` 内容，它只记录安装元数据，不含敏感信息。
