# 来源与整合边界

核对日期：2026-10-21。已按用户确认重新定位主风格，原参考技能均保留。

| 来源 | 采用 | 边界 |
|---|---|---|
| Claude 插件 `anthropic-skills:opus-code-animation` | 主视觉与代码动效方法；「黄白口播辅助动画标准」、原点阵背景、同一制作记录的荧光黄绿色板；截图上传、扫描对比、居中构图、无新增字幕及原生竖屏 4K 交付 | 本包保留[原标准](huangbai-broll-standard.md)和背景；不套用其其他案例里的纸艺、角色、报幕、署名或配乐 |
| Codex `ego-browser` | 已有登录态、同任务空间、观察后操作；提供无声网页连续帧后备通路 | 页面操作始终在 Ego Lite；只有连续帧后备通路不含音轨 |
| Codex `screenstudio` | 真实横屏窗口／重点局部录制、声音、暂停续录、标记、工程与分段验证；优先使用软件中的放大、缩小和平移组织观看 | 接入见 [screenstudio-recording.md](screenstudio-recording.md)；当前接口未提供编辑方法时核实实际软件界面，不把接口边界当成放弃运镜的理由；成片效果须实际导出检查，不覆盖黄白风格 |
| Codex `sd-2-5-prompt`／`dreamina-canvas-cli` | AI 剧情与情境的分镜、资产参考、提示词及确认后生成 | 流程见 [ai-video.md](ai-video.md)；生成前核对参数与积分并确认，默认原生声音开启，不用生成画面伪造操作证据 |
| Codex `motion`／Claude `ui-motion-reveal` | 输入、系统响应、结果采用不同动作；父层运镜、子层显现；容器与内容适度交叠 | 只取适用运动方法，不覆盖黄白标准的配色、布局与无字幕要求 |
| Codex `talk-motion` | 台词／动作锚点、一个视觉主角、素材身份与口播连续性、定点修改和验收 | 不继承黄色品牌、强制配音效或强制标题 |
| Codex `hyperframes`／`hyperframes-core`／`hyperframes-cli`，Claude `hyperframes-animation`／`hyperframes-creative` | 复杂合成时的确定性时间轴、媒体管理、检查，以及适用运动方法 | 不是本次确认的原风格，用户未选时不强行更换代码路线 |
| Codex `faceless-explainer` | 信息随台词发展、构建过程解释概念、留阅读时间 | 不把真实操作都替换成虚构界面，不引入强制解释字 |
| Codex `vidscript`／`mac-video-preview` | 每视频独立目录、下载后验流、总览与加密片段、原声分轨检查、兼容副本 | 不扩大为歌曲识别、源文档修改或上传发布 |
| 13 条参考视频 | 一操作一重点、局部放大、输入—响应—结果、对应比较、作品巡览 | 原片观察见 [source-study.md](source-study.md)；章节标题仅为原片观察，不能推翻当前无新增标题默认值 |
| Instagram [Rourke](https://www.instagram.com/rourke/) 最近 30 条非置顶视频 | 操作演示与动画结合、同素材承接、结果与原片对应、UI 输入到生成结果的关系 | 逐条观察见 [rourke-study.md](rourke-study.md)；不照搬作者配色、密集标题、多层面板、小窗口或营销话术；成片中的界面演示不自动认定为真实录屏 |

## 风格定位证据

Claude 本地记录显示 2026-09-28 21:06（北京时间）调用 `anthropic-skills:opus-code-animation`，22:18 调用节庆用途的 `anthropic-skills:minimal-chinese-motion`。前者插件内另有用户专属深色口播辅助标准；本轮用户明确确认采用这一份。

之前仅查普通 `~/.claude/skills`，漏掉 Claude 桌面插件目录，错误地把 HyperFrames 深色青绿示例当候选。该候选已撤销；主风格以本包原标准及背景为准。以后核对 Claude 技能要兼顾普通技能目录、桌面插件与实际调用记录，不能把“目录里有”说成“用户最近用过”。

## 验证边界

网页连续帧通路已在 Ego Lite 本地测试页验证输入、筛选、重置、连续捕获、时间戳编码与失败拦截。Screen Studio 本次已检查连接、空闲状态与来源读取，未新增录像、声音或带样式导出实测；原技能已有的录制测试范围见其自身说明。代码模板以模拟素材验证构图与扫描动作，不把模拟界面称为真实产品操作。实际网站入口、权限、声音捕获和高频动画仍按每次任务现场核实。
