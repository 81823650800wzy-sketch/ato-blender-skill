"""Export timed reference frames and mixed-audio features; not aesthetic approval."""
import argparse, csv, io, json, math, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

def run(args):
    result = subprocess.run(args, capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', errors='replace')[-3000:])
    return result.stdout

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('video', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--start', type=float, default=0)
    p.add_argument('--end', type=float)
    p.add_argument('--sample-fps', type=float, default=2)
    p.add_argument('--audio', action='store_true')
    args = p.parse_args()
    probe = json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(args.video)]))
    duration = float(probe['format']['duration'])
    end = duration if args.end is None else args.end
    if not all(math.isfinite(x) for x in [args.start,end,args.sample_fps]):
        p.error('Times and sampling rate must be finite')
    if not (0 <= args.start < end <= duration and 0 < args.sample_fps <= 120):
        p.error('Require 0 <= start < end <= duration and 0 < sample-fps <= 120')
    times = np.arange(args.start,end,1/args.sample_fps)
    if len(times)>600:
        p.error('Over 600 samples: split into windows or lower sample-fps')
    args.out.mkdir(parents=True,exist_ok=False)
    sheets=[]
    for page in range(0,len(times),16):
        chosen=times[page:page+16]
        sheet=Image.new('RGB',(1280,208*math.ceil(len(chosen)/4)),'#181818')
        draw=ImageDraw.Draw(sheet)
        for j,t in enumerate(chosen):
            data=run(['ffmpeg','-v','error','-ss',f'{t:.6f}','-i',str(args.video),'-frames:v','1',
                      '-vf','scale=320:180:force_original_aspect_ratio=decrease','-threads','1',
                      '-f','image2pipe','-vcodec','png','-'])
            with Image.open(io.BytesIO(data)) as im:
                x,y=(j%4)*320,(j//4)*208
                sheet.paste(im,(x+(320-im.width)//2,y+25+(180-im.height)//2))
                draw.text((x+5,y+5),f'target {t:.4f}s',fill='white')
        name=f'frames_{page//16+1:03d}.jpg'
        sheet.save(args.out/name,quality=93); sheets.append(name)
    aud={'available':any(s['codec_type']=='audio' for s in probe['streams'])}
    if args.audio and aud['available']:
        wav=args.out/'mixed_audio.wav'
        run(['ffmpeg','-v','error','-ss',str(args.start),'-i',str(args.video),'-t',str(end-args.start),
             '-vn','-ac','1','-ar','16000','-c:a','pcm_s16le',str(wav)])
        with wave.open(str(wav),'rb') as f:
            sr=f.getframerate()
            a=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(np.float64)/32768
        hop,size=160,512; freq=np.fft.rfftfreq(size,1/sr); prev=np.zeros(size//2+1)
        with (args.out/'audio_features.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f)
            writer.writerow(['source_seconds','rms','positive_flux_0_200Hz','positive_flux_200_2000Hz','positive_flux_2000_8000Hz'])
            for pos in range(0,max(0,len(a)-size+1),hop):
                chunk=a[pos:pos+size]; spec=abs(np.fft.rfft(chunk*np.hanning(size)))
                flux=np.maximum(spec-prev,0);prev=spec
                bands=[float(flux[(freq>=lo)&(freq<hi)].sum()) for lo,hi in [(0,200),(200,2000),(2000,8001)]]
                writer.writerow([round(args.start+(pos+size/2)/sr,6),float(np.sqrt(np.mean(chunk*chunk))),*bands])
        aud.update({'file':wav.name,'features':'audio_features.csv',
                    'note':'Mixed-track energy/flux only; no beat/SFX identity or listening approval.'})
    report={'source':str(args.video.resolve()),'source_probe':probe,'window':[args.start,end],
            'sample_fps':args.sample_fps,'requested_sample_times':times.tolist(),'contact_sheets':sheets,
            'frame_note':'Timestamp-targeted samples, not all source frames or exact VFR frame indices.',
            'audio':aud,'visual_approval':False,'listening_verified':False}
    (args.out/'evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'samples':len(times),'sheets':len(sheets),'audio':aud},ensure_ascii=False))

if __name__=='__main__': main()
