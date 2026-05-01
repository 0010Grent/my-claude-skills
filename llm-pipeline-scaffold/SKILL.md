---
name: llm-pipeline-scaffold
description: LLM 批量流水线脚手架，提炼自三个生产项目的设计模式，支持断点续传、长时间无人值守、可选自动提示词迭代优化。触发词：scaffold a pipeline
origin: custom
---

# LLM Pipeline Scaffold

> 提炼自 `label-pipeline`（AIStudio 容器长任务）、`finforge`（自动迭代优化）、`rubric自动生成器`（generate-verify 双验证）三个生产项目的设计模式。
>
> **适用场景**：以 LLM 为核心的批量内容生成/标注/评估流水线，需要断点续传、长时间无人值守运行，可选自动提示词迭代优化。

---

## 使用方式

用户说"新建一个流水线项目"或"scaffold a pipeline"时，按以下步骤执行：

1. 询问四个参数（见「§0 参数收集」）
2. 生成目录骨架（见「§1 目录结构」）
3. 写入各模块代码（见「§2–§6 模板」）
4. 写入启动脚本（见「§7 长任务运行」）
5. 写入项目级 CLAUDE.md（见「§8 CLAUDE.md 模板」）
6. 完成后对照「§9 复用检查清单」

---

## §0 参数收集

启动前询问用户：

| 参数 | 选项 | 影响 |
|------|------|------|
| 运行环境 | `local-conda` / `aistudio-container` | 虚拟环境方式、init.sh 是否生成、tmux TMOUT 检查 |
| 流水线类型 | `gen-verify`（生成+验证）/ `label-filter`（标注+过滤）/ `custom` | 阶段数量和命名 |
| 是否启用自动迭代优化 | `yes` / `no` | 是否生成 `optimizer/` 目录 |
| LLM Provider | `openai-compat`（含 Gemini/matrixllm 代理）/ `anthropic` | client 初始化代码 |

---

## §1 目录结构规范

```
{project}/
├── main.py                   # 统一入口：argparse + asyncio.run(main())
├── config.py                 # dotenv 加载，所有常量集中于此
├── .env                      # 实际密钥（gitignore）
├── .env.example              # 密钥模板（提交仓库）
├── requirements.txt
├── start_pipeline.sh         # tmux + nohup 守护启动脚本
├── prompts/
│   ├── gen_system.txt
│   ├── gen_user.txt
│   ├── verify_system.txt     # 声明"不了解生成背景"，保证验证独立性
│   └── verify_user.txt
├── core/
│   ├── checkpoint.py         # CheckpointManager（JSONL追加）
│   ├── llm_client.py         # AsyncOpenAI + 重试 + 5级JSON容错
│   ├── models.py             # InputRow / OutputRow dataclass
│   └── pipeline.py           # 阶段调度 + 哨兵文件完整性检测
├── optimizer/                # 仅 --with-optimizer 时生成
│   ├── evaluator.py          # 批次评估 → EvalReport
│   ├── prompt_optimizer.py   # 置信度过滤 + 自动写入 + 回滚
│   └── structural_rows.json  # 结构性失败行索引（初始为 []）
└── data/
    └── {run_name}/
        ├── raw/              # 输入文件备份（只读）
        ├── processed/        # 中间产物 + checkpoint.jsonl
        ├── output/           # 最终结果
        └── logs/             # pipeline.log / error_patterns.jsonl / changelog.jsonl
```

**run_name 命名规范**：`{YYYYMMDD}_{dataset_id}`，如 `20260415_q1000`。

---

## §2 config.py 模板

```python
# config.py
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# LLM
API_KEY      = os.environ["API_KEY"]
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_A      = os.getenv("MODEL_A", "gpt-4o")          # 生成模型（高温）
MODEL_B      = os.getenv("MODEL_B", "gpt-4o-mini")     # 验证/评估模型（低温）

# 并发与重试
CONCURRENCY = int(os.getenv("CONCURRENCY", "5"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# 目录
DATA_DIR    = Path(__file__).parent / "data"
PROMPTS_DIR = Path(__file__).parent / "prompts"
```

