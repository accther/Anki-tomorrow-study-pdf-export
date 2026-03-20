# Release Copy

This file contains bilingual release copy for:

- GitHub repository
- GitHub release notes
- AnkiWeb add-on listing


## 1. GitHub Repository

### Repository Name

Tomorrow Study PDF Export

### Short Description

EN:
Export tomorrow's Anki study queue to a printable PDF, with deck filtering and scheduler-based ordering.

中文：
将 Anki 第二天的学习队列导出为可打印 PDF，支持牌组筛选，并尽量保持与调度器一致的学习顺序。


### About / Introduction

EN:
Tomorrow Study PDF Export is an Anki add-on for macOS that prepares tomorrow's study cards as a printable PDF. It supports deck-range selection, includes due review and learning cards, can include tomorrow's available new cards, and tries to preserve Anki's actual study order by simulating tomorrow on a temporary collection snapshot.

The PDF is designed for paper-based practice: questions and answers are separated, each question includes blank space for writing, and a small response strip is provided so you can record paper results before syncing them back into Anki.

中文：
Tomorrow Study PDF Export 是一个面向 macOS 的 Anki 插件，用于把第二天要学习的卡片整理成可打印的 PDF。它支持按牌组范围导出，包含到期的复习卡和学习卡，也可以包含第二天预计会出现的新卡，并通过在临时数据库快照上模拟“明天”的方式，尽量保持与 Anki 应用内一致的学习顺序。

生成的 PDF 面向纸质练习场景：题目与答案分开排版，题目下方预留书写空白，并提供简洁的作答记录栏，方便先在纸上完成学习，再回到 Anki 同步结果。


### Key Features

EN:
- Select one or more decks before exporting
- Include child decks by default
- Export tomorrow's due review and learning cards
- Optionally include tomorrow's available new cards
- Preserve Anki study order as closely as possible
- Separate question pages and answer appendix
- Leave writing space under each question for paper practice
- Support math formula rendering and complex card templates through WebView-based PDF rendering

中文：
- 导出前可选择一个或多个牌组
- 默认包含子牌组
- 支持导出第二天到期的复习卡和学习卡
- 可选包含第二天预计出现的新卡
- 尽量保持与 Anki 应用一致的学习顺序
- 题目与答案分开排版
- 每道题下方预留书写区域，适合纸面练习
- 基于 WebView 渲染，尽量兼容数学公式和复杂模板卡片


### Compatibility

EN:
- Platform: macOS
- Tested with: Anki 25.09.2

中文：
- 平台：macOS
- 已测试版本：Anki 25.09.2


### Known Limitations

EN:
- The export result is based on the collection state at the moment of export.
- If you study cards or change deck options after exporting, the actual order shown in Anki on the next day may change.
- When Anki's scheduler queue API is unavailable, the add-on falls back to a manual ordering strategy, which may be less exact for some advanced scheduling configurations.
- Rendering of highly customized card templates may still depend on the template's own scripts and styles.

中文：
- 导出结果以导出当下的卡组状态为准。
- 如果导出后继续学习或修改了牌组选项，第二天 Anki 中的实际顺序可能发生变化。
- 当 Anki 调度器队列接口不可用时，插件会退回到手动排序兜底逻辑，某些复杂调度场景下顺序可能不如主路径精确。
- 高度定制化的卡片模板最终显示效果仍可能受到模板自身脚本和样式的影响。


## 2. GitHub Release Notes

### Version Title

v1.0.0

### Release Notes

EN:
Initial public release of Tomorrow Study PDF Export.

This release includes:
- Deck-scope selection before export
- Optional child deck inclusion
- Tomorrow queue simulation on a temporary SQLite snapshot
- Scheduler-first card ordering
- Printable PDF output with separated questions and answers
- Writing space and response strip for paper-based study
- Improved support for MathJax, LaTeX, and script-based card templates
- Default PDF output path set to Downloads

中文：
Tomorrow Study PDF Export 首个公开版本。

本版本包含：
- 导出前选择牌组范围
- 可选包含子牌组
- 基于临时 SQLite 快照模拟第二天学习队列
- 优先按 Anki 调度器顺序导出卡片
- 输出适合打印的 PDF，题目与答案分开排版
- 题目区域预留书写空白，并附带纸面记录栏
- 改进对 MathJax、LaTeX 和脚本型模板卡片的支持
- 默认 PDF 输出目录为 Downloads


## 3. AnkiWeb Listing

### Add-on Title

Tomorrow Study PDF Export

### One-Line Summary

EN:
Export tomorrow's Anki study queue to a printable PDF with deck filtering and scheduler-based ordering.

中文：
将 Anki 第二天学习队列导出为可打印 PDF，支持牌组筛选，并尽量保持与调度器一致的顺序。


### Full Description

EN:
Tomorrow Study PDF Export is an Anki add-on for users who want to prepare tomorrow's cards in a paper-friendly format.

Instead of exporting an entire deck blindly, the add-on creates a temporary collection snapshot, simulates tomorrow's study day, and then tries to read cards in the same order Anki would present them. The exported PDF separates questions and answers, adds writing space for paper practice, and includes a compact response strip so users can mark paper results before syncing them back into Anki.

Main features:
- Select one or more decks
- Include child decks
- Export tomorrow's due review and learning cards
- Optionally include tomorrow's available new cards
- Preserve Anki order as closely as possible
- Separate questions and answers for printing
- Better support for formulas and complex templates through WebView-based rendering

Tested on:
- macOS
- Anki 25.09.2

Important notes:
- The export reflects your collection state at the moment you generate the PDF.
- If you continue studying or change deck options afterwards, the next day's in-app queue may differ.

中文：
Tomorrow Study PDF Export 适合希望提前把第二天学习内容整理成纸质资料的 Anki 用户。

它不是简单地把整个牌组直接打印出来，而是先创建一个临时数据库快照，模拟“第二天”的学习日，再尽量按 Anki 实际会出卡的顺序读取卡片。导出的 PDF 会将题目和答案分开排版，在题目下方预留书写空间，并附带简洁的作答记录栏，方便先进行纸面练习，再回到 Anki 同步结果。

主要功能：
- 选择一个或多个牌组导出
- 支持包含子牌组
- 导出第二天到期的复习卡和学习卡
- 可选包含第二天预计出现的新卡
- 尽量保持与 Anki 学习顺序一致
- 题目与答案分开，适合打印
- 基于 WebView 渲染，尽量兼容公式和复杂模板

测试环境：
- macOS
- Anki 25.09.2

注意事项：
- 导出结果以生成 PDF 当下的卡组状态为准。
- 如果导出后继续学习或修改牌组选项，第二天在 Anki 中看到的实际队列可能会不同。


### Support / Homepage

EN:
Recommended support link: your GitHub repository or GitHub Issues page.

中文：
建议将支持链接填写为你的 GitHub 仓库主页或 GitHub Issues 页面。


## 4. Suggested Tags / Keywords

EN:
- anki
- pdf
- print
- export
- scheduler
- study planning
- paper practice
- mathjax

中文：
- Anki
- PDF
- 打印
- 导出
- 调度
- 学习计划
- 纸面练习
- 公式渲染
