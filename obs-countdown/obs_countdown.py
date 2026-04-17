"""
OBS Countdown Script
Reads a target datetime or duration from a file and displays a live countdown
in a Text (GDI+/FreeType2) source.

File format (countdown.txt):
    TARGET: YYYY-MM-DD HH:MM:SS
  OR
    DURATION: HH:MM:SS  (sets countdown from now when file is written)
"""

import obspython as obs
import os
from datetime import datetime

# ── Script state ─────────────────────────────────────────────────────────────
_source_name = ""
_file_path = ""
_done_text = "LIVE!"
_fmt = "short"         # "short" → HH:MM:SS, "long" → Xd Xh Xm Xs
_timer_active = False


# ── Core logic ────────────────────────────────────────────────────────────────
def _read_target() -> datetime | None:
    """Parse countdown.txt and return the target datetime, or None on error."""
    path = _file_path.strip()
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "r") as fh:
            for raw in fh:
                line = raw.strip()
                if line.startswith("#") or not line:
                    continue
                if line.upper().startswith("TARGET:"):
                    val = line.split(":", 1)[1].strip()
                    return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    return None


def _format_delta(total_seconds: float) -> str:
    if total_seconds <= 0:
        return _done_text

    secs = int(total_seconds)
    days, rem = divmod(secs, 86400)
    hours, rem = divmod(rem, 3600)
    mins, secs = divmod(rem, 60)

    if _fmt == "long":
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours or days:
            parts.append(f"{hours}h")
        if mins or hours or days:
            parts.append(f"{mins}m")
        parts.append(f"{secs}s")
        return " ".join(parts)

    # short: always HH:MM:SS (or D:HH:MM:SS when ≥1 day)
    if days:
        return f"{days}:{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{hours:02d}:{mins:02d}:{secs:02d}"


def _set_source_text(text: str):
    source = obs.obs_get_source_by_name(_source_name)
    if source is None:
        return
    settings = obs.obs_data_create()
    obs.obs_data_set_string(settings, "text", text)
    obs.obs_source_update(source, settings)
    obs.obs_data_release(settings)
    obs.obs_source_release(source)


def _tick(_):
    target = _read_target()
    if target is None:
        _set_source_text("—")
        return
    delta = (target - datetime.now()).total_seconds()
    _set_source_text(_format_delta(delta))


# ── OBS script API ────────────────────────────────────────────────────────────
def script_description():
    return (
        "<b>OBS Countdown</b><br>"
        "Displays a live countdown in a Text source by reading a target time "
        "from a plain-text file on disk.<br><br>"
        "File format:<br>"
        "<code>TARGET: YYYY-MM-DD HH:MM:SS</code>"
    )


def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_path(
        props, "file_path", "Countdown file",
        obs.OBS_PATH_FILE, "*.txt", None
    )

    src = obs.obs_properties_add_list(
        props, "source_name", "Text source",
        obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING
    )
    sources = obs.obs_enum_sources()
    if sources:
        for s in sources:
            if obs.obs_source_get_unversioned_id(s) in (
                "text_gdiplus", "text_ft2_source"
            ):
                obs.obs_property_list_add_string(
                    src,
                    obs.obs_source_get_name(s),
                    obs.obs_source_get_name(s),
                )
        obs.source_list_release(sources)

    obs.obs_properties_add_text(
        props, "done_text", "Text when finished", obs.OBS_TEXT_DEFAULT
    )
    fmt = obs.obs_properties_add_list(
        props, "fmt", "Display format",
        obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING
    )
    obs.obs_property_list_add_string(fmt, "Short  (HH:MM:SS)", "short")
    obs.obs_property_list_add_string(fmt, "Long   (Xd Xh Xm Xs)", "long")
    return props


def script_defaults(settings):
    obs.obs_data_set_default_string(settings, "done_text", "LIVE!")
    obs.obs_data_set_default_string(settings, "fmt", "short")


def script_update(settings):
    global _source_name, _file_path, _done_text, _fmt, _timer_active

    _source_name = obs.obs_data_get_string(settings, "source_name")
    _file_path   = obs.obs_data_get_string(settings, "file_path")
    _done_text   = obs.obs_data_get_string(settings, "done_text") or "LIVE!"
    _fmt         = obs.obs_data_get_string(settings, "fmt") or "short"

    if _timer_active:
        obs.timer_remove(_tick)

    if _source_name and _file_path:
        obs.timer_add(_tick, 1000)
        _timer_active = True
    else:
        _timer_active = False


def script_unload():
    if _timer_active:
        obs.timer_remove(_tick)
