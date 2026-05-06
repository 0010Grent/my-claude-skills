#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DST="$HOME/.claude/skills"
SKILLS_BAK="$HOME/.claude/.skills-backup"
AGENTS_SRC="$REPO_DIR/agents"
AGENTS_DST="$HOME/.claude/agents"
AGENTS_BAK="$HOME/.claude/.agents-backup"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "Installing my-claude-skills (symlink mode)..."
echo ""

# ─── Skills ───
mkdir -p "$SKILLS_DST"

installed=0
updated=0
skipped=0
replaced=0

for skill_dir in "$REPO_DIR"/*/; do
    skill_name="$(basename "$skill_dir")"
    src_file="$skill_dir/SKILL.md"

    # 只处理包含 SKILL.md 的目录
    if [ ! -f "$src_file" ]; then
        continue
    fi

    dst_dir="$SKILLS_DST/$skill_name"

    if [ -L "$dst_dir" ]; then
        # 已经是 symlink：检查指向是否正确
        current_target="$(readlink "$dst_dir")"
        if [ "$current_target" = "$skill_dir" ]; then
            echo -e "  ${GREEN}ok${NC}        /$skill_name"
            ((skipped++))
        else
            ln -sfn "$skill_dir" "$dst_dir"
            echo -e "  ${YELLOW}updated${NC}   /$skill_name"
            ((updated++))
        fi
    elif [ -d "$dst_dir" ]; then
        # 已存在目录（旧版 rsync 副本）：备份并替换为 symlink
        backup_dir="$SKILLS_BAK/$(basename "$dst_dir").$(date +%s)"
        mkdir -p "$SKILLS_BAK"
        mv "$dst_dir" "$backup_dir"
        ln -sfn "$skill_dir" "$dst_dir"
        echo -e "  ${YELLOW}replaced${NC}  /$skill_name (backup -> $(basename "$backup_dir"))"
        ((replaced++))
    else
        # 首次安装
        ln -sfn "$skill_dir" "$dst_dir"
        echo -e "  ${GREEN}installed${NC} /$skill_name"
        ((installed++))
    fi
done

echo ""
echo -e "Skills: ${GREEN}$installed${NC} installed, ${YELLOW}$updated${NC} updated, $replaced replaced, $skipped unchanged."

# ─── Agents ───
a_installed=0
a_updated=0
a_skipped=0
a_replaced=0

if [ -d "$AGENTS_SRC" ]; then
    mkdir -p "$AGENTS_DST"

    for agent_file in "$AGENTS_SRC"/*.md; do
        [ -f "$agent_file" ] || continue

        agent_name="$(basename "$agent_file")"
        dst_agent="$AGENTS_DST/$agent_name"

        if [ -L "$dst_agent" ]; then
            current_target="$(readlink "$dst_agent")"
            if [ "$current_target" = "$agent_file" ]; then
                echo -e "  ${GREEN}ok${NC}        agents/$agent_name"
                ((a_skipped++))
            else
                ln -sfn "$agent_file" "$dst_agent"
                echo -e "  ${YELLOW}updated${NC}   agents/$agent_name"
                ((a_updated++))
            fi
        elif [ -f "$dst_agent" ]; then
            backup_file="$AGENTS_BAK/$(basename "$dst_agent").$(date +%s)"
            mkdir -p "$AGENTS_BAK"
            mv "$dst_agent" "$backup_file"
            ln -sfn "$agent_file" "$dst_agent"
            echo -e "  ${YELLOW}replaced${NC}  agents/$agent_name (backup -> $(basename "$backup_file"))"
            ((a_replaced++))
        else
            ln -sfn "$agent_file" "$dst_agent"
            echo -e "  ${GREEN}installed${NC} agents/$agent_name"
            ((a_installed++))
        fi
    done
fi

echo ""
echo -e "Agents: ${GREEN}$a_installed${NC} installed, ${YELLOW}$a_updated${NC} updated, $a_replaced replaced, $a_skipped unchanged."
echo ""
echo "Done. All skills/agents are now symlinked."
echo "Any future edits in $REPO_DIR will reflect immediately in Claude Code."
echo ""
