#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DST="$HOME/.claude/skills"
AGENTS_SRC="$REPO_DIR/agents"
AGENTS_DST="$HOME/.claude/agents"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "Installing my-claude-skills..."
echo ""

# ─── Skills ───
mkdir -p "$SKILLS_DST"

installed=0
updated=0
skipped=0

for skill_dir in "$REPO_DIR"/*/; do
    skill_name="$(basename "$skill_dir")"
    src_file="$skill_dir/SKILL.md"

    # 只处理包含 SKILL.md 的目录
    if [ ! -f "$src_file" ]; then
        continue
    fi

    dst_dir="$SKILLS_DST/$skill_name"
    dst_skill="$dst_dir/SKILL.md"

    if [ -d "$dst_dir" ]; then
        # 已存在：比较 SKILL.md，有变化则同步整个目录
        if ! diff -q "$src_file" "$dst_skill" > /dev/null 2>&1; then
            rsync -a --delete \
                --exclude='CLAUDE.md' \
                --exclude='outputs/' \
                --exclude='__pycache__/' \
                --exclude='*.pyc' \
                "$skill_dir" "$dst_dir/"
            echo -e "  ${YELLOW}updated${NC}   /$skill_name"
            ((updated++))
        else
            echo -e "  ${GREEN}ok${NC}        /$skill_name"
            ((skipped++))
        fi
    else
        # 首次安装：同步整个目录（排除私有/生成文件）
        mkdir -p "$dst_dir"
        rsync -a \
            --exclude='CLAUDE.md' \
            --exclude='outputs/' \
            --exclude='__pycache__/' \
            --exclude='*.pyc' \
            "$skill_dir" "$dst_dir/"
        echo -e "  ${GREEN}installed${NC} /$skill_name"
        ((installed++))
    fi
done

echo ""
echo -e "Skills: ${GREEN}$installed${NC} installed, ${YELLOW}$updated${NC} updated, $skipped unchanged."

# ─── Agents ───
a_installed=0
a_updated=0
a_skipped=0

if [ -d "$AGENTS_SRC" ]; then
    mkdir -p "$AGENTS_DST"

    for agent_file in "$AGENTS_SRC"/*.md; do
        # 防止 glob 未匹配时返回原字符串
        [ -f "$agent_file" ] || continue

        agent_name="$(basename "$agent_file")"
        dst_agent="$AGENTS_DST/$agent_name"

        if [ -f "$dst_agent" ]; then
            if ! diff -q "$agent_file" "$dst_agent" > /dev/null 2>&1; then
                cp "$agent_file" "$dst_agent"
                echo -e "  ${YELLOW}updated${NC}   agents/$agent_name"
                ((a_updated++))
            else
                echo -e "  ${GREEN}ok${NC}        agents/$agent_name"
                ((a_skipped++))
            fi
        else
            cp "$agent_file" "$dst_agent"
            echo -e "  ${GREEN}installed${NC} agents/$agent_name"
            ((a_installed++))
        fi
    done
fi

echo ""
echo -e "Agents: ${GREEN}$a_installed${NC} installed, ${YELLOW}$a_updated${NC} updated, $a_skipped unchanged."
echo ""
echo "Restart Claude Code for the new skills and agents to take effect."
echo ""
