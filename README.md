#  AI Code Reviewer

An AI-powered pull request reviewer built with **Python**, the **OpenAI API**, **Docker**, and **GitHub Actions**.

Every time a pull request is opened or updated, the bot reads the code changes, reviews them for bugs, security problems, performance issues, and your team's own coding rules, then posts a structured review as a comment on the PR. It can also **block merging** when serious issues are found.



---
##  Features

- **Automatic reviews** on every new or updated pull request
- **Structured feedback**: summary, issues sorted by severity (🔴 Critical, 🟠 Warning, 🟡 Suggestion), suggested fixes, and a verdict
- **Custom coding rules**: write your team's rules in plain English, and violations are flagged with a 📏 tag
- **Merge gate**: fail the check (and block merging) on critical issues, warnings, or a "changes requested" verdict
- **Configurable per repository** with a simple `.ai-reviewer.yml` file
- **Cost control**: skips lock files and binary files, ignores paths you choose, and limits the diff size
- **One comment per PR**: the bot updates its previous review instead of spamming new comments
- **Secure by design**: settings are read from the base branch, so a PR can't change its own rules

---

##  How it works

```
Pull request opened or updated
        │
        ▼
GitHub Actions starts the reviewer
        │
        ├─ 1. Reads .ai-reviewer.yml from the base branch (or uses defaults)
        ├─ 2. Downloads the PR's code changes (diff)
        ├─ 3. Removes ignored and generated files, trims very large diffs
        ├─ 4. Sends the changes to OpenAI with a prompt built from your settings
        ├─ 5. Receives a structured JSON review (issues, severities, verdict)
        ├─ 6. Posts or updates the review comment on the PR
        └─ 7. Fails the check if the merge gate is triggered
```

---

##  Quick start (GitHub Actions)

### 1. Add your OpenAI API key

In your repository: **Settings → Secrets and variables → Actions → New repository secret**

- **Name:** `OPENAI_API_KEY`
- **Secret:** your OpenAI API key (only the key, with no quotes or spaces)

### 2. Make sure the workflow exists

The workflow lives in `.github/workflows/ai-review.yml`. It runs automatically when a pull request is opened, updated, or reopened.


### 3. Open a pull request

Within about a minute, the review appears as a comment on your PR. That's it! 🎉

> **Note:** Pull requests from **forks** don't receive repository secrets, so the reviewer can't run on them.

---

##  Settings (`.ai-reviewer.yml`)

Add a `.ai-reviewer.yml` file to the root of your repository to customize the reviewer.
**Every setting is optional.** Anything you leave out uses its default value.

> ⚠️ The settings are read from the **base branch** (usually `main`). Changes to the settings file only take effect **after they are merged**. This prevents a pull request from turning off its own rules.

### Full example

```yaml
review:
  focus: [bugs, security, performance, readability]
  custom_rules:
    - "Function and variable names must use snake_case"
    - "Every public function must have a docstring"
    - "Use the logging module instead of print() for logs"
  rule_severity: warning
  ignore_paths:
    - "docs/*"
    - "*.md"
  language: English
  tone: friendly

output:
  summary: true
  verdict: true
  severity_labels: true
  show_fixes: true

gate:
  block_on: critical
```

### `review`: what the AI looks for

| Setting | Values | Default | Description |
|---|---|---|---|
| `focus` | `bugs`, `security`, `performance`, `readability`, `tests`, `documentation` | `[bugs, security, performance, readability]` | Which areas the AI should check |
| `custom_rules` | list of text | none | Your team's coding rules in plain English. Every violation is reported as an issue with a 📏 tag |
| `rule_severity` | `critical`, `warning`, `suggestion` | `warning` | How serious a broken custom rule is |
| `ignore_paths` | list of patterns | none | Files or folders to skip. `*` matches anything, e.g. `docs/*`, `*.md`, `tests/fixtures/*` |
| `language` | any language name | `English` | Language of the review text, e.g. `Arabic`, `French` |
| `tone` | `friendly`, `strict`, `concise` | `friendly` | Writing style of the review |

