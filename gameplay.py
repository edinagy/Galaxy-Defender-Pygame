import math
import random

import pygame

from ally_ship import AllyShip
from background import Star
from boss import Boss
from bullet import Bullet
from combat_drone import CombatDrone
from crossfire import CrossfireTurret
from enemy import Enemy
from enemy_bullet import EnemyBullet
from explosion import Explosion
from hit_effect import HitEffect
from homing_missile import HomingMissile
from player import Player
from powerups import PowerUp
from space_events import SpaceEventManager
from storm_asteroid import StormAsteroid
from ui import draw_game_ui


# MOD TEMPORAR DE TEST PENTRU BOSS:
# True  = bossul final apare imediat cand incepe gameplay-ul.
# False = jocul ruleaza normal toate cele 9 challenge-uri inainte de boss.
TEST_BOSS_INSTANT = False


class Gameplay:
    def __init__(
        self,
        screen,
        font,
        game_over_font,
        restart_font,
        shoot_sound,
        enemy_destroy_sound,
        explosion_sound,
        boss_music_path,
        boss_phase_warning_sound,
        energy_pulse_sound,
        event_sounds,
        get_music_volume,
        save_score,
    ):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        self.font = font
        self.game_over_font = game_over_font
        self.restart_font = restart_font
        self.battle_title_font = pygame.font.Font(
            None,
            76,
        )
        self.battle_subtitle_font = pygame.font.Font(
            None,
            33,
        )
        self.ally_label_font = pygame.font.Font(
            None,
            18,
        )

        self.shoot_sound = shoot_sound
        self.enemy_destroy_sound = enemy_destroy_sound
        self.explosion_sound = explosion_sound
        self.boss_music_path = boss_music_path
        self.boss_phase_warning_sound = boss_phase_warning_sound
        self.energy_pulse_sound = energy_pulse_sound
        self.event_sounds = event_sounds
        self.get_music_volume = get_music_volume
        self.save_score = save_score

        # Fundalul luptei folosește același sistem Dead Star din cinematică.
        original_background = pygame.image.load(
            "assets/images/intro/"
            "dead_star_background.png"
        ).convert()
        self.gameplay_background = (
            pygame.transform.smoothscale(
                original_background,
                (
                    self.width + 70,
                    self.height + 50,
                ),
            )
        )

        # Acest strat întunecă fundalul pentru a păstra gameplay-ul lizibil.
        self.background_tint = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )
        self.background_tint.fill(
            (8, 3, 15, 105)
        )

        self.stars = [
            Star(self.width, self.height)
            for _ in range(55)
        ]

        # Managerul coordonează pericolele dinamice din sistemul Dead Star.
        self.space_event_manager = SpaceEventManager(
            self.width,
            self.height,
        )

        self.reset()

    # Resetează lupta și poate porni de la scorul câștigat în campanie.
    def reset(self, starting_score=0):
        # Daca Retry este apasat dupa boss, muzica veche este oprita inainte
        # ca toate valorile luptei sa fie reconstruite.
        if getattr(self, "boss_music_started", False):
            self.stop_boss_music()

        self.starting_score = max(
            0,
            int(starting_score),
        )
        self.player = Player()

        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.explosions = []
        self.powerups = []
        self.hit_effects = []
        self.allied_ships = []
        self.ally_bullets = []
        self.combat_drones = []
        self.storm_asteroids = []
        self.crossfire_turrets = []
        self.crossfire_bullets = []
        self.homing_missiles = []
        self.boss_projectiles = []
        self.crossfire_formation_deployed = False
        self.crossfire_bonus_awarded = False

        # Aceste valori rămân rezervate exclusiv viitorului boss final.
        # Niciun boss intermediar nu mai este creat automat între wave-uri.
        self.boss = None
        self.boss_spawned = False
        self.boss_defeated = False
        self.victory = False
        self.victory_score_saved = False
        self.boss_music_started = False
        self.boss_phase_three_music_set = False
        self.last_audio_event = None

        self.enemy_spawn_timer = 0
        self.spawn_delay = 60

        self.score = self.starting_score
        # Valoare temporară pentru testarea tuturor evenimentelor.
        # După ce terminăm testele, revenim la 5 vieți.
        self.lives = 100
        self.wave = 1
        self.boss_count = 0
        self.enemies_killed = 0

        self.combo = 0
        self.combo_timer = 0
        self.multiplier = 1

        # Fiecare nivel mai puternic lansează mai multe proiectile, așa că are
        # o cadență puțin mai lentă. Astfel arma evoluează fără să elimine
        # instantaneu toți inamicii înainte ca aceștia să poată ataca.
        self.player_shoot_timer = 0
        self.player_shoot_delay = 10
        self.player_shoot_delays = {
            1: 10,
            2: 13,
            3: 16,
            4: 18,
        }

        # După apariția unui upgrade de armă, altul nu poate apărea imediat.
        # 900 de cadre înseamnă aproximativ 15 secunde la 60 FPS.
        self.weapon_drop_cooldown = 0
        self.weapon_drop_cooldown_duration = 900

        # ENERGY PULSE este o abilitate specială încărcată prin luptă.
        # Unda se extinde din navă și fiecare țintă poate fi lovită o singură
        # dată la o activare, indiferent câte cadre rămâne în interiorul ei.
        self.energy_pulse_timer = 0
        self.energy_pulse_duration = 52
        self.energy_pulse_maximum_radius = int(
            math.hypot(self.width, self.height) * 0.55
        )
        self.energy_pulse_hit_objects = set()

        # Efectele de impact sunt controlate aici, separat de viața navei.
        # Flash-ul roșu confirmă lovitura, iar shake-ul mișcă scurt arena.
        self.damage_flash_timer = 0
        self.damage_flash_duration = 18
        self.screen_shake_timer = 0
        self.screen_shake_strength = 0

        # Timerul controleaza prezentarea cinematica dintre fazele bossului.
        self.boss_phase_transition_timer = 0
        self.boss_phase_transition_duration = 150
        self.boss_transition_phase = 1

        # Primul val este precedat de o scurtă introducere cinematică.
        # Pentru testarea bossului pastram doar un singur cadru de asteptare.
        if TEST_BOSS_INSTANT:
            self.battle_intro_duration = 1
        else:
            self.battle_intro_duration = 240
        self.battle_intro_timer = (
            self.battle_intro_duration
        )
        self.first_formation_spawned = False
        self.elite_waves_spawned = set()
        self.background_timer = 0

        # Un wave nu poate fi schimbat instantaneu doar pentru că jucătorul
        # are o armă puternică. După minimum 25 de secunde și 20 de eliminări,
        # spawn-urile se opresc, arena se golește și începe tranziția scurtă.
        self.wave_elapsed_timer = 0
        self.minimum_wave_duration = 1500
        self.wave_transition_timer = 0
        self.wave_transition_duration = 72

        # Evenimentele revin la cooldown la fiecare rundă nouă.
        self.space_event_manager.reset()

        self.game_over = False

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_r and self.game_over:
            self.reset(self.starting_score)

        elif self.victory and event.key in (
            pygame.K_RETURN,
            pygame.K_ESCAPE,
        ):
            return "menu"

        elif event.key == pygame.K_e:
            self._activate_energy_pulse()

        elif event.key == pygame.K_ESCAPE:
            return "pause"

        return None

    # Adaugă energie în funcție de eliminare și de multiplicatorul combo.
    def _charge_energy_pulse(self, base_amount):
        # Țintele distruse chiar de undă nu o pot reîncărca imediat.
        # Această regulă elimină bucla în care o singură activare pregătea
        # aproape instantaneu următoarea utilizare.
        if self.energy_pulse_timer > 0:
            return

        if self.player.special_energy >= self.player.maximum_special_energy:
            return

        # Combo-ul rămâne valoros, dar oferă numai un punct suplimentar la
        # multiplicator x3 sau x5, nu până la patru puncte la fiecare țintă.
        combo_bonus = 1 if self.multiplier >= 3 else 0
        self.player.special_energy = min(
            self.player.maximum_special_energy,
            self.player.special_energy + base_amount + combo_bonus,
        )

    # Pornește unda numai când bara este complet încărcată.
    def _activate_energy_pulse(self):
        ability_is_blocked = (
            self.game_over
            or self.victory
            or self.battle_intro_timer > 0
            or self.boss_phase_transition_timer > 0
            or self.energy_pulse_timer > 0
        )
        if ability_is_blocked:
            return False

        if (
            self.player.special_energy
            < self.player.maximum_special_energy
        ):
            return False

        self.player.special_energy = 0
        self.energy_pulse_timer = self.energy_pulse_duration
        self.energy_pulse_hit_objects.clear()
        self.energy_pulse_sound.play()
        self._trigger_screen_shake(7, 13)
        return True

    # Returnează True când centrul obiectului a fost atins de unda curentă.
    def _energy_pulse_reached(self, object_rect, pulse_radius):
        return math.hypot(
            object_rect.centerx - self.player.rect.centerx,
            object_rect.centery - self.player.rect.centery,
        ) <= pulse_radius

    # Extinde unda, curăță proiectile și rănește pericolele o singură dată.
    def _update_energy_pulse(self):
        if self.energy_pulse_timer <= 0:
            return

        self.energy_pulse_timer -= 1
        pulse_progress = 1.0 - (
            self.energy_pulse_timer
            / self.energy_pulse_duration
        )
        pulse_radius = int(
            self.energy_pulse_maximum_radius
            * pulse_progress
        )

        # Proiectilele dispar numai când frontul undei ajunge la ele.
        projectile_groups = (
            self.enemy_bullets,
            self.boss_projectiles,
            self.crossfire_bullets,
        )
        for projectile_group in projectile_groups:
            for projectile in projectile_group[:]:
                if self._energy_pulse_reached(
                    projectile.rect,
                    pulse_radius,
                ):
                    projectile_group.remove(projectile)

        # Rachetele lovite sunt detonate fără să rănească jucătorul.
        for missile in self.homing_missiles[:]:
            if self._energy_pulse_reached(
                missile.collision_rect,
                pulse_radius,
            ):
                self._detonate_homing_missile(
                    missile,
                    award_score=True,
                    damage_in_blast=False,
                )

        # Navele normale primesc trei puncte de damage; elita rămâne o luptă.
        for enemy in self.enemies[:]:
            object_id = id(enemy)
            if (
                object_id in self.energy_pulse_hit_objects
                or not self._energy_pulse_reached(
                    enemy.rect,
                    pulse_radius,
                )
            ):
                continue

            self.energy_pulse_hit_objects.add(object_id)
            for _ in range(3):
                enemy.take_damage()
                if enemy.is_dead():
                    break

            if enemy.is_dead():
                self._destroy_enemy(enemy)

        # Pericolele evenimentelor primesc damage controlat, nu sunt șterse.
        event_targets = (
            (
                self.combat_drones,
                1,
                lambda target: target.rect,
                lambda target: target.take_damage(),
                lambda target: target.is_dead(),
                self._destroy_combat_drone,
            ),
            (
                self.crossfire_turrets,
                3,
                lambda target: target.rect,
                lambda target: target.take_damage(),
                lambda target: target.is_destroyed(),
                self._destroy_crossfire_turret,
            ),
            (
                self.storm_asteroids,
                2,
                lambda target: target.collision_rect,
                lambda target: target.take_damage(),
                lambda target: target.health <= 0,
                self._destroy_storm_asteroid,
            ),
        )
        for (
            target_group,
            damage,
            get_rect,
            apply_damage,
            is_destroyed,
            destroy_target,
        ) in event_targets:
            for target in target_group[:]:
                object_id = id(target)
                if (
                    object_id in self.energy_pulse_hit_objects
                    or not self._energy_pulse_reached(
                        get_rect(target),
                        pulse_radius,
                    )
                ):
                    continue

                self.energy_pulse_hit_objects.add(object_id)
                for _ in range(damage):
                    apply_damage(target)
                    if is_destroyed(target):
                        break

                if is_destroyed(target):
                    destroy_target(target)

        if self.energy_pulse_timer == 0:
            self.energy_pulse_hit_objects.clear()

    def _shoot(self):
        weapon_level = self.player.weapon_level
        ship_width = self.player.image.get_width()
        center_x = self.player.rect.centerx
        left_weapon_x = self.player.x + ship_width * 0.27
        right_weapon_x = self.player.x + ship_width * 0.73
        bullet_y = self.player.y + 4

        # Nivel 1: un singur laser precis pe centrul navei.
        if weapon_level == 1:
            self.bullets.append(
                Bullet(
                    center_x,
                    bullet_y,
                    weapon_level=1,
                )
            )

        # Nivel 2: două lasere paralele lansate de pe aripi.
        elif weapon_level == 2:
            for bullet_x in (
                left_weapon_x,
                right_weapon_x,
            ):
                self.bullets.append(
                    Bullet(
                        bullet_x,
                        bullet_y,
                        weapon_level=2,
                    )
                )

        # Nivel 3: un laser central și două proiectile diagonale.
        elif weapon_level == 3:
            self.bullets.extend(
                (
                    Bullet(
                        center_x,
                        bullet_y,
                        weapon_level=3,
                    ),
                    Bullet(
                        left_weapon_x,
                        bullet_y + 7,
                        velocity_x=-2.2,
                        velocity_y=-11.7,
                        weapon_level=3,
                    ),
                    Bullet(
                        right_weapon_x,
                        bullet_y + 7,
                        velocity_x=2.2,
                        velocity_y=-11.7,
                        weapon_level=3,
                    ),
                )
            )

        # Nivel 4: două lasere laterale și o lance centrală cu damage dublu.
        else:
            self.bullets.extend(
                (
                    Bullet(
                        center_x,
                        bullet_y - 5,
                        velocity_y=-13.2,
                        damage=2,
                        weapon_level=4,
                        heavy=True,
                    ),
                    Bullet(
                        left_weapon_x,
                        bullet_y + 8,
                        velocity_x=-2.7,
                        velocity_y=-12.0,
                        weapon_level=4,
                    ),
                    Bullet(
                        right_weapon_x,
                        bullet_y + 8,
                        velocity_x=2.7,
                        velocity_y=-12.0,
                        weapon_level=4,
                    ),
                )
            )

        self.shoot_sound.play()

    # Verifica permanent tasta SPACE, nu doar evenimentul unei apasari.
    def _update_player_autofire(self):
        pressed_keys = pygame.key.get_pressed()

        if not pressed_keys[pygame.K_SPACE]:
            # Dupa eliberare, urmatoarea apasare trage imediat.
            self.player_shoot_timer = 0
            return

        if self.player_shoot_timer > 0:
            self.player_shoot_timer -= 1

        if self.player_shoot_timer <= 0:
            self._shoot()
            self.player_shoot_timer = (
                self.player_shoot_delays.get(
                    self.player.weapon_level,
                    self.player_shoot_delay,
                )
            )

    def update(self):
        self.background_timer += 1

        # Cooldown-ul scade inclusiv în momentele scurte de tranziție.
        if self.weapon_drop_cooldown > 0:
            self.weapon_drop_cooldown -= 1

        # Efectele vizuale expiră chiar dacă lupta tocmai s-a încheiat.
        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= 1

        if self.screen_shake_timer > 0:
            self.screen_shake_timer -= 1
        else:
            self.screen_shake_strength = 0

        if self.boss_phase_transition_timer > 0:
            self.boss_phase_transition_timer -= 1

        for star in self.stars:
            star.update()

        if self.game_over or self.victory:
            return

        self.player.move(
            self.width,
            self.height,
        )
        self.player.update()

        # În timpul avertizării jucătorul se poate poziționa,
        # dar inamicii și proiectilele nu sunt încă activate.
        if self.battle_intro_timer > 0:
            self.battle_intro_timer -= 1

            if self.battle_intro_timer == 0:
                if TEST_BOSS_INSTANT:
                    self._start_final_boss_if_ready()
                else:
                    self._spawn_first_wave_formation()

            return

        # În pauza scurtă dintre wave-uri, jucătorul se poate poziționa și
        # poate colecta power-up-uri, dar nu apar alte pericole.
        if self.wave_transition_timer > 0:
            self.wave_transition_timer -= 1
            self._move_objects()
            self._update_effects()
            self._remove_offscreen_objects()
            self._powerup_player_collisions()

            if self.wave_transition_timer == 0:
                self.enemy_spawn_timer = 0
                self._spawn_elite_for_wave()

            return

        self.wave_elapsed_timer += 1

        self._update_player_autofire()
        self._update_combo()
        self._update_difficulty()
        self._update_space_events()
        self._update_allied_reinforcements()
        self._update_drone_swarm()
        self._update_asteroid_storm()
        self._update_crossfire_protocol()
        self._update_homing_missile_barrage()
        self._start_final_boss_if_ready()
        self._spawn_enemies()
        self._enemy_shooting()
        self._update_final_boss()
        self._update_energy_pulse()
        self._move_objects()
        self._update_effects()
        self._remove_offscreen_objects()
        self._handle_collisions()
        self._try_finish_wave()

        if self.lives <= 0:
            # Salvează exact scorul total afișat jucătorului în timpul run-ului.
            self.save_score(self.score)
            self.game_over = True
            self.stop_boss_music()

    # Actualizează pericolele de mediu și aplică efectul impactului.
    def _update_space_events(self):
        # Evenimentele noi nu pornesc în timpul unei lupte cu boss-ul.
        # Dacă un eveniment era deja activ, acesta este lăsat să se termine.
        if (
            self.boss is not None
            and not (
                self.space_event_manager
                .event_is_running()
            )
        ):
            return

        # Imaginea navei include mult spațiu transparent.
        # Un dreptunghi mai mic oferă o coliziune corectă jucătorului.
        player_hitbox = pygame.Rect(
            int(self.player.x + 38),
            int(self.player.y + 25),
            self.player.image.get_width() - 76,
            self.player.image.get_height() - 55,
        )

        event_hit = (
            self.space_event_manager.update(
                player_hitbox,
                self.wave,
                self.player.shield,
            )
        )

        # Gravity Wave impinge nava si curbeaza toate proiectilele.
        # Efectul este aplicat dupa miscarea jucatorului, astfel incat
        # acesta poate lupta permanent impotriva atractiei laterale.
        self._apply_gravity_wave()
        self._apply_black_hole_physics()

        # Cererea este consumată o singură dată când formația aliată sosește.
        if (
            self.space_event_manager
            .consume_reinforcement_deployment()
        ):
            self._deploy_allied_reinforcements()

        drone_squad_size = (
            self.space_event_manager
            .consume_drone_squad_deployment()
        )

        if drone_squad_size > 0:
            self._deploy_drone_squad(
                drone_squad_size
            )

        if not event_hit:
            return

        self._damage_player(
            shake_strength=9,
            shake_duration=13,
        )

    # Aplică într-un singur loc toate regulile unei lovituri primite.
    # Metoda evită codul repetat și garantează același feedback pentru orice atac.
    def _damage_player(
        self,
        shake_strength=8,
        shake_duration=12,
    ):
        # Shield-ul absoarbe prima lovitură fără să consume o viață.
        if self.player.shield:
            self.player.shield = False
            self.player.shield_timer = 0
            self._trigger_screen_shake(4, 7)
            return False

        # În perioada de invulnerabilitate, loviturile noi sunt ignorate.
        if self.player.invincible:
            return False

        self.lives -= 1
        # O lovitură reală scade arma cu un singur nivel.
        # Shield-ul și cadrele de invulnerabilitate nu produc downgrade.
        self.player.downgrade_weapon()
        self.player.invincible = True
        # 105 cadre înseamnă aproximativ 1,75 secunde la 60 FPS.
        self.player.invincible_timer = 105
        self.combo = 0
        self.combo_timer = 0
        self.multiplier = 1

        self.damage_flash_timer = self.damage_flash_duration
        self._trigger_screen_shake(
            shake_strength,
            shake_duration,
        )
        self.hit_effects.append(
            HitEffect(
                self.player.rect.centerx,
                self.player.rect.centery,
            )
        )

        # Dupa update stim exact daca un challenge nou tocmai a inceput.
        self._play_new_event_sound()
        return True

    # Reda o singura data efectul asociat challenge-ului care tocmai a pornit.
    def _play_new_event_sound(self):
        current_event = self.space_event_manager.current_event

        if current_event is self.last_audio_event:
            return

        self.last_audio_event = current_event
        if current_event is None:
            return

        manager = self.space_event_manager
        if current_event is manager.solar_storm:
            event_name = "solar_storm"
        elif current_event is manager.gravity_wave:
            event_name = "gravity_wave"
        elif current_event is manager.reinforcements:
            event_name = "reinforcements"
        elif current_event is manager.drone_swarm:
            event_name = "drone_swarm"
        elif current_event is manager.radiation_cloud:
            event_name = "radiation_cloud"
        elif current_event is manager.black_hole_pulse:
            event_name = "black_hole"
        elif current_event is manager.asteroid_storm:
            event_name = "asteroid_storm"
        elif current_event is manager.crossfire_protocol:
            event_name = "crossfire"
        elif current_event is manager.missile_barrage:
            event_name = "missile_barrage"
        else:
            return

        event_sound = self.event_sounds.get(event_name)
        if event_sound is not None:
            event_sound.play()

    # Pornește sau intensifică mișcarea camerei fără să scurteze un shake activ.
    def _trigger_screen_shake(self, strength, duration):
        self.screen_shake_strength = max(
            self.screen_shake_strength,
            int(strength),
        )
        self.screen_shake_timer = max(
            self.screen_shake_timer,
            int(duration),
        )

    # Aplica forta Gravity Wave fara a produce damage direct.
    def _apply_gravity_wave(self):
        gravity_force = (
            self.space_event_manager
            .get_player_force()
        )
        projectile_curve = (
            self.space_event_manager
            .get_projectile_curve()
        )

        if gravity_force != 0:
            self.player.x += gravity_force

            # Nava ramane mereu complet in interiorul ferestrei.
            self.player.x = max(
                0,
                min(
                    self.width
                    - self.player.image.get_width(),
                    self.player.x,
                ),
            )
            self.player.rect.topleft = (
                int(self.player.x),
                int(self.player.y),
            )

        if projectile_curve == 0:
            return

        # Atat gloantele jucatorului, cat si cele inamice sunt deviate.
        for bullet in self.bullets:
            bullet.x += projectile_curve
            bullet.rect.topleft = (
                int(bullet.x),
                int(bullet.y),
            )

        for enemy_bullet in self.enemy_bullets:
            enemy_bullet.x += projectile_curve
            enemy_bullet.rect.topleft = (
                int(enemy_bullet.x),
                int(enemy_bullet.y),
            )

        for ally_bullet in self.ally_bullets:
            ally_bullet.x += projectile_curve
            ally_bullet.rect.topleft = (
                int(ally_bullet.x),
                int(ally_bullet.y),
            )

    # Aplică atracția radială și absoarbe obiectele ajunse în miez.
    def _apply_black_hole_physics(self):
        gravity_data = (
            self.space_event_manager
            .get_black_hole_gravity_data()
        )

        if gravity_data is None:
            return

        (
            black_hole_x,
            black_hole_y,
            gravity_strength,
            horizon_radius,
            absorption_radius,
        ) = gravity_data

        # Jucătorul poate lupta împotriva forței folosind tastele de mișcare.
        self._pull_object_toward_black_hole(
            self.player,
            black_hole_x,
            black_hole_y,
            gravity_strength,
            1.0,
        )
        self.player.x = max(
            0,
            min(
                self.width
                - self.player.image.get_width(),
                self.player.x,
            ),
        )
        self.player.y = max(
            0,
            min(
                self.height
                - self.player.image.get_height(),
                self.player.y,
            ),
        )
        self.player.rect.topleft = (
            int(self.player.x),
            int(self.player.y),
        )

        # Proiectilele sunt cele mai ușoare și se curbează cel mai puternic.
        projectile_groups = [
            self.bullets,
            self.ally_bullets,
            self.enemy_bullets,
        ]

        for projectile_group in projectile_groups:
            for projectile in projectile_group[:]:
                self._pull_object_toward_black_hole(
                    projectile,
                    black_hole_x,
                    black_hole_y,
                    gravity_strength,
                    1.35,
                )

                if self._object_near_black_hole(
                    projectile,
                    black_hole_x,
                    black_hole_y,
                    absorption_radius,
                ):
                    projectile_group.remove(projectile)

        # Inamicii mari sunt atrași mai lent, dar pot fi înghițiți.
        for enemy in self.enemies[:]:
            self._pull_object_toward_black_hole(
                enemy,
                black_hole_x,
                black_hole_y,
                gravity_strength,
                0.52,
            )

            if self._object_near_black_hole(
                enemy,
                black_hole_x,
                black_hole_y,
                horizon_radius,
            ):
                self.explosions.append(
                    Explosion(
                        enemy.rect.centerx,
                        enemy.rect.centery,
                    )
                )
                self.enemies.remove(enemy)

        # Power-up-urile pot fi pierdute dacă jucătorul nu le recuperează.
        for powerup in self.powerups[:]:
            self._pull_object_toward_black_hole(
                powerup,
                black_hole_x,
                black_hole_y,
                gravity_strength,
                0.72,
            )

            if self._object_near_black_hole(
                powerup,
                black_hole_x,
                black_hole_y,
                absorption_radius,
            ):
                self.powerups.remove(powerup)

        # Aceste liste sunt de obicei goale, deoarece evenimentele nu se
        # suprapun, dar tratamentul păstrează sistemul sigur și extensibil.
        for allied_ship in self.allied_ships:
            self._pull_object_toward_black_hole(
                allied_ship,
                black_hole_x,
                black_hole_y,
                gravity_strength,
                0.58,
            )

        for drone in self.combat_drones:
            self._pull_object_toward_black_hole(
                drone,
                black_hole_x,
                black_hole_y,
                gravity_strength,
                0.72,
            )

    # Calculează forța în funcție de distanța dintre obiect și singularitate.
    def _pull_object_toward_black_hole(
        self,
        game_object,
        black_hole_x,
        black_hole_y,
        gravity_strength,
        force_multiplier,
    ):
        distance_x = (
            black_hole_x - game_object.rect.centerx
        )
        distance_y = (
            black_hole_y - game_object.rect.centery
        )
        distance = max(
            1.0,
            math.hypot(distance_x, distance_y),
        )
        maximum_distance = math.hypot(
            self.width,
            self.height,
        )
        proximity = max(
            0.0,
            1.0 - distance / maximum_distance,
        )
        applied_force = (
            gravity_strength
            * force_multiplier
            * (0.38 + proximity * 1.12)
        )

        game_object.x += (
            distance_x / distance
        ) * applied_force
        game_object.y += (
            distance_y / distance
        ) * applied_force
        game_object.rect.topleft = (
            int(game_object.x),
            int(game_object.y),
        )

    # Verifică distanța dintre centrul unui obiect și miezul găurii negre.
    @staticmethod
    def _object_near_black_hole(
        game_object,
        black_hole_x,
        black_hole_y,
        danger_radius,
    ):
        return math.hypot(
            game_object.rect.centerx - black_hole_x,
            game_object.rect.centery - black_hole_y,
        ) <= danger_radius

    # Creează cele două nave care intră din partea de jos a arenei.
    def _deploy_allied_reinforcements(self):
        self.allied_ships.clear()

        formation_data = [
            (
                int(self.width * 0.28),
                int(self.height * 0.57),
                "ALPHA-1",
            ),
            (
                int(self.width * 0.72),
                int(self.height * 0.62),
                "ALPHA-2",
            ),
        ]

        for center_x, target_y, callsign in formation_data:
            self.allied_ships.append(
                AllyShip(
                    center_x,
                    target_y,
                    self.height,
                    callsign,
                )
            )

    # Actualizează navele aliate și colectează proiectilele lor.
    def _update_allied_reinforcements(self):
        allies_departing = (
            self.space_event_manager
            .reinforcements_are_departing()
        )

        for allied_ship in self.allied_ships[:]:
            if allies_departing:
                allied_ship.start_departure()

            allied_ship.update()

            new_bullet = allied_ship.try_shoot(
                self.enemies
            )

            if new_bullet is not None:
                self.ally_bullets.append(new_bullet)

            if allied_ship.has_departed():
                self.allied_ships.remove(
                    allied_ship
                )

    # Creează un grup de drone în jurul marginilor superioare ale arenei.
    def _deploy_drone_squad(self, squad_size):
        for drone_index in range(squad_size):
            entry_type = drone_index % 3

            if entry_type == 0:
                start_x = random.randint(
                    30,
                    self.width - 80,
                )
                start_y = random.randint(-120, -45)
            elif entry_type == 1:
                start_x = random.randint(-100, -50)
                start_y = random.randint(70, 260)
            else:
                start_x = random.randint(
                    self.width + 45,
                    self.width + 100,
                )
                start_y = random.randint(70, 260)

            self.combat_drones.append(
                CombatDrone(
                    start_x,
                    start_y,
                )
            )

    # Actualizează dronele, retragerea și proiectilele lor țintite.
    def _update_drone_swarm(self):
        swarm_departing = (
            self.space_event_manager
            .drone_swarm_is_departing()
        )

        for drone in self.combat_drones[:]:
            if swarm_departing:
                drone.start_departure()

            drone.update(
                self.player.rect,
                self.width,
                self.height,
            )

            new_bullet = drone.try_shoot(
                self.player.rect
            )

            if new_bullet is not None:
                self.enemy_bullets.append(new_bullet)

            if drone.has_departed():
                self.combat_drones.remove(drone)

    # Creează asteroizii solicitați și accelerează resturile la final.
    def _update_asteroid_storm(self):
        spawn_requests = (
            self.space_event_manager
            .consume_asteroid_spawn_requests()
        )
        difficulty_wave = (
            self.space_event_manager
            .get_asteroid_difficulty_wave()
        )

        for size_type, entry_direction in spawn_requests:
            self.storm_asteroids.append(
                StormAsteroid(
                    self.width,
                    self.height,
                    size_type,
                    entry_direction,
                    difficulty_wave,
                )
            )

        if (
            self.space_event_manager
            .asteroid_storm_is_departing()
        ):
            for asteroid in self.storm_asteroids:
                asteroid.start_departure()

    # Creează formația de patru turele în arcul superior al arenei.
    def _deploy_crossfire_formation(self):
        self.crossfire_turrets.clear()
        formation_data = [
            (0.12, 0.15, "NODE-A"),
            (0.36, 0.27, "NODE-B"),
            (0.64, 0.27, "NODE-C"),
            (0.88, 0.15, "NODE-D"),
        ]

        for turret_index, formation_entry in enumerate(
            formation_data
        ):
            horizontal_ratio, vertical_ratio, callsign = (
                formation_entry
            )
            self.crossfire_turrets.append(
                CrossfireTurret(
                    int(self.width * horizontal_ratio),
                    int(self.height * vertical_ratio),
                    self.width,
                    callsign,
                    turret_index,
                )
            )

        self.crossfire_formation_deployed = True
        self.crossfire_bonus_awarded = False

    # Actualizează turelele, fazele, ultima salvă și retragerea.
    def _update_crossfire_protocol(self):
        if (
            self.space_event_manager
            .consume_crossfire_deployment()
        ):
            self._deploy_crossfire_formation()

        current_phase = (
            self.space_event_manager
            .get_crossfire_phase()
        )
        final_salvo = (
            self.space_event_manager
            .consume_crossfire_final_salvo()
        )
        formation_departing = (
            self.space_event_manager
            .crossfire_is_departing()
        )

        for turret in self.crossfire_turrets[:]:
            if final_salvo:
                self.crossfire_bullets.extend(
                    turret.create_final_salvo(
                        self.player.rect
                    )
                )

            if formation_departing:
                turret.start_departure()

            turret.update()

            if current_phase > 0:
                self.crossfire_bullets.extend(
                    turret.try_shoot(
                        self.player.rect,
                        current_phase,
                    )
                )

            if turret.has_departed():
                self.crossfire_turrets.remove(
                    turret
                )

        # Distrugerea tuturor turelelor termină evenimentul și dă bonus.
        if (
            self.crossfire_formation_deployed
            and not self.crossfire_turrets
            and current_phase > 0
            and not self.crossfire_bonus_awarded
        ):
            event_ended_early = (
                self.space_event_manager
                .notify_crossfire_destroyed()
            )

            if event_ended_early:
                self.score += 1000
                self.crossfire_bonus_awarded = True
                self.crossfire_formation_deployed = False

    # Creeaza si actualizeaza rachetele cerute de cele trei salve.
    def _update_homing_missile_barrage(self):
        launch_requests = (
            self.space_event_manager
            .consume_missile_launch_requests()
        )
        difficulty_wave = (
            self.space_event_manager
            .get_missile_difficulty_wave()
        )

        # Fiecare cerere contine tipul rachetei si marginea de intrare.
        for missile_type, entry_direction in launch_requests:
            self.homing_missiles.append(
                HomingMissile(
                    self.width,
                    self.height,
                    missile_type,
                    entry_direction,
                    difficulty_wave,
                )
            )

        missiles_departing = (
            self.space_event_manager
            .missile_barrage_is_departing()
        )

        for missile in self.homing_missiles[:]:
            # Dupa oprirea retelei, rachetele continua drept inainte.
            if missiles_departing:
                missile.disable_tracking()

            missile.update(
                self.player.rect,
                self.width,
                self.height,
            )

            # Combustibilul terminat provoaca o ultima explozie.
            if missile.is_expired():
                self._detonate_homing_missile(
                    missile,
                    damage_in_blast=True,
                )
            elif missile.is_off_screen(
                self.width,
                self.height,
            ):
                self.homing_missiles.remove(missile)

    # Distruge o racheta, creeaza explozia si poate acorda puncte.
    def _detonate_homing_missile(
        self,
        missile,
        award_score=False,
        damage_in_blast=False,
    ):
        if missile not in self.homing_missiles:
            return

        self.homing_missiles.remove(missile)
        self.explosions.append(
            Explosion(
                missile.rect.centerx,
                missile.rect.centery,
            )
        )

        distance_to_player = math.hypot(
            self.player.rect.centerx
            - missile.rect.centerx,
            self.player.rect.centery
            - missile.rect.centery,
        )
        player_inside_blast = (
            damage_in_blast
            and distance_to_player
            <= missile.blast_radius
        )

        # Rachetele grele si exploziile apropiate primesc efect sonor puternic.
        if (
            missile.missile_type == "heavy"
            or player_inside_blast
        ):
            self.explosion_sound.play()
            self._trigger_screen_shake(
                8 if player_inside_blast else 5,
                11,
            )

        if player_inside_blast:
            self._damage_player_from_missile()

        if award_score:
            self.combo += 1
            self.combo_timer = 170
            self._update_multiplier()
            self.score += (
                missile.points * self.multiplier
            )
            self._charge_energy_pulse(1)

    # Aplica o lovitura navei, respectand shield-ul si invincibilitatea.
    def _damage_player_from_missile(self):
        self._damage_player(
            shake_strength=12,
            shake_duration=16,
        )

    # Creează formația care deschide primul val al războiului.
    def _spawn_first_wave_formation(self):
        if self.first_formation_spawned:
            return

        formation_data = [
            (90, -120, "scout"),
            (315, -190, "scout"),
            (545, -250, "fighter"),
            (830, -190, "scout"),
            (1050, -120, "scout"),
        ]

        for enemy_x, enemy_y, enemy_type in (
            formation_data
        ):
            self.enemies.append(
                Enemy(
                    enemy_x,
                    enemy_y,
                    enemy_type,
                    self.wave,
                )
            )

        # Primul wave primeste elita imediat dupa formatia introductiva.
        self._spawn_elite_for_wave()
        self.first_formation_spawned = True
        self.enemy_spawn_timer = 0

    # Creeaza exact o elita la inceputul fiecarui wave.
    def _spawn_elite_for_wave(self):
        if self.wave in self.elite_waves_spawned:
            return

        elite_width = 250
        self.enemies.append(
            Enemy(
                self.width // 2 - elite_width // 2,
                -300,
                "elite",
                self.wave,
            )
        )
        self.elite_waves_spawned.add(self.wave)

    def _update_combo(self):
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo = 0
            self.multiplier = 1

    def _update_multiplier(self):
        if self.combo >= 50:
            self.multiplier = 5
        elif self.combo >= 25:
            self.multiplier = 3
        elif self.combo >= 10:
            self.multiplier = 2
        else:
            self.multiplier = 1

    def _update_difficulty(self):
        # Ritmul pornește relaxat și crește în principal odată cu wave-ul.
        # Scorul luptei oferă doar un bonus mic, ca progresia să nu sară brusc.
        combat_score = max(
            0,
            self.score - self.starting_score,
        )
        wave_reduction = min(
            28,
            max(0, self.wave - 1) * 4,
        )
        score_reduction = min(
            4,
            combat_score // 5000,
        )
        self.spawn_delay = max(
            38,
            70 - wave_reduction - score_reduction,
        )

    # Creează numai inamici normali; boss-ul final va avea un trigger separat.
    def _spawn_enemies(self):
        # Obiectivul și timpul minim au fost atinse. Nu mai adăugăm nave noi,
        # iar cele aflate deja în arenă își termină atacurile și pleacă.
        if (
            self.enemies_killed >= 20
            and self.wave_elapsed_timer
            >= self.minimum_wave_duration
        ):
            return

        # Solar Storm oprește spawn-urile, deoarece impulsurile umplu arena.
        # Gravity Wave păstrează o luptă mai rară, ca efectul să aibă sens.
        if self.space_event_manager.blocks_enemy_spawns():
            return

        # Când vom adăuga boss-ul final, inamicii normali se vor opri aici.
        if self.boss is not None:
            return

        # Inamicii rămân în arenă, deci limităm numărul simultan.
        gravity_wave_active = (
            self.space_event_manager
            .gravity_wave_is_running()
        )
        reinforcements_active = (
            self.space_event_manager
            .reinforcements_are_active()
        )
        radiation_cloud_active = (
            self.space_event_manager
            .radiation_cloud_is_active()
        )
        black_hole_active = (
            self.space_event_manager
            .black_hole_is_active()
        )

        # Gravity Wave pastreaza lupta activa, dar reduce aglomeratia.
        if gravity_wave_active:
            maximum_enemies = min(
                7,
                3 + self.wave // 2,
            )
            current_spawn_delay = int(
                self.spawn_delay * 1.6
            )
        elif reinforcements_active:
            # Suportul aliat este echilibrat printr-un atac inamic mai mare.
            maximum_enemies = min(
                14,
                7 + self.wave,
            )
            current_spawn_delay = max(
                22,
                int(self.spawn_delay * 0.72),
            )
        elif radiation_cloud_active:
            # Vizibilitatea redusă este compensată prin mai puțini inamici.
            maximum_enemies = min(
                8,
                4 + self.wave // 2,
            )
            current_spawn_delay = int(
                self.spawn_delay * 1.45
            )
        elif black_hole_active:
            # Păstrăm lupta activă, dar evităm prea multe obiecte atrase.
            maximum_enemies = min(
                7,
                3 + self.wave // 2,
            )
            current_spawn_delay = int(
                self.spawn_delay * 1.6
            )
        else:
            maximum_enemies = min(
                12,
                5 + self.wave,
            )
            current_spawn_delay = self.spawn_delay

        if len(self.enemies) >= maximum_enemies:
            return

        self.enemy_spawn_timer += 1

        if self.enemy_spawn_timer < current_spawn_delay:
            return

        enemy_x = random.randint(
            0,
            self.width - 100,
        )

        # La început domină scout-ii. Fiecare wave mută treptat șansa spre
        # fighter și tank, fără să elimine complet niciun tip de inamic.
        composition_progress = min(
            8,
            max(0, self.wave - 1),
        )
        enemy_weights = (
            55 - composition_progress * 4,
            35 + composition_progress,
            10 + composition_progress * 3,
        )
        enemy_type = random.choices(
            ["scout", "fighter", "tank"],
            weights=enemy_weights,
        )[0]

        self.enemies.append(
            Enemy(
                enemy_x,
                -100,
                enemy_type,
                self.wave,
            )
        )

        self.enemy_spawn_timer = 0

    def _enemy_shooting(self):
        event_is_active = (
            self.space_event_manager.event_is_running()
        )

        for enemy in self.enemies:
            # O nava aflata in retragere nu mai poate incepe alt atac.
            if enemy.movement_state == "departing":
                continue

            # Inamicul poate ataca din timpul intrarii, imediat ce partea de jos
            # a navei este vizibila. Nu mai trebuie sa ajunga la patrulare.
            if enemy.rect.bottom < 55:
                continue

            # In timpul challenge-urilor, timerul scade numai o data la doua
            # cadre. Inamicii continua sa atace, dar nu acopera pericolul
            # principal al evenimentului cu prea multe proiectile.
            can_advance_shoot_timer = (
                not event_is_active
                or self.background_timer % 2 == 0
            )

            if (
                enemy.shoot_timer > 0
                and can_advance_shoot_timer
            ):
                enemy.shoot_timer -= 1

            # ELITA: avertizare violet, apoi cinci proiectile in evantai.
            if enemy.enemy_type == "elite":
                if enemy.elite_charge_timer > 0:
                    enemy.elite_charge_timer -= 1

                    if enemy.elite_charge_timer == 0:
                        self._fire_elite_salvo(enemy)
                        enemy.shoot_timer = enemy.get_attack_delay(
                            360,
                            480,
                        )

                    continue

                if enemy.shoot_timer <= 0:
                    enemy.elite_charge_timer = (
                        enemy.elite_charge_duration
                    )

                continue

            # SCOUT ROSU: doua proiectile rapide, trase pe rand intr-o rafala.
            if enemy.enemy_type == "scout":
                if (
                    enemy.burst_shots_remaining <= 0
                    and enemy.shoot_timer <= 0
                ):
                    enemy.burst_shots_remaining = 2
                    enemy.burst_delay = 0

                if enemy.burst_shots_remaining <= 0:
                    continue

                if enemy.burst_delay > 0:
                    enemy.burst_delay -= 1
                    continue

                self.enemy_bullets.append(
                    EnemyBullet(
                        enemy.rect.centerx - 5,
                        enemy.rect.bottom - 8,
                        0,
                        4.7 * enemy.projectile_speed_multiplier,
                        "rapid",
                    )
                )
                enemy.burst_shots_remaining -= 1
                enemy.burst_delay = max(
                    8,
                    int(11 * enemy.attack_cooldown_scale),
                )

                if enemy.burst_shots_remaining == 0:
                    enemy.attacks_completed += 1
                    enemy.shoot_timer = enemy.get_attack_delay(
                        300,
                        390,
                    )

                    if (
                        enemy.attacks_completed
                        >= enemy.maximum_attacks
                    ):
                        enemy.start_departure()

                continue

            if enemy.shoot_timer > 0:
                continue

            # TANK VERDE: trei globuri de plasma intr-un evantai lat.
            if enemy.enemy_type == "tank":
                # Glontul central coboara drept, iar celelalte doua formeaza
                # un evantai simetric si usor de citit in jurul lui.
                center_angle = math.pi / 2

                for angle_offset in (-0.27, 0, 0.27):
                    projectile_angle = center_angle + angle_offset
                    self.enemy_bullets.append(
                        EnemyBullet(
                            enemy.rect.centerx - 6,
                            enemy.rect.bottom - 15,
                            math.cos(projectile_angle)
                            * 3.25
                            * enemy.projectile_speed_multiplier,
                            math.sin(projectile_angle)
                            * 3.25
                            * enemy.projectile_speed_multiplier,
                            "spread",
                        )
                    )

                enemy.shoot_timer = enemy.get_attack_delay(
                    390,
                    510,
                )

                enemy.attacks_completed += 1
                if (
                    enemy.attacks_completed
                    >= enemy.maximum_attacks
                ):
                    enemy.start_departure()

                continue

            # FIGHTER ALBASTRU: lanseaza un proiectil mai lent, drept in jos.
            self.enemy_bullets.append(
                EnemyBullet(
                    enemy.rect.centerx - 8,
                    enemy.rect.bottom - 12,
                    0,
                    3.5 * enemy.projectile_speed_multiplier,
                    "aimed",
                )
            )
            enemy.shoot_timer = enemy.get_attack_delay(
                330,
                450,
            )

            enemy.attacks_completed += 1
            if (
                enemy.attacks_completed
                >= enemy.maximum_attacks
            ):
                enemy.start_departure()

    # Salva elitei este puternica, dar merge in jos si este anuntata din timp.
    def _fire_elite_salvo(self, enemy):
        center_angle = math.pi / 2

        for angle_offset in (-0.36, -0.18, 0, 0.18, 0.36):
            projectile_angle = center_angle + angle_offset
            self.enemy_bullets.append(
                EnemyBullet(
                    enemy.rect.centerx - 7,
                    enemy.rect.bottom - 20,
                    math.cos(projectile_angle)
                    * 3.25
                    * enemy.projectile_speed_multiplier,
                    math.sin(projectile_angle)
                    * 3.25
                    * enemy.projectile_speed_multiplier,
                    "elite",
                )
            )

    # Creeaza bossul imediat dupa terminarea celor noua challenge-uri.
    def _start_final_boss_if_ready(self):
        if self.boss_spawned or self.victory:
            return

        # Modul temporar de test sare peste cele noua challenge-uri.
        if (
            not TEST_BOSS_INSTANT
            and not self.space_event_manager.final_boss_is_ready()
        ):
            return

        # Curatam arena pentru ca intrarea bossului sa fie clara si corecta.
        self.enemies.clear()
        self.enemy_bullets.clear()
        self.combat_drones.clear()
        self.crossfire_turrets.clear()
        self.crossfire_bullets.clear()
        self.storm_asteroids.clear()
        self.homing_missiles.clear()
        self.powerups.clear()

        self.boss = Boss(
            self.width,
            self.height,
        )
        self.boss_spawned = True
        self.boss_defeated = False
        self.boss_projectiles.clear()
        self._start_boss_music()

    # Incarca piesa bossului si o repeta continuu pana la finalul confruntarii.
    def _start_boss_music(self):
        if self.boss_music_started:
            return

        try:
            pygame.mixer.music.fadeout(900)
            pygame.mixer.music.load(self.boss_music_path)
            pygame.mixer.music.set_volume(
                self.get_music_volume() * 0.68
            )
            pygame.mixer.music.play(-1, fade_ms=1200)
            self.boss_music_started = True
        except pygame.error:
            # Jocul continua normal chiar daca sistemul audio nu poate reda muzica.
            self.boss_music_started = False

    # Faza finala mareste intensitatea muzicii fara sa reporneasca piesa.
    def _intensify_boss_music(self):
        if self.boss_phase_three_music_set:
            return

        pygame.mixer.music.set_volume(
            min(1.0, self.get_music_volume() * 0.92)
        )
        self.boss_phase_three_music_set = True

    # Oprirea cu fade evita taierea brusca la Victory sau Game Over.
    def stop_boss_music(self):
        if self.boss_music_started:
            pygame.mixer.music.fadeout(1200)
        self.boss_music_started = False
        self.boss_phase_three_music_set = False

    # Sincronizeaza sliderul Music cu intensitatea fazei curente a bossului.
    def sync_boss_music_volume(self):
        if not self.boss_music_started:
            return

        intensity = (
            0.92
            if self.boss_phase_three_music_set
            else 0.68
        )
        pygame.mixer.music.set_volume(
            min(1.0, self.get_music_volume() * intensity)
        )

    # Actualizeaza miscarea, atacurile si exploziile bossului final.
    def _update_final_boss(self):
        if self.boss is None:
            return

        new_projectiles = self.boss.update(
            self.player.rect
        )

        self.boss_projectiles.extend(new_projectiles)

        explosion_requests = (
            self.boss.consume_explosion_requests()
        )
        for explosion_index, explosion_position in enumerate(
            explosion_requests
        ):
            self.explosions.append(
                Explosion(
                    explosion_position[0],
                    explosion_position[1],
                )
            )
            # Sunetul nu este pornit pentru fiecare explozie simultana.
            if explosion_index == 0:
                self.explosion_sound.play()
                self._trigger_screen_shake(8, 13)

        if (
            self.boss.is_defeated()
            and not self.boss_defeated
        ):
            self.boss_defeated = True
            self.victory = True
            self.stop_boss_music()
            self.score += 10000
            self.combo += 10
            self.combo_timer = 600
            self._update_multiplier()

            if not self.victory_score_saved:
                # Victory folosește același scor total afișat pe HUD.
                self.save_score(self.score)
                self.victory_score_saved = True

    def _move_objects(self):
        for bullet in self.bullets:
            bullet.move()

        for ally_bullet in self.ally_bullets:
            ally_bullet.move()

        for enemy_bullet in self.enemy_bullets:
            enemy_bullet.move(self.player.rect)

        for boss_projectile in self.boss_projectiles:
            boss_projectile.update(
                self.player.rect
            )

        for asteroid in self.storm_asteroids:
            asteroid.update()

        for crossfire_bullet in self.crossfire_bullets:
            crossfire_bullet.move()

        for enemy in self.enemies:
            enemy.move(
                self.width,
                self.height,
            )

        for powerup in self.powerups:
            powerup.move()

    def _update_effects(self):
        for explosion in self.explosions[:]:
            explosion.update()

            if explosion.finished:
                self.explosions.remove(explosion)

        for effect in self.hit_effects[:]:
            effect.update()

            if effect.finished:
                self.hit_effects.remove(effect)

    def _remove_offscreen_objects(self):
        for bullet in self.bullets[:]:
            if bullet.y < -bullet.height:
                self.bullets.remove(bullet)

        for ally_bullet in self.ally_bullets[:]:
            if (
                ally_bullet.y < -ally_bullet.height
                or ally_bullet.x < -ally_bullet.width
                or ally_bullet.x > self.width
            ):
                self.ally_bullets.remove(
                    ally_bullet
                )

        for enemy_bullet in self.enemy_bullets[:]:
            if (
                enemy_bullet.y > self.height + enemy_bullet.height
                or enemy_bullet.x < -enemy_bullet.width
                or enemy_bullet.x > self.width + enemy_bullet.width
            ):
                self.enemy_bullets.remove(enemy_bullet)

        for boss_projectile in self.boss_projectiles[:]:
            if boss_projectile.is_off_screen(
                self.width,
                self.height,
            ):
                self.boss_projectiles.remove(
                    boss_projectile
                )

        for powerup in self.powerups[:]:
            if powerup.y > self.height:
                self.powerups.remove(powerup)

        for asteroid in self.storm_asteroids[:]:
            if asteroid.is_off_screen(
                self.width,
                self.height,
            ):
                self.storm_asteroids.remove(
                    asteroid
                )

        for crossfire_bullet in self.crossfire_bullets[:]:
            if crossfire_bullet.is_off_screen(
                self.width,
                self.height,
            ):
                self.crossfire_bullets.remove(
                    crossfire_bullet
                )

        for enemy in self.enemies[:]:
            # Retragerea dupa doua atacuri nu produce damage, scor sau loot.
            if enemy.has_departed():
                self.enemies.remove(enemy)
                continue

            if enemy.y <= self.height:
                continue

            self.enemies.remove(enemy)

            # În timpul unui eveniment, navele scăpate nu consumă vieți.
            if self.space_event_manager.event_is_running():
                continue

            self.lives -= 1
            self.player.downgrade_weapon()
            self.combo = 0
            self.combo_timer = 0
            self.multiplier = 1

    def _handle_collisions(self):
        self._player_bullet_missile_collisions()
        self._player_bullet_crossfire_collisions()
        self._player_bullet_asteroid_collisions()
        self._player_bullet_drone_collisions()
        self._ally_bullet_enemy_collisions()
        self._player_bullet_enemy_collisions()
        self._player_bullet_boss_collisions()
        self._enemy_bullet_ally_collisions()
        self._enemy_bullet_player_collisions()
        self._boss_projectile_player_collisions()
        self._boss_laser_player_collisions()
        self._crossfire_bullet_player_collisions()
        self._missile_missile_collisions()
        self._missile_player_collisions()
        self._asteroid_player_collisions()
        self._powerup_player_collisions()

    # Gloantele jucatorului pot distruge rachetele inainte de impact.
    def _player_bullet_missile_collisions(self):
        for bullet in self.bullets[:]:
            for missile in self.homing_missiles[:]:
                if not bullet.rect.colliderect(
                    missile.collision_rect
                ):
                    continue

                if bullet in self.bullets:
                    self.bullets.remove(bullet)

                missile_destroyed = False
                for _ in range(bullet.damage):
                    missile_destroyed = (
                        missile.take_damage()
                        or missile_destroyed
                    )
                    if missile_destroyed:
                        break
                self.hit_effects.append(
                    HitEffect(
                        missile.rect.centerx,
                        missile.rect.centery,
                    )
                )

                if missile_destroyed:
                    self._detonate_homing_missile(
                        missile,
                        award_score=True,
                        damage_in_blast=True,
                    )

                break

    # Doua rachete armate se pot lovi si distruge reciproc.
    def _missile_missile_collisions(self):
        missile_snapshot = self.homing_missiles[:]

        for first_index, first_missile in enumerate(
            missile_snapshot
        ):
            if (
                first_missile not in self.homing_missiles
                or not first_missile.is_dangerous()
                or first_missile.age <= 65
            ):
                continue

            for second_missile in missile_snapshot[
                first_index + 1:
            ]:
                if (
                    second_missile not in self.homing_missiles
                    or not second_missile.is_dangerous()
                    or second_missile.age <= 65
                ):
                    continue

                if not first_missile.collision_rect.colliderect(
                    second_missile.collision_rect
                ):
                    continue

                self._detonate_homing_missile(
                    first_missile,
                    damage_in_blast=True,
                )
                self._detonate_homing_missile(
                    second_missile,
                    damage_in_blast=True,
                )
                break

    # Impactul unei rachete armate produce damage si o elimina din arena.
    def _missile_player_collisions(self):
        player_hitbox = pygame.Rect(
            int(self.player.x + 38),
            int(self.player.y + 25),
            self.player.image.get_width() - 76,
            self.player.image.get_height() - 55,
        )

        for missile in self.homing_missiles[:]:
            if (
                not missile.is_dangerous()
                or not player_hitbox.colliderect(
                    missile.collision_rect
                )
            ):
                continue

            self._detonate_homing_missile(
                missile,
                damage_in_blast=True,
            )

    # Proiectilele jucătorului scad viața turelelor Crossfire.
    def _player_bullet_crossfire_collisions(self):
        for bullet in self.bullets[:]:
            for turret in self.crossfire_turrets[:]:
                if not bullet.rect.colliderect(
                    turret.rect
                ):
                    continue

                if bullet in self.bullets:
                    self.bullets.remove(bullet)

                for _ in range(bullet.damage):
                    turret.take_damage()
                    if turret.is_destroyed():
                        break
                self.hit_effects.append(
                    HitEffect(
                        bullet.rect.centerx,
                        bullet.rect.centery,
                    )
                )

                if turret.is_destroyed():
                    self._destroy_crossfire_turret(
                        turret
                    )

                break

    # Elimină turela și acordă puncte pentru reducerea presiunii.
    def _destroy_crossfire_turret(self, turret):
        self.explosions.append(
            Explosion(
                turret.rect.centerx,
                turret.rect.centery,
            )
        )
        self.explosion_sound.play()
        self.combo += 3
        self.combo_timer = 240
        self._update_multiplier()
        self.score += 300 * self.multiplier
        self._charge_energy_pulse(4)

        if turret in self.crossfire_turrets:
            self.crossfire_turrets.remove(turret)

    # Proiectilele Crossfire folosesc hitbox-ul redus al navei.
    def _crossfire_bullet_player_collisions(self):
        player_hitbox = pygame.Rect(
            int(self.player.x + 38),
            int(self.player.y + 25),
            self.player.image.get_width() - 76,
            self.player.image.get_height() - 55,
        )

        for crossfire_bullet in self.crossfire_bullets[:]:
            if not crossfire_bullet.rect.colliderect(
                player_hitbox
            ):
                continue

            self.crossfire_bullets.remove(
                crossfire_bullet
            )

            if self.player.shield:
                self._damage_player()
                continue

            if self.player.invincible:
                continue

            self._damage_player(
                shake_strength=8,
                shake_duration=11,
            )

    # Proiectilele jucătorului scad rezistența asteroizilor.
    def _player_bullet_asteroid_collisions(self):
        for bullet in self.bullets[:]:
            for asteroid in self.storm_asteroids[:]:
                if not bullet.rect.colliderect(
                    asteroid.collision_rect
                ):
                    continue

                if bullet in self.bullets:
                    self.bullets.remove(bullet)

                asteroid_destroyed = False
                for _ in range(bullet.damage):
                    asteroid_destroyed = (
                        asteroid.take_damage()
                        or asteroid_destroyed
                    )
                    if asteroid_destroyed:
                        break
                self.hit_effects.append(
                    HitEffect(
                        bullet.rect.centerx,
                        bullet.rect.centery,
                    )
                )

                if asteroid_destroyed:
                    self._destroy_storm_asteroid(
                        asteroid
                    )

                break

    # Elimină asteroidul și acordă scor în funcție de mărime.
    def _destroy_storm_asteroid(self, asteroid):
        self.explosions.append(
            Explosion(
                asteroid.rect.centerx,
                asteroid.rect.centery,
            )
        )

        if asteroid.radius >= 32:
            self.explosion_sound.play()

        self.combo += 1
        self.combo_timer = 160
        self._update_multiplier()
        self.score += (
            asteroid.points * self.multiplier
        )
        self._charge_energy_pulse(1)

        if asteroid in self.storm_asteroids:
            self.storm_asteroids.remove(asteroid)

    # Coliziunea directă distruge asteroidul și afectează nava.
    def _asteroid_player_collisions(self):
        player_hitbox = pygame.Rect(
            int(self.player.x + 38),
            int(self.player.y + 25),
            self.player.image.get_width() - 76,
            self.player.image.get_height() - 55,
        )

        for asteroid in self.storm_asteroids[:]:
            if not player_hitbox.colliderect(
                asteroid.collision_rect
            ):
                continue

            self.storm_asteroids.remove(asteroid)
            self.explosions.append(
                Explosion(
                    asteroid.rect.centerx,
                    asteroid.rect.centery,
                )
            )

            self._damage_player(
                shake_strength=12,
                shake_duration=16,
            )

            break

    # Proiectilele jucătorului pot distruge dronele dintr-o singură lovitură.
    def _player_bullet_drone_collisions(self):
        for bullet in self.bullets[:]:
            for drone in self.combat_drones[:]:
                if not bullet.rect.colliderect(
                    drone.rect
                ):
                    continue

                for _ in range(bullet.damage):
                    drone.take_damage()
                    if drone.is_dead():
                        break

                if bullet in self.bullets:
                    self.bullets.remove(bullet)

                self.hit_effects.append(
                    HitEffect(
                        drone.rect.centerx,
                        drone.rect.centery,
                    )
                )

                if drone.is_dead():
                    self._destroy_combat_drone(
                        drone
                    )

                break

    # Elimină drona, creează explozia și acordă punctele aferente.
    def _destroy_combat_drone(self, drone):
        self.explosions.append(
            Explosion(
                drone.rect.centerx,
                drone.rect.centery,
            )
        )
        self.explosion_sound.play()
        self.combo += 1
        self.combo_timer = 150
        self._update_multiplier()
        self.score += (
            drone.points * self.multiplier
        )
        self._charge_energy_pulse(2)

        if drone in self.combat_drones:
            self.combat_drones.remove(drone)

    # Proiectilele aliate rănesc inamicii și oferă scor jucătorului.
    def _ally_bullet_enemy_collisions(self):
        for ally_bullet in self.ally_bullets[:]:
            for enemy in self.enemies[:]:
                if not ally_bullet.rect.colliderect(
                    enemy.rect
                ):
                    continue

                enemy.take_damage()

                self.hit_effects.append(
                    HitEffect(
                        enemy.rect.centerx,
                        enemy.rect.centery,
                    )
                )

                if ally_bullet in self.ally_bullets:
                    self.ally_bullets.remove(
                        ally_bullet
                    )

                if enemy.is_dead():
                    self._destroy_enemy(enemy)

                break

    def _player_bullet_enemy_collisions(self):
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if not bullet.rect.colliderect(
                    enemy.rect
                ):
                    continue

                for _ in range(bullet.damage):
                    enemy.take_damage()
                    if enemy.is_dead():
                        break

                self.hit_effects.append(
                    HitEffect(
                        enemy.x
                        + enemy.image.get_width() // 2,
                        enemy.y
                        + enemy.image.get_height() // 2,
                    )
                )

                if bullet in self.bullets:
                    self.bullets.remove(bullet)

                if enemy.is_dead():
                    self._destroy_enemy(enemy)

                break

    def _destroy_enemy(self, enemy):
        enemy_center_x = enemy.rect.centerx
        enemy_center_y = enemy.rect.centery

        if enemy.enemy_type == "elite":
            # Elita se destrama prin mai multe explozii raspandite pe nava.
            # Efectul este mai mare decat explozia unui inamic obisnuit.
            elite_explosion_offsets = [
                (0, 0),
                (-72, -38),
                (72, -38),
                (-52, 48),
                (52, 48),
                (0, -78),
                (0, 78),
            ]
            for offset_x, offset_y in elite_explosion_offsets:
                self.explosions.append(
                    Explosion(
                        enemy_center_x + offset_x,
                        enemy_center_y + offset_y,
                    )
                )

            self._trigger_screen_shake(14, 22)
        else:
            self.explosions.append(
                Explosion(
                    enemy_center_x,
                    enemy_center_y,
                )
            )

        self.explosion_sound.play()

        self.combo += 1
        self.combo_timer = 180
        self._update_multiplier()

        self.score += (
            enemy.points
            * self.multiplier
        )
        self._charge_energy_pulse(
            8 if enemy.enemy_type == "elite" else 2
        )

        # Elita este obiectivul special al wave-ului si nu inlocuieste unul
        # dintre cei 20 de inamici normali necesari pentru wave-ul urmator.
        if enemy.counts_toward_wave:
            self.enemies_killed = min(
                20,
                self.enemies_killed + 1,
            )

        powerup = PowerUp(
            enemy_center_x - 18,
            enemy_center_y - 18,
        )

        if enemy.enemy_type == "elite":
            # Elita oferă garantat un power-up real. Dacă un upgrade de armă
            # a apărut recent, elita oferă scut sau viață ca să nu urcăm prea
            # repede toate cele patru niveluri ale armei.
            if self.weapon_drop_cooldown > 0:
                powerup.powerup_type = random.choice(
                    (
                        "shield",
                        "life",
                    )
                )
            else:
                powerup.powerup_type = random.choice(
                    (
                        "weapon_upgrade",
                        "shield",
                        "life",
                    )
                )

        # Un upgrade de armă valid pornește pauza până la următoarea apariție.
        if powerup.powerup_type == "weapon_upgrade":
            if self.weapon_drop_cooldown > 0:
                powerup.powerup_type = None
            else:
                self.weapon_drop_cooldown = (
                    self.weapon_drop_cooldown_duration
                )

        # Tipul None înseamnă că inamicul nu a lăsat niciun obiect vizibil.
        if powerup.powerup_type is not None:
            self.powerups.append(powerup)

        if enemy in self.enemies:
            self.enemies.remove(enemy)

        # Finalizarea wave-ului este verificată după toate coliziunile cadrului.
        # Astfel nu pornim următorul wave din interiorul unei liste iterate.

    # Închide wave-ul numai când obiectivul, timpul și arena sunt toate gata.
    def _try_finish_wave(self):
        if (
            self.boss is not None
            or self.wave_transition_timer > 0
            or self.enemies_killed < 20
            or self.wave_elapsed_timer < self.minimum_wave_duration
            or self.space_event_manager.event_is_running()
        ):
            return

        arena_still_hostile = (
            bool(self.enemies)
            or bool(self.combat_drones)
            or bool(self.storm_asteroids)
            or bool(self.crossfire_turrets)
            or bool(self.homing_missiles)
        )
        if arena_still_hostile:
            return

        self.wave += 1
        self.enemies_killed = 0
        self.wave_elapsed_timer = 0
        self.wave_transition_timer = (
            self.wave_transition_duration
        )

        # Curățăm doar proiectilele rămase, nu power-up-urile câștigate.
        self.bullets.clear()
        self.enemy_bullets.clear()
        self.boss_projectiles.clear()
        self.crossfire_bullets.clear()
        self._trigger_screen_shake(4, 8)

    def _player_bullet_boss_collisions(self):
        if self.boss is None:
            return

        for bullet in self.bullets[:]:
            hit_result = self.boss.hit_by_player(
                bullet.rect,
                # Bossul primește damage separat echilibrat. La 10x, arma de
                # nivel maxim putea sări o fază înaintea primului atac real.
                damage=5 * bullet.damage,
            )

            # "miss" inseamna ca glontul este inca in spatiul transparent.
            # Il lasam sa continue pana ajunge la corp sau la un generator.
            if hit_result == "miss":
                continue

            if bullet in self.bullets:
                self.bullets.remove(bullet)

            self.hit_effects.append(
                HitEffect(
                    bullet.rect.centerx,
                    bullet.rect.centery,
                )
            )

            if hit_result == "generator_destroyed":
                self.score += 750
                self.combo += 3
                self.combo_timer = 300
                self._update_multiplier()

            elif hit_result == "phase_changed":
                # Tranzitia curata proiectilele vechi si ofera o pauza scurta.
                self.boss_projectiles.clear()
                self.enemy_bullets.clear()
                self.crossfire_bullets.clear()
                self.homing_missiles.clear()
                self.explosion_sound.play()
                self._trigger_screen_shake(14, 24)
                self.boss_phase_transition_timer = (
                    self.boss_phase_transition_duration
                )
                self.boss_transition_phase = self.boss.phase
                # Gameplay deseneaza acum prezentarea completa a fazei,
                # deci ascundem bannerul vechi al bossului ca sa nu se suprapuna.
                self.boss.phase_banner_timer = 0
                self.boss_phase_warning_sound.play()

                if self.boss.phase == 3:
                    self._intensify_boss_music()

            elif hit_result == "destroyed":
                self._destroy_boss()
                break

    # Porneste distrugerea cinematica; bossul ramane vizibil pana la final.
    def _destroy_boss(self):
        if self.boss is None:
            return

        self.boss.begin_destruction()
        self.boss_projectiles.clear()
        self.enemy_bullets.clear()
        self.boss_count = 1
        # Vechiul sunet greu functioneaza mai bine ca impact al unei nave distruse.
        # Il redam mai rar, ca luptele aglomerate sa nu devina zgomotoase.
        if random.random() < 0.55:
            self.enemy_destroy_sound.play()
        self._trigger_screen_shake(18, 32)

    # Navele aliate pot absorbi trei lovituri înainte să fie distruse.
    def _enemy_bullet_ally_collisions(self):
        for enemy_bullet in self.enemy_bullets[:]:
            for allied_ship in self.allied_ships[:]:
                if not enemy_bullet.rect.colliderect(
                    allied_ship.rect
                ):
                    continue

                if enemy_bullet in self.enemy_bullets:
                    self.enemy_bullets.remove(
                        enemy_bullet
                    )

                allied_ship.take_damage()

                self.hit_effects.append(
                    HitEffect(
                        allied_ship.rect.centerx,
                        allied_ship.rect.centery,
                    )
                )

                if allied_ship.is_destroyed():
                    self.explosions.append(
                        Explosion(
                            allied_ship.rect.centerx,
                            allied_ship.rect.centery,
                        )
                    )
                    self.explosion_sound.play()
                    self.allied_ships.remove(
                        allied_ship
                    )

                break

    def _enemy_bullet_player_collisions(self):
        for enemy_bullet in self.enemy_bullets[:]:
            if not enemy_bullet.rect.colliderect(
                self.player.rect
            ):
                continue

            if enemy_bullet in self.enemy_bullets:
                self.enemy_bullets.remove(
                    enemy_bullet
                )

            self._damage_player(
                shake_strength=7,
                shake_duration=10,
            )

    # Proiectilele bossului folosesc hitbox-ul redus al navei.
    def _boss_projectile_player_collisions(self):
        player_hitbox = pygame.Rect(
            int(self.player.x + 38),
            int(self.player.y + 25),
            self.player.image.get_width() - 76,
            self.player.image.get_height() - 55,
        )

        for boss_projectile in self.boss_projectiles[:]:
            if not boss_projectile.rect.colliderect(
                player_hitbox
            ):
                continue

            self.boss_projectiles.remove(
                boss_projectile
            )
            self._damage_player_from_boss()

    # Laserul produce damage numai dupa terminarea avertizarii rosii.
    def _boss_laser_player_collisions(self):
        if self.boss is None:
            return

        player_hitbox = pygame.Rect(
            int(self.player.x + 38),
            int(self.player.y + 25),
            self.player.image.get_width() - 76,
            self.player.image.get_height() - 55,
        )

        for laser in self.boss.lasers:
            if (
                laser.is_dangerous()
                and laser.rect.colliderect(player_hitbox)
            ):
                self._damage_player_from_boss()
                break

    # Shield-ul absoarbe prima lovitura; invincibilitatea evita damage repetat.
    def _damage_player_from_boss(self):
        self._damage_player(
            shake_strength=14,
            shake_duration=19,
        )

    def _powerup_player_collisions(self):
        for powerup in self.powerups[:]:
            if not powerup.rect.colliderect(
                self.player.rect
            ):
                continue

            if powerup.powerup_type in (
                "weapon_upgrade",
                "double_shot",
            ):
                upgraded = self.player.upgrade_weapon()
                if not upgraded:
                    # La nivelul maxim, power-up-ul rămâne valoros prin scor.
                    self.score += 750

            elif powerup.powerup_type == "shield":
                self.player.shield = True
                self.player.shield_timer = 300

            elif powerup.powerup_type == "life":
                if self.lives < 5:
                    self.lives += 1
                else:
                    self.score += 500

            if powerup in self.powerups:
                self.powerups.remove(powerup)

    def draw(self):
        self._draw_dead_star_background()

        for star in self.stars:
            star.draw(self.screen)

        # Stratul este desenat peste stele, astfel încât acestea să fie discrete.
        self.screen.blit(
            self.background_tint,
            (0, 0),
        )

        if self.boss is not None:
            self.boss.draw_lasers(self.screen)

        self.player.draw(self.screen)

        for bullet in self.bullets:
            bullet.draw(self.screen)

        for ally_bullet in self.ally_bullets:
            ally_bullet.draw(self.screen)

        for enemy_bullet in self.enemy_bullets:
            enemy_bullet.draw(self.screen)

        for boss_projectile in self.boss_projectiles:
            boss_projectile.draw(self.screen)

        for crossfire_bullet in self.crossfire_bullets:
            crossfire_bullet.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        for asteroid in self.storm_asteroids:
            asteroid.draw(self.screen)

        for missile in self.homing_missiles:
            missile.draw(
                self.screen,
                self.player.rect,
            )

        for turret in self.crossfire_turrets:
            turret.draw(
                self.screen,
                self.ally_label_font,
            )

        for drone in self.combat_drones:
            drone.draw(self.screen)

        for allied_ship in self.allied_ships:
            allied_ship.draw(
                self.screen,
                self.ally_label_font,
            )

        if self.boss is not None:
            self.boss.draw(self.screen)

        for powerup in self.powerups:
            powerup.draw(self.screen)

        for explosion in self.explosions:
            explosion.draw(self.screen)

        for effect in self.hit_effects:
            effect.draw(self.screen)

        # Evenimentele aparțin arenei, deci se mișcă împreună cu aceasta.
        if not self.game_over and not self.victory:
            self.space_event_manager.draw(
                self.screen
            )

        # Unda aparține arenei și este desenată înainte de aplicarea shake-ului.
        self._draw_energy_pulse()

        # Camera este deplasată numai după ce întreaga arenă a fost desenată.
        # HUD-ul este desenat ulterior și rămâne stabil, ca într-un joc premium.
        self._apply_screen_shake()

        if self.victory:
            draw_game_ui(
                self.screen,
                self.font,
                self.score,
                self.lives,
                self.wave,
                self.multiplier,
                self.player,
            )
            self._draw_victory()
        elif not self.game_over:
            draw_game_ui(
                self.screen,
                self.font,
                self.score,
                self.lives,
                self.wave,
                self.multiplier,
                self.player,
            )

            if self.battle_intro_timer > 0:
                self._draw_battle_intro()

            if self.wave_transition_timer > 0:
                self._draw_wave_transition()

            if self.boss_phase_transition_timer > 0:
                self._draw_boss_phase_transition()
        else:
            self._draw_game_over()

        # Flash-ul este ultimul strat și colorează subtil tot ecranul la impact.
        self._draw_damage_flash()

    # Desenează frontul circular și lumina interioară a abilității speciale.
    def _draw_energy_pulse(self):
        if self.energy_pulse_timer <= 0:
            return

        pulse_progress = 1.0 - (
            self.energy_pulse_timer
            / self.energy_pulse_duration
        )
        pulse_radius = max(
            3,
            int(
                self.energy_pulse_maximum_radius
                * pulse_progress
            ),
        )
        fade = max(0.0, 1.0 - pulse_progress)
        pulse_surface = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )
        pulse_center = self.player.rect.center

        pygame.draw.circle(
            pulse_surface,
            (35, 190, 255, int(28 * fade)),
            pulse_center,
            pulse_radius,
        )
        pygame.draw.circle(
            pulse_surface,
            (115, 235, 255, int(220 * fade)),
            pulse_center,
            pulse_radius,
            7,
        )
        pygame.draw.circle(
            pulse_surface,
            (225, 130, 255, int(170 * fade)),
            pulse_center,
            max(1, pulse_radius - 10),
            3,
        )
        self.screen.blit(pulse_surface, (0, 0))

    # Deplasează pentru câteva cadre imaginea arenei în direcții aleatoare.
    def _apply_screen_shake(self):
        if self.screen_shake_timer <= 0:
            return

        strength = max(1, self.screen_shake_strength)
        offset_x = random.randint(-strength, strength)
        offset_y = random.randint(-strength, strength)

        arena_snapshot = self.screen.copy()
        self.screen.fill((2, 3, 12))
        self.screen.blit(
            arena_snapshot,
            (offset_x, offset_y),
        )

    # Desenează o tentă roșie care dispare rapid după pierderea unei vieți.
    def _draw_damage_flash(self):
        if self.damage_flash_timer <= 0:
            return

        progress = (
            self.damage_flash_timer
            / self.damage_flash_duration
        )
        flash_alpha = int(105 * progress)
        flash = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )
        flash.fill((255, 25, 45, flash_alpha))
        self.screen.blit(flash, (0, 0))

        # Rama luminoasă accentuează impactul fără să ascundă proiectilele.
        border_alpha = int(210 * progress)
        pygame.draw.rect(
            self.screen,
            (255, 65, 80, border_alpha),
            (3, 3, self.width - 6, self.height - 6),
            6,
            border_radius=8,
        )

    # Prezinta noua faza a bossului printr-o secventa scurta si clara.
    def _draw_boss_phase_transition(self):
        timer = self.boss_phase_transition_timer
        duration = self.boss_phase_transition_duration
        elapsed = duration - timer

        # Fade-in rapid, mentinere, apoi fade-out spre revenirea in lupta.
        if elapsed < 24:
            visibility = elapsed / 24
        elif timer < 32:
            visibility = timer / 32
        else:
            visibility = 1.0

        darkness = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )
        darkness.fill((3, 1, 12, int(172 * visibility)))
        self.screen.blit(darkness, (0, 0))

        if self.boss_transition_phase == 2:
            title_text = "PHASE 2  //  DEFENSE NETWORK"
            objective_text = "DESTROY BOTH SHIELD GENERATORS"
            accent_color = (185, 75, 255)
        else:
            title_text = "PHASE 3  //  CORE OVERLOAD"
            objective_text = "THE CORE IS EXPOSED"
            accent_color = (255, 55, 105)

        # Unda luminoasa se extinde din centrul bossului.
        pulse_progress = min(1.0, elapsed / 72)
        pulse_radius = int(45 + pulse_progress * 430)
        pulse_surface = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )
        pygame.draw.circle(
            pulse_surface,
            (*accent_color, int(185 * visibility * (1 - pulse_progress * 0.65))),
            (self.width // 2, 185),
            pulse_radius,
            max(2, int(7 - pulse_progress * 4)),
        )
        self.screen.blit(pulse_surface, (0, 0))

        panel_rect = pygame.Rect(
            self.width // 2 - 400,
            self.height // 2 - 92,
            800,
            184,
        )
        panel = pygame.Surface(
            panel_rect.size,
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            panel,
            (8, 5, 24, int(225 * visibility)),
            panel.get_rect(),
            border_radius=14,
        )
        pygame.draw.rect(
            panel,
            (*accent_color, int(220 * visibility)),
            panel.get_rect(),
            2,
            border_radius=14,
        )
        self.screen.blit(panel, panel_rect.topleft)

        alert = self.ally_label_font.render(
            "WARNING  //  HOSTILE SYSTEM EVOLUTION DETECTED",
            True,
            accent_color,
        )
        title = self.battle_title_font.render(
            title_text,
            True,
            (245, 238, 255),
        )
        objective = self.battle_subtitle_font.render(
            objective_text,
            True,
            (205, 215, 235),
        )

        for text_surface, y_position in (
            (alert, panel_rect.y + 25),
            (title, panel_rect.y + 55),
            (objective, panel_rect.y + 128),
        ):
            text_surface.set_alpha(int(255 * visibility))
            self.screen.blit(
                text_surface,
                (
                    self.width // 2
                    - text_surface.get_width() // 2,
                    y_position,
                ),
            )

    # Deplasează foarte lent fundalul pentru a evita o imagine complet statică.
    def _draw_dead_star_background(self):
        horizontal_offset = int(
            -35
            + math.sin(
                self.background_timer * 0.004
            )
            * 5
        )
        vertical_offset = int(
            -25
            + math.cos(
                self.background_timer * 0.003
            )
            * 3
        )

        self.screen.blit(
            self.gameplay_background,
            (
                horizontal_offset,
                vertical_offset,
            ),
        )

    # Anunță noul wave fără să acopere arena mai mult de 1,2 secunde.
    def _draw_wave_transition(self):
        elapsed_frames = (
            self.wave_transition_duration
            - self.wave_transition_timer
        )
        fade_frames = 14
        if elapsed_frames < fade_frames:
            visibility = elapsed_frames / fade_frames
        elif self.wave_transition_timer < fade_frames:
            visibility = self.wave_transition_timer / fade_frames
        else:
            visibility = 1.0

        banner_width = min(620, self.width - 80)
        banner_height = 118
        banner = pygame.Surface(
            (banner_width, banner_height),
            pygame.SRCALPHA,
        )
        banner.fill((5, 9, 24, int(215 * visibility)))
        pygame.draw.rect(
            banner,
            (65, 190, 255, int(210 * visibility)),
            banner.get_rect(),
            2,
            border_radius=14,
        )
        pygame.draw.line(
            banner,
            (210, 85, 255, int(240 * visibility)),
            (35, 3),
            (banner_width - 35, 3),
            4,
        )

        title_surface = self.battle_title_font.render(
            f"WAVE {self.wave:02d}",
            True,
            (225, 245, 255),
        )
        threat_tier = min(
            5,
            1 + max(0, self.wave - 1) // 2,
        )
        subtitle_surface = self.battle_subtitle_font.render(
            f"THREAT LEVEL {threat_tier}  //  ELITE INBOUND",
            True,
            (215, 125, 255),
        )
        title_surface.set_alpha(int(255 * visibility))
        subtitle_surface.set_alpha(int(255 * visibility))
        banner.blit(
            title_surface,
            (
                banner_width // 2
                - title_surface.get_width() // 2,
                13,
            ),
        )
        banner.blit(
            subtitle_surface,
            (
                banner_width // 2
                - subtitle_surface.get_width() // 2,
                77,
            ),
        )
        self.screen.blit(
            banner,
            (
                self.width // 2 - banner_width // 2,
                self.height // 2 - banner_height // 2,
            ),
        )

    # Desenează avertizarea și titlul primului val.
    def _draw_battle_intro(self):
        elapsed_frames = (
            self.battle_intro_duration
            - self.battle_intro_timer
        )

        if elapsed_frames < 90:
            title = "DEAD STAR COMBAT ZONE"
            subtitle = "ENEMY TERRITORY"
            title_color = (255, 125, 130)
        elif self.battle_intro_timer > 35:
            title = "WAVE 01"
            subtitle = "HOSTILE FLEET INBOUND"
            title_color = (230, 242, 255)
        else:
            title = "ENGAGE"
            subtitle = "WEAPONS FREE"
            title_color = (115, 225, 255)

        banner = pygame.Surface(
            (self.width, 190),
            pygame.SRCALPHA,
        )
        banner.fill((5, 3, 14, 188))
        pygame.draw.line(
            banner,
            (210, 55, 70, 170),
            (0, 2),
            (self.width, 2),
            3,
        )
        pygame.draw.line(
            banner,
            (70, 180, 255, 145),
            (0, banner.get_height() - 3),
            (
                self.width,
                banner.get_height() - 3,
            ),
            3,
        )

        title_surface = self.battle_title_font.render(
            title,
            True,
            title_color,
        )
        subtitle_surface = (
            self.battle_subtitle_font.render(
                subtitle,
                True,
                (205, 218, 235),
            )
        )

        banner.blit(
            title_surface,
            (
                self.width // 2
                - title_surface.get_width() // 2,
                35,
            ),
        )
        banner.blit(
            subtitle_surface,
            (
                self.width // 2
                - subtitle_surface.get_width()
                // 2,
                112,
            ),
        )
        self.screen.blit(
            banner,
            (
                0,
                self.height // 2 - 105,
            ),
        )

    # Desenează panoul central comun pentru Game Over și Victory.
    def _draw_result_panel(
        self,
        title,
        subtitle,
        accent_color,
        prompt,
    ):
        overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )
        overlay.fill((2, 4, 15, 205))
        self.screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(
            self.width // 2 - 395,
            self.height // 2 - 225,
            790,
            450,
        )
        panel = pygame.Surface(
            panel_rect.size,
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            panel,
            (5, 10, 27, 235),
            panel.get_rect(),
            border_radius=20,
        )
        pygame.draw.rect(
            panel,
            (*accent_color, 185),
            panel.get_rect(),
            2,
            border_radius=20,
        )
        pygame.draw.line(
            panel,
            (*accent_color, 245),
            (35, 0),
            (panel_rect.width - 35, 0),
            4,
        )
        self.screen.blit(panel, panel_rect.topleft)

        status_text = self.ally_label_font.render(
            "GALACTIC DEFENSE COMMAND  //  MISSION REPORT",
            True,
            accent_color,
        )
        title_text = self.game_over_font.render(
            title,
            True,
            (238, 246, 255),
        )
        subtitle_text = self.battle_subtitle_font.render(
            subtitle,
            True,
            (175, 193, 218),
        )
        score_label = self.ally_label_font.render(
            "FINAL COMBAT SCORE",
            True,
            (115, 140, 175),
        )
        score_text = self.battle_title_font.render(
            f"{self.score:,}".replace(",", " "),
            True,
            (255, 193, 92),
        )
        prompt_text = self.restart_font.render(
            prompt,
            True,
            (205, 225, 242),
        )

        elements = [
            (status_text, panel_rect.y + 35),
            (title_text, panel_rect.y + 74),
            (subtitle_text, panel_rect.y + 178),
            (score_label, panel_rect.y + 244),
            (score_text, panel_rect.y + 270),
            (prompt_text, panel_rect.y + 372),
        ]
        for surface, y_position in elements:
            self.screen.blit(
                surface,
                (
                    self.width // 2
                    - surface.get_width() // 2,
                    y_position,
                ),
            )

        pygame.draw.line(
            self.screen,
            accent_color,
            (panel_rect.x + 160, panel_rect.y + 352),
            (panel_rect.right - 160, panel_rect.y + 352),
            2,
        )

    # Afișează concluzia luptei după secvența finală de explozii.
    def _draw_victory(self):
        self._draw_result_panel(
            title="GALAXY DEFENDED",
            subtitle="THE DEAD STAR SOVEREIGN HAS FALLEN",
            accent_color=(75, 215, 255),
            prompt="ENTER  //  RETURN TO MAIN MENU",
        )

    # Afișează raportul de înfrângere și comanda pentru o nouă încercare.
    def _draw_game_over(self):
        self._draw_result_panel(
            title="MISSION FAILED",
            subtitle="YOUR SHIP WAS LOST IN ENEMY TERRITORY",
            accent_color=(255, 73, 105),
            prompt="R  //  RETRY MISSION",
        )
