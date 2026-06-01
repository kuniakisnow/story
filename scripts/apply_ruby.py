#!/usr/bin/env python3
"""
Apply ruby annotations to blog posts based on _data/ruby.yml.

Usage:
    python scripts/apply_ruby.py          # Apply annotations
    python scripts/apply_ruby.py --dry-run  # Show changes without modifying
"""

import re
import os
import sys
import argparse
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_DIR / "_data"
POSTS_DIR = REPO_DIR / "_posts"
RUBY_FILE = DATA_DIR / "ruby.yml"

RUBY_PATTERN = re.compile(
    r'<ruby>([^<]{1,100}?)<rp>《</rp><rt>[^<]{0,500}?</rt><rp>》</rp></ruby>'
)
INLINE_CODE = re.compile(r'`[^`\n]+`')
CODE_BLOCK = re.compile(r'```[\s\S]*?```')
HTML_TAG = re.compile(r'<[a-zA-Z][^>]*>')


def load_ruby_dict(ruby_file):
    entries = []
    current = {}
    with open(ruby_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip().lstrip('\ufeff')
            if line.startswith('- word:'):
                if current:
                    entries.append((current['word'], current['ruby']))
                val = line[len('- word: '):].strip().strip('"').strip("'").lstrip('\ufeff')
                current = {'word': val}
            elif line.startswith('  ruby:') and current:
                val = line[len('  ruby: '):].strip().strip('"').strip("'")
                current['ruby'] = val
        if current:
            entries.append((current['word'], current['ruby']))
    entries.sort(key=lambda x: (-len(x[0]), x[0]))
    return entries


def strip_ruby(text):
    return RUBY_PATTERN.sub(r'\1', text)


def protect_code_blocks(text):
    blocks = {}
    inline_blocks = {}

    def replace_block(m):
        idx = len(blocks)
        placeholder = f'%%%CODE_BLOCK_{idx}%%%'
        blocks[placeholder] = m.group(0)
        return placeholder

    text = CODE_BLOCK.sub(replace_block, text)

    def replace_inline(m):
        idx = len(inline_blocks)
        placeholder = f'%%%INLINE_CODE_{idx}%%%'
        inline_blocks[placeholder] = m.group(0)
        return placeholder

    text = INLINE_CODE.sub(replace_inline, text)
    return text, blocks, inline_blocks


def protect_html_tags(text):
    tags = {}

    def replace_tag(m):
        idx = len(tags)
        placeholder = f'%%%HTML_TAG_{idx}%%%'
        tags[placeholder] = m.group(0)
        return placeholder

    text = HTML_TAG.sub(replace_tag, text)
    return text, tags


def restore_placeholders(text, *placeholder_dicts):
    for d in placeholder_dicts:
        for placeholder, original in sorted(d.items(), key=lambda x: -len(x[0])):
            text = text.replace(placeholder, original)
    return text


def _char_class(c):
    """Return character class: 'kanji', 'hiragana', 'katakana', 'ascii_alnum', or 'other'."""
    cp = ord(c)
    if 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or 0xF900 <= cp <= 0xFAFF:
        return 'kanji'
    if 0x3040 <= cp <= 0x309F:
        return 'hiragana'
    if 0x30A0 <= cp <= 0x30FF or 0x2E80 <= cp <= 0x2FFF:
        return 'katakana'
    if c.isascii() and c.isalnum():
        return 'ascii_alnum'
    return 'other'


def _at_word_boundary(text, pos, length):
    """Check that match is at a word boundary (not inside a longer token)."""
    if pos > 0:
        prev = text[pos - 1]
        first = text[pos]
        if _char_class(prev) == _char_class(first) != 'other':
            return False
    end = pos + length
    if end < len(text):
        nxt = text[end]
        last = text[end - 1]
        if _char_class(last) == _char_class(nxt) != 'other':
            return False
    return True


def apply_ruby(text, ruby_entries):
    result = []
    i = 0
    replaced_positions = set()

    while i < len(text):
        if i in replaced_positions:
            i += 1
            continue

        matched = False
        for word, ruby in ruby_entries:
            if text[i:i + len(word)] == word:
                if word.startswith('%%%'):
                    i += 1
                    matched = True
                    break
                if '%%%' in text[i:i + len(word)]:
                    i += 1
                    matched = True
                    break
                if not _at_word_boundary(text, i, len(word)):
                    continue

                replacement = f'<ruby>{word}<rp>《</rp><rt>{ruby}</rt><rp>》</rp></ruby>'
                result.append(replacement)
                for j in range(i, i + len(word)):
                    replaced_positions.add(j)
                i += len(word)
                matched = True
                break

        if not matched:
            result.append(text[i])
            i += 1

    return ''.join(result)


def split_front_matter(content):
    # Handle possible BOM
    stripped = content.lstrip('\ufeff')
    bom_offset = len(content) - len(stripped)
    if stripped.startswith('---'):
        end_idx = stripped.find('---', 3) + bom_offset
        if end_idx != -1 and end_idx >= bom_offset:
            front_matter = content[:end_idx + 3]
            body = content[end_idx + 3:]
            return front_matter, body
    return '', content


def process_file(filepath, ruby_entries, dry_run=False):
    with open(filepath, 'r', encoding='utf-8') as f:
        original_content = f.read()

    content = original_content

    # Step 1: Split front matter
    front_matter, body = split_front_matter(content)

    # Step 2: Strip existing ruby from body (front matter never has ruby)
    body = strip_ruby(body)

    # Step 3: Protect code blocks and HTML tags in body
    body, code_blocks, inline_blocks = protect_code_blocks(body)
    body, html_tags = protect_html_tags(body)

    # Step 4: Apply ruby to body
    body = apply_ruby(body, ruby_entries)

    # Step 5: Restore protected elements
    body = restore_placeholders(body, code_blocks, inline_blocks, html_tags)

    # Step 6: Reassemble (preserve original formatting)
    new_content = front_matter + body if front_matter else body

    if new_content != original_content:
        if dry_run:
            print(f'  [MODIFIED] {filepath.name}')
            orig_lines = original_content.split('\n')
            new_lines = new_content.split('\n')
            for i, (ol, nl) in enumerate(zip(orig_lines, new_lines)):
                if ol != nl:
                    safe_ol = ol.encode('utf-8', errors='replace').decode('utf-8')
                    safe_nl = nl.encode('utf-8', errors='replace').decode('utf-8')
                    print(f'    L{i+1}: -{safe_ol}')
                    print(f'         +{safe_nl}')
            if len(orig_lines) != len(new_lines):
                print(f'    (line count changed: {len(orig_lines)} -> {len(new_lines)})')
            return False
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'  [UPDATED] {filepath.name}')
            return True
    else:
        print(f'  [UNCHANGED] {filepath.name}')
        return False


def main():
    parser = argparse.ArgumentParser(description='Apply ruby annotations to blog posts.')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without modifying files.')
    args = parser.parse_args()

    mode = 'DRY RUN' if args.dry_run else 'APPLY'
    print(f'=== Ruby Annotation Tool ({mode}) ===')

    if not RUBY_FILE.exists():
        print(f'[ERROR] Ruby file not found: {RUBY_FILE}')
        sys.exit(1)

    ruby_entries = load_ruby_dict(RUBY_FILE)
    print(f'Loaded {len(ruby_entries)} ruby entries')

    post_files = sorted(POSTS_DIR.glob('*.md'))
    print(f'Processing {len(post_files)} posts...')

    modified_count = 0
    for filepath in post_files:
        if process_file(filepath, ruby_entries, args.dry_run):
            modified_count += 1

    print(f'\nDone. {modified_count} files modified.')


if __name__ == '__main__':
    main()
