# Background

在推进RDEC AI落地Studios的合作过程中，我们需要沉淀一些AI通用能力项以推广和复用到其他Studios，因此我们建立一个知识库空间，用于团队沉淀知识分享、宣讲材料、Show Case等。



# 文档撰写要求

- 英文编写文档
- 文档统一存放到docs目录下，使用Markdown文档编写
- 文档关联的二进制资源（图片、视频等），统一保存到文档所在目录下的assets文件夹内
- 同一能力项需要中文版时，在英文名后追加`_cn`（如`figma2ue-standalone_V1_cn.html`）；落地页会自动把中英文版本合并为一张卡片，并在打开的页面右上角提供中英文切换，无需单独展示两份
- 落地页卡片文案以Markdown源文档为准（首个标题 + 其后第一段）；暂无中文Markdown的能力项，中文文案取自`scripts/translations.json`（AI译文，可人工维护），补齐中文文档后自动以文档为准
- HTML 展示页由 Markdown 自动生成，无需手工维护：`python3 scripts/build_docs.py` 会为没有 HTML 的 Markdown 生成 `xxx-standalone_V1.html`；再次修改 Markdown 后重新执行同一命令，脚本按内容哈希检测到变更并重建对应 HTML（CI 部署时会自动执行）
  - `--check`：只检查不写文件，存在缺失或过期页面时退出码 1
  - `--force`：按 Markdown 重新生成全部页面（用于接管历史手工维护的 HTML）
  - `--adopt`：给历史手工页面补上指纹，之后即可增量检测
- 本地预览：`python3 scripts/build_docs.py && python3 scripts/generate_index.py`



# 已有能力项

| 分类   | 能力项                           | Studios                            | 研发负责人              | 状态     | ShowCase Git地址                                             | HTML地址                                                     |
| ------ | -------------------------------- | ---------------------------------- | ----------------------- | -------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 知识库 | 研发知识库DeepWiki               | Nikke, GST, Yager                  | zichao                  | 使用中   | [rd-knowledge-base-deepwiki-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/rd-knowledge-base-deepwiki-standalone_V1.html) | [rd-knowledge-base-deepwiki-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/rd-knowledge-base-deepwiki-standalone_V1.html) |
| 知识库 |                                  | Mundfish                           | zichao                  | 试用中   |                                                              |                                                              |
| 程序   | AI Coding / Code Review          | 永星, Funcom, GST, Sharkmob        | yaodong                 |          | [code-review-agent_V1.md](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/code-review-agent_V1.md) | [code-review-agent-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/code-review-agent-standalone_V1.html) |
| 程序   | PSD还原UMG                       | 永星                               | leto                    | 使用中   | [psd2umg_V1.md](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/psd2umg_V1.md) | [psd2umg-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/psd2umg-standalone_V1.html) |
| 程序   | PSD转Prefab                      | Nikke                              | xiongwei                | 使用中   | [psd2prefab_V1.md](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/psd2prefab_V1.md) | [psd2prefab-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/psd2prefab-standalone_V1.html) |
| 程序   | Figma UX File生成In-game UI Demo | sharkmob有需求，后续可以推给Sumo和 | xiongwei                | Demo     | [figma2ue_V1.md](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/figma2ue_V1.md) / [中](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/figma2ue_V1_cn.md) | [figma2ue-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/figma2ue-standalone_V1.html) / [中](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/figma2ue-standalone_V1_cn.html) |
| 程序   | Figma转Unity                     |                                    | xiongwei                | Demo     | [figma2unity_V1.md](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/figma2unity_V1.md) / [中](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/figma2unity_V1_cn.md) | [figma2unity-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/figma2unity-standalone_V1.html) / [中](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/figma2unity-standalone_V1_cn.html) |
| 程序   | AI Audit                         | Funcom, Techland                   | siqi / shaowei / jingru | 开发中   | [ai_auditing_V1.md](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/ai_auditing_V1.md) | [ai_auditing-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/ai_auditing-standalone_V1.html) |
| 程序   | 资源和谐识别工具                 | Nikke                              | alen                    | 使用中   | [Intelligent Character Asset Retrieval_V1.md](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/Intelligent%20Character%20Asset%20Retrieval_V1.md) | [Intelligent Character Asset Retrieval-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/Intelligent%20Character%20Asset%20Retrieval-standalone_V1.html) |
| 程序   | P4版本合并                       | Nikke                              | alen                    | 使用中   | [p4-merge-workflow_V1.md](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/p4-merge-workflow_V1.md) | [p4-merge-workflow-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/p4-merge-workflow-standalone_V1.html) |
| 程序   | 蓝盾/jenkins流水线失败归因       | 永星                               | yang                    | 使用中   | [ci-error-analysis_V1.md](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/ci-error-analysis_V1.md) | [ci-error-analysis-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/ci-error-analysis-standalone_V1.html) |
| 程序   | jira/TAPD Tikect 分析和整理      | Funcom，GST                        | yaodong                 | 使用中   | [jira-issue-triage_V1.md](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/jira-issue-triage_V1.md) | [jira-issue-triage-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/jira-issue-triage-standalone_V1.html) |
| 程序   | 代码仓库依赖项扫描Skill          | Funcom                             | xuqing                  | 使用中   |                                                              |                                                              |
| 美术   | 2D图片微调                       | Nikke                              | jingru                  | 开发中   |                                                              |                                                              |
| 美术   | 3D mesh模型训练                  | Funcom                             | jingru / siqi           | 开发中   | [3d-mesh-model_V1.md](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/3d-mesh-model_V1.md) | [3d-mesh-model-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/3d-mesh-model-standalone_V1.html) |
| 美术   | 3D 动作模型训练                  | GST                                | jingru                  | 开发中   | [3d-motion-model_V1.md](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/3d-motion-model_V1.md) | [3d-motion-model-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/3d-motion-model-standalone_V1.html) |
| 美术   | 2D 切图                          | 永星Nikke                          | xiongwei                | 使用中   | [refMatch_V1.md](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/refMatch_V1.md) | [refmatch-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/refmatch-standalone_V1.html) |
| 美术   | 3D模型重拓扑/减面                |                                    | shaowei                 | 方案调研 | [3d-remesh-retopology_V1.md](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/3d-remesh-retopology_V1.md) | [3d-remesh-retopology-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/3d-remesh-retopology-standalone_V1.html) |
| 程序   | NamingAudit 命名检查（PSD / UE）  | RDEC 内部                          | xiongwei                | 使用中   | [namingaudit_V1.md](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/namingaudit_V1.md) / [中](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/namingaudit_V1_cn.md) | [namingaudit-standalone_V1.html](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/namingaudit-standalone_V1.html) / [中](https://git.tencent.com/rdec/ai_show_cases/blob/master/docs/namingaudit-standalone_V1_cn.html) |
