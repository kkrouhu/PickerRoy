from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np
import pytest

from framepick import exporter
from framepick.models import Candidate, VideoInfo


@pytest.fixture
def source(monkeypatch, tmp_path):
    video = VideoInfo("v", str(tmp_path / "source.mp4"), 2, 12, 10, 24, "h264")
    candidate = Candidate("first-abcde", "v", "shot", 0, 0.5, "unused.jpg")
    image = np.full((10, 12, 3), [43, 98, 136], dtype=np.uint8)

    def fake_export(_video, _time, destination, image_format, _crop):
        extension = ".png" if image_format.upper() == "PNG" else ".jpg"
        ok, data = cv2.imencode(extension, image)
        assert ok
        data.tofile(str(destination))

    monkeypatch.setattr(exporter, "export_frame", fake_export)
    monkeypatch.setattr(exporter, "optimized_export_image", lambda image, *_: image)
    return video, candidate


@pytest.mark.parametrize("optimized", [False, True])
@pytest.mark.parametrize("image_format", ["PNG", "JPEG"])
def test_repeat_export_preserves_existing_bytes_and_numbers_new_file(source, tmp_path, optimized, image_format):
    video, candidate = source
    folder = tmp_path / "exports"
    [first] = exporter.export_candidates(video, [candidate], folder, image_format, optimized)
    first_bytes = first.read_bytes()
    [second] = exporter.export_candidates(video, [candidate], folder, image_format, optimized)
    assert first.name == f"source_0000000500ms_abcde{'_optimized' if optimized else ''}{'.png' if image_format == 'PNG' else '.jpg'}"
    assert second.name == f"{first.stem}_2{first.suffix}"
    assert first.read_bytes() == first_bytes
    assert cv2.imread(str(second)).shape[:2] == (10, 12)
    assert set(folder.iterdir()) == {first, second}


@pytest.mark.parametrize("optimized", [False, True])
def test_candidate_suffix_collision_in_one_batch_is_safe(source, tmp_path, optimized):
    video, first = source
    second = Candidate("different-abcde", "v", "shot", 0, 0.5, "unused.jpg")
    outputs = exporter.export_candidates(video, [first, second], tmp_path / "exports", optimized=optimized)
    assert len(set(outputs)) == 2
    assert all(path.stat().st_size > 0 for path in outputs)


@pytest.mark.parametrize("optimized", [False, True])
def test_concurrent_exports_claim_distinct_names(source, tmp_path, optimized):
    video, candidate = source
    folder = tmp_path / "exports"
    with ThreadPoolExecutor(max_workers=4) as executor:
        jobs = [executor.submit(exporter.export_candidates, video, [candidate], folder, "PNG", optimized)
                for _ in range(8)]
        outputs = [job.result()[0] for job in jobs]
    assert len(set(outputs)) == 8
    assert set(folder.iterdir()) == set(outputs)
    assert all(cv2.imread(str(path)).shape[:2] == (10, 12) for path in outputs)


@pytest.mark.parametrize("optimized", [False, True])
def test_decode_failure_preserves_user_file_and_cleans_temporary_output(source, monkeypatch, tmp_path, optimized):
    video, candidate = source
    folder = tmp_path / "exports"
    [existing] = exporter.export_candidates(video, [candidate], folder, optimized=optimized)
    sentinel = b"existing user data: keep exactly"
    existing.write_bytes(sentinel)
    created = []

    def fail_decode(_video, _time, path, *_):
        created.append(Path(path))
        Path(path).write_bytes(b"partial decode")
        raise RuntimeError("generated decode failure")

    monkeypatch.setattr(exporter, "export_frame", fail_decode)
    with pytest.raises(RuntimeError, match="generated decode failure"):
        exporter.export_candidates(video, [candidate], folder, optimized=optimized)
    assert existing.read_bytes() == sentinel
    assert set(folder.iterdir()) == {existing}
    assert all(not path.exists() for path in created)


def test_enhancement_failure_preserves_user_file_and_cleans_both_temporaries(source, monkeypatch, tmp_path):
    video, candidate = source
    folder = tmp_path / "exports"
    [existing] = exporter.export_candidates(video, [candidate], folder, optimized=True)
    before = existing.read_bytes()
    decoded_paths = []
    original_decode = exporter.export_frame

    def record_decode(_video, _time, path, *args):
        decoded_paths.append(Path(path))
        original_decode(_video, _time, path, *args)

    def fail_enhance(*_):
        raise RuntimeError("generated enhancement failure")

    monkeypatch.setattr(exporter, "export_frame", record_decode)
    monkeypatch.setattr(exporter, "optimized_export_image", fail_enhance)
    with pytest.raises(RuntimeError, match="generated enhancement failure"):
        exporter.export_candidates(video, [candidate], folder, optimized=True)
    assert existing.read_bytes() == before
    assert set(folder.iterdir()) == {existing}
    assert all(not path.exists() for path in decoded_paths)


@pytest.mark.parametrize("optimized", [False, True])
def test_publication_failure_removes_only_its_partial_file(source, monkeypatch, tmp_path, optimized):
    video, candidate = source
    folder = tmp_path / "exports"
    [existing] = exporter.export_candidates(video, [candidate], folder, optimized=optimized)
    before = existing.read_bytes()

    def fail_copy(_source, output):
        output.write(b"partial publication")
        raise OSError("generated full disk")

    monkeypatch.setattr(exporter.shutil, "copyfileobj", fail_copy)
    with pytest.raises(OSError, match="generated full disk"):
        exporter.export_candidates(video, [candidate], folder, optimized=optimized)
    assert existing.read_bytes() == before
    assert set(folder.iterdir()) == {existing}


def test_preexisting_numbered_file_and_symlink_are_not_touched(source, tmp_path):
    video, candidate = source
    folder = tmp_path / "exports"
    folder.mkdir()
    first = folder / "source_0000000500ms_abcde.png"
    target = tmp_path / "unrelated.txt"
    target.write_bytes(b"private user file")
    try:
        first.symlink_to(target)
    except OSError:
        pytest.skip("Symlinks not available on this filesystem")
    numbered = folder / "source_0000000500ms_abcde_2.png"
    numbered.write_bytes(b"another user file")
    [exported] = exporter.export_candidates(video, [candidate], folder)
    assert exported.name == "source_0000000500ms_abcde_3.png"
    assert first.is_symlink()
    assert target.read_bytes() == b"private user file"
    assert numbered.read_bytes() == b"another user file"
