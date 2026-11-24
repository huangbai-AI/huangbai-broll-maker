# 在 Ego Lite 录制真实网页

## 范围

本页是只录网页内容的无声路线。真实窗口录制优先采用 [Screen Studio 接入](screenstudio-recording.md)，网页操作仍使用 Ego Lite；需要声音时不得静默回退到本页的无声捕获。

附带脚本使用已安装 Ego Lite 的 `page.cdp` 和 `page.events()` 记录连续网页帧，再按真实时间戳编码。不会另启浏览器，不复制登录凭据。录的是网页内容区域，不是浏览器地址栏／桌面，**不包含声音**。高频动画的实际流畅度取决于捕获频率，需要查看导出报告。

流程根据本机 `ego-browser skill` 2.1.0 实测。每次任务仍需先读取当前版本指南；不要沿用失效 API。底层依据：[Chromium Page 协议](https://chromedevtools.github.io/devtools-protocol/tot/Page/)，含 `startScreencast`、`screencastFrame`、`screencastFrameAck`、`stopScreencast`。

## 录前准备

1. 运行 `ego-browser skill`，在当前目标的同一个任务空间中查看页面。没有任务空间才创建一次，并记下空间编号及页面标签；`record-ego.mjs` 只接收现有空间，不自行创建／接管。
2. 快照观察、确定目标，排练必要操作；动作目标来自当前快照或已核实的网页元素，不能猜选择器。
3. 页面加载稳定、字体与媒体就绪，回到可安全重复的开始位置。桌面网站保留真实横屏窗口尺寸与布局，保存前后状态；9:16只是最终成片画幅，不能据此把桌面网页视口改成1080×1920。仅本来就是移动端演示或用户明确指定时，才使用对应竖屏源界面。
4. 根据每句的关键动作写 `actions`。单次 0–45 秒，长段拆开；`at` 是从录制开始算起的秒数，等待应留足余量，不用来跳过实际结果检查。

## 调用

在本次任务生成一个新的 `.mjs` 文件，并用绝对路径。下面 `SKILL_DIR` 表示当前技能所在目录，`SPACE_ID`／`PAGE_LABEL` 必须替换为真实已观察值。

```js
// /absolute/task/work/record-shot-01.mjs
const {record} = await import('file:///absolute/SKILL_DIR/scripts/record-ego.mjs');
await record({
  spaceId: SPACE_ID,
  pageLabel: 'PAGE_LABEL',
  outputDir: '/absolute/task/work/broll/raw/shot-01-take-01',
  width: 1920, height: 1080, duration: 8,
  actions: [
    {at: .8, type: 'move', x: 420, y: 310, label: '指向已观察的目标'},
    {at: 1.3, type: 'fill', selector: '已观察到的唯一选择器', text: '演示文本'},
    {at: 2.8, type: 'click', selector: '已观察到的按钮', label: '执行这一项操作'},
    {at: 3.5, type: 'waitForSelector', selector: '已核实的结果元素', timeout: 4000}
  ]
}, {taskSpace});
```

由 Ego 运行（不是普通 Node）：

```sh
ego-browser nodejs -e 'await import("file:///absolute/task/work/record-shot-01.mjs")'
python3 /absolute/SKILL_DIR/scripts/encode-recording.py \
  /absolute/task/work/broll/raw/shot-01-take-01 \
  /absolute/task/outputs/broll/shot-01.mp4
```

支持动作：`move`、`click`、`fill`、`press`、`wheel`、`waitForSelector`。滚动前先把鼠标放到真实可滚动区域。对实际网站需要更复杂控制时，由助手按照 Ego 当前指南编写该段操作，不把通用动作列表当成能访问任意功能的保证。

脚本写入 `before.txt`、`after.txt`、连续 JPEG 与 `recording.json`；导出脚本写 MP4 和 `.verification.json`。默认拒绝非空帧目录与已存在的输出文件。步骤失败保留诊断记录，不把失败素材导出为成功。作用中的尺寸覆盖会在结束清理；中断后先检查现场，必要时调用 `Page.stopScreencast`／`Emulation.clearDeviceMetricsOverride` 清理自己设置的状态。

## 验证和失败处理

- 本脚本只采集源素材，不自动完成[中央重点、安全区和口播组合](framing-and-layout.md)。采完仍需安排缩放、取景和平移；静态整页、贴顶搜索框或低清局部不能因为脚本返回成功就算成片。
- 检查原始帧与导出尺寸。改变视口后，最初几帧可能仍是旧尺寸；混用会压扁后续内容。先确认稳定的实际源画幅，再重录或保留原始记录、剔除旧视口帧制作修复副本，不能无提示拉伸。时间戳若乱序，只按真实捕获时间整理并保留原顺序记录，不伪造时间或补操作。
- 对照前后状态验证动作真的发生，不能仅看鼠标点击返回。结果异步到达时按实际状态等待，并在最终镜头留阅读时间。
- 导出后看 `.verification.json` 的 `observedFramesPerSecond`、`exportFPS`、时长、大小、视频编码；30fps 导出不等于 30fps 原生捕获。协议在静止页面可能只发变化帧，因此低均值不单独证明丢帧；需查看运动区间。
- 打开成片，抽查首帧、操作前后和最后一秒。快滚动时出现跳帧则降低捕获尺寸、减慢动作或分段重录；不要用假补帧冒充保真。
- 当前指南缺少高层录屏入口时先试 `page.cdp`，已经实测可取帧。不支持时先查可用开源窗口录制方案与系统权限，再按环境选路；不能未经验证就声称某工具可用。
- 需要声音或浏览器外壳时，这个脚本不够。采用经当前环境验证的系统／窗口捕获，涉及系统屏幕共享选择器由用户处理；原音轨必须保留。
- 用户拿走控制权、空间停用或权限界面出现时遵守 Ego 交接规则，不换新空间绕过。完成时按指南清理本任务空间；需要用户登录时保持原空间等用户完成。

登录凭据和快照可能包含个人数据，只放在任务本地过程目录，不进入可分享技能包。


## 原生录制衔接

需要完整窗口、更流畅的连续动作或系统声音时，转读 [Screen Studio 接入](screenstudio-recording.md)。该通路保存原工程与录像分段，不经过本页的 JPEG 帧编码器。
