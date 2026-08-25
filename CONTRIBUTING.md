# 贡献指南 (Contributing)

感谢你考虑为 `li-mtrie-2026` 做贡献! 🎉

## 适用场景

本 skill 是为**全国大学生数学建模竞赛**（国赛/美赛/校赛）设计的端到端工作流。
- 主要用户: 学生（96 小时比赛）+ 教练
- 目标: 缩短从"读题"到"提交论文"的时间, 减少格式错误

## 如何贡献

### 1. 提 Issue
- 🐛 **Bug**: 跑 SKILL.md 流程时遇到错误
- 💡 **Feature**: 想要新功能 / 改进建议 / 缺失的题型支持
- ❓ **Question**: 流程不清楚 / 怎么用 / 为什么这样设计

模板会自动加载, 请按提示填。

### 2. 提 PR (代码改动)

**提 PR 前必做**:
1. ✅ Fork 仓库, 从 `main` 分支建新分支 (`git checkout -b feat/your-feature`)
2. ✅ 改完后跑本地 smoke test: `py references/scripts/profile_data.py <your-test-xlsx>`
3. ✅ 跑 `py tools/pack.py` 确保打包成功
4. ✅ 写 commit message 格式: `<scope>: <subject>`, 例:
   - `docs: 加美赛 MCM 模板适配`
   - `fix(pack.py): 修中文文件名 GBK 编码问题`
   - `feat: 加 LLM-based 模型比选推荐`

**PR 模板会自动加载**, 会问:
- 关联的 Issue
- 改了什么 / 为什么改
- 截图 / 验证步骤
- 是否更新了 CHANGELOG / SKILL.md / README

### 3. 加新参考论文

如果想加第 6/7/... 篇参考论文:
1. 在 `references/获奖论文/` 新建 `题目-学校-年份-奖项.md`
2. 模板参考 `板凳龙-南科大-2024国一.md` 的 8 节结构
3. 重点: §3 关键技术 (skill 借鉴清单) + §5 与 skill 关联
4. 更新 `SKILL.md` line 24-26 的"5 篇参考论文速查"
5. 更新 `CHANGELOG.md`

### 4. 加新模板

`references/code-template.py` (数据驱动题) 和 `mechanism-template.py` (机理题)
- 加新模板前先提 Issue 讨论, 避免重复
- 必须含: `# -*- coding: utf-8 -*-` + 中文 docstring + 字号/线宽/DPI 预设

## 不要做的事 ❌

- ❌ 提交 `求解/` `题目/` `数据/` 里的赛题/数据（学生隐私 + 版权）
- ❌ 改 SKILL.md 的 frontmatter description 字段（影响 skill 触发）
- ❌ 提交大文件 (单文件 > 5MB), 用 .gitignore 排除
- ❌ 删别人提的 PR / Issue 评论

## 开发流程

```
1. Issue 讨论 (可选, 大改动建议)
   ↓
2. Fork + 新分支
   ↓
3. 改代码 + 写 commit
   ↓
4. push + 开 PR (用模板)
   ↓
5. CI 自动跑 smoke test
   ↓
6. 维护者 review
   ↓
7. merge 到 main
```

## 测试规范

提交前必跑:
```bash
# 1. 打包
py tools/pack.py

# 2. 验证 zip 完整性
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead("li-mtrie-2026-完整包.zip")
$bad = $zip.Entries | Where-Object { $_.FullName -match '\.(aux|log|out|toc|pyc)$' }
"中间产物: $($bad.Count) (应为 0)"

# 3. 写 / 改 SKILL.md 文档后, 用 writing-for-agents skill 自审
```

## 行为准则

- 友好、尊重、就事论事
- 评审 PR 时先肯定贡献, 再提改进
- 争议先在 Issue 讨论, 不要直接在 PR 里争论

## License

贡献即同意按 [MIT License](LICENSE) 授权。

---

**有问题?** 在 [Issue](https://github.com/z376/li-mtrie-2026/issues) 提问, 邮件不回复。
