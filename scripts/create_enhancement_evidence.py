"""Create same-frame evidence through PickerRoy's shipping export path.

Outputs may contain private footage. Keep them local until publishing rights are
confirmed. Never copy this output directory into a public release automatically.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFont
from framepick import __version__
from framepick.exporter import export_candidates
from framepick.media import probe_video
from framepick.models import Candidate
from framepick.quality import enhancement_diagnostics


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('video', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--times', required=True, help='Comma-separated seconds, 4 to 6 frames')
    args = parser.parse_args()
    seconds = [float(value) for value in args.times.split(',')]
    if not 4 <= len(seconds) <= 6:
        parser.error('Choose 4 to 6 frames')
    out = args.output.resolve()
    if out.exists():
        parser.error('Use a new evidence directory to preserve earlier comparisons')
    out.mkdir(parents=True)
    source = args.video.resolve()
    video = probe_video(source)
    records = []
    font_path = '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
    title_font = ImageFont.truetype(font_path, 34)
    small_font = ImageFont.truetype(font_path, 23)
    for index, second in enumerate(seconds, 1):
        if second < 0 or second >= video.duration:
            raise ValueError('Frame timestamp lies outside the source video')
        candidate = Candidate(id=f'evidence_f{index:04}', video_id=video.id, shot_id='evidence',
                              shot_index=index, timestamp=second, preview_path='', labels=['Landscape'])
        start = time.perf_counter()
        original = export_candidates(video, [candidate], out/'original', 'PNG')[0]
        original_seconds = time.perf_counter()-start
        start = time.perf_counter()
        enhanced = export_candidates(video, [candidate], out/'enhanced', 'PNG', optimized=True)[0]
        enhanced_seconds = time.perf_counter()-start
        before = cv2.imread(str(original))
        after = cv2.imread(str(enhanced))
        assert before.shape == after.shape, 'Enhancement must not change output dimensions'
        diagnostics = enhancement_diagnostics(before)
        comparison = out / f'comparison-{index:02}.jpg'
        board = Image.new('RGB', (2048, 910), '#f5f5f3')
        draw = ImageDraw.Draw(board)
        draw.text((40, 25), '原画质导出', font=title_font, fill='#181b19')
        draw.text((1056, 25), '增强画质', font=title_font, fill='#181b19')
        for column, file in enumerate([original, enhanced]):
            with Image.open(file) as image:
                image.thumbnail((972, 735), Image.Resampling.LANCZOS)
                x = 28 + column*1020 + (972-image.width)//2
                board.paste(image, (x, 100+(735-image.height)//2))
        draw.text((40, 856), f'{index:02} / {second:.2f}s · 同一帧  同一尺寸 {before.shape[1]} × {before.shape[0]} · 本地实际导出',
                  font=small_font, fill='#616960')
        board.save(comparison, quality=96, subsampling=0)
        records.append({'index': index, 'requested_second': second, 'width':before.shape[1], 'height':before.shape[0],
                        'original':str(original.relative_to(out)), 'enhanced':str(enhanced.relative_to(out)),
                        'comparison':comparison.name, 'original_sha256':sha(original), 'enhanced_sha256':sha(enhanced),
                        'original_export_seconds':round(original_seconds,3), 'enhanced_export_seconds':round(enhanced_seconds,3),
                        'mean_absolute_channel_difference':round(float(cv2.absdiff(before, after).mean()),3),
                        'diagnostics':diagnostics})
        print(json.dumps(records[-1], ensure_ascii=False), flush=True)
    manifest = {'app_version':__version__, 'source_file':str(source), 'source_sha256':sha(source),
                'privacy':'LOCAL ONLY — publishing rights not yet confirmed',
                'method':'Both PNGs use export_candidates at the same requested timestamp and original crop. '
                         'Only the enhanced path applies optimized_export_image. Presentation boards resize both identically.',
                'frames':records}
    (out/'evidence-manifest-private.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
