import os
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FOLDER = PROJECT_ROOT / "release" / "screenshots" / "intro"

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

temporary_data = tempfile.TemporaryDirectory(prefix="galaxy-defender-intro-")
os.environ["GALAXY_DEFENDER_DATA_DIR"] = temporary_data.name
sys.path.insert(0, str(PROJECT_ROOT))

import pygame

from main import GalaxyDefender


def advance(scene, target_time):
    scene.reset()
    frame_count = int(target_time * 60)
    for _ in range(frame_count):
        scene.update(1.0 / 60.0)


def main():
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    game = GalaxyDefender()
    captures = (
        ("01_homeworld_alert.png", game.planet_scene, 7.2),
        ("02_hangar_orders.png", game.hangar_scene, 8.3),
        ("03_launch_warning.png", game.launch_scene, 8.2),
        ("04_vortex_control_lost.png", game.vortex_scene, 7.6),
        ("05_debris_manual_control.png", game.asteroid_scene, 1.6),
        ("06_aperture_last_contact.png", game.anomaly_scene, 6.5),
        ("07_unknown_transit.png", game.wormhole_scene, 6.9),
        ("08_dead_star_reveal.png", game.dead_star_scene, 6.5),
    )

    try:
        for filename, scene, target_time in captures:
            advance(scene, target_time)
            scene.draw()
            pygame.image.save(game.screen, OUTPUT_FOLDER / filename)
            print(f"Captured {filename} at {target_time:.1f}s")
    finally:
        game.platform_services.shutdown()
        pygame.quit()
        temporary_data.cleanup()


if __name__ == "__main__":
    main()
