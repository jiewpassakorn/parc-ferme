# parc-ferme

Automated PR code reviews using Claude AI.

ดึง diff จาก GitHub PR ผ่าน `gh` CLI แล้วส่งให้ Claude วิเคราะห์ตาม review profile ที่เลือก

## Prerequisites

- **Python 3.10+**
- **[pipx](https://pipx.pypa.io/)** — สำหรับติดตั้ง CLI tools (`brew install pipx` หรือ `pip install pipx`)
- **[gh](https://cli.github.com/)** — GitHub CLI (ต้อง login แล้ว: `gh auth login`)
- **[claude](https://claude.ai/claude-code)** — Claude Code CLI

## Installation

```bash
# วิธีแนะนำ: ติดตั้งผ่าน pipx (ใช้ได้ทั่วระบบ)
pipx install git+https://github.com/jiewpassakorn/parc-ferme.git
```

<details>
<summary>วิธีอื่น (สำหรับ development)</summary>

```bash
git clone https://github.com/jiewpassakorn/parc-ferme.git
cd parc-ferme
make install

# หรือ editable mode สำหรับ dev
pipx install -e .
```

</details>

## Quick Start

```bash
# รีวิว PR #123 ด้วย default profile
parc-ferme 123

# ใช้ GitHub URL ก็ได้
parc-ferme https://github.com/owner/repo/pull/123
```

## Usage

```
parc-ferme [PR] [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `PR` | PR number (e.g. `123`) หรือ GitHub URL |

### Options

| Flag | Short | Description |
|------|-------|-------------|
| `--profile NAME` | `-p` | เลือก review profile (`default`/`security`/`performance`/`angular`) |
| `--comment` | `-c` | โพสต์ผลรีวิวเป็น PR comment บน GitHub |
| `--comment-mode MODE` | | `create` (สร้างใหม่) หรือ `update` (แก้อันล่าสุด) |
| `--repo OWNER/REPO` | `-R` | ระบุ repo (ถ้าไม่ได้อยู่ใน git directory ของ repo นั้น) |
| `--config PATH` | | ระบุ path ของ config file ตรงๆ |
| `--dry-run` | | แสดง prompt ที่จะส่งให้ Claude โดยไม่รันจริง |
| `--output FILE` | `-o` | บันทึกผลรีวิวลงไฟล์ |
| `--timeout SECONDS` | | กำหนด timeout สำหรับ Claude review (default: 300) |
| `--strict` | | Exit code 1 ถ้าพบ CRITICAL issues (สำหรับ CI/CD) |
| `--list-profiles` | | แสดง profiles ทั้งหมดที่ใช้ได้ |
| `--no-color` | | ปิดสีใน terminal output |
| `--verbose` | `-v` | แสดงข้อมูล debug เพิ่มเติม |
| `--version` | | แสดงเวอร์ชัน |

## Examples

```bash
# รีวิว PR #42 ด้วย security profile
parc-ferme 42 --profile security

# รีวิวแล้วโพสต์เป็น comment บน GitHub
parc-ferme 42 --comment

# รีวิวแล้วแก้ comment เดิม (ไม่สร้างใหม่)
parc-ferme 42 --comment --comment-mode update

# ดู prompt ก่อนรันจริง (ไม่ต้องมี claude CLI)
parc-ferme 42 --dry-run

# บันทึกผลรีวิวลงไฟล์
parc-ferme 42 --output review.md

# ใช้ใน CI/CD: fail ถ้ามี CRITICAL issues
parc-ferme 42 --strict

# ระบุ repo สำหรับ PR ของ repo อื่น
parc-ferme 42 -R owner/repo

# ดู profiles ที่มี
parc-ferme --list-profiles
```

## Review Profiles

| Profile | Focus |
|---------|-------|
| `default` | Bugs, security, breaking changes, code smells, typos |
| `security` | XSS, injection, secrets, CSRF, auth bypass, SSRF, prototype pollution |
| `performance` | Memory leaks, N+1 queries, bundle size, re-renders, algorithm complexity |
| `angular` | Angular patterns, RxJS, TypeScript, module federation, OnDestroy cleanup |

## Configuration

สร้างไฟล์ `.reviewrc.yml` ที่:
- **Project root** (หรือ git root) — config เฉพาะโปรเจกต์
- **`~/.config/parc-ferme/.reviewrc.yml`** — config ระดับ user

Project-level จะ override user-level ถ้ามี key ซ้ำกัน

### ตัวอย่าง .reviewrc.yml

```yaml
# Default profile เมื่อไม่ระบุ --profile
default_profile: angular

# Override Claude model (e.g., sonnet, opus, haiku)
# claude_model: sonnet

# Auto-comment settings
comment:
  enabled: false          # true = โพสต์ comment ทุกครั้งโดยไม่ต้องใส่ --comment
  mode: create            # "create" (สร้างใหม่) หรือ "update" (แก้อันล่าสุด)

# Custom profiles
profiles:
  # ต่อยอดจาก built-in profile
  my-angular:
    extends: angular
    extra_instructions: |
      This project uses Module Federation.
      Pay attention to shared module config and remote entry exports.

  # สร้าง profile ใหม่ทั้งหมด
  finiq:
    description: "FinIQ project-specific review"
    system_role: "senior code reviewer specializing in financial software"
    rules:
      - "Only flag REAL issues, not style preferences"
      - "Be concise, no filler, no praise"
      - "If no issues found, just say: LGTM"
    checks:
      - "Financial calculations: floating point precision, rounding errors"
      - "Stored procedures: incorrect parameter ordering, missing error handling"
      - "Security: XSS, injection, exposed secrets"
    output_format: "[SEVERITY] file:line — description"
```

### Config Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `default_profile` | string | `"default"` | Profile ที่ใช้เมื่อไม่ระบุ `--profile` |
| `claude_model` | string | `null` | Override model ของ Claude (e.g., `sonnet`, `opus`) |
| `review_timeout` | int | `300` | Timeout สำหรับ Claude review (วินาที) |
| `comment.enabled` | bool | `false` | โพสต์ comment อัตโนมัติทุกครั้ง |
| `comment.mode` | string | `"create"` | `"create"` หรือ `"update"` |
| `profiles` | object | `null` | Custom profiles (ดูตัวอย่างด้านบน) |

## Development

```bash
# Install with dev dependencies
make dev

# Run tests
make test

# List profiles
make profiles

# Clean build artifacts
make clean
```

## Limitations

- Diff ที่ใหญ่เกิน 100,000 ตัวอักษร จะถูกตัดอัตโนมัติ (review เฉพาะส่วนแรก)
- ต้อง login `gh` CLI ก่อนใช้งาน (`gh auth login`)
- ต้องมี `claude` CLI ติดตั้งอยู่ (ยกเว้น `--dry-run`)

## Disclaimer

- โปรเจกต์นี้**ไม่ได้มีส่วนเกี่ยวข้อง ไม่ได้รับการรับรอง หรือสนับสนุนจาก Anthropic, PBC**
- "Claude" เป็น trademark ของ Anthropic, PBC
- ผลรีวิวที่ได้เป็น **AI-generated suggestions** — ควรตรวจสอบก่อน merge เสมอ
- การใช้งาน Claude อยู่ภายใต้ [Anthropic's Acceptable Use Policy](https://www.anthropic.com/legal/aup)