### `output`: what the comment shows

| Setting | Values | Default | Description |
|---|---|---|---|
| `summary` | `true` / `false` | `true` | Show the summary of what the PR does |
| `verdict` | `true` / `false` | `true` | Show the final verdict (Approve / Approve with suggestions / Changes requested) |
| `severity_labels` | `true` / `false` | `true` | Show 🔴 🟠 🟡 labels on issues |
| `show_fixes` | `true` / `false` | `true` | Show a suggested fix for each issue |
| `comment_style` | `summary`, `inline`, `both` | `summary` | `summary`: one comment with all issues. `inline`: each issue is posted on its exact line, plus a short summary. `both`: the full summary and the line comments |
### `gate`: when to block merging

| Setting | Values | Default | Description |
|---|---|---|---|
| `block_on` | `never`, `critical`, `warning`, `changes_requested` | `never` | When the check should fail |

What each value means:

- **`never`**: only comment, never fail the check
- **`critical`**: fail if there is at least one 🔴 critical issue
- **`warning`**: fail if there is at least one 🔴 critical or 🟠 warning issue
- **`changes_requested`**: fail if the AI's verdict is "Changes requested"

> 💡 If a custom rule should **block merging**, set `rule_severity` to the same level as `block_on` (or higher). For example, `rule_severity: critical` with `block_on: critical`.

### Example setups

**Strict security reviewer that blocks merges:**
```yaml
review:
  focus: [security, bugs]
  tone: strict
gate:
  block_on: critical
```

**Short, comment-only reviews in Arabic:**
```yaml
review:
  language: Arabic
  tone: concise
output:
  summary: false
  show_fixes: false
gate:
  block_on: never
```

**Enforce team style rules:**
```yaml
review:
  custom_rules:
    - "Use type hints on all function parameters"
    - "No function longer than 40 lines"
  rule_severity: warning
gate:
  block_on: warning
```

If the settings file has a mistake (a typo in a setting name, an invalid value, or broken YAML), the reviewer stops and prints a clear error explaining what's wrong and which values are allowed.

---

##  Blocking merges

The reviewer can **fail the check**, but GitHub only **blocks the merge button** if you tell it to:

1. Repository → **Settings → Rules → Rulesets → New branch ruleset**
2. **Name:** `protect-main`, **Enforcement status:** Active
3. **Target branches:** Include default branch
4. Enable **Require status checks to pass** → **Add checks** → search for `review`
5. Click **Create**

> The `review` check only appears in the search after the workflow has run at least once.

When a merge is blocked, the comment shows a ⛔ banner. Fix the issues and push again; the bot reviews the new changes automatically.

---

##  Run it locally with Docker



### 1. Create a GitHub token

GitHub → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**

- **Repository access:** Only select repositories → choose your repo
- **Permissions:**
  - Contents: **Read-only**
  - Pull requests: **Read and write**
  - Issues: **Read and write**

### 2. Create your `.env` file

Copy the template:

```bash
cp .env.example .env        # Windows PowerShell: copy .env.example .env
```

Then fill it in:

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | Your OpenAI API key |
| `GITHUB_TOKEN` | ✅ | The token from step 1 |
| `GITHUB_REPOSITORY` | ✅ | `username/repo-name` |
| `PR_NUMBER` | ✅ (locally) | The pull request number to review |
| `OPENAI_MODEL` | | Model to use (default: `gpt-5.4-mini`) |
| `DRY_RUN` | | `true` prints the review in the terminal instead of posting it |
| `MAX_DIFF_CHARS` | | Maximum diff size sent to the AI (default: `60000`) |



### 3. Run

```bash
docker compose run --rm tests       # run unit tests + linter
docker compose run --rm reviewer    # run the reviewer
```



---





##  Exit codes

| Code | Meaning |
|---|---|
| `0` | Review finished successfully |
| `1` | Unexpected error (network, API, etc.) |
| `2` | Configuration error (missing variable or invalid settings file) |
| `3` | Merge blocked by the `gate` settings |
