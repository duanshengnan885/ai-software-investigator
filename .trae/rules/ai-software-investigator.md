---
description: 豆包 MarsCode / Trae 软件法医调查规则。用于程序崩溃、Bug 定位、竞态条件、黑盒异常排查。
globs: *
alwaysApply: false
---

# AI Software Investigator 调查协议

当用户要求定位或修复 Bug、偶发崩溃、性能骤降时：
1. **禁止直接猜测与修改代码**。
2. 运行 `investigator auto --dir . --problem "<问题描述>"` 执行自主闭环调查。
3. 遵循证据第一原则：每一个推断必须对应 `.investigation/evidence.jsonl` 中的证据 ID。
4. 修复后使用 100 次独立运行验证无复发，严禁宣称“100% 修复”。
