import os
import unittest
from pathlib import Path


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STEAM_ASSETS = PROJECT_ROOT / "release" / "steam_assets"


class SteamAssetsTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_required_steam_assets_have_current_dimensions(self):
        expected_sizes = {
            "store_header_920x430.png": (920, 430),
            "store_small_462x174.png": (462, 174),
            "store_main_1232x706.png": (1232, 706),
            "store_vertical_748x896.png": (748, 896),
            "library_capsule_600x900.png": (600, 900),
            "library_hero_3840x1240.png": (3840, 1240),
            "library_logo_1280x360.png": (1280, 360),
            "library_header_920x430.png": (920, 430),
            "shortcut_icon_256.png": (256, 256),
            "app_icon_184.jpg": (184, 184),
        }
        for filename, expected_size in expected_sizes.items():
            with self.subTest(filename=filename):
                path = STEAM_ASSETS / filename
                self.assertTrue(path.is_file())
                self.assertEqual(
                    pygame.image.load(path).get_size(),
                    expected_size,
                )

    def test_store_package_contains_five_full_hd_gameplay_screenshots(self):
        screenshots = sorted((STEAM_ASSETS / "screenshots").glob("*.png"))
        self.assertGreaterEqual(len(screenshots), 5)
        for screenshot in screenshots:
            with self.subTest(filename=screenshot.name):
                self.assertEqual(
                    pygame.image.load(screenshot).get_size(),
                    (1920, 1080),
                )


if __name__ == "__main__":
    unittest.main()
