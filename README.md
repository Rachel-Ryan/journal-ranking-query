# 期刊等级查询 Skill

[English README](README_EN.md)

一个面向学术研究者的离线 Agent Skill。给定期刊名称、缩写、曾用名、ISSN、eISSN 或 CN 号后，它可以确定性查询最新收录快照中的 JCR 分区与影响因子、新锐期刊分区、SSCI、CCF、FMS 和 CSSCI 信息。

本项目主要面向中国学者，优先提供中文说明。它采用开放的 [Agent Skills](https://agentskills.io/) 目录结构，至少支持 Codex 和 Claude Code；其他能够读取 `SKILL.md`、执行本地 Python 并保留 SQLite 资源的 Agent 平台也可以使用。

## 主要特点

- 完全离线，仅依赖Python标准库。
- 支持期刊名称、缩写、曾用名、ISSN、eISSN和CN号的精确查询与模糊发现。
- 返回全部相关分区，并对模糊匹配和同名期刊进行歧义保护。
- CCF国际 A/B/C 与中文科技期刊 T1/T2/T3 分开输出。
- 仅查询各来源最新快照，不包含2025中科院分区。

## 当前数据范围

| 数据 | 版本 | 记录数 | 目录来源 |
|---|---:|---:|---|
| JCR期刊、影响因子及分区 | 2025 | 22,643 |[ShowJCR](https://github.com/hitfyd/ShowJCR) |
| 新锐期刊分区 | 2026 | 22,299 |[ShowJCR](https://github.com/hitfyd/ShowJCR) |
| SSCI期刊目录 | 2026 | 3,537 |[博汇学术](http://www.upubfast.com/wos.html) |
| CCF推荐国际学术刊物 | 2026 | 295 | [ShowJCR](https://github.com/hitfyd/ShowJCR)|
| CCF计算领域高质量科技期刊 | 2025 | 68 |[ShowJCR](https://github.com/hitfyd/ShowJCR) |
| FMS中文期刊 | 2025 | 94 | [FMS官方网站](https://www.fms-journal.net/)|
| FMS英文期刊 | 2025 | 1,183 | [FMS官方网站](https://www.fms-journal.net/)|
| CSSCI来源期刊 | 2025—2026 | 674 | [高校图书馆](https://lib.sdx.js.cn/col/col2622/index.html)|

SSCI是否收录以2026年SSCI目录为准；SSCI学科的分区和排名来自同一期刊的JCR 2025对应学科。详情参见 [数据与匹配方法](references/data-and-method.md)。

## 让 Agent 自动安装并测试

把下面整段提示词发给 Codex、Claude Code 或其他具备本地文件和命令执行能力的 Agent。先将第一行的仓库地址替换为你的实际地址。

```text
请从以下仓库安装并测试 `journal-ranking-query` Skill：

仓库地址：<GitHub仓库URL>

请先阅读仓库中的 `README.md` 和 `SKILL.md`，然后：
1. 自动识别当前Agent平台并安装到用户级Skills目录；Codex使用 `~/.codex/skills/journal-ranking-query`，Claude Code使用 `~/.claude/skills/journal-ranking-query`。
2. 确认Python ≥ 3.8，并从安装后的目录运行 `python3 tests/smoke_test.py`；必要时改用 `python` 或 `py -3`。
3. 最后报告安装位置、Python版本和测试结果；如果测试失败，请说明原因，不要执行无关修改。
```

## 手动安装

需要Python 3.8或更高版本。安装时必须保留整个仓库，不能只复制 `SKILL.md`。

### Codex

```bash
git clone <你的GitHub仓库URL> ~/.codex/skills/journal-ranking-query
```

如设置了 `CODEX_HOME`，安装到其下的 `skills/journal-ranking-query`。

### Claude Code

```bash
git clone <你的GitHub仓库URL> ~/.claude/skills/journal-ranking-query
```

项目级安装可复制到 `<项目目录>/.claude/skills/journal-ranking-query`。其他Agent平台应将完整仓库导入其Skills目录，并允许执行本地Python。

## 安装后测试

```bash
python3 tests/smoke_test.py
```

测试会检查数据范围、精确与模糊查询、同名歧义以及中科院分区排除情况。也可直接查询：

```bash
python3 scripts/query_journal.py "Journal of Finance" --format text
```

## 查询结果约定

脚本默认输出JSON。只有 `exact` 和 `selected_entity` 可以直接报告等级；`ambiguous` 和 `fuzzy_candidates` 必须先确认期刊身份。`not_found` 或 `not_listed` 只表示当前快照中没有相应记录，不构成期刊质量评价。

## 数据与免责声明

- 本项目不是Clarivate、SSCI、CCF、FMS、CSSCI或新锐期刊分区的官方网站。
- 查询结果仅供科研、投稿和信息检索参考；正式认定应以评价机构当期发布内容为准。


## 致谢

- [ShowJCR](https://github.com/hitfyd/ShowJCR)：部分期刊目录数据来自该项目；
- [2026JCR期刊分区查询网页](https://brentnvp-art.github.io/jcr-query/)：受该项目启发；