**.env.example**：
```bash
API_KEY=your-api-key-here
API_BASE_URL=https://api.openai.com/v1
MODEL_A=gpt-4o
MODEL_B=gpt-4o-mini
CONCURRENCY=5
MAX_RETRIES=3
```

---

## §3 core/checkpoint.py 模板

JSONL 追加式断点续传。每项任务完成后**立即写磁盘**，崩溃最多丢失当前批次，重启自动跳过已完成项。

```python
# core/checkpoint.py
import json
from pathlib import Path


class CheckpointManager:
    def __init__(self, path: Path):
        self.path = path
        self._done: dict[int, dict] = self._load()

    def _load(self) -> dict[int, dict]:
        if not self.path.exists():
            return {}
        done = {}
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
                if rec.get("status") in ("passed", "failed", "skipped"):
                    done[rec["index"]] = rec
            except json.JSONDecodeError:
                continue  # 单行损坏不影响其他行
        return done

    def is_done(self, index: int) -> bool:
        return index in self._done

    def get(self, index: int) -> dict:
        return self._done.get(index, {})

    def mark(self, index: int, status: str, **extra):
        """完成后立即追加，不等待批次结束。"""
        entry = {"index": index, "status": status, **extra}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._done[index] = entry

    def done_count(self) -> int:
        return len(self._done)
```

---

## §4 core/llm_client.py 模板

包含：信号量并发控制、tenacity 重试、5 级容错 JSON 解析、错误追加日志。

```python
# core/llm_client.py
import asyncio
import json
import logging
import re
import time
from pathlib import Path

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)
_error_log: Path | None = None


def set_error_log(path: Path):
    global _error_log
    _error_log = path


def _log_error(error_type: str, msg: str, context: dict | None = None):
    if not _error_log:
        return
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "error_type": error_type,
        "error_msg": msg,
        "context": context or {},
    }
    with open(_error_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def call_llm(
    client: AsyncOpenAI,
    model: str,
    system: str,
    user: str,
    temperature: float = 0.7,
    row_index: int | None = None,
) -> str | None:
    """调用 LLM，返回原始文本；截断输出直接丢弃。"""
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=temperature,
        )
        choice = resp.choices[0]
        if choice.finish_reason == "length":
            _log_error("truncated_output", "finish_reason=length", {"row": row_index})
            logger.warning("row %s: 输出被截断（finish_reason=length），丢弃", row_index)
            return None
        return choice.message.content
    except Exception as e:
        _log_error("api_error", str(e), {"row": row_index, "model": model})
        raise


def parse_json_tolerant(raw: str) -> dict:
    """5 级容错 JSON 解析，覆盖 LLM 常见格式问题。"""
    # 1. 去除 markdown 代码块后直接解析
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 2. 提取最外层 { } 区间
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    # 3. 补全截断括号（用栈追踪嵌套深度）
    repaired = _repair_truncated_json(cleaned)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # 4. 平坦补全（兜底）
    attempt = cleaned + "}" * max(0, cleaned.count("{") - cleaned.count("}"))
    try:
        return json.loads(attempt)
    except json.JSONDecodeError:
        pass

    # 5. 返回空字典，让调用方降级处理
    _log_error("json_parse_error", f"5 级容错均失败: {raw[:200]}", {})
    return {}


def _repair_truncated_json(s: str) -> str:
    """用栈追踪括号嵌套，按正确顺序补全缺失的关闭符。"""
    stack = []
    in_string = False
    escape_next = False
    pairs = {"{": "}", "[": "]"}
    closes = set(pairs.values())

    for ch in s:
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in pairs:
            stack.append(pairs[ch])
        elif ch in closes and stack and stack[-1] == ch:
            stack.pop()

    return s + "".join(reversed(stack))
```

---

## §5 core/pipeline.py 模板（多段串行 + 哨兵文件）

