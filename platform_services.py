import json
from pathlib import Path

from runtime_paths import user_data_path
from score_validation import steam_score_value, validate_run_submission


class LocalPlatformServices:
    """Fallback complet pentru rularea jocului fără clientul Steam."""

    platform_name = "LOCAL"
    steam_available = False

    def __init__(self, queue_path=None):
        self.pending_achievements = set()
        self.pending_scores = []
        self.queue_path = (
            Path(queue_path)
            if queue_path is not None
            else user_data_path("platform_queue.json")
        )
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_queue()

    def _load_queue(self):
        try:
            data = json.loads(self.queue_path.read_text(encoding="utf-8"))
            self.pending_achievements = set(
                value
                for value in data.get("achievements", [])
                if isinstance(value, str)
            )
            self.pending_scores = [
                entry
                for entry in data.get("scores", [])
                if isinstance(entry, dict)
            ][-25:]
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            self.pending_achievements = set()
            self.pending_scores = []

    def _save_queue(self):
        payload = {
            "achievements": sorted(self.pending_achievements),
            "scores": self.pending_scores[-25:],
        }
        temporary_path = Path(str(self.queue_path) + ".tmp")
        temporary_path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(self.queue_path)

    def update(self):
        return None

    def shutdown(self):
        return None

    def unlock_achievement(self, achievement_id):
        self.pending_achievements.add(str(achievement_id))
        self._save_queue()
        return False

    def submit_score(self, score, details=None):
        details = details if isinstance(details, dict) else {}
        is_valid, validation_reason = validate_run_submission(score, details)
        if not is_valid:
            return False
        self.pending_scores.append(
            {
                "score": max(0, int(score)),
                "steam_score": steam_score_value(score),
                "details": details,
                "validation": validation_reason,
            }
        )
        self._save_queue()
        return False

    def cloud_file(self, filename):
        return user_data_path(filename)


class SteamPlatformServices(LocalPlatformServices):
    platform_name = "STEAM"
    steam_available = True

    def __init__(self, bridge):
        self.bridge = bridge
        super().__init__()
        self._flush_pending_operations()

    def _bridge_call(self, method_name, *args, default=False):
        try:
            return getattr(self.bridge, method_name)(*args)
        except (OSError, RuntimeError, TypeError, ValueError, AttributeError):
            return default

    def _flush_pending_operations(self):
        for achievement_id in list(self.pending_achievements):
            if self._bridge_call("set_achievement", achievement_id):
                self.pending_achievements.discard(achievement_id)

        remaining_scores = []
        for entry in self.pending_scores:
            details = entry.get("details", {})
            is_valid, _reason = validate_run_submission(
                entry.get("score", 0),
                details,
            )
            if not is_valid:
                continue
            score_details = [
                int(details.get("stage", 1)),
                int(details.get("wave", 1)),
                int(details.get("best_combo", 0)),
                int(details.get("best_graze", 0)),
                int(details.get("duration_seconds", 0)),
            ]
            uploaded = self._bridge_call(
                "upload_score",
                "GLOBAL_SCORE",
                steam_score_value(entry.get("score", 0)),
                score_details,
            )
            if not uploaded:
                remaining_scores.append(entry)
        self.pending_scores = remaining_scores
        self._save_queue()

    def update(self):
        self._bridge_call("run_callbacks", default=None)

    def shutdown(self):
        self._bridge_call("shutdown", default=None)

    def unlock_achievement(self, achievement_id):
        if self._bridge_call("set_achievement", str(achievement_id)):
            self.pending_achievements.discard(str(achievement_id))
            self._save_queue()
            return True
        return super().unlock_achievement(achievement_id)

    def submit_score(self, score, details=None):
        details = details if isinstance(details, dict) else {}
        is_valid, _reason = validate_run_submission(score, details)
        if not is_valid:
            return False

        score_details = [
            int(details.get("stage", 1)),
            int(details.get("wave", 1)),
            int(details.get("best_combo", 0)),
            int(details.get("best_graze", 0)),
            int(details.get("duration_seconds", 0)),
        ]
        if self._bridge_call(
            "upload_score",
            "GLOBAL_SCORE",
            steam_score_value(score),
            score_details,
        ):
            return True
        return super().submit_score(score, details)


def create_platform_services():
    # Bridge-ul nativ este adăugat după primirea AppID-ului și SDK-ului din
    # Steamworks. Interfața jocului rămâne neschimbată, iar fallback-ul
    # păstrează operațiile local până atunci.
    try:
        from steam_bridge import SteamBridge

        bridge = SteamBridge()
        if bridge.initialize():
            return SteamPlatformServices(bridge)
    except (
        ImportError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
        AttributeError,
    ):
        pass
    return LocalPlatformServices()
