import json
from copy import deepcopy
from pathlib import Path

from runtime_paths import user_data_path


# Valorile folosite atunci când jocul este pornit pentru prima dată.
DEFAULT_SAVE_DATA = {
    "intro_completed": False,
    "tutorial_completed": False,
    "current_scene": "planet",
    "checkpoint": 0,
    "campaign_score": 0,
    "highest_score": 0,
    "music_volume": 0.5,
    "sound_volume": 1.0,
    "fullscreen": False,
    "resolution": [1280, 720],
    "unlocked_achievements": [],
}

PROGRESS_KEYS = (
    "intro_completed",
    "tutorial_completed",
    "current_scene",
    "checkpoint",
    "campaign_score",
    "highest_score",
    "unlocked_achievements",
)
SETTINGS_KEYS = (
    "music_volume",
    "sound_volume",
    "fullscreen",
    "resolution",
)


# Clasa responsabilă de încărcarea și salvarea progresului jucătorului.
class SaveManager:

    # Stabilește locația fișierului save.json și încarcă progresul existent.
    def __init__(self, save_path=None, settings_path=None):
        if save_path is None:
            save_path = user_data_path("save.json")

        self.save_path = Path(save_path)
        self.settings_path = (
            Path(settings_path)
            if settings_path is not None
            else self.save_path.with_name("settings.json")
        )
        self.data = self.load()

    # Creează o copie nouă a valorilor implicite.
    # deepcopy împiedică modificarea accidentală a dicționarului original.
    @staticmethod
    def _default_data():
        return deepcopy(DEFAULT_SAVE_DATA)

    # Încarcă salvarea existentă.
    # Dacă fișierul lipsește, este gol sau este corupt, creează unul nou.
    def load(self):
        loaded_progress = self._read_data_file(self.save_path)
        if loaded_progress is None:
            loaded_progress = {}

        loaded_settings = self._read_data_file(self.settings_path)
        if loaded_settings is None:
            # Migrează transparent setările din vechiul save.json combinat.
            loaded_settings = {
                key: loaded_progress[key]
                for key in SETTINGS_KEYS
                if key in loaded_progress
            }

        complete_data = self._default_data()
        complete_data.update(loaded_progress)
        complete_data.update(loaded_settings)

        complete_data = self._validate_data(complete_data)
        self._write_split_data(complete_data)
        return complete_data

    @staticmethod
    def _read_data_file(path):
        try:
            with path.open("r", encoding="utf-8") as data_file:
                loaded_data = json.load(data_file)
            if isinstance(loaded_data, dict):
                return loaded_data
        except (json.JSONDecodeError, OSError, ValueError):
            pass
        return None

    # Verifică valorile citite, pentru ca o salvare greșită să nu strice jocul.
    def _validate_data(self, data):
        validated_data = self._default_data()

        if isinstance(data.get("intro_completed"), bool):
            validated_data["intro_completed"] = data[
                "intro_completed"
            ]

        if isinstance(data.get("current_scene"), str):
            validated_data["current_scene"] = data[
                "current_scene"
            ]

        checkpoint = data.get("checkpoint")
        if isinstance(checkpoint, int) and checkpoint >= 0:
            validated_data["checkpoint"] = checkpoint

        campaign_score = data.get("campaign_score")
        if (
            isinstance(campaign_score, int)
            and campaign_score >= 0
        ):
            validated_data["campaign_score"] = campaign_score

        highest_score = data.get("highest_score")
        if (
            isinstance(highest_score, int)
            and highest_score >= 0
        ):
            validated_data["highest_score"] = highest_score

        music_volume = data.get("music_volume")
        if isinstance(music_volume, (int, float)):
            validated_data["music_volume"] = max(
                0.0,
                min(1.0, float(music_volume)),
            )

        sound_volume = data.get("sound_volume")
        if isinstance(sound_volume, (int, float)):
            validated_data["sound_volume"] = max(
                0.0,
                min(1.0, float(sound_volume)),
            )

        if isinstance(data.get("fullscreen"), bool):
            validated_data["fullscreen"] = data["fullscreen"]

        resolution = data.get("resolution")
        if (
            isinstance(resolution, (list, tuple))
            and len(resolution) == 2
            and all(isinstance(value, int) for value in resolution)
            and 800 <= resolution[0] <= 7680
            and 450 <= resolution[1] <= 4320
        ):
            validated_data["resolution"] = [
                resolution[0],
                resolution[1],
            ]

        if isinstance(data.get("tutorial_completed"), bool):
            validated_data["tutorial_completed"] = data[
                "tutorial_completed"
            ]

        unlocked_achievements = data.get("unlocked_achievements")
        if isinstance(unlocked_achievements, list):
            validated_data["unlocked_achievements"] = sorted(
                {
                    value
                    for value in unlocked_achievements
                    if isinstance(value, str) and value
                }
            )

        return validated_data

    # Salvează toate datele curente pe disc.
    def save(self):
        self.data = self._validate_data(self.data)
        self._write_split_data(self.data)

    def _write_split_data(self, data):
        progress_data = {
            key: deepcopy(data[key])
            for key in PROGRESS_KEYS
        }
        settings_data = {
            key: deepcopy(data[key])
            for key in SETTINGS_KEYS
        }
        self._write_data(self.save_path, progress_data)
        self._write_data(self.settings_path, settings_data)

    # Scrie datele mai întâi într-un fișier temporar.
    # Astfel, salvarea principală nu rămâne incompletă dacă jocul se închide.
    @staticmethod
    def _write_data(path, data):
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = path.with_suffix(
            ".tmp"
        )

        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as save_file:
            json.dump(
                data,
                save_file,
                indent=4,
                ensure_ascii=False,
            )

        temporary_path.replace(path)

    # Returnează True dacă jucătorul a terminat deja introducerea.
    def is_intro_completed(self):
        return self.data["intro_completed"]

    def is_tutorial_completed(self):
        return self.data["tutorial_completed"]

    def complete_tutorial(self):
        if self.data["tutorial_completed"]:
            return False
        self.data["tutorial_completed"] = True
        self.save()
        return True

    def queue_tutorial_replay(self):
        self.data["tutorial_completed"] = False
        self.save()

    # Returnează True dacă jucătorul a ajuns după primul checkpoint.
    # Permite CONTINUE chiar dacă intro-ul complet nu a fost încă terminat.
    def has_campaign_progress(self):
        return (
            self.data["intro_completed"]
            or self.data["current_scene"] != "planet"
            or self.data["checkpoint"] > 0
            or self.data["campaign_score"] > 0
        )

    # Marchează introducerea drept terminată și salvează prima zonă de război.
    def complete_intro(
        self,
        current_scene="dead_star",
        checkpoint=0,
    ):
        self.data["intro_completed"] = True
        self.data["current_scene"] = current_scene
        self.data["checkpoint"] = checkpoint
        self.save()

    # Salvează ultimul checkpoint sigur atins de jucător.
    def save_checkpoint(
        self,
        current_scene,
        checkpoint,
        campaign_score=None,
    ):
        self.data["current_scene"] = current_scene
        self.data["checkpoint"] = max(
            0,
            int(checkpoint),
        )

        if campaign_score is not None:
            self.data["campaign_score"] = max(
                0,
                int(campaign_score),
            )

        self.save()

    # Salvează scorul total al campaniei fără să modifice leaderboard-ul.
    def save_campaign_score(self, score):
        self.data["campaign_score"] = max(
            0,
            int(score),
        )
        self.save()

    # Actualizează recordul numai dacă noul scor este mai mare.
    def save_highest_score(self, score):
        score = max(0, int(score))

        if score > self.data["highest_score"]:
            self.data["highest_score"] = score
            self.save()

    def get_unlocked_achievements(self):
        return list(self.data.get("unlocked_achievements", []))

    def unlock_achievement(self, achievement_id):
        achievement_id = str(achievement_id)
        unlocked = set(self.get_unlocked_achievements())
        if achievement_id in unlocked:
            return False
        unlocked.add(achievement_id)
        self.data["unlocked_achievements"] = sorted(unlocked)
        self.save()
        return True

    # Salvează volumele și starea modului fullscreen.
    def save_settings(
        self,
        music_volume,
        sound_volume,
        fullscreen,
        resolution,
    ):
        self.data["music_volume"] = music_volume
        self.data["sound_volume"] = sound_volume
        self.data["fullscreen"] = fullscreen
        self.data["resolution"] = [
            int(resolution[0]),
            int(resolution[1]),
        ]
        self.save()

    # Resetează doar campania pentru NEW GAME.
    # Recordul și setările utilizatorului sunt păstrate.
    def reset_campaign(self):
        self.data["intro_completed"] = False
        self.data["current_scene"] = "planet"
        self.data["checkpoint"] = 0
        self.data["campaign_score"] = 0
        self.save()
