# prompt-regression-lab

`prompt-regression-lab` 是一个面向提示词工程、工作流编排和本地模型接入项目的离线回归测试 CLI。它读取 YAML 或 JSON 测试集，渲染变量，执行 golden 输出比对和规则断言，生成 Markdown/JSON 报告，并用退出码作为 CI 质量门。

项目目标不是“跑一个 demo”，而是让团队可以把 prompt 评测像单元测试一样纳入日常工程流程，尤其适合：

- 对提示模板、系统提示、后处理逻辑做回归保护
- 对本地推理输出、缓存响应、历史基线结果做稳定性检查
- 在 CI 中阻止明显退化合入主分支

## 特性

- 支持 YAML 与 JSON 测试集
- 支持 `{{ variable }}` 变量渲染，含环境变量回退
- 支持 golden 输出比对
- 支持规则断言：
  - `contains`
  - `regex`
  - `json-path-lite`
  - `numeric tolerance`
- 支持 Markdown 和 JSON 报告
- 支持 JUnit XML 报告，便于 GitHub Actions、GitLab CI、Jenkins 等系统展示失败用例
- 支持 `--fail-on-missing-golden`、`--max-failures` 等 CI 质量门参数
- 仅使用 Python 标准库，无外部运行时依赖

## 安装

要求 Python 3.10+

```bash
python -m pip install -e .
```

安装后可使用：

```bash
prompt-regression-lab --help
prlab --help
python -m prompt_regression_lab --help
```

## 快速开始

### 1. 准备测试集

示例文件见 [examples/sample-suite.yaml](examples/sample-suite.yaml)。

```yaml
suite: marketing-regressions
defaults:
  vars:
    brand: Orbit
    audience: developers
cases:
  - id: short-tagline
    prompt: "Write a short tagline for {{ brand }} targeting {{ audience }}."
    actual: "Orbit helps developers ship reliable prompts."
    golden: "Orbit helps developers ship reliable prompts."
    assertions:
      - type: contains
        value: "developers"
      - type: regex
        pattern: "Orbit\\s+helps"
```

### 2. 运行测试

```bash
prlab run examples/sample-suite.yaml --format markdown --output reports/sample-report.md
```

如果所有用例通过，命令退出码为 `0`；若存在失败则退出码为 `1`。这让它可以直接接入 CI。

### 3. 生成双格式报告

```bash
prlab run examples/sample-suite.yaml ^
  --format both ^
  --output reports/sample-report.md ^
  --json-output reports/sample-report.json ^
  --junit-output reports/sample-report.junit.xml
```

## 测试集格式

顶层字段：

- `suite`: 测试集名称
- `defaults.vars`: 默认变量
- `cases`: 用例数组

每个 case 支持字段：

- `id`: 必填，用例唯一标识
- `description`: 可选说明
- `vars`: 当前用例变量，会覆盖默认变量
- `prompt`: 可选，渲染后的 prompt 会出现在报告中
- `actual`: 必填，待评测输出
- `golden`: 可选，基线输出
- `assertions`: 可选，断言数组

`actual`、`golden`、`prompt` 都支持 `{{ name }}` 变量模板。变量优先级：

1. `case.vars`
2. `defaults.vars`
3. 环境变量

## 断言说明

### contains

```yaml
- type: contains
  value: "expected phrase"
  ignore_case: true
```

### regex

```yaml
- type: regex
  pattern: '"status"\\s*:\\s*"ok"'
```

### json-path-lite

适用于 JSON 文本输出。支持轻量路径，如：

- `user.name`
- `items[0].score`

```yaml
- type: json-path-lite
  path: "items[0].score"
  equals: 0.99
```

### numeric tolerance

适用于从文本中抽取数字后进行容差判断。

```yaml
- type: numeric_tolerance
  expected: 0.91
  tolerance: 0.02
```

或指定正则提取目标数字：

```yaml
- type: numeric_tolerance
  expected: 42
  tolerance: 0
  pattern: "score:\\s*([0-9.]+)"
```

## CLI 用法

```bash
prlab run SUITE_PATH [options]
```

常用参数：

