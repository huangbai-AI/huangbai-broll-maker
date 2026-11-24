/** 在现有 Ego Lite 页面中记录连续画面。由 ego-browser nodejs 导入。 */
import fs from 'node:fs/promises';
import path from 'node:path';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
export async function record(config, api) {
  const {spaceId, pageLabel, outputDir, duration=8, width=1920, height=1080, quality=90, actions=[]} = config;
  if (!Number.isInteger(spaceId) || !pageLabel || !path.isAbsolute(outputDir)) throw Error('需要现有空间编号、页面标签、绝对输出目录');
  if (!(duration > 0 && duration <= 45) || !Number.isInteger(width) || !Number.isInteger(height) || width<320 || height<320) throw Error('单次录制需在 0–45 秒，画面宽高至少 320');
  for (const a of actions) if (!Number.isFinite(a.at) || a.at<0 || a.at>=duration || !['click','fill','press','move','wheel','waitForSelector'].includes(a.type)) throw Error('无效的动作或动作时间');
  await fs.mkdir(outputDir, {recursive:true});
  if ((await fs.readdir(outputDir)).length) throw Error('输出目录非空，请使用新目录，防止混入旧帧');
  const task = await api.taskSpace(spaceId), page = task.page(pageLabel);
  const before = await page.snapshot();
  await fs.writeFile(path.join(outputDir,'before.txt'),before);
  const originalMetrics = await page.cdp('Page.getLayoutMetrics');
  const eventsLog = [], frames = [];
  let actionError, pumpError, started=false, metricsChanged=false;
  const runAction = async a => {
    switch(a.type) {
      case 'click': return page.click(a.selector,{label:a.label||'执行演示步骤'});
      case 'fill': return page.fill(a.selector,a.text);
      case 'press': return page.press(a.selector,a.key);
      case 'move': return page.mouse.move(a.x,a.y,{label:a.label||'移向演示目标'});
      case 'wheel': return page.mouse.wheel(a.dx||0,a.dy||0,{label:a.label||'滚动查看内容'});
      case 'waitForSelector': return page.waitForSelector(a.selector,{state:'visible',timeout:Math.min(a.timeout||5000,10000)});
    }
  };
  const drain = async () => {
    const es = await page.events();
    for (const e of es) if(e.method==='Page.screencastFrame') {
      const p=e.params, name=`frame-${String(frames.length).padStart(6,'0')}.jpg`;
      // 先确认接收，避免浏览器因积压停止发帧。
      await page.cdp('Page.screencastFrameAck',{sessionId:p.sessionId});
      await fs.writeFile(path.join(outputDir,name),Buffer.from(p.data,'base64'));
      frames.push({file:name,timestamp:p.metadata.timestamp,receivedAt:Date.now()});
    }
  };
  let clockStart;
  try {
    await page.cdp('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});metricsChanged=true;
    await page.cdp('Page.bringToFront');
    await page.events();
    await page.cdp('Page.startScreencast',{format:'jpeg',quality,maxWidth:width,maxHeight:height,everyNthFrame:1});started=true;
    clockStart=Date.now();
    const pump=(async()=>{try {while(Date.now()-clockStart<duration*1000){await drain();await sleep(12);}} catch(e){pumpError=e;}})();
    const act=(async()=>{try {for(const a of [...actions].sort((a,b)=>a.at-b.at)){
      const wait=clockStart+a.at*1000-Date.now();if(wait>0)await sleep(wait);
      if(Date.now()-clockStart>=duration*1000)throw Error('动作执行超过录制时长，请缩短动作或拆段');
      await runAction(a);if(Date.now()-clockStart>duration*1000)throw Error('最后动作超出录制区间，请延长该段或拆分');eventsLog.push({...a,actualAt:(Date.now()-clockStart)/1000});
    }}catch(e){actionError=e;}})();
    await Promise.all([pump,act]);
    await page.cdp('Page.stopScreencast');started=false;
    await drain();
    await fs.writeFile(path.join(outputDir,'after.txt'),await page.snapshot());
  } finally {
    if(started)await page.cdp('Page.stopScreencast').catch(()=>{});
    if(metricsChanged)await page.cdp('Emulation.clearDeviceMetricsOverride').catch(()=>{});
  }
  const meta={mode:'ego-tab-screencast',requestedDuration:duration,width,height,audio:false,frames,actions:eventsLog,
    originalViewport:originalMetrics.cssLayoutViewport,complete:!actionError&&!pumpError,error:String(actionError||pumpError||'')};
  await fs.writeFile(path.join(outputDir,'recording.json'),JSON.stringify(meta,null,2));
  if(actionError||pumpError)throw actionError||pumpError;
  if(frames.length<2)throw Error('未取得连续画面，保留现场；不能用单张截图冒充录屏');
  console.log(JSON.stringify({outputDir,frames:frames.length,seconds:duration,audio:false,status:'captured'}));
  return meta;
}