```python
# core/pipeline.py
import asyncio
import json
import logging
from pathlib import Path

from openai import AsyncOpenAI
from config import CONCURRENCY
from core.checkpoint import CheckpointManager
from core.models import InputRow, OutputRow

logger = logging.getLogger(__name__)


def sentinel_exists(round_dir: Path) -> bool:
    """哨兵文件存在 = 该轮次完整结束。"""
    return (round_dir / "eval_report.json").exists()


def next_round_number(output_base: Path) -> int:
    """返回下一个可用轮次编号；未完成的轮次（缺哨兵文件）复用其编号。"""
    n = 1
    while True:
        rd = output_base / f"round_{n}"
        if not rd.exists() or not sentinel_exists(rd):
            return n
        n += 1


async def run_batch(
    rows: list[InputRow],
    process_fn,          # async (row, ...) -> OutputRow | None
    checkpoint: CheckpointManager,
    **kwargs,
) -> list[OutputRow]:
    sem = asyncio.Semaphore(CONCURRENCY)
    total = len(rows)
    counter = {"done": 0}

    async def process_one(row: InputRow) -> OutputRow | None:
        async with sem:
            result = await process_fn(row, checkpoint=checkpoint, **kwargs)
        counter["done"] += 1
        done = counter["done"]
        if done % 20 == 0 or done == total:
            logger.info("进度：%d / %d (%.1f%%)", done, total, 100 * done / total)
        return result

    results = await asyncio.gather(*[process_one(r) for r in rows])
    return [r for r in results if r is not None]
```

---

## §6 提示词角色分离规范

验证者 system prompt **必须**包含独立声明，防止确认偏误：

```
# verify_system.txt
你是独立审核专家，对内容的生成背景和出题意图一无所知。
你只根据内容本身进行质量判断，不为生成者的意图辩护。
评估时严格按照以下维度逐一判断：
[维度列表]
```

生成者与验证者配置：

| 角色 | 温度 | 说明 |
|------|------|------|
| 生成者（MODEL_A） | 0.7+ | 鼓励多样化 |
| 验证者（MODEL_B） | 0.2  | 稳定严格判断 |
| 评估者（MODEL_B） | 0.3  | 批次级分析 |

---

## §7 长任务运行

### 7A. start_pipeline.sh（通用模板）

```bash
#!/usr/bin/env bash
# 用法：bash start_pipeline.sh <run_name> [额外参数]
#
# local-conda 模式：直接用 conda 激活的 python
# aistudio-container 模式：先 source init.sh，再启动

set -euo pipefail

RUN_NAME="${1:?用法: $0 <run_name>}"
shift
EXTRA_ARGS="$*"
SESSION="pipeline_${RUN_NAME}"
LOG_DIR="data/${RUN_NAME}/logs"

mkdir -p "$LOG_DIR"

# ── AIStudio 容器模式：取消注释下面两行 ──
# source /ossfs/workspace/.persist/init.sh
# PYTHON=".venv/bin/python"

# ── Local 模式 ──
PYTHON="python"

echo "[start] 检查 tmux..."
if ! command -v tmux &>/dev/null; then
    echo "[warn] tmux 未安装，降级为 nohup"
    nohup $PYTHON main.py --run-name "$RUN_NAME" $EXTRA_ARGS \
        > "$LOG_DIR/pipeline.log" 2>&1 &
    echo $! > "$LOG_DIR/run.pid"
    echo "[ok] 后台启动 PID=$(cat $LOG_DIR/run.pid)"
    exit 0
fi

# 检查 TMOUT（AIStudio 容器常见坑）
if [ -n "${TMOUT:-}" ] && [ "$TMOUT" -gt 0 ]; then
    echo "[warn] TMOUT=$TMOUT，会话可能超时自动退出。建议在 ~/.bashrc 中设置 TMOUT=0"
fi

# 创建或复用 tmux 会话
if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "[warn] 会话 $SESSION 已存在，直接 attach"
else
    tmux new-session -d -s "$SESSION" \
        "$PYTHON main.py --run-name $RUN_NAME $EXTRA_ARGS \
         2>&1 | tee $LOG_DIR/pipeline.log; \
         echo '[done] 流水线结束，按任意键退出'; read"
    echo "[ok] tmux 会话 $SESSION 已创建"
fi

echo "查看日志：tail -f $LOG_DIR/pipeline.log"
echo "进入会话：tmux attach -t $SESSION"
echo "脱离会话：Ctrl+b 然后 d"
```

