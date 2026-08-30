import os
import sys
import tempfile
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FOLDER = PROJECT_ROOT / "release" / "screenshots"

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

temporary_data = tempfile.TemporaryDirectory(prefix="galaxy-defender-qa-")
os.environ["GALAXY_DEFENDER_DATA_DIR"] = temporary_data.name
sys.path.insert(0, str(PROJECT_ROOT))

import pygame

from main import GalaxyDefender
from scene_manager import SceneManager


def save_frame(game, filename):
    game.draw()
    pygame.image.save(game.screen, OUTPUT_FOLDER / filename)


def main():
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    game = GalaxyDefender()

    try:
        for _ in range(40):
            game.update(1.0 / 60.0)
        save_frame(game, "01_main_menu.png")

        game.scene_manager.change_scene(SceneManager.SETTINGS)
        game.settings_animation_timer = game.settings_animation_duration
        game.save_manager.complete_tutorial()
        game._handle_settings_click(game.replay_tutorial_button.center)
        if game.save_manager.is_tutorial_completed():
            raise RuntimeError("Replay Tutorial did not queue the next run.")
        save_frame(game, "02_controller_settings.png")

        game.gameplay.reset(starting_score=0, tutorial_enabled=True)
        game.gameplay.tutorial_step = 2
        game.gameplay.tutorial_step_timer = 24
        game.gameplay.player.special_energy = (
            game.gameplay.player.maximum_special_energy
        )
        game.scene_manager.change_scene(SceneManager.GAMEPLAY)
        save_frame(game, "03_first_run_tutorial.png")

        game.gameplay.reset(starting_score=18450, tutorial_enabled=False)
        game.gameplay.stage = 2
        game.gameplay.wave = 3
        game.gameplay.combo = 18
        game.gameplay.best_combo = 18
        game.gameplay.multiplier = 4
        game.gameplay.graze_chain = 25
        game.gameplay.best_graze_chain = 25
        game.gameplay.total_grazes = 25
        game.gameplay._apply_stage_background_tint()
        game.gameplay._spawn_first_wave_formation()
        game.gameplay.battle_intro_timer = 0
        visible_enemies = [
            enemy
            for enemy in game.gameplay.enemies
            if enemy.enemy_type in ("scout", "fighter", "shield_carrier")
        ][:4]
        showcase_positions = ((110, 105), (365, 155), (650, 95), (930, 145))
        for enemy, (enemy_x, enemy_y) in zip(
            visible_enemies,
            showcase_positions,
        ):
            enemy.x = float(enemy_x)
            enemy.y = float(enemy_y)
            enemy.rect.topleft = (enemy_x, enemy_y)
            enemy.movement_state = "patrolling"
        game.gameplay.enemies = visible_enemies
        game.scene_manager.change_scene(SceneManager.GAMEPLAY)
        game.achievement_manager.unlock("DAREDEVIL")
        for _ in range(24):
            game.achievement_manager.update()
        save_frame(game, "03_stage_two_gameplay.png")

        game.achievement_manager.active_notification = None
        game.achievement_manager.notification_queue.clear()
        game.achievement_manager.notification_timer = 0

        game.gameplay.player.special_energy = (
            game.gameplay.player.maximum_special_energy
        )
        game.gameplay.energy_ready_timer = (
            game.gameplay.energy_ready_duration
        )
        save_frame(game, "04_energy_ready_feedback.png")

        game.gameplay.energy_ready_timer = 0
        game.gameplay.lives = 1
        save_frame(game, "05_critical_hull_feedback.png")
        game.gameplay.lives = 5

        start_time = time.perf_counter()
        benchmark_frames = 180
        for _ in range(benchmark_frames):
            game.gameplay.update()
            game.gameplay.draw()
        elapsed = max(0.0001, time.perf_counter() - start_time)
        print(
            f"Rendered {benchmark_frames} gameplay frames at "
            f"{benchmark_frames / elapsed:.1f} uncapped FPS."
        )
    finally:
        game.platform_services.shutdown()
        pygame.quit()
        temporary_data.cleanup()


if __name__ == "__main__":
    main()
