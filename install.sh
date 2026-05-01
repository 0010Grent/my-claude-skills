#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO_DIR/skills"
SKILLS_DST="$HOME/.claude/skills"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "Installing my-claude-skills..."
echo ""

if [ ! -d "$SKILLS_SRC" ]; then
    echo -e "${RED}Error: skills/ directory not found in $REPO_DIR${NC}"
    exit 1
fi

mkdir -p "$SKILLS_DST"

installed=0
updated=0

for skill_dir in "$SKILLS_SRC"/*/; do
    skill_name="$(basename "$skill_dir")"
    src_file="$skill_dir/SKILL.md"
    dst_dir="$SKILLS_DST/$skill_name"
    dst_file="$dst_dir/SKILL.md"

    if [ ! -f "$src_file" ]; then
        continue
    fi

    if [ -f "$dst_file" ]; then
        if ! diff -q "$src_file" "$dst_file" > /dev/null 2>&1; then
            cp "$src_file" "$dst_file"
            echo -e "  ${YELLOW}updated${NC}  /$skill_name"
            ((updated++))
        else
            echo -e "  ${GREEN}ok${NC}       /$skill_name"
        fi
    else
        mkdir -p "$dst_dir"
        cp "$src_file" "$dst_file"
        echo -e "  ${GREEN}installed${NC} /$skill_name"
        ((installed++))
    fi
done

echo ""
echo -e "${GREEN}Done.${NC} $installed installed, $updated updated."
echo ""
echo "Restart Claude Code for the new skills to take effect."
echo ""
