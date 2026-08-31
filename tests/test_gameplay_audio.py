import os
from pathlib import Path
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from gameplay_audio import (
    EVENTS,
    SOUND_PATHS,
    GameplayAudioDirector,
)
from gameplay import Gameplay


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class GameplayAudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.mixer.set_num_channels(24)

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_all_premium_combat_assets_exist_and_load(self):
        for sound_name, relative_path in SOUND_PATHS.items():
            path = PROJECT_ROOT / relative_path
            self.assertTrue(path.is_file(), sound_name)
            sound = pygame.mixer.Sound(str(path))
            self.assertGreater(sound.get_length(), 0.0, sound_name)

    def test_every_event_references_valid_assets_and_mix_values(self):
        for event_name, event in EVENTS.items():
            self.assertTrue(event.variants, event_name)
            self.assertTrue(
                all(name in SOUND_PATHS for name in event.variants),
                event_name,
            )
            self.assertTrue(
                all(name in SOUND_PATHS for name, _gain in event.layers),
                event_name,
            )
            self.assertGreater(event.gain, 0.0, event_name)
            self.assertLessEqual(event.gain, 1.0, event_name)
            self.assertIn(
                event.group,
                GameplayAudioDirector.CHANNEL_GROUPS,
            )

    def test_weapon_levels_and_special_threats_have_unique_events(self):
        required_events = {
            *(f"player_fire_{level}" for level in range(1, 5)),
            "enemy_fire_scout",
            "enemy_fire_fighter",
            "enemy_fire_tank",
            "enemy_fire_shield",
            "enemy_fire_phase",
            "enemy_fire_elite",
            "player_shield_absorb",
            "energy_pulse",
            "boss_phase",
            "boss_destroyed",
            "event_phase_storm",
        }
        self.assertTrue(required_events.issubset(EVENTS))

    def test_rate_limiting_prevents_autofire_audio_stacking(self):
        director = GameplayAudioDirector(0.8)
        self.assertTrue(director.play("player_fire_1"))
        self.assertFalse(director.play("player_fire_1"))
        director.update()
        self.assertFalse(director.play("player_fire_1"))
        director.update()
        self.assertTrue(director.play("player_fire_1"))

    def test_master_volume_updates_active_channel_gain(self):
        director = GameplayAudioDirector(1.0)
        director.play("energy_pulse")
        director.set_master_volume(0.25)
        active_volumes = [
            channel.get_volume()
            for channel in director.channels["priority"]
            if channel.get_busy()
        ]
        self.assertTrue(active_volumes)
        self.assertTrue(all(volume <= 0.10 for volume in active_volumes))

    def test_gameplay_emits_semantic_weapon_and_shield_events(self):
        class SilentSound:
            def play(self):
                return None

        class RecordingDirector:
            def __init__(self):
                self.events = []

            def reset(self):
                self.events.clear()

            def update(self):
                return None

            def play(self, event_name, strength=1.0):
                self.events.append((event_name, strength))
                return True

        recorder = RecordingDirector()
        sound = SilentSound()
        screen = pygame.display.set_mode((1280, 720))
        gameplay = Gameplay(
            screen,
            pygame.font.Font(None, 30),
            pygame.font.Font(None, 72),
            pygame.font.Font(None, 32),
            sound,
            sound,
            sound,
            "unused_boss_music.wav",
            sound,
            sound,
            {},
            lambda: 0.5,
            lambda _score: None,
            lambda: 0,
            audio_director=recorder,
        )

        gameplay.player.weapon_level = 4
        gameplay._shoot()
        gameplay.player.activate_shield(60)
        gameplay._damage_player()

        event_names = [event[0] for event in recorder.events]
        self.assertIn("player_fire_4", event_names)
        self.assertIn("player_shield_absorb", event_names)


if __name__ == "__main__":
    unittest.main()
