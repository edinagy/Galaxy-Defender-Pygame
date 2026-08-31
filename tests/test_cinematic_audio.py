import os
from pathlib import Path
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from cinematic_audio import (
    ASTEROID_EVENT_SOUNDS,
    SCENE_CUES,
    SCENE_TEXTURES,
    SOUND_PATHS,
    CinematicAudioDirector,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCENE_DURATIONS = {
    "planet": 13.0,
    "hangar": 12.0,
    "launch": 11.5,
    "vortex": 12.0,
    "asteroids": 32.0,
    "anomaly": 9.5,
    "wormhole": 12.0,
    "dead_star": 13.0,
}


class CinematicAudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.set_num_channels(24)

    @classmethod
    def tearDownClass(cls):
        pygame.mixer.stop()

    def test_all_cinematic_assets_exist_and_load(self):
        for sound_name, relative_path in SOUND_PATHS.items():
            path = PROJECT_ROOT / relative_path
            self.assertTrue(path.is_file(), sound_name)
            sound = pygame.mixer.Sound(str(path))
            self.assertGreater(sound.get_length(), 0.0, sound_name)

    def test_scene_cues_are_ordered_and_inside_timelines(self):
        self.assertEqual(set(SCENE_CUES), set(SCENE_DURATIONS))
        self.assertEqual(set(SCENE_TEXTURES), set(SCENE_DURATIONS))

        for scene_name, cues in SCENE_CUES.items():
            cue_times = [cue.time for cue in cues]
            self.assertEqual(cue_times, sorted(cue_times), scene_name)
            self.assertTrue(
                all(0.0 <= cue.time < SCENE_DURATIONS[scene_name] for cue in cues),
                scene_name,
            )
            self.assertTrue(
                all(cue.sound in SOUND_PATHS for cue in cues),
                scene_name,
            )

    def test_director_switches_scenes_and_stops_outside_cinematic(self):
        director = CinematicAudioDirector(0.8)
        director.update("planet", 0.0)
        director.update("planet", 2.23)
        self.assertEqual(director.current_scene, "planet")
        self.assertGreaterEqual(director.next_cue_index, 3)

        director.update("hangar", 0.0)
        self.assertEqual(director.current_scene, "hangar")
        self.assertTrue(director.texture_channel.get_busy())

        director.update("menu", 0.0)
        self.assertIsNone(director.current_scene)

    def test_asteroid_events_reference_valid_variants(self):
        for variants, gain in ASTEROID_EVENT_SOUNDS.values():
            self.assertTrue(variants)
            self.assertTrue(all(name in SOUND_PATHS for name in variants))
            self.assertGreater(gain, 0.0)
            self.assertLessEqual(gain, 1.0)


if __name__ == "__main__":
    unittest.main()
