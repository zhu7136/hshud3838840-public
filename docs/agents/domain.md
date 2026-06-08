# Domain 文档

工程技能在探索代码库时应如何消费本仓库的领域文档。

## 探索前先读取这些

- **`CONTEXT.md`** 在仓库根目录，或
- **`CONTEXT-MAP.md`** 在仓库根目录（如果存在）— 它指向每个上下文的 `CONTEXT.md`。读取与主题相关的每个文件。
- **`docs/adr/`** — 读取与你即将工作的领域相关的 ADR。在 multi-context 仓库中，还要检查 `src/<context>/docs/adr/` 中的上下文特定决策。

如果这些文件中的任何一个不存在，**静默继续**。不要标记它们的缺失；不要建议预先创建它们。生产者技能（`/grill-with-docs`）会在术语或决策实际解决时惰性创建它们。

## 文件结构

Single-context 仓库（大多数仓库）：

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-event-sourced-orders.md
│   └── 0002-postgres-for-write-model.md
└── src/
```

Multi-context 仓库（根目录存在 `CONTEXT-MAP.md`）：

```
/
├── CONTEXT-MAP.md
├── docs/adr/                          ← 系统级决策
└── src/
    ├── ordering/
    │   ├── CONTEXT.md
    │   └── docs/adr/                  ← 上下文特定决策
    └── billing/
        ├── CONTEXT.md
        └── docs/adr/
```

## 使用术语表的词汇

当你的输出命名领域概念时（在 issue 标题、重构提案、假设、测试名称中），使用 `CONTEXT.md` 中定义的术语。不要偏离术语表明确避免的同义词。

如果你需要的概念尚未在术语表中，这是一个信号 — 要么你在发明项目不使用的语言（重新考虑），要么存在真正的空白（为 `/grill-with-docs` 记录它）。

## 标记 ADR 冲突

如果你的输出与现有 ADR 矛盾，明确指出而不是静默覆盖：

> _与 ADR-0007（事件溯源订单）矛盾 — 但值得重新讨论，因为……_
