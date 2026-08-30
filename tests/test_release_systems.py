import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from achievement_manager import ACHIEVEMENTS, AchievementManager
from controller_manager import ControllerManager
from platform_services import LocalPlatformServices, SteamPlatformServices
from player import Player
from save_manager import SaveManager
from score_validation import STEAM_INT32_MAX, steam_score_value, validate_run_submission


class ReleaseSystemsTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_save_manager_persists_achievements(self):
        with tempfile.TemporaryDirectory() as folder:
            save_path = Path(folder) / "save.json"
            manager = SaveManager(save_path)

            self.assertTrue(manager.unlock_achievement("FIRST_BLOOD"))
            self.assertFalse(manager.unlock_achievement("FIRST_BLOOD"))

            reloaded = SaveManager(save_path)
            self.assertEqual(
                reloaded.get_unlocked_achievements(),
                ["FIRST_BLOOD"],
            )

    def test_tutorial_completion_survives_new_game_and_can_be_replayed(self):
        with tempfile.TemporaryDirectory() as folder:
            save_path = Path(folder) / "save.json"
            manager = SaveManager(save_path)

            self.assertFalse(manager.is_tutorial_completed())
            self.assertTrue(manager.complete_tutorial())
            manager.reset_campaign()
            self.assertTrue(manager.is_tutorial_completed())

            manager.queue_tutorial_replay()
            self.assertFalse(manager.is_tutorial_completed())
            self.assertFalse(SaveManager(save_path).is_tutorial_completed())

    def test_save_manager_migrates_machine_settings_out_of_cloud_save(self):
        with tempfile.TemporaryDirectory() as folder:
            save_path = Path(folder) / "save.json"
            save_path.write_text(
                json.dumps(
                    {
                        "intro_completed": True,
                        "checkpoint": 4,
                        "music_volume": 0.2,
                        "fullscreen": True,
                        "resolution": [1920, 1080],
                    }
                ),
                encoding="utf-8",
            )

            manager = SaveManager(save_path)
            cloud_progress = json.loads(save_path.read_text(encoding="utf-8"))
            local_settings = json.loads(
                manager.settings_path.read_text(encoding="utf-8")
            )

            self.assertTrue(manager.data["intro_completed"])
            self.assertEqual(manager.data["music_volume"], 0.2)
            self.assertNotIn("resolution", cloud_progress)
            self.assertNotIn("fullscreen", cloud_progress)
            self.assertEqual(local_settings["resolution"], [1920, 1080])
            self.assertTrue(local_settings["fullscreen"])

    def test_local_platform_queue_survives_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            queue_path = Path(folder) / "platform_queue.json"
            platform = LocalPlatformServices(queue_path)
            platform.unlock_achievement("DAREDEVIL")
            platform.submit_score(
                12345,
                {
                    "score": 12345,
                    "stage": 2,
                    "wave": 4,
                    "duration_seconds": 300,
                },
            )

            reloaded = LocalPlatformServices(queue_path)
            self.assertIn("DAREDEVIL", reloaded.pending_achievements)
            self.assertEqual(reloaded.pending_scores[-1]["score"], 12345)
            self.assertEqual(
                reloaded.pending_scores[-1]["details"]["stage"],
                2,
            )

    def test_steam_bridge_failure_falls_back_to_persistent_queue(self):
        class FailingBridge:
            def set_achievement(self, _achievement_id):
                raise RuntimeError("Steam unavailable")

            def upload_score(self, _name, _score, _details):
                raise RuntimeError("Steam unavailable")

            def run_callbacks(self):
                raise RuntimeError("Steam unavailable")

            def shutdown(self):
                raise RuntimeError("Steam unavailable")

        with tempfile.TemporaryDirectory() as folder:
            platform = SteamPlatformServices.__new__(SteamPlatformServices)
            platform.bridge = FailingBridge()
            LocalPlatformServices.__init__(
                platform,
                Path(folder) / "platform_queue.json",
            )

            platform.unlock_achievement("FIRST_BLOOD")
            platform.submit_score(
                5000,
                {
                    "score": 5000,
                    "stage": 1,
                    "wave": 1,
                    "duration_seconds": 120,
                },
            )
            platform.update()
            platform.shutdown()

            self.assertIn("FIRST_BLOOD", platform.pending_achievements)
            self.assertEqual(platform.pending_scores[-1]["score"], 5000)

    def test_achievement_manager_unlocks_and_draws_notification(self):
        with tempfile.TemporaryDirectory() as folder:
            save_manager = SaveManager(Path(folder) / "save.json")
            platform = LocalPlatformServices(
                Path(folder) / "platform_queue.json"
            )
            manager = AchievementManager(save_manager, platform)

            self.assertTrue(manager.unlock("FIRST_BLOOD"))
            self.assertFalse(manager.unlock("FIRST_BLOOD"))
            self.assertIn("FIRST_BLOOD", manager.unlocked)
            self.assertIn("FIRST_BLOOD", platform.pending_achievements)
            manager.update()
            manager.draw(self.screen)
            self.assertGreater(manager.notification_timer, 0)

    def test_achievement_evaluation_covers_release_goals(self):
        with tempfile.TemporaryDirectory() as folder:
            save_manager = SaveManager(Path(folder) / "save.json")
            platform = LocalPlatformServices(
                Path(folder) / "platform_queue.json"
            )
            manager = AchievementManager(save_manager, platform)
            gameplay = SimpleNamespace(
                enemies_killed=1,
                best_combo=25,
                combo=25,
                best_graze_chain=25,
                boss_count=1,
                stage=3,
                score=100000,
                flawless_bosses=1,
            )

            manager.evaluate_gameplay(gameplay)

            expected_gameplay_achievements = set(ACHIEVEMENTS) - {
                "STORY_COMPLETE"
            }
            self.assertTrue(
                expected_gameplay_achievements.issubset(manager.unlocked)
            )

    def test_controller_button_and_hat_mapping(self):
        self.assertEqual(
            ControllerManager.translate_button(0).key,
            pygame.K_RETURN,
        )
        self.assertEqual(
            ControllerManager.translate_button(2).key,
            pygame.K_e,
        )
        self.assertEqual(
            ControllerManager.translate_button(3).key,
            pygame.K_F1,
        )
        self.assertEqual(
            ControllerManager.translate_hat((0, 1)).key,
            pygame.K_UP,
        )
        self.assertIsNone(ControllerManager.translate_button(99))

    def test_controller_deadzone_and_player_analog_movement(self):
        self.assertEqual(
            ControllerManager.apply_deadzone(0.05, 0.05),
            (0.0, 0.0),
        )
        movement = ControllerManager.apply_deadzone(1.0, 0.0)
        self.assertAlmostEqual(movement[0], 1.0)
        self.assertAlmostEqual(movement[1], 0.0)

        player = Player()
        starting_x = player.x
        player.set_controller_movement((1.0, 0.0))
        player.move(1280, 720)
        self.assertGreater(player.x, starting_x)

    def test_score_submission_validation_and_steam_cap(self):
        valid_details = {
            "score": 125000,
            "stage": 2,
            "wave": 4,
            "duration_seconds": 600,
        }
        self.assertEqual(
            validate_run_submission(125000, valid_details),
            (True, "ok"),
        )
        self.assertEqual(
            validate_run_submission(
                125001,
                valid_details,
            )[1],
            "score_mismatch",
        )
        self.assertFalse(
            validate_run_submission(
                -1,
                {**valid_details, "score": -1},
            )[0]
        )
        self.assertFalse(
            validate_run_submission(
                125000,
                {**valid_details, "duration_seconds": 0},
            )[0]
        )
        self.assertFalse(
            validate_run_submission(
                125000,
                {**valid_details, "score": "not-a-number"},
            )[0]
        )
        self.assertEqual(
            steam_score_value(STEAM_INT32_MAX + 99),
            STEAM_INT32_MAX,
        )


if __name__ == "__main__":
    unittest.main()
