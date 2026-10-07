# Validation

Validated 2026-10-07 on Windows, Python 3.12, Blender 4.5.10 LTS.

- Skill frontmatter validation: passed (Python UTF-8 mode).
- Python source compilation: passed.
- `python scripts/test_contours.py`: 7 tests passed.
- Blender bridge: imported synthetic camera/phone poses and RGBA assets; saved relative image paths and rendered a 320×180 frame. Preview inspected for left/right widget placement.
- Media helper: a synthetic 1-second 24-fps H.264/AAC clip fully decoded; 24 video frames, duration 1.0 seconds, encoded contact sheet and JSON report generated.

These tests verify helper behavior and compatibility. They do not certify automatic semantic segmentation, real footage calibration, music sync, or final visual quality. No user media is included in the fixtures or repository.
