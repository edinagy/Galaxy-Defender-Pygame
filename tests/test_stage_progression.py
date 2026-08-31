import os
import unittest


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from boss import Boss
from bullet import Bullet
from enemy import Enemy
from enemy_bullet import EnemyBullet
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

    def test_first_run_tutorial_requires_move_fire_and_energy_pulse(self):
        gameplay, _saved_scores = self.create_gameplay()
        completions = []
        gameplay.complete_tutorial_callback = lambda: completions.append(True)
        gameplay.reset(tutorial_enabled=True)

        self.assertTrue(gameplay.tutorial_active)
        self.assertEqual(gameplay.battle_intro_timer, 0)

        gameplay.player.x += 60
        gameplay.player.rect.x = int(gameplay.player.x)
        gameplay._update_tutorial()
        self.assertEqual(gameplay.tutorial_step, 1)

        gameplay.bullets.append(
            Bullet(gameplay.player.rect.centerx, gameplay.player.rect.top)
        )
        gameplay._update_tutorial()
        self.assertEqual(gameplay.tutorial_step, 2)
        self.assertEqual(
            gameplay.player.special_energy,
            gameplay.player.maximum_special_energy,
        )

        gameplay.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)
        )
        self.assertEqual(gameplay.tutorial_step, 3)
        gameplay.tutorial_finished_timer = 1
        gameplay._update_tutorial()

        self.assertFalse(gameplay.tutorial_active)
        self.assertEqual(completions, [True])
        self.assertGreater(gameplay.battle_intro_timer, 0)

    def test_first_stage_delays_the_opening_elite_without_removing_it(self):
        gameplay, _saved_scores = self.create_gameplay()
        gameplay._spawn_first_wave_formation()

        self.assertFalse(
            any(enemy.enemy_type == "elite" for enemy in gameplay.enemies)
        )
        self.assertEqual(gameplay.opening_elite_delay_timer, 480)

        gameplay.opening_elite_delay_timer = 1
        gameplay._update_opening_elite()
        self.assertTrue(
            any(enemy.enemy_type == "elite" for enemy in gameplay.enemies)
        )

    def test_tutorial_can_be_skipped_by_keyboard_or_controller_mapping(self):
        gameplay, _saved_scores = self.create_gameplay()
        completions = []
        gameplay.complete_tutorial_callback = lambda: completions.append(True)
        gameplay.reset(tutorial_enabled=True)

        gameplay.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F1)
        )

        self.assertFalse(gameplay.tutorial_active)
        self.assertEqual(completions, [True])
        self.assertEqual(gameplay.battle_intro_timer, 150)

    def test_energy_ready_and_breach_feedback_are_triggered(self):
        gameplay, _saved_scores = self.create_gameplay()
        gameplay.player.special_energy = 99
        gameplay._charge_energy_pulse(1)
        self.assertEqual(
            gameplay.energy_ready_timer,
            gameplay.energy_ready_duration,
        )

        escaped_enemy = Enemy(100, gameplay.height + 20, "scout", 1, 1)
        escaped_enemy.y = gameplay.height + escaped_enemy.image.get_height()
        escaped_enemy.rect.y = int(escaped_enemy.y)
        gameplay.enemies.append(escaped_enemy)
        lives_before = gameplay.lives
        gameplay._remove_offscreen_objects()

        self.assertEqual(gameplay.lives, lives_before - 1)
        self.assertEqual(
            gameplay.breach_warning_timer,
            gameplay.breach_warning_duration,
        )

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
        self.assertAlmostEqual(
            stage_two_boss.stage_health_multiplier,
            1.25,
        )
        self.assertAlmostEqual(
            stage_two_boss.stage_attack_rate,
            1.12,
        )
        self.assertAlmostEqual(
            stage_two_boss.stage_projectile_speed,
            1.07,
        )
        self.assertEqual(
            stage_two_boss.phase_two_threshold,
            int(stage_two_boss.max_hp * 2 / 3),
        )

    def test_phase_sovereign_attack_is_exclusive_to_stage_two_plus(self):
        player_rect = pygame.Rect(610, 610, 32, 44)
        stage_one_boss = Boss(1280, 720, 1)
        stage_one_boss.state = "active"
        stage_one_boss.phase_attack_timer = 9999
        stage_one_boss._create_attacks(player_rect)
        self.assertFalse(stage_one_boss.phase_attack_active)
        self.assertEqual(stage_one_boss.phase_exit_portals, [])

        stage_two_boss = Boss(1280, 720, 2)
        stage_two_boss.state = "active"
        stage_two_boss.y = stage_two_boss.target_y
        stage_two_boss._update_rectangles()
        stage_two_boss.phase_attack_timer = 345
        first_frame_projectiles = stage_two_boss._create_attacks(
            player_rect
        )

        self.assertEqual(first_frame_projectiles, [])
        self.assertTrue(stage_two_boss.phase_attack_active)
        self.assertEqual(len(stage_two_boss.phase_exit_portals), 1)
        self.assertGreater(stage_two_boss.phase_attack_charge_timer, 0)

        phase_projectiles = []
        safety_frames = 0
        while stage_two_boss.phase_attack_active and safety_frames < 500:
            phase_projectiles.extend(
                stage_two_boss._create_attacks(player_rect)
            )
            safety_frames += 1

        self.assertFalse(stage_two_boss.phase_attack_active)
        self.assertEqual(len(phase_projectiles), 6)
        self.assertTrue(
            all(
                projectile.projectile_type == "phase"
                for projectile in phase_projectiles
            )
        )

    def test_phase_sovereign_adds_second_exit_from_stage_three(self):
        boss = Boss(1280, 720, 3)
        boss.state = "active"
        boss.phase = 3
        boss._start_phase_portal_attack(
            pygame.Rect(610, 610, 32, 44)
        )

        self.assertEqual(len(boss.phase_exit_portals), 2)
        self.assertEqual(boss.phase_attack_total_salvos, 3)
        boss.phase_attack_charge_timer = 0
        salvo = boss._update_phase_portal_attack()
        self.assertEqual(len(salvo), 4)
        self.assertTrue(
            all(
                projectile.projectile_type == "phase"
                for projectile in salvo
            )
        )

    def test_phase_sovereign_cancels_portals_during_phase_changes(self):
        boss = Boss(1280, 720, 2)
        player_rect = pygame.Rect(610, 610, 32, 44)
        boss._start_phase_portal_attack(player_rect)
        self.assertTrue(boss.phase_attack_active)

        boss._start_phase_two()
        self.assertFalse(boss.phase_attack_active)
        self.assertEqual(boss.phase_exit_portals, [])

        boss.transition_timer = 0
        boss._start_phase_portal_attack(player_rect)
        boss._start_phase_three()
        self.assertFalse(boss.phase_attack_active)
        self.assertEqual(boss.phase_exit_portals, [])

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

    def test_combo_milestones_continue_beyond_x5_multiplier(self):
        gameplay, _saved_scores = self.create_gameplay()

        milestone_expectations = (
            (10, 2, "COMBAT LINK"),
            (25, 3, "UNTOUCHABLE"),
            (50, 5, "LEGENDARY"),
            (100, 5, "GODLIKE"),
        )
        for combo_value, multiplier, title in milestone_expectations:
            gameplay.combo = combo_value
            gameplay._update_multiplier()
            self.assertEqual(gameplay.multiplier, multiplier)
            self.assertEqual(gameplay.combo_milestone_title, title)
            self.assertGreater(gameplay.combo_milestone_timer, 0)

        gameplay.combo = 173
        gameplay._update_multiplier()
        self.assertEqual(gameplay.combo, 173)
        self.assertEqual(gameplay.multiplier, 5)
        self.assertEqual(gameplay.best_combo, 173)

    def test_lost_combo_records_chain_and_creates_shatter_effect(self):
        gameplay, _saved_scores = self.create_gameplay()
        gameplay.combo = 87
        gameplay._update_multiplier()
        starting_lives = gameplay.lives

        damage_was_applied = gameplay._damage_player()

        self.assertTrue(damage_was_applied)
        self.assertEqual(gameplay.lives, starting_lives - 1)
        self.assertEqual(gameplay.combo, 0)
        self.assertEqual(gameplay.multiplier, 1)
        self.assertEqual(gameplay.best_combo, 87)
        self.assertEqual(gameplay.combo_lost_value, 87)
        self.assertGreater(gameplay.combo_lost_timer, 0)
        self.assertEqual(len(gameplay.combo_break_shards), 18)

        gameplay._draw_combo_feedback()
        for _ in range(gameplay.combo_lost_duration + 5):
            gameplay._update_combo_feedback()
        self.assertEqual(gameplay.combo_lost_timer, 0)

    def test_shield_hit_does_not_break_combo(self):
        gameplay, _saved_scores = self.create_gameplay()
        gameplay.combo = 14
        gameplay.multiplier = 2
        gameplay.player.activate_shield(300)

        damage_was_applied = gameplay._damage_player()

        self.assertFalse(damage_was_applied)
        self.assertEqual(gameplay.combo, 14)
        self.assertEqual(gameplay.multiplier, 2)

    def test_graze_rewards_each_projectile_only_once(self):
        gameplay, _saved_scores = self.create_gameplay()
        player_hitbox = gameplay.player.get_hitbox()
        bullet = EnemyBullet(0, 0)
        bullet.rect = pygame.Rect(
            player_hitbox.right + 5,
            player_hitbox.centery - 4,
            8,
            8,
        )
        gameplay.enemy_bullets = [bullet]
        starting_score = gameplay.score
        starting_energy = gameplay.player.special_energy

        gameplay._update_graze_system()

        self.assertEqual(gameplay.graze_chain, 1)
        self.assertEqual(gameplay.total_grazes, 1)
        self.assertGreater(gameplay.score, starting_score)
        self.assertGreater(
            gameplay.player.special_energy,
            starting_energy,
        )
        first_rewarded_score = gameplay.score

        gameplay._update_graze_system()
        self.assertEqual(gameplay.graze_chain, 1)
        self.assertEqual(gameplay.total_grazes, 1)
        self.assertEqual(gameplay.score, first_rewarded_score)

    def test_graze_chain_increases_capped_risk_bonus(self):
        gameplay, _saved_scores = self.create_gameplay()
        gameplay.combo = 10
        gameplay._update_multiplier()
        gameplay.graze_chain = 9
        starting_score = gameplay.score

        awarded_score = gameplay._register_graze((640, 360))

        self.assertEqual(gameplay.graze_chain, 10)
        self.assertEqual(gameplay.best_graze_chain, 10)
        self.assertEqual(gameplay._get_graze_tier(10), 2)
        # 10 puncte * risk x2 * combo x2.
        self.assertEqual(awarded_score, 40)
        self.assertEqual(gameplay.score - starting_score, 40)
        self.assertGreater(gameplay.graze_milestone_timer, 0)
        self.assertEqual(gameplay._get_graze_tier(999), 5)

    def test_shield_breaks_graze_chain_but_preserves_combat_combo(self):
        gameplay, _saved_scores = self.create_gameplay()
        gameplay.combo = 14
        gameplay.multiplier = 2
        gameplay.graze_chain = 18
        gameplay.best_graze_chain = 18
        gameplay.player.activate_shield(300)

        damage_was_applied = gameplay._damage_player()

        self.assertFalse(damage_was_applied)
        self.assertEqual(gameplay.combo, 14)
        self.assertEqual(gameplay.multiplier, 2)
        self.assertEqual(gameplay.graze_chain, 0)
        self.assertEqual(gameplay.best_graze_chain, 18)

    def test_phase_storm_projectile_can_award_graze(self):
        gameplay, _saved_scores = self.create_gameplay()
        manager = gameplay.space_event_manager
        manager.reset(2)
        event = manager.phase_storm
        manager.current_event = event
        event.state = "active"
        event.active_timer = 300
        event.volley_timer = 999
        event.volley_count = event.total_volleys
        event.portals = []
        player_hitbox = gameplay.player.get_hitbox()
        event.projectiles = [
            {
                "x": float(player_hitbox.right + 12),
                "y": float(player_hitbox.centery),
                "dx": 0.0,
                "dy": 0.0,
                "radius": 5,
                "trail": [],
                "grazed": False,
            }
        ]

        gameplay._update_space_events()

        self.assertEqual(gameplay.graze_chain, 1)
        self.assertEqual(gameplay.total_grazes, 1)
        self.assertTrue(event.projectiles[0]["grazed"])

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

    def test_player_core_hitbox_allows_wings_to_dodge_boss_projectiles(self):
        gameplay, _saved_scores = self.create_gameplay()
        hitbox = gameplay.player.get_hitbox()

        self.assertEqual(hitbox.size, (32, 44))
        self.assertEqual(hitbox.center, gameplay.player.rect.center)

        wing_projectile = type("BossProjectile", (), {})()
        wing_projectile.rect = pygame.Rect(
            gameplay.player.rect.left + 5,
            gameplay.player.rect.centery - 5,
            10,
            10,
        )
        self.assertTrue(
            wing_projectile.rect.colliderect(gameplay.player.rect)
        )
        self.assertFalse(wing_projectile.rect.colliderect(hitbox))

        starting_lives = gameplay.lives
        gameplay.boss_projectiles = [wing_projectile]
        gameplay._boss_projectile_player_collisions()
        self.assertEqual(gameplay.boss_projectiles, [wing_projectile])
        self.assertEqual(gameplay.lives, starting_lives)

        core_projectile = type("BossProjectile", (), {})()
        core_projectile.rect = pygame.Rect(0, 0, 8, 8)
        core_projectile.rect.center = hitbox.center
        gameplay.boss_projectiles = [core_projectile]
        gameplay._boss_projectile_player_collisions()
        self.assertEqual(gameplay.boss_projectiles, [])
        self.assertEqual(gameplay.lives, starting_lives - 1)

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
