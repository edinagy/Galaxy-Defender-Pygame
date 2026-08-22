import json
from copy import deepcopy
from pathlib import Path


# Valorile folosite atunci când jocul este pornit pentru prima dată.
DEFAULT_SAVE_DATA = {
    "intro_completed": False,
    "current_scene": "planet",
    "checkpoint": 0,
    "campaign_score": 0,
    "highest_score": 0,
    "music_volume": 0.5,
    "sound_volume": 1.0,
    "fullscreen": False,
    "resolution": [1280, 720],
}


# Clasa responsabilă de încărcarea și salvarea progresului jucătorului.
class SaveManager:

    # Stabilește locația fișierului save.json și încarcă progresul existent.
    def __init__(self, save_path=None):
        if save_path is None:
            project_folder = Path(__file__).resolve().parent
            save_path = project_folder / "data" / "save.json"

        self.save_path = Path(save_path)
        self.data = self.load()

    # Creează o copie nouă a valorilor implicite.
    # deepcopy împiedică modificarea accidentală a dicționarului original.
    @staticmethod
    def _default_data():
        return deepcopy(DEFAULT_SAVE_DATA)

    # Încarcă salvarea existentă.
    # Dacă fișierul lipsește, este gol sau este corupt, creează unul nou.
    def load(self):
        if not self.save_path.exists():
            default_data = self._default_data()
            self._write_data(default_data)
            return default_data

        try:
            with self.save_path.open(
                "r",
                encoding="utf-8",
            ) as save_file:
                loaded_data = json.load(save_file)

            if not isinstance(loaded_data, dict):
                raise ValueError(
                    "Salvarea trebuie să conțină un obiect JSON."
                )

        except (
            json.JSONDecodeError,
            OSError,
            ValueError,
        ):
            default_data = self._default_data()
            self._write_data(default_data)
            return default_data

        # Completează automat cheile noi dacă jocul este actualizat.
        complete_data = self._default_data()
        complete_data.update(loaded_data)

        # Verifică și corectează tipurile valorilor importante.
        complete_data = self._validate_data(complete_data)

        # Rescrie fișierul dacă au fost adăugate sau corectate valori.
        if complete_data != loaded_data:
            self._write_data(complete_data)

        return complete_data

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

        return validated_data

    # Salvează toate datele curente pe disc.
    def save(self):
        self.data = self._validate_data(self.data)
        self._write_data(self.data)

    # Scrie datele mai întâi într-un fișier temporar.
    # Astfel, salvarea principală nu rămâne incompletă dacă jocul se închide.
    def _write_data(self, data):
        self.save_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = self.save_path.with_suffix(
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

        temporary_path.replace(self.save_path)

    # Returnează True dacă jucătorul a terminat deja introducerea.
    def is_intro_completed(self):
        return self.data["intro_completed"]

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