- `--format {markdown,json,both}`: 输出格式
- `--output PATH`: Markdown 报告路径
- `--json-output PATH`: JSON 报告路径
- `--junit-output PATH`: JUnit XML 报告路径
- `--fail-on-missing-golden`: 遇到缺失 golden 直接失败
- `--max-failures N`: 失败达到 N 后提前停止
- `--strict`: 等价于开启严格质量门
- `--version`: 查看版本

### 退出码

- `0`: 全部通过
- `1`: 有测试失败或断言失败
- `2`: 输入文件、格式或参数错误

## 在 CI 中使用

仓库已包含 GitHub Actions 配置 [`.github/workflows/ci.yml`](.github/workflows/ci.yml)。

典型步骤：

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
prlab run examples/sample-suite.yaml --strict
```

你也可以在自己的 prompt 项目中把测试集放进 `prompts/tests/`，然后在 CI 中执行：

```bash
prlab run prompts/tests/regressions.yaml \
  --format both \
  --output artifacts/regression.md \
  --json-output artifacts/regression.json \
  --junit-output artifacts/regression.junit.xml
```

## 设计边界与限制

- 本工具不调用任何外部 AI API，也不负责生成模型输出
- 它假设 `actual` 输出已经由你的本地流程、缓存结果或上游作业准备好
- YAML 解析器是内置的轻量子集实现，适用于常见映射/列表/标量结构；若测试数据包含复杂 YAML 特性，建议使用 JSON
- `json-path-lite` 只支持点路径和数组索引，不支持完整 JSONPath 语法
- `numeric_tolerance` 默认从文本中提取第一个数字

## 报告输出

- Markdown：面向 reviewer，包含每个 case 的 prompt、actual、golden、assertions 和 errors。
- JSON：面向脚本、dashboard 或后续 agent 分析。
- JUnit XML：面向 CI 测试面板；每个 prompt case 映射为一个 `<testcase>`，失败 case 会写入 `<failure>` 和 `<system-out>`。

## 开发与测试

运行：

```bash
python -m unittest discover -s tests -v
```

本项目内置了 12+ 个单元测试，覆盖：

- CLI 行为
- 变量渲染
- YAML/JSON 载入
- 断言逻辑
- 报告输出
- 错误输入

## 项目结构

```text
src/prompt_regression_lab/
  cli.py
  loader.py
  render.py
  assertions.py
  runner.py
  report.py
tests/
examples/
.github/workflows/ci.yml
```

## 贡献

欢迎提交 issue 和 PR。开始前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

本项目使用 [MIT License](LICENSE)。

---

## English

`prompt-regression-lab` is an offline regression testing CLI for prompt-centric projects. It loads YAML or JSON suites, renders variables, compares golden outputs, evaluates rule-based assertions, emits Markdown/JSON reports, and returns CI-friendly exit codes.

### Why this project exists

Prompt changes often break behavior in subtle ways long before they are noticed in production. This tool gives teams a lightweight, dependency-free way to treat prompt regression checks like ordinary automated tests.

### Core capabilities

- Load suites from YAML or JSON
- Render `{{ variable }}` placeholders with case/default/env precedence
- Compare against golden outputs
- Evaluate `contains`, `regex`, `json-path-lite`, and `numeric_tolerance` assertions
- Generate Markdown and JSON reports
- Generate JUnit XML reports for CI test panels
- Fail CI on regressions, missing golden values, or strict quality-gate settings
- Run fully offline with Python standard library only

### Quick start

```bash
python -m pip install -e .
prlab run examples/sample-suite.yaml \
  --format both \
  --output reports/report.md \
  --json-output reports/report.json \
  --junit-output reports/report.junit.xml
```

### Intended workflow

Use `prompt-regression-lab` after your own pipeline has already produced candidate outputs. The tool does not call model APIs; it validates prepared outputs and turns regressions into deterministic pass/fail signals for local development and CI.

JUnit XML output maps every prompt case to a testcase so CI systems can display prompt regressions beside ordinary unit tests.

### Limitations

- No model invocation is included by design
- Built-in YAML support intentionally covers a practical subset, not the entire YAML spec
- `json-path-lite` is intentionally minimal

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and release notes workflow.
