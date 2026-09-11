# Mathematical Modeling Competition Skill

面向 CUMCM、MCM/ICM 等数学建模竞赛的 Codex Skill，覆盖审题、假设敏感性分析、数据审计、建模、可复现实验、结果追溯、论文写作、图表、机器预检与独立审稿。

## 主要能力

- 先做题意歧义与假设敏感性预检，再选择模型。
- 增加核心语义审计、子问题依赖图、方法适配证书和假设追踪矩阵，防止关键词触发算法与模型拼盘。
- 以阶段交接契约固定输入、输出、建模口径、验证与未决风险。
- 先建立透明基线，再按问题需要增加复杂模型。
- 通过实验记录和结果注册表追溯论文中的关键结论。
- 区分证据型数据图与解释型概念图。
- 支持 Word、LaTeX、Typst 路由，并通过 `FORMAT_LOCK.json` 锁定当届官方规则来源、文件哈希和可选 Word 模板。
- 内置 CUMCM DOCX 格式守卫：检查 A4、2.5 cm 页边距、摘要首页、页脚居中页码、无目录、附录代码与支撑材料清单；严格模式禁止蓝色等非黑色标题。
- 提供跨平台论文预检器，检查空稿、占位符、缺失资源、格式混写、匿名元数据和结果证据。
- 预检 CUMCM 支撑材料，并对空泛标题、方法堆砌和只报软件结果给出警告。
- 通过 `HUMAN_TASKS.md` 管理签字、正式模拟器、有限测试次数、现场数据和最终提交等人工关卡。
- 在最终润色前使用冻结提交包进行独立盲审。

## 目录

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── workflow.md
│   ├── validation-and-reproducibility.md
│   ├── writing-and-visuals.md
│   ├── reasoning-quality-gates.md
│   ├── human-verification-gates.md
│   ├── cumcm-template-lock.md
│   ├── cumcm-2026-compliance.md
│   └── cumcm-2026-format-fingerprint.md
├── scripts/
│   ├── init_competition_workspace.py
│   ├── build_archive_index.py
│   ├── cumcm_format_lock.py
│   └── paper_preflight.py
└── tests/
```

## 安装

将整个仓库克隆到个人 Codex Skills 目录，不要只复制 `SKILL.md`。

Windows PowerShell：

```powershell
git clone https://github.com/111aaa327/math-modeling-competition-skill.git "$env:USERPROFILE\.codex\skills\math-modeling-competition"
```

安装后可显式调用：

```text
$math-modeling-competition
```

## 测试

仅依赖 Python 标准库；PDF 文本检查可选使用 `pypdf`。

```powershell
python -m unittest discover -s tests -v
```

## 工具示例

初始化一个不覆盖已有内容的竞赛工作区：

```powershell
python scripts/init_competition_workspace.py --path <workspace> --competition "CUMCM 2026"
```

执行论文机器预检：

```powershell
python scripts/paper_preflight.py --paper <paper.docx|paper.pdf|main.tex|main.typ|paper.md> --project <workspace> --registry <RESULT_REGISTRY.json> --support-archive <support.zip> --output <report.json>
```

锁定 CUMCM 官方格式来源并审计 Word 论文：

```powershell
python scripts/cumcm_format_lock.py lock --workspace <workspace> --official-rules <workspace/00_rules/official/论文格式规范.pdf> --edition 2026 --style-profile classic-black
python scripts/cumcm_format_lock.py audit --workspace <workspace> --paper <paper.docx> --strict-style --output <format-report.json>
```

当前核验的 2026 格式规范源文件 SHA-256 为 `d77de49534649b46ca195d32bd9c56a1fbe06dc96fdcf3e1199e6dd7d9831f4a`。全国规范没有统一规定字体、字号、行距和颜色；`classic-black` 是用于贴近传统国赛论文的保守队内样式，不冒充官方排版要求。若锁定了经过验证的 Word 模板，模板样式优先。

机器预检不能替代数学验证、官方规则复核或最终逐页视觉检查。

## 规则边界

- 当前赛事官方规则优先于本 Skill、课程、提示词和往年论文。
- `references/cumcm-2026-compliance.md` 是便捷基线，提交前必须回到官网和正式通知复核。
- 正式比赛期间应遵守当届关于独立参赛、联网和匿名性的已核验要求。
- 不虚构数据、实验、引用、结果或下载链接。

## 来源说明

该 Skill 为独立编写。设计过程中参考并评估了 [jihe520/MathModelAgent](https://github.com/jihe520/MathModelAgent) 的公开工作流思路，但没有复制其受限论文模板、Web 服务代码或跳过权限检查的启动方式。

## 配套裁判 Skill

[math-modeling-judge-skill](https://github.com/111aaa327/math-modeling-judge-skill) 用于对冻结后的论文、代码、数据和结果文件进行独立盲审。建议由主 Skill 负责产出，由裁判 Skill 在隔离上下文中只读审查，再把 P0/P1/P2 问题交回主任务修改。

## License

暂未指定开源许可证。公开仓库允许浏览；如需复制、修改或再分发，请先联系仓库所有者确认授权。