### 7B. AIStudio 容器专用：init.sh

```bash
#!/usr/bin/env bash
# /ossfs/workspace/.persist/init.sh
# 每次容器重启后执行：激活虚拟环境 + 进入项目目录

PROJECT_DIR="/ossfs/workspace/{project_name}"
VENV_DIR="/ossfs/workspace/.persist/venv"

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 进入项目目录
cd "$PROJECT_DIR"

# 清除超时设置（防止 tmux 会话被 TMOUT 杀死）
unset TMOUT

echo "[init] 环境已激活：$(python --version)"
echo "[init] 当前目录：$(pwd)"
```

虚拟环境符号链接（创建一次，重启后无需重建）：

```bash
# 在容器内执行一次：
python -m venv /ossfs/workspace/.persist/venv
ln -s /ossfs/workspace/.persist/venv {project_dir}/.venv
pip install -r requirements.txt
```

### 7C. 长任务操作速查

```bash
# 查看日志（实时）
tail -f data/{run_name}/logs/pipeline.log

# 重新进入 tmux 会话
tmux attach -t pipeline_{run_name}

# 检查进程是否存活
ps aux | grep "main.py"

# 统计错误分布
python -c "
import json, collections
errs = [json.loads(l) for l in open('data/{run_name}/logs/error_patterns.jsonl')]
print(collections.Counter(e['error_type'] for e in errs).most_common())
"
```

---

## §8 自动迭代优化模块（可选）

仅当用户需要多轮自动提示词优化时生成 `optimizer/` 目录。

### 核心三层闭环

```
本轮结果 → [评估 LLM] → EvalReport（fail_groups + row_hints + suggestions）
                │
                ▼
        extract_suggestions()
                │
           置信度评分（见下方公式）
          ≥ 阈值（默认 0.55）？
         /         \
       是             否
       │               │
  备份 → 写入      挂起到 pending_suggestions.json
  changelog        （可人工确认）
       │
       ▼
  下轮提示词生效 → 通过率对比上轮
                        │
                   下降 > 5%？
                        │
                     rollback()
                  从备份恢复提示词
```

### 失败类型三分法

| 类型 | 含义 | 处置 |
|------|------|------|
| `structural` | 输入数据本身无法满足要求 | 持久化到 `structural_rows.json`，跨轮跳过 |
| `entity` | 特定实体不满足，换实体可解决 | 下轮换参数重试，不改提示词 |
| `prompt` | 提示词措辞导致 | 进入置信度评分 → 自动写入 |

### 置信度评分公式

```python
def confidence(suggestion: dict, total: int, already_modified: set) -> float:
    fail_count = suggestion["fail_count"]
    cur = suggestion.get("current_text", "")
    sug = suggestion.get("suggested_text", "")

    coverage = min(fail_count / max(total * 0.3, 1), 1.0)
    text_precision = 1.0 if len(cur) <= 200 else max(0.0, 1.0 - (len(cur) - 200) / 800)
    cur_chars = set(cur)
    sug_chars = set(sug)
    union = cur_chars | sug_chars
    jaccard = len(cur_chars & sug_chars) / len(union) if union else 0
    conservatism = 1.0 if 0.3 <= jaccard <= 0.7 else max(0.0, 1.0 - abs(jaccard - 0.5) * 2)

    score = 0.5 * coverage + 0.3 * text_precision + 0.2 * conservatism

    if not cur:
        score *= 0.75                           # 纯追加模式，风险高
    if suggestion["file"] in already_modified:
        score *= 0.50                           # 同轮已改过该文件

    return round(score, 4)
```

### per-row hint 递进升级

```python
def build_retry_hint(idx: int, hint_state: dict, fail_reason: str) -> str:
    state = hint_state.get(str(idx))
    if not state:
        return f"上一轮验证失败，原因：{fail_reason}。请换角度重新生成。"
    n = state["rounds_failed"]
    hint = state["hint"]
    prefix = "【强制切换】" if n >= 3 else ""
    return (
        f"上一轮失败（已连续 {n} 轮）。"
        f"行动指令：{prefix}{hint}。"
        f"请严格按此指令重新生成，不得保留原有方向。"
    )
```

