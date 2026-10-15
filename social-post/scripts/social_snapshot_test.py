"""Owned coherent-read, Unicode, freshness and growing-history controls."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import social_data as query
import social_snapshot as snapshot
from log_outcome import prepare_records
from social_data_feature_matrix_test import _post, _snapshot
from social_store import commit_records, exclusive_store_lock, load_jsonl, store_revision, write_jsonl


def rejects(error, action) -> None:
    try:
        action()
    except error:
        return
    raise AssertionError("negative snapshot control was accepted")


def seed(root: Path) -> None:
    write_jsonl(root / "data/posts.jsonl", [_post()])
    write_jsonl(root / "data/insight_snapshots.jsonl", [
        _snapshot("owned-fb", "facebook", "2026-08-30T10:00:00+08:00", "developing", 100)])


def unicode_controls(root: Path) -> None:
    path = root / "unicode.jsonl"
    records = [{"caption": "甲\u2028乙\u2029丙\u0085丁"}, {"caption": "第二篇\n同一列"}]
    write_jsonl(path, records)
    assert load_jsonl(path) == records
    data = ("\ufeff" + "\r\n".join(json.dumps(x, ensure_ascii=False) for x in records) + "\r\n").encode("utf-8")
    path.write_bytes(data)
    assert load_jsonl(path) == records
    for data in (b"[]\n", b"{bad}\n"):
        path.write_bytes(data)
        rejects(ValueError, lambda: load_jsonl(path))


def reader_controls(root: Path) -> None:
    empty = root / "does-not-exist"
    revision, rows = snapshot.read_store_snapshot(empty)
    assert not empty.exists() and all(not value for value in rows.values()), "read created state"
    digest = hashlib.sha256()
    for name in snapshot.DATA_FILENAMES:
        digest.update(name.encode() + b"\0\0")
    assert revision == digest.hexdigest()
    seed(root)
    calls, original = [], Path.read_bytes
    def counted(path):
        if path.parent == root / "data":
            calls.append(path.name)
        return original(path)
    with patch.object(Path, "read_bytes", counted):
        revision, rows = snapshot.read_store_snapshot(root / "data")
    assert len(calls) == 2 and len(set(calls)) == 2, "ledger was reread"
    assert revision == store_revision(root / "data") and len(rows["posts.jsonl"]) == 1
    lock = root / "data/.write.lock"
    lock.mkdir()
    try:
        rejects(TimeoutError, lambda: snapshot.read_store_snapshot(root / "data", timeout_seconds=0))
    finally:
        lock.rmdir()
    from concurrent.futures import ThreadPoolExecutor
    with exclusive_store_lock(root / "data"):
        assert snapshot.read_store_snapshot(root / "data")[0] == revision, "owner read deadlocked"
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(snapshot.read_store_snapshot, root / "data", timeout_seconds=0)
            rejects(TimeoutError, future.result)


def interleaved_writer(root: Path) -> None:
    seed(root)
    data = root / "data"
    old_revision = store_revision(data)
    new_post = {**_post(), "post_id": "new-owned-post"}
    new_snapshot = _snapshot("new-owned-snapshot", "facebook", "2026-08-30T10:00:00+08:00", "developing", 200,
                             post_id=new_post["post_id"])
    original, triggered = Path.read_bytes, False
    def interleave(path):
        nonlocal triggered
        before = original(path)
        if path == data / "posts.jsonl" and not triggered:
            triggered = True
            commit_records({data / "posts.jsonl": [_post(), new_post],
                            data / "insight_snapshots.jsonl": [new_snapshot]},
                           data_dir=data, expected_revision=old_revision)
        return before
    with patch.object(Path, "read_bytes", interleave):
        revision, records = snapshot.read_store_snapshot(data)
    assert triggered and revision == store_revision(data) and len(records["posts.jsonl"]) == 2
    assert records["insight_snapshots.jsonl"][0]["post_id"] == new_post["post_id"]
    rejects(RuntimeError, lambda: commit_records({data / "posts.jsonl": [_post()]},
                                                 data_dir=data, expected_revision=old_revision))


def query_controls(root: Path) -> None:
    seed(root)
    original, calls = query._validated_store, 0
    def captured(path):
        nonlocal calls
        calls += 1
        result = original(path)
        changed = _snapshot("later", "facebook", "2026-08-30T10:00:00+08:00", "developing", 999)
        write_jsonl(path / "data/insight_snapshots.jsonl", [changed])
        return result
    with patch.object(query, "_validated_store", captured):
        rows = query.feature_matrix(root)
    assert calls == 1 and rows[0]["outcome"]["primary_metrics"]["viewers"] == 100
    assert query.feature_matrix(root)[0]["outcome"]["primary_metrics"]["viewers"] == 999
    for action in (query.feature_coverage_report, query.series_summary):
        seed(root)
        with patch.object(query, "_validated_store", wraps=original) as reader:
            action(root)
        assert reader.call_count == 1, "query combined multiple ledger snapshots"


def baseline_controls(api) -> None:
    posts = [{"analysis_status": "complete"} for _ in range(7)]
    posts.append({"analysis_status": "excluded_placeholder", "analysis_eligible": False})
    result = {"counts": {"posts": 8, "snapshots": 6, "experiments": 3, "account_snapshots": 1}, "posts": posts}
    episodes = [{"episode": n, "platform": "combined", "watch_percent": percent}
                for n, percent in ((1, 61.1), (2, 38.9), (3, 41.1))]
    platforms = [{"platform": name, "watch_seconds": None, "watch_percent": None}
                 for name in ("facebook", "instagram", "youtube")]
    def summary(_root, series):
        return episodes if series == "reborn-married-driver" else platforms
    with patch.object(api, "series_summary", summary):
        api.check_private_baseline(result)
        expanded = copy.deepcopy(result)
        expanded["posts"].append({"analysis_status": "complete"})
        expanded["counts"]["posts"] += 1
        api.check_private_baseline(expanded)
        expanded["posts"][7]["analysis_eligible"] = True
        rejects(AssertionError, lambda: api.check_private_baseline(expanded))
        episodes.pop()
        rejects(AssertionError, lambda: api.check_private_baseline(result))


def run_self_test(api=None) -> None:
    for control in (unicode_controls, reader_controls, interleaved_writer, query_controls):
        with tempfile.TemporaryDirectory(prefix="social-coherent-read-") as raw:
            control(Path(raw))
    if api is not None:
        baseline_controls(api)


if __name__ == "__main__":
    run_self_test()
    print("SOCIAL_SNAPSHOT_TESTS_PASS")
