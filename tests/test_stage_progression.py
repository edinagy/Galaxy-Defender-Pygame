import os
import unittest


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from boss import Boss
from bullet import Bullet
from enemy import Enemy
from gameplay import Gameplay


class SilentSound:

    def play(self):
        return None


class StageProgressionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def create_gameplay(self):
        saved_scores = []
        sound = SilentSound()
        gameplay = Gameplay(
            self.screen,
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
            saved_scores.append,
            lambda: 0,
        )
        return gameplay, saved_scores

    def test_sovereign_continues_into_stage_two(self):
        gameplay, saved_scores = self.create_gameplay()
        gameplay.score = 25000
        gameplay.lives = 7
        gameplay.player.weapon_level = 3
        gameplay.player.special_energy = 64

        gameplay._complete_stage()

        self.assertFalse(gameplay.victory)
        self.assertEqual(gameplay.completed_stage, 1)
        self.assertEqual(gameplay.score, 35000)
        # Leaderboard-ul este actualizat abia la finalul rundei endless.
        self.assertEqual(saved_scores, [])
        self.assertGreater(gameplay.stage_transition_timer, 0)

        gameplay.stage_transition_timer = 1
        gameplay.update()

        self.assertEqual(gameplay.stage, 2)
        self.assertEqual(gameplay.wave, 1)
        self.assertEqual(gameplay.lives, 7)
        self.assertEqual(gameplay.player.weapon_level, 3)
        self.assertEqual(gameplay.player.special_energy, 64)
        self.assertEqual(gameplay.space_event_manager.stage, 2)
        self.assertLess(
            gameplay.space_event_manager.event_cooldown,
            900,
        )
        self.assertIsNone(gameplay.boss)
        self.assertFalse(gameplay.boss_spawned)
        self.assertTrue(gameplay.first_formation_spawned)
        carriers = [
            enemy
            for enemy in gameplay.enemies
            if enemy.enemy_type == "shield_carrier"
        ]
        self.assertEqual(len(carriers), 1)

        score_before_bonus = gameplay.score
        gameplay._award_score(100)
        self.assertEqual(
            gameplay.score - score_before_bonus,
            150,
        )

        # Același flux poate continua din nou, nu este limitat la Stage 2.
        gameplay._complete_stage()
        gameplay.stage_transition_timer = 1
        gameplay.update()
        self.assertEqual(gameplay.stage, 3)
        self.assertEqual(gameplay.wave, 1)

    def test_stage_two_scales_enemies_and_boss(self):
        stage_one_enemy = Enemy(0, -100, "fighter", 1, 1)
        stage_two_enemy = Enemy(0, -100, "fighter", 1, 2)

        self.assertAlmostEqual(
            stage_two_enemy.entry_speed,
            stage_one_enemy.entry_speed * 1.25,
        )
        self.assertLess(
            stage_two_enemy.attack_cooldown_scale,
            stage_one_enemy.attack_cooldown_scale,
        )
        self.assertGreater(
            stage_two_enemy.projectile_speed_multiplier,
            stage_one_enemy.projectile_speed_multiplier,
        )

        stage_one_boss = Boss(1280, 720, 1)
        stage_two_boss = Boss(1280, 720, 2)
        self.assertGreater(stage_two_boss.max_hp, stage_one_boss.max_hp)
        self.assertGreater(
            stage_two_boss.stage_attack_rate,
            stage_one_boss.stage_attack_rate,
        )

    def test_combo_persists_until_player_loses_a_life(self):
        gameplay, _saved_scores = self.create_gameplay()
        gameplay.combo = 27
        gameplay.multiplier = 3
        gameplay.combo_timer = 1

        for _ in range(900):
            gameplay._update_combo()

        self.assertEqual(gameplay.combo, 27)
        self.assertEqual(gameplay.multiplier, 3)

        # Trecerea într-un stage nou păstrează seria obținută la boss.
        gameplay.completed_stage = 1
        gameplay._begin_next_stage()
        self.assertEqual(gameplay.combo, 27)
        self.assertEqual(gameplay.multiplier, 3)

        gameplay._damage_player()
        self.assertEqual(gameplay.combo, 0)
        self.assertEqual(gameplay.multiplier, 1)

    def test_shield_hit_does_not_break_combo(self):
        gameplay, _saved_scores = self.create_gameplay()
        gameplay.combo = 14
        gameplay.multiplier = 2
        gameplay.player.activate_shield(300)

        damage_was_applied = gameplay._damage_player()

        self.assertFalse(damage_was_applied)
        self.assertEqual(gameplay.combo, 14)
        self.assertEqual(gameplay.multiplier, 2)

    def test_phase_storm_is_exclusive_to_stage_two_and_beyond(self):
        gameplay, _saved_scores = self.create_gameplay()
        manager = gameplay.space_event_manager

        manager.reset(1)
        self.assertEqual(len(manager.events), 9)
        self.assertNotIn(manager.phase_storm, manager.events)

        manager.reset(2)
        self.assertEqual(len(manager.events), 10)
        self.assertIn(manager.phase_storm, manager.events)

    def test_phase_storm_telegraphs_and_fires_avoidable_projectiles(self):
        gameplay, _saved_scores = self.create_gameplay()
        event = gameplay.space_event_manager.phase_storm
        player_hitbox = gameplay.player.rect.copy()

        event.start(5)
        event.warning_timer = 1
        self.assertFalse(event.update(player_hitbox, 5))
        self.assertEqual(event.state, "active")
        self.assertGreaterEqual(len(event.portals), 3)

        for portal in event.portals:
            portal["warning_timer"] = 1
        event.update(player_hitbox, 5)
        event.update(player_hitbox, 5)

        self.assertEqual(
            len(event.projectiles),
            event.portal_count,
        )

        event.portals = []
        event.volley_timer = 999
        event.projectiles = [
            {
                "x": float(player_hitbox.centerx),
                "y": float(player_hitbox.centery),
                "dx": 0.0,
                "dy": 0.0,
                "radius": 10,
                "trail": [],
            }
        ]
        self.assertTrue(event.update(player_hitbox, 5))
        self.assertEqual(event.projectiles, [])

        event.draw(self.screen)

    def test_phase_storm_completion_awards_score_combo_and_energy(self):
        gameplay, _saved_scores = self.create_gameplay()
        manager = gameplay.space_event_manager
        manager.reset(2)
        manager.current_event = manager.phase_storm
        manager.phase_storm.state = "recovery"
        manager.phase_storm.recovery_timer = 1
        starting_score = gameplay.score
        starting_energy = gameplay.player.special_energy

        gameplay._update_space_events()

        self.assertIsNone(manager.current_event)
        self.assertGreater(gameplay.score, starting_score)
        self.assertEqual(gameplay.combo, 5)
        self.assertGreater(
            gameplay.player.special_energy,
            starting_energy,
        )

    def test_shield_carrier_protects_nearby_enemy_but_not_itself(self):
        gameplay, _saved_scores = self.create_gameplay()
        gameplay.stage = 2

        carrier = Enemy(
            400,
            60,
            "shield_carrier",
            1,
            2,
        )
        carrier.movement_state = "patrolling"
        carrier.rect.topleft = (400, 60)

        protected_enemy = Enemy(
            650,
            110,
            "fighter",
            1,
            2,
        )
        protected_enemy.movement_state = "patrolling"
        protected_enemy.rect.topleft = (650, 110)
        gameplay.enemies = [carrier, protected_enemy]

        protected_health = protected_enemy.health
        blocked_bullet = Bullet(
            protected_enemy.rect.centerx,
            protected_enemy.rect.centery,
        )
        blocked_bullet.rect.center = protected_enemy.rect.center
        gameplay.bullets = [blocked_bullet]
        gameplay._player_bullet_enemy_collisions()

        self.assertEqual(protected_enemy.health, protected_health)
        self.assertEqual(gameplay.bullets, [])
        self.assertGreater(carrier.shield_hit_timer, 0)

        carrier_health = carrier.health
        carrier_bullet = Bullet(
            carrier.rect.centerx,
            carrier.rect.centery,
        )
        carrier_bullet.rect.center = carrier.rect.center
        gameplay.bullets = [carrier_bullet]
        gameplay._player_bullet_enemy_collisions()

        self.assertEqual(carrier.health, carrier_health - 1)
        self.assertEqual(gameplay.bullets, [])

    def test_shield_carrier_fires_twin_defensive_bolts(self):
        gameplay, _saved_scores = self.create_gameplay()
        carrier = Enemy(
            500,
            70,
            "shield_carrier",
            1,
            2,
        )
        carrier.movement_state = "patrolling"
        carrier.rect.topleft = (500, 70)
        carrier.shoot_timer = 0
        gameplay.enemies = [carrier]

        gameplay._enemy_shooting()

        self.assertEqual(len(gameplay.enemy_bullets), 2)
        self.assertTrue(
            all(
                bullet.bullet_type == "shield"
                for bullet in gameplay.enemy_bullets
            )
        )

    def test_phase_hunter_spawns_on_stage_two_even_waves(self):
        gameplay, _saved_scores = self.create_gameplay()
        gameplay.stage = 2
        gameplay.wave = 2
        gameplay.enemies = []
        gameplay.phase_hunter_waves_spawned.clear()

        gameplay._spawn_phase_hunter_for_wave()
        gameplay._spawn_phase_hunter_for_wave()

        hunters = [
            enemy
            for enemy in gameplay.enemies
            if enemy.enemy_type == "phase_hunter"
        ]
        self.assertEqual(len(hunters), 1)

        gameplay.wave = 3
        gameplay._spawn_phase_hunter_for_wave()
        self.assertEqual(
            len(
                [
                    enemy
                    for enemy in gameplay.enemies
                    if enemy.enemy_type == "phase_hunter"
                ]
            ),
            1,
        )

    def test_phase_hunter_is_invulnerable_only_while_phased(self):
        gameplay, _saved_scores = self.create_gameplay()
        hunter = Enemy(500, 80, "phase_hunter", 2, 2)
        hunter.movement_state = "patrolling"
        hunter.rect.topleft = (500, 80)
        hunter.phase_state = "phased"
        gameplay.enemies = [hunter]

        starting_health = hunter.health
        self.assertFalse(hunter.can_be_hit())
        self.assertFalse(hunter.take_damage())
        self.assertEqual(hunter.health, starting_health)

        passing_bullet = Bullet(
            hunter.rect.centerx,
            hunter.rect.centery,
        )
        passing_bullet.rect.center = hunter.rect.center
        gameplay.bullets = [passing_bullet]
        gameplay._player_bullet_enemy_collisions()
        self.assertEqual(gameplay.bullets, [passing_bullet])

        hunter.phase_state = "materializing"
        self.assertTrue(hunter.can_be_hit())
        self.assertTrue(hunter.take_damage())
        self.assertEqual(hunter.health, starting_health - 1)

    def test_phase_hunter_fires_targeted_salvo_after_materializing(self):
        gameplay, _saved_scores = self.create_gameplay()
        hunter = Enemy(500, 80, "phase_hunter", 2, 2)
        hunter.movement_state = "patrolling"
        hunter.phase_state = "materializing"
        hunter.phase_timer = 1
        hunter.rect.topleft = (500, 80)
        gameplay.enemies = [hunter]

        hunter.move(gameplay.width, gameplay.height)
        self.assertEqual(hunter.phase_state, "visible")
        self.assertTrue(hunter.phase_attack_pending)

        gameplay._enemy_shooting()

        self.assertFalse(hunter.phase_attack_pending)
        self.assertEqual(len(gameplay.enemy_bullets), 3)
        self.assertTrue(
            all(
                bullet.bullet_type == "phase"
                for bullet in gameplay.enemy_bullets
            )
        )
        self.assertGreater(
            sum(
                bullet.speed_y
                for bullet in gameplay.enemy_bullets
            ),
            0,
        )


if __name__ == "__main__":
    unittest.main()
