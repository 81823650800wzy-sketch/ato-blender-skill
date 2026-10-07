"""Probe, fully decode and contact-sheet an encoded output; not a visual approval."""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('video', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--expected-seconds', type=float)
    p.add_argument('--expected-frames', type=int)
    a = p.parse_args()
    probe = subprocess.run(['ffprobe','-v','error','-count_frames','-show_streams',
                            '-show_format','-of','json',str(a.video)], check=True,
                           capture_output=True, text=True)
    data = json.loads(probe.stdout)
    video = next(s for s in data['streams'] if s['codec_type']=='video')
    duration = float(video.get('duration', data['format']['duration']))
    rate = video['avg_frame_rate'].split('/')
    fps = float(rate[0])/float(rate[1])
    issues = []
    if a.expected_seconds is not None and abs(duration-a.expected_seconds)>max(.03,1/fps):
        issues.append('Duration differs from requested range')
    if a.expected_frames is not None and int(video['nb_read_frames']) != a.expected_frames:
        issues.append('Decoded frame count differs')
    decode = subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(a.video),'-f','null','-'],
                            capture_output=True, text=True)
    if decode.returncode: issues.append('Full decode failed: '+decode.stderr)
    a.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        pattern = str(Path(temp)/'%03d.png')
        subprocess.run(['ffmpeg','-v','error','-i',str(a.video),'-vf',
                        f'fps={12/max(duration,.001)},scale=320:-1','-frames:v','12',pattern],check=True)
        paths = sorted(Path(temp).glob('*.png'))
        height = Image.open(paths[0]).height
        sheet = Image.new('RGB',(320*4,(height+24)*3),'#171923')
        draw = ImageDraw.Draw(sheet)
        for i,path in enumerate(paths):
            x,y=(i%4)*320,(i//4)*(height+24)
            with Image.open(path) as frame: sheet.paste(frame,(x,y))
            draw.text((x+4,y+height+3),f'sample {i+1}',fill='white')
        sheet.save(a.out/'encoded_contact.jpg',quality=92)
    report={'probe':data,'full_decode_passed':decode.returncode==0,'issues':issues,
            'visual_approval':False,'audio_sync_verified':False}
    (a.out/'media_review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'duration':duration,'fps':fps,'issues':issues}))
    raise SystemExit(1 if issues else 0)


if __name__ == '__main__': main()
