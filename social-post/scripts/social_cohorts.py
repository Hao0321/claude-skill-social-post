"""Pure platform/media/ownership boundaries; never infer a viral ranking."""

from __future__ import annotations

from collections import Counter
from typing import Any

MEDIA_FAMILIES = ("text_image", "video")
OWN = "own"
EXTERNAL = "external"
VIDEO_SURFACES = frozenset({"reel_caption", "shorts_caption", "short_video_caption", "video_caption", "youtube_description"})
TEXT_SURFACES = frozenset({"background_text", "background_text_post", "facebook_background_text", "plain_text", "text_post",
                           "photo_caption", "image_caption", "carousel_caption"})
VIDEO_TYPES = frozenset({"ai_short_drama", "beyblade_short_video", "reel", "short", "video", "long_video"})
TEXT_TYPES = frozenset({"background_text_post", "text_post", "image_post", "photo_post", "carousel"})


def media_family(post: dict[str, Any]) -> str:
    """Known evidence only; conflicting/unknown declarations stay quarantined."""
    declared = post.get("media_family")
    if declared is not None and declared not in MEDIA_FAMILIES:
        raise ValueError("unknown media family")
    surface = post.get("format_features", {}).get("surface")
    content = post.get("content_type")
    signals = set()
    if surface in VIDEO_SURFACES or content in VIDEO_TYPES:
        signals.add("video")
    if surface in TEXT_SURFACES or content in TEXT_TYPES:
        signals.add("text_image")
    if declared:
        signals.add(declared)
    return next(iter(signals)) if len(signals) == 1 else "unknown"


def owner_scope(post: dict[str, Any]) -> str:
    value = post.get("owner_scope", OWN)
    if value in {EXTERNAL, "third_party_reference_not_hao_account"}:
        return EXTERNAL
    return OWN if value == OWN else "unknown"


def cohort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (row.get("owner_scope"), row.get("platform"), row.get("media_family"),
            row.get("content_type"), row.get("layout", {}).get("surface"), row.get("maturity"))


def channel_inventory(rows: list[dict[str, Any]], platforms: tuple[str, ...]) -> dict[str, Any]:
    """List independent learning partitions without averaging unlike metrics."""
    channels = []
    for platform in platforms:
        for family in MEDIA_FAMILIES:
            selected = [row for row in rows if row.get("owner_scope") == OWN
                        and row.get("platform") == platform and row.get("media_family") == family]
            counts = Counter((row.get("content_type"), row.get("layout", {}).get("surface"),
                              row.get("maturity")) for row in selected)
            channels.append({"platform": platform, "media_family": family, "owner_scope": OWN,
                             "post_count": len({row["post_id"] for row in selected}),
                             "snapshot_rows": len(selected),
                             "cohorts": [{"content_type": key[0], "surface": key[1],
                                          "maturity": key[2], "rows": count}
                                         for key, count in sorted(counts.items(), key=lambda item: str(item[0]))],
                             "video_metrics_applicable": family == "video"})
    return {"channels": channels,
            "quarantined_rows": sum(row.get("platform") not in platforms
                                    or row.get("media_family") == "unknown"
                                    or row.get("owner_scope") != OWN for row in rows),
            "cross_channel_ranking": False, "automatic_rule_update": False}