---

## §9 项目级 CLAUDE.md 模板

在新项目根目录写入（根据实际情况填充占位符）：

```markdown
# CLAUDE.md

## 运行环境

<!-- 填写：local-conda / aistudio-container -->

```bash
# local-conda
conda activate {env_name}
cd {project_dir}

# aistudio-container（重启后）
source /ossfs/workspace/.persist/init.sh
```

## 常用命令

```bash
# 正式运行
python main.py --run-name {YYYYMMDD}_{dataset}

# 后台长任务
bash start_pipeline.sh {run_name}

# 冒烟测试
python main.py --dry-run --limit 3

# 断点续传（自动检测，重启直接运行即可）
python main.py --run-name {existing_run_name}

# 查看日志
tail -f data/{run_name}/logs/pipeline.log

# 查看错误分布
python -c "import json,collections; print(collections.Counter(json.loads(l)['error_type'] for l in open('data/{run_name}/logs/error_patterns.jsonl')).most_common())"
```

## 环境变量（.env）

| 变量 | 说明 |
|------|------|
| `API_KEY` | API 密钥 |
| `API_BASE_URL` | LLM endpoint |
| `MODEL_A` | 生成模型 |
| `MODEL_B` | 验证/评估模型 |
| `CONCURRENCY` | 并发数（默认 5） |
| `MAX_RETRIES` | 重试次数（默认 3） |

## 架构

```
main.py → core/pipeline.py → [stage_generate → stage_verify → stage_evaluate]
                                    ↑               ↑
                               prompts/gen_*   prompts/verify_*
```

## 数据目录

`data/{run_name}/raw/`：输入备份（只读）
`data/{run_name}/processed/checkpoint.jsonl`：断点文件
`data/{run_name}/output/`：最终结果
`data/{run_name}/logs/`：日志 + 错误记录
```

---

## §10 复用检查清单

在新项目开始编码前逐项确认：

### 流水线结构
- [ ] 各阶段职责单一，输入/输出类型通过 dataclass 明确
- [ ] 生成者（MODEL_A）与验证者（MODEL_B）使用**不同模型**
- [ ] verify_system.txt 包含独立声明（"不了解生成背景"）
- [ ] 评估阶段与验证阶段分离：验证是逐行判断，评估是批次分析

### 持久化与断点续传
- [ ] 结果文件使用 JSONL **追加写入**，不批量缓存后写入
- [ ] 检查点在任务完成后**立即**写入，不等待批次结束
- [ ] 使用**哨兵文件**（`eval_report.json`）标记轮次/批次完整性
- [ ] 重启时读取已完成集合，自动跳过已处理项

### 稳健性
- [ ] JSON 解析有 5 级容错，`finish_reason=length` 时直接丢弃不解析
- [ ] 信号量控制并发，并发数从 `.env` 读取
- [ ] tenacity 重试包装 LLM 调用（至少 3 次，指数退避）
- [ ] 错误追加到 `error_patterns.jsonl`，不打印到终端后丢失

### 长任务保护
- [ ] 使用 tmux 或 nohup，**不依赖默认终端**运行长任务
- [ ] AIStudio 容器：检查并 `unset TMOUT`，避免会话被自动杀死
- [ ] `.venv` 符号链接到 `/ossfs/` 持久化目录（AIStudio 容器模式）
- [ ] 日志输出重定向到文件，不依赖终端显示

### 自动迭代（启用时）
- [ ] 写入建议前校验 `current_text` 在目标文件中真实存在
- [ ] 写入前备份提示词到 `workspace/prompt_backups/round_N/`
- [ ] 通过率下降 > 5% 时自动回滚并记录 changelog
- [ ] `structural` 类失败持久化隔离，不参与后续轮次
- [ ] per-row hint 随失败轮次递进升级（3 轮失败后前缀「强制切换」）
- [ ] 评估降级时（`fail_groups=[]`）不触发优化，记录 `[评估降级]` 标志
