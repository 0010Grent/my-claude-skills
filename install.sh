#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DST="$HOME/.claude/skills"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "Installing my-claude-skills..."
echo ""

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
echo -e "${GREEN}Done.${NC} $installed installed, $updated updated, $skipped unchanged."
echo ""
echo "Restart Claude Code for the new skills to take effect."
echo ""
