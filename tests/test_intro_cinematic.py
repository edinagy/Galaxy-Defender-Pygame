import os
import unittest


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from intro.anomaly_scene import AnomalyScene, SCENE_DURATION as ANOMALY_DURATION
from intro.anomaly_scene import STORY_CUES as ANOMALY_CUES
from intro.asteroid_scene import AsteroidObstacle
from intro.asteroid_scene import STORY_CUES as ASTEROID_CUES
from intro.dead_star_scene import (
    ENEMY_REVEAL_ASSETS,
    DeadStarScene,
    SCENE_DURATION as DEAD_STAR_DURATION,
)
from intro.dead_star_scene import STORY_CUES as DEAD_STAR_CUES
from intro.hangar_scene import HangarScene, SCENE_DURATION as HANGAR_DURATION
from intro.hangar_scene import STORY_CUES as HANGAR_CUES
from intro.launch_scene import LaunchScene, SCENE_DURATION as LAUNCH_DURATION
from intro.launch_scene import STORY_CUES as LAUNCH_CUES
from intro.planet_scene import PlanetScene, SCENE_DURATION as PLANET_DURATION
from intro.planet_scene import STORY_CUES as PLANET_CUES
from intro.vortex_scene import VortexScene, SCENE_DURATION as VORTEX_DURATION
from intro.vortex_scene import STORY_CUES as VORTEX_CUES
from intro.wormhole_scene import WormholeScene, SCENE_DURATION as WORMHOLE_DURATION
from intro.wormhole_scene import STORY_CUES as WORMHOLE_CUES


class IntroCinematicTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_story_cues_are_ordered_and_fit_inside_each_scene(self):
        scripts = (
            (PLANET_CUES, PLANET_DURATION),
            (HANGAR_CUES, HANGAR_DURATION),
            (LAUNCH_CUES, LAUNCH_DURATION),
            (VORTEX_CUES, VORTEX_DURATION),
            (ANOMALY_CUES, ANOMALY_DURATION),
            (WORMHOLE_CUES, WORMHOLE_DURATION),
            (DEAD_STAR_CUES, DEAD_STAR_DURATION),
        )
        for cues, duration in scripts:
            previous_end = 0.0
            for start, end, speaker, dialogue, channel in cues:
                self.assertGreaterEqual(start, previous_end)
                self.assertGreater(end, start)
                self.assertLessEqual(end, duration)
                self.assertTrue(speaker)
                self.assertTrue(dialogue)
                self.assertTrue(channel)
                previous_end = end

    def test_story_keeps_a_clear_cause_and_effect_chain(self):
        combined_story = " ".join(
            cue[3]
            for cues in (
                PLANET_CUES,
                HANGAR_CUES,
                LAUNCH_CUES,
                VORTEX_CUES,
                ASTEROID_CUES,
                ANOMALY_CUES,
                WORMHOLE_CUES,
                DEAD_STAR_CUES,
            )
            for cue in cues
        ).lower()
        for required_beat in (
            "breached the perimeter",
            "three patrols vanished",
            "gravitational lens",
            "manual control",
            "command link terminated",
            "source signal confirmed",
            "weapons restrictions removed",
        ):
            self.assertIn(required_beat, combined_story)

    def test_cinematic_scenes_render_representative_transmissions(self):
        scenes = (
            (PlanetScene(self.screen), 7.2),
            (HangarScene(self.screen), 8.3),
            (LaunchScene(self.screen), 8.2),
            (VortexScene(self.screen), 7.6),
            (AnomalyScene(self.screen), 6.5),
            (WormholeScene(self.screen), 6.9),
            (DeadStarScene(self.screen), 6.5),
        )
        for scene, elapsed_time in scenes:
            scene.elapsed_time = elapsed_time
            scene.update(0.0)
            scene.draw()
            self.assertEqual(scene.screen.get_size(), (1280, 720))

    def test_asteroid_obstacles_use_transparent_realistic_assets(self):
        AsteroidObstacle._realistic_sources = None
        asteroid = AsteroidObstacle(1280, 0.5)

        self.assertEqual(len(AsteroidObstacle._realistic_sources), 2)
        self.assertTrue(asteroid.base_image.get_flags() & pygame.SRCALPHA)
        self.assertGreater(asteroid.base_image.get_bounding_rect().width, 0)
        self.assertGreater(asteroid.base_image.get_bounding_rect().height, 0)

    def test_dead_star_reveals_the_current_enemy_lineup(self):
        scene = DeadStarScene(self.screen)
        expected_types = {
            "scout",
            "fighter",
            "tank",
            "shield_carrier",
            "phase_hunter",
        }

        self.assertEqual(set(ENEMY_REVEAL_ASSETS), expected_types)
        self.assertEqual(
            {enemy["type"] for enemy in scene.enemy_formation},
            expected_types,
        )
        self.assertTrue(
            ENEMY_REVEAL_ASSETS["scout"][0].endswith("_v2.png")
        )
        self.assertTrue(
            ENEMY_REVEAL_ASSETS["fighter"][0].endswith("_v2.png")
        )
        self.assertTrue(
            ENEMY_REVEAL_ASSETS["tank"][0].endswith("_v2.png")
        )


if __name__ == "__main__":
    unittest.main()
