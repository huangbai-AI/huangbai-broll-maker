#!/usr/bin/env python3
"""按真实时间戳合成 Ego 连续帧；不会把采样帧率伪称为原生 30fps。"""
import argparse,json,subprocess,math,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('capture_dir',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
d=a.capture_dir.resolve();meta=json.loads((d/'recording.json').read_text());frames=meta['frames']
if meta.get('mode') not in ['ego-tab-screencast','code-motion-sampled']:raise SystemExit('未知素材模式，拒绝误标来源')
if not meta.get('complete'):raise SystemExit('录屏步骤未完整完成，请检查 recording.json；不导出失败片段')
if len(frames)<2:raise SystemExit('连续帧不足')
if a.output.exists():raise SystemExit('输出文件已存在，请换新文件名')
ts=[f['timestamp'] for f in frames]
if any(not isinstance(t,(float,int)) or not math.isfinite(t) for t in ts) or any(b<a for a,b in zip(ts,ts[1:])):raise SystemExit('录屏时间戳无效')
duration=meta['requestedDuration'];offsets=[t-ts[0] for t in ts]
lines=['ffconcat version 1.0']
for i,f in enumerate(frames):
 name=f['file']
 if not re.fullmatch(r'frame-\d{6}\.jpg',name) or not (d/name).is_file():raise SystemExit('帧文件名或路径无效')
 end=offsets[i+1] if i+1<len(frames) else duration
 delta=max(1/1000,end-offsets[i]);lines += [f"file '{name}'",f'duration {delta:.9f}']
lines += [f"file '{frames[-1]['file']}'"]
concat=d/'frames.ffconcat';concat.write_text('\n'.join(lines)+'\n')
a.output.parent.mkdir(parents=True,exist_ok=True)
inputs=['-safe','1','-f','concat','-i',str(concat)]
if meta.get('mode')=='code-motion-sampled':
 fps=meta.get('fps')
 if fps not in [24,25,30,50,60] or len(frames)!=math.ceil(duration*fps):raise SystemExit('动效帧序列不完整')
 if [f['file'] for f in frames]!=[f'frame-{i:06d}.jpg' for i in range(len(frames))]:raise SystemExit('动效帧必须按连续编号排序')
 inputs=['-framerate',str(fps),'-i',str(d/'frame-%06d.jpg')]
export_fps=meta.get('fps',30) if meta.get('mode')=='code-motion-sampled' else 30
subprocess.run(['ffmpeg','-v','error','-n',*inputs,'-t',str(duration),'-vf','scale=trunc(iw/2)*2:trunc(ih/2)*2:in_range=pc:out_range=tv:in_color_matrix=bt601:out_color_matrix=bt709,format=yuv420p,tpad=stop_mode=clone:stop_duration=45,fps='+str(export_fps), '-color_range','tv','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-c:v','libx264','-threads','4','-crf','18','-preset','medium','-pix_fmt','yuv420p','-movflags','+faststart',str(a.output)],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(a.output)]))
actualDuration=float(probe['format']['duration'])
if abs(actualDuration-duration)>.1:raise SystemExit(f'导出时长不一致：预期 {duration}，实际 {actualDuration}')
report={'output':str(a.output.resolve()),'capturedFrames':len(frames),'observedFramesPerSecond':round((len(frames)-1)/max(.001,offsets[-1]),2),'exportFPS':export_fps,'mode':meta.get('mode','unknown'),'audio':False,'probe':probe}
a.output.with_suffix('.verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='probe'},ensure_ascii=False))
