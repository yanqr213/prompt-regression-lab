# Contributing

感谢你考虑为 `prompt-regression-lab` 做贡献。

## 开发环境

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

## 提交建议

- 保持 CLI 行为稳定，避免无必要破坏性变更
- 新增断言类型时，请同步补充 README 与测试
- 修复 bug 时，请优先添加回归测试
- 尽量保持标准库实现，新增依赖前请说明必要性

## 文档

- README 中文为主，但必须同步维护 English section
- 更新用户可见行为时，请在 `CHANGELOG.md` 记录

## 发布检查

发布前建议确认：

1. `python -m pip install -e .` 成功
2. `python -m unittest discover -s tests -v` 全绿
3. `prlab run examples/sample-suite.yaml --strict` 通过
4. 工作区中无 `__pycache__`、`*.egg-info` 等临时产物

## Pull Request

PR 描述建议包含：

- 背景与目标
- 关键实现思路
- 测试覆盖情况
- 兼容性风险
