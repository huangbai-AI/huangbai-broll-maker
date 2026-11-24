/** 把本技能式 renderAt(t) 页面逐帧采样。它是代码动效导出，不是真实操作录屏。 */
import fs from 'node:fs/promises';
import path from 'node:path';
export async function renderMotion(config,api){
 const {spaceId,pageLabel,outputDir,width=2160,height=3840,duration=8,fps=30}=config;
 if(!Number.isInteger(spaceId)||!pageLabel||!path.isAbsolute(outputDir))throw Error('需要现有空间、页面和绝对目录');
 if(!(duration>0&&duration<=45)||![24,25,30,50,60].includes(fps)||!Number.isInteger(width)||!Number.isInteger(height)||width<320||height<320)throw Error('时长、帧率或尺寸无效');
 await fs.mkdir(outputDir,{recursive:true});if((await fs.readdir(outputDir)).length)throw Error('输出目录非空，请使用新目录');
 const task=await api.taskSpace(spaceId),page=task.page(pageLabel);
 if(!await page.evaluate(()=>typeof window.renderAt==='function'))throw Error('这不是支持 renderAt(t) 的自有代码动效页面，请勿将真实网站冒充动效采样');
 let changed=false;const frames=[];
 try{
  await page.cdp('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});changed=true;
  await page.evaluate(async()=>{window.previewPlaying=false;if(window.__ready)await window.__ready;await document.fonts.ready});
  const count=Math.ceil(duration*fps);
  for(let i=0;i<count;i++){
   await page.evaluate(t=>window.renderAt(t),i/fps);
   const shot=await page.cdp('Page.captureScreenshot',{format:'jpeg',quality:95,fromSurface:true,captureBeyondViewport:false});
   const file=`frame-${String(i).padStart(6,'0')}.jpg`;
   await fs.writeFile(path.join(outputDir,file),Buffer.from(shot.data,'base64'));
   frames.push({file,timestamp:i/fps});
  }
 }finally{if(changed)await page.cdp('Emulation.clearDeviceMetricsOverride').catch(()=>{});}
 const meta={mode:'code-motion-sampled',width,height,requestedDuration:duration,fps,audio:false,complete:true,frames};
 await fs.writeFile(path.join(outputDir,'recording.json'),JSON.stringify(meta,null,2));
 console.log(JSON.stringify({outputDir,frames:frames.length,seconds:duration,fps,mode:meta.mode}));return meta;
}
