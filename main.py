import math
import random
from pathlib import Path

import pygame

# Importă clasele folosite de aplicație.
from background import Star
from display_manager import DisplayManager
from enemy import Enemy
from gameplay import Gameplay
from intro.anomaly_scene import AnomalyScene
from intro.asteroid_scene import AsteroidScene
from intro.dead_star_scene import DeadStarScene
from intro.hangar_scene import HangarScene
from intro.launch_scene import LaunchScene
from intro.planet_scene import PlanetScene
from intro.vortex_scene import VortexScene
from intro.wormhole_scene import WormholeScene
from player import Player
from save_manager import SaveManager
from scene_manager import SceneManager


# Dimensiunea ferestrei și numărul maxim de cadre pe secundă.
WIDTH = 1280
HEIGHT = 720
FPS = 60


# Clasa principală a jocului.
# Ea inițializează Pygame și coordonează meniul, scenele și gameplay-ul.
class GalaxyDefender:

    # Creează fereastra, sunetele, meniul, gameplay-ul și toate butoanele.
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        # Setările de bază ale ferestrei.
        self.width = WIDTH
        self.height = HEIGHT
        self.running = True

        # Încarcă progresul și setările salvate ale jucătorului.
        self.save_manager = SaveManager()
        saved_data = self.save_manager.data

        self.music_volume = saved_data[
            "music_volume"
        ]
        self.sound_volume = saved_data[
            "sound_volume"
        ]
        self.fullscreen = saved_data["fullscreen"]
        self.selected_resolution = tuple(
            saved_data["resolution"]
        )

        # Creează fereastra principală a jocului.
        self.display_manager = DisplayManager(
            resolution=self.selected_resolution,
            fullscreen=self.fullscreen,
        )
        self.selected_resolution = (
            self.display_manager.resolution
        )
        self.screen = self.display_manager.canvas
        pygame.display.set_caption(
            "Galaxy Defender"
        )

        self.clock = pygame.time.Clock()

        # SceneManager reține ce ecran este activ în acest moment.
        self.scene_manager = SceneManager(
            SceneManager.MENU
        )

        # Fonturile folosite în meniu, HUD și ecranul Game Over.
        self.font = pygame.font.Font(None, 40)
        self.game_over_font = pygame.font.Font(
            None,
            90,
        )
        self.restart_font = pygame.font.Font(
            None,
            40,
        )
        self.menu_font = pygame.font.Font(None, 55)
        self.menu_button_font = pygame.font.Font(None, 32)
        self.menu_label_font = pygame.font.Font(None, 21)
        self.menu_subtitle_font = pygame.font.Font(None, 27)
        self.menu_micro_font = pygame.font.Font(None, 16)
        self.menu_protocol_font = pygame.font.Font(None, 19)
        self.archive_score_font = pygame.font.Font(None, 43)
        self.archive_rank_font = pygame.font.Font(None, 29)
        self.archive_row_font = pygame.font.Font(None, 23)
        self.pause_value_font = pygame.font.Font(None, 36)
        self.pause_button_font = pygame.font.Font(None, 27)
        self.title_font = pygame.font.Font(
            None,
            100,
        )

        # Laserul jucatorului este foarte scurt, ca sa ramana placut la autofire.
        self.shoot_sound = pygame.mixer.Sound(
            "assets/sounds/laser_shot.wav"
        )
        # Vechiul sunet de shotgun este pastrat pentru distrugerea inamicilor.
        self.enemy_destroy_sound = pygame.mixer.Sound(
            "assets/sounds/enemy_destroy.wav"
        )
        self.explosion_sound = pygame.mixer.Sound(
            "assets/sounds/explosion.wav"
        )
        self.boss_phase_warning_sound = pygame.mixer.Sound(
            "assets/sounds/boss_phase_warning.wav"
        )
        self.energy_pulse_sound = pygame.mixer.Sound(
            "assets/sounds/energy_pulse.wav"
        )

        # Fiecare challenge are o semnatura audio proprie, redata o singura data.
        event_sound_files = {
            "solar_storm": "event_solar_storm.wav",
            "gravity_wave": "event_gravity_wave.wav",
            "reinforcements": "event_reinforcements.wav",
            "drone_swarm": "event_drone_swarm.wav",
            "radiation_cloud": "event_radiation_cloud.wav",
            "black_hole": "event_black_hole.wav",
            "asteroid_storm": "event_asteroid_storm.wav",
            "crossfire": "event_crossfire.wav",
            "missile_barrage": "event_missile_barrage.wav",
        }
        self.event_sounds = {
            event_name: pygame.mixer.Sound(
                f"assets/sounds/{file_name}"
            )
            for event_name, file_name in event_sound_files.items()
        }

        # Directorul audio retine piesa activa si evita repornirea ei continuu.
        self.music_tracks = {
            "menu": "assets/music/menu_music.wav",
            "cinematic": "assets/music/cinematic_music.wav",
            "gameplay": "assets/music/gameplay_music.wav",
        }
        self.current_music_mode = None

        # Ambiantele scenelor ruleaza pe un canal separat fata de muzica.
        # Astfel, muzica cinematică ramane continua intre cadrele povestii.
        # Canalul 0 este rezervat exclusiv ambiantelor cinematice.
        # Altfel, Pygame il putea reutiliza pentru gloante sau explozii si
        # intrerupea imediat sunetul de fundal al scenei.
        pygame.mixer.set_num_channels(16)
        pygame.mixer.set_reserved(2)
        self.ambience_channel = pygame.mixer.Channel(0)
        self.scene_action_channel = pygame.mixer.Channel(1)
        ambience_files = {
            SceneManager.PLANET: "ambience_planet.wav",
            SceneManager.HANGAR: "ambience_hangar.wav",
            SceneManager.LAUNCH: "ambience_launch.wav",
            SceneManager.VORTEX: "ambience_vortex.wav",
            SceneManager.ASTEROIDS: "ambience_asteroids.wav",
            SceneManager.ANOMALY: "ambience_anomaly.wav",
            SceneManager.WORMHOLE: "ambience_wormhole.wav",
            SceneManager.DEAD_STAR: "ambience_dead_star.wav",
        }
        self.scene_ambiences = {
            scene_name: pygame.mixer.Sound(
                f"assets/sounds/{file_name}"
            )
            for scene_name, file_name in ambience_files.items()
        }
        # Aceste piste nu sunt muzica: contin actiunile exact sincronizate
        # cu timpul fiecarei scene (verificari, motoare, lansare, alarme etc.).
        scene_action_files = {
            SceneManager.PLANET: "scene_action_planet.wav",
            SceneManager.HANGAR: "scene_action_hangar.wav",
            SceneManager.LAUNCH: "scene_action_launch.wav",
            SceneManager.VORTEX: "scene_action_vortex.wav",
            SceneManager.ASTEROIDS: "scene_action_asteroids.wav",
            SceneManager.ANOMALY: "scene_action_anomaly.wav",
            SceneManager.WORMHOLE: "scene_action_wormhole.wav",
            SceneManager.DEAD_STAR: "scene_action_dead_star.wav",
        }
        self.scene_action_sounds = {
            scene_name: pygame.mixer.Sound(
                f"assets/sounds/{file_name}"
            )
            for scene_name, file_name in scene_action_files.items()
        }
        self.current_ambience_scene = None
        self._apply_sound_volume()
        pygame.mixer.music.set_volume(
            self.music_volume
        )

        # Creează obiectul care conține toate mecanicile de gameplay.
        self.gameplay = Gameplay(
            screen=self.screen,
            font=self.font,
            game_over_font=self.game_over_font,
            restart_font=self.restart_font,
            shoot_sound=self.shoot_sound,
            enemy_destroy_sound=self.enemy_destroy_sound,
            explosion_sound=self.explosion_sound,
            boss_music_path="assets/music/boss_music.wav",
            boss_phase_warning_sound=self.boss_phase_warning_sound,
            energy_pulse_sound=self.energy_pulse_sound,
            event_sounds=self.event_sounds,
            get_music_volume=lambda: self.music_volume,
            save_score=self.save_score,
            get_best_score=lambda: self.save_manager.data[
                "highest_score"
            ],
        )

        # Jocul porneste cu atmosfera calma a meniului principal.
        self._play_music_mode("menu", fade_ms=900)

        # Creează prima scenă cinematică a campaniei.
        self.planet_scene = PlanetScene(
            self.screen
        )

        # Creează scena în care nava este verificată înainte de lansare.
        self.hangar_scene = HangarScene(
            self.screen
        )

        # Creează scena în care nava părăsește planeta și urcă spre spațiu.
        self.launch_scene = LaunchScene(
            self.screen
        )

        # Creează scena de apropiere de anomalia gravitațională.
        self.vortex_scene = VortexScene(
            self.screen
        )

        # Creează primul nivel jucabil al campaniei: câmpul de asteroizi.
        self.asteroid_scene = AsteroidScene(
            self.screen
        )

        # Creează avertizarea gravitațională de după câmpul de asteroizi.
        self.anomaly_scene = AnomalyScene(
            self.screen
        )

        # Creează tranzitul prin wormhole și momentul de ieșire.
        self.wormhole_scene = WormholeScene(
            self.screen
        )

        # Creează ultima secvență a intro-ului în sistemul Dead Star.
        self.dead_star_scene = DeadStarScene(
            self.screen
        )

        # Încarcă și redimensionează fundalul meniului.
        self.menu_background = pygame.image.load(
            "assets/images/menu_background.png"
        ).convert()
        self.menu_background = pygame.transform.scale(
            self.menu_background,
            (self.width, self.height),
        )
        self.menu_interface_overlay = (
            self._create_menu_interface_overlay()
        )

        # Creează nava și obiectele decorative din meniul principal.
        self.menu_player = Player()
        self.menu_ship_base_x = 153
        self.menu_ship_base_y = 476
        self.menu_ship_float_timer = 0.0
        self.menu_player.x = self.menu_ship_base_x
        self.menu_player.y = self.menu_ship_base_y
        self.menu_player.rect.topleft = (
            self.menu_player.x,
            self.menu_player.y,
        )

        # Fundalul meniului contine deja un camp de stele detaliat.
        # Nu mai adaugam particule albe sau inamici decorativi peste el,
        # deoarece aglomerau imaginea si pareau fulgi de zapada.
        self.stars = []
        self.menu_enemies = []
        self.menu_enemy_spawn_timer = 0
        self.logo_timer = 0
        self.confirm_new_game = False
        self.confirm_new_game_timer = 0
        self.confirm_new_game_animation_duration = 36
        self.leaderboard_animation_timer = 0
        self.leaderboard_animation_duration = 64
        self.pause_animation_timer = 0
        self.pause_animation_duration = 48
        self.settings_animation_timer = 0
        self.settings_animation_duration = 52
        self.settings_saved_feedback_timer = 0
        self.active_settings_slider = None

        self._create_buttons()

    # Creeaza o singura data vignette-ul si liniile sci-fi ale meniului.
    def _create_menu_interface_overlay(self):
        overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )

        # Gradientele laterale separa informatia de fundalul ilustrat.
        for horizontal_x in range(self.width):
            left_ratio = max(
                0.0,
                1.0 - horizontal_x / 560,
            )
            right_ratio = max(
                0.0,
                (horizontal_x - (self.width - 520)) / 520,
            )
            darkness = int(
                max(left_ratio * 115, right_ratio * 165)
            )

            if darkness > 0:
                pygame.draw.line(
                    overlay,
                    (2, 6, 18, darkness),
                    (horizontal_x, 0),
                    (horizontal_x, self.height),
                )

        pygame.draw.line(
            overlay,
            (70, 190, 255, 135),
            (54, 58),
            (54, self.height - 58),
            2,
        )
        pygame.draw.line(
            overlay,
            (190, 65, 255, 105),
            (self.width - 54, 58),
            (self.width - 54, self.height - 58),
            2,
        )

        # Marcajele scurte sugereaza o interfata de navigatie spatiala.
        for marker_y in range(85, self.height - 60, 55):
            pygame.draw.line(
                overlay,
                (75, 150, 205, 95),
                (54, marker_y),
                (68, marker_y),
                1,
            )
            pygame.draw.line(
                overlay,
                (155, 85, 210, 80),
                (self.width - 68, marker_y),
                (self.width - 54, marker_y),
                1,
            )

        return overlay

    # Creează dreptunghiurile folosite pentru detectarea clickurilor pe butoane.
    def _create_buttons(self):
        menu_button_x = self.width - 425
        menu_button_width = 340
        menu_button_height = 58

        self.play_button = pygame.Rect(
            menu_button_x,
            286,
            menu_button_width,
            menu_button_height,
        )
        self.leaderboard_button = pygame.Rect(
            menu_button_x,
            364,
            menu_button_width,
            menu_button_height,
        )
        self.settings_button = pygame.Rect(
            menu_button_x,
            442,
            menu_button_width,
            menu_button_height,
        )
        self.exit_button = pygame.Rect(
            menu_button_x,
            520,
            menu_button_width,
            menu_button_height,
        )

        self.continue_button = pygame.Rect(
            menu_button_x,
            220,
            menu_button_width,
            54,
        )
        self.new_game_button = pygame.Rect(
            menu_button_x,
            288,
            menu_button_width,
            54,
        )
        self.saved_leaderboard_button = pygame.Rect(
            menu_button_x,
            356,
            menu_button_width,
            54,
        )
        self.saved_settings_button = pygame.Rect(
            menu_button_x,
            424,
            menu_button_width,
            54,
        )
        self.saved_exit_button = pygame.Rect(
            menu_button_x,
            492,
            menu_button_width,
            54,
        )

        self.confirm_new_game_button = pygame.Rect(
            310,
            455,
            310,
            62,
        )
        self.cancel_new_game_button = pygame.Rect(
            660,
            455,
            310,
            62,
        )
        self.leaderboard_back_button = pygame.Rect(
            470,
            625,
            340,
            50,
        )

        self.resume_button = pygame.Rect(
            690,
            310,
            325,
            62,
        )
        self.pause_settings_button = pygame.Rect(
            690,
            390,
            325,
            62,
        )
        self.pause_menu_button = pygame.Rect(
            690,
            470,
            325,
            62,
        )

        self.music_minus_button = pygame.Rect(
            160,
            303,
            42,
            42,
        )
        self.music_plus_button = pygame.Rect(
            550,
            303,
            42,
            42,
        )
        self.sound_minus_button = pygame.Rect(
            160,
            408,
            42,
            42,
        )
        self.sound_plus_button = pygame.Rect(
            550,
            408,
            42,
            42,
        )
        self.music_slider_rect = pygame.Rect(
            215,
            315,
            320,
            18,
        )
        self.sound_slider_rect = pygame.Rect(
            215,
            420,
            320,
            18,
        )
        self.resolution_minus_button = pygame.Rect(
            690,
            303,
            48,
            48,
        )
        self.resolution_plus_button = pygame.Rect(
            1062,
            303,
            48,
            48,
        )
        self.fullscreen_button = pygame.Rect(
            965,
            386,
            130,
            44,
        )
        self.settings_back_button = pygame.Rect(
            470,
            625,
            340,
            50,
        )

    # Citește scorurile din leaderboard.txt și păstrează primele zece rezultate.
    @staticmethod
    def load_leaderboard():
        leaderboard_path = (
            Path(__file__).resolve().parent
            / "leaderboard.txt"
        )

        try:
            scores = []

            with leaderboard_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                for line in file:
                    line = line.strip()

                    if line.isdigit():
                        scores.append(int(line))

            scores.sort(reverse=True)
            return scores[:10]

        except FileNotFoundError:
            return []

    # Salvează un scor nou în leaderboard și păstrează doar primele zece scoruri.
    def save_score(self, score):
        leaderboard_path = (
            Path(__file__).resolve().parent
            / "leaderboard.txt"
        )

        scores = self.load_leaderboard()
        scores.append(score)
        scores.sort(reverse=True)

        with leaderboard_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            for saved_score in scores[:10]:
                file.write(f"{saved_score}\n")

        # Salvează și recordul general în save.json.
        self.save_manager.save_highest_score(
            score
        )

    # Aplică volumul ales tuturor efectelor sonore folosite de gameplay.
    def _apply_sound_volume(self):
        self.shoot_sound.set_volume(
            self.sound_volume * 0.48
        )
        self.enemy_destroy_sound.set_volume(
            self.sound_volume * 0.55
        )
        self.explosion_sound.set_volume(
            self.sound_volume
        )
        self.boss_phase_warning_sound.set_volume(
            self.sound_volume * 0.72
        )
        self.energy_pulse_sound.set_volume(
            self.sound_volume * 0.82
        )
        for event_sound in self.event_sounds.values():
            event_sound.set_volume(
                self.sound_volume * 0.62
            )
        # Ambianta este tinuta sub muzica si efectele importante ale scenei.
        self.ambience_channel.set_volume(
            self.sound_volume * 0.28
        )
        # Actiunile sincronizate trebuie auzite clar peste muzica si ambianta.
        self.scene_action_channel.set_volume(
            self.sound_volume
        )

    # Schimba numai stratul ambiental atunci cand se schimba scena cinematica.
    def _sync_scene_ambience(self):
        current_scene = self.scene_manager.current_scene

        if current_scene == self.current_ambience_scene:
            return

        self.ambience_channel.fadeout(450)
        self.scene_action_channel.fadeout(180)
        self.current_ambience_scene = None

        ambience = self.scene_ambiences.get(current_scene)
        if ambience is None:
            return

        self.ambience_channel.play(
            ambience,
            loops=-1,
            fade_ms=550,
        )

        scene_action = self.scene_action_sounds.get(
            current_scene
        )
        if scene_action is not None:
            # Pista porneste de la secunda zero impreuna cu scena si nu se repeta.
            self.scene_action_channel.play(
                scene_action,
                loops=0,
                fade_ms=80,
            )
        self.current_ambience_scene = current_scene

    # Porneste piesa ceruta numai daca nu este deja activa.
    def _play_music_mode(self, music_mode, fade_ms=800):
        if self.current_music_mode == music_mode:
            return

        if music_mode is None:
            pygame.mixer.music.fadeout(fade_ms)
            self.current_music_mode = None
            return

        try:
            pygame.mixer.music.fadeout(fade_ms)
            pygame.mixer.music.load(
                self.music_tracks[music_mode]
            )
            # Muzica sustine scena, dar nu acopera motoarele si actiunile.
            mode_gain = {
                "menu": 0.70,
                "cinematic": 0.42,
                "gameplay": 0.68,
            }.get(music_mode, 1.0)
            pygame.mixer.music.set_volume(
                self.music_volume * mode_gain
            )
            pygame.mixer.music.play(-1, fade_ms=fade_ms)
            self.current_music_mode = music_mode
        except pygame.error:
            # Lipsa unui dispozitiv audio nu opreste jocul.
            self.current_music_mode = None

    # Alege automat muzica potrivita pentru scena afisata.
    def _sync_scene_music(self):
        current_scene = self.scene_manager.current_scene
        cinematic_scenes = {
            SceneManager.PLANET,
            SceneManager.HANGAR,
            SceneManager.LAUNCH,
            SceneManager.VORTEX,
            SceneManager.ASTEROIDS,
            SceneManager.ANOMALY,
            SceneManager.WORMHOLE,
            SceneManager.DEAD_STAR,
        }

        # Settings poate fi deschis si peste Pause; in acel caz pastram
        # muzica luptei, nu schimbam atmosfera cu cea a meniului.
        settings_from_pause = (
            current_scene == SceneManager.SETTINGS
            and self.scene_manager.previous_scene
            == SceneManager.PAUSE
        )

        if settings_from_pause:
            if self.gameplay.boss_music_started:
                self.current_music_mode = "boss"
                return
            desired_mode = "gameplay"
        elif current_scene in (
            SceneManager.MENU,
            SceneManager.LEADERBOARD,
            SceneManager.SETTINGS,
        ):
            desired_mode = "menu"
        elif current_scene in cinematic_scenes:
            desired_mode = "cinematic"
        elif current_scene in (
            SceneManager.GAMEPLAY,
            SceneManager.PAUSE,
        ):
            if self.gameplay.boss_music_started:
                self.current_music_mode = "boss"
                return
            if self.gameplay.victory or self.gameplay.game_over:
                desired_mode = None
            else:
                desired_mode = "gameplay"
        else:
            desired_mode = "menu"

        self._play_music_mode(desired_mode)

    # Bucla principală: citește evenimentele, actualizează jocul și desenează scena.
    def run(self):
        while self.running:
            # delta_time reprezintă timpul trecut de la cadrul anterior.
            # Scenele cinematice îl folosesc pentru animații independente de FPS.
            delta_time = (
                self.clock.tick(FPS) / 1000.0
            )

            for event in pygame.event.get():
                self.handle_event(event)

            self.update(delta_time)
            self.draw()

            # Copiaza cadrul logic pe monitor atunci cand suntem in fullscreen.
            self._present_frame()
            pygame.display.flip()

        pygame.quit()

    # Trimite fiecare eveniment către scena care este activă.
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        current_scene = (
            self.scene_manager.current_scene
        )

        if current_scene == SceneManager.PLANET:
            planet_action = (
                self.planet_scene.handle_event(event)
            )

            if planet_action == "hangar":
                self._finish_planet_scene()
            elif planet_action == "menu":
                self.scene_manager.change_scene(
                    SceneManager.MENU
                )

            return

        if current_scene == SceneManager.HANGAR:
            hangar_action = (
                self.hangar_scene.handle_event(event)
            )

            if hangar_action == "launch":
                self._finish_hangar_scene()
            elif hangar_action == "menu":
                self.scene_manager.change_scene(
                    SceneManager.MENU
                )

            return

        if current_scene == SceneManager.LAUNCH:
            launch_action = (
                self.launch_scene.handle_event(event)
            )

            if launch_action == "vortex":
                self._finish_launch_scene()
            elif launch_action == "menu":
                self.scene_manager.change_scene(
                    SceneManager.MENU
                )

            return

        if current_scene == SceneManager.VORTEX:
            vortex_action = (
                self.vortex_scene.handle_event(event)
            )

            if vortex_action == "asteroids":
                self._finish_vortex_scene()
            elif vortex_action == "menu":
                self.scene_manager.change_scene(
                    SceneManager.MENU
                )

            return

        if current_scene == SceneManager.ASTEROIDS:
            asteroid_action = (
                self.asteroid_scene.handle_event(event)
            )

            if asteroid_action == "anomaly":
                self._finish_asteroid_scene()
            elif asteroid_action == "retry":
                self.asteroid_scene.reset(
                    self.save_manager.data[
                        "campaign_score"
                    ]
                )
                self.save_manager.save_checkpoint(
                    SceneManager.ASTEROIDS,
                    0,
                )
            elif asteroid_action == "menu":
                self.scene_manager.change_scene(
                    SceneManager.MENU
                )

            return

        if current_scene == SceneManager.ANOMALY:
            anomaly_action = (
                self.anomaly_scene.handle_event(event)
            )

            if anomaly_action == "wormhole":
                self._finish_anomaly_scene()
            elif anomaly_action == "menu":
                self.scene_manager.change_scene(
                    SceneManager.MENU
                )

            return

        if current_scene == SceneManager.WORMHOLE:
            wormhole_action = (
                self.wormhole_scene.handle_event(event)
            )

            if wormhole_action == "dead_star":
                self._finish_wormhole_scene()
            elif wormhole_action == "menu":
                self.scene_manager.change_scene(
                    SceneManager.MENU
                )

            return

        if current_scene == SceneManager.DEAD_STAR:
            dead_star_action = (
                self.dead_star_scene.handle_event(event)
            )

            if dead_star_action == "gameplay":
                self._finish_dead_star_scene()
            elif dead_star_action == "menu":
                self.scene_manager.change_scene(
                    SceneManager.MENU
                )

            return

        if current_scene == SceneManager.GAMEPLAY:
            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            ):
                gameplay_action = self.gameplay.handle_click(
                    self._to_game_position(event.pos)
                )
            else:
                gameplay_action = self.gameplay.handle_event(event)

            if gameplay_action == "pause":
                self.scene_manager.change_scene(
                    SceneManager.PAUSE
                )
            elif gameplay_action == "menu":
                # Dupa Victory, ENTER sau ESC revine in meniul principal.
                self.scene_manager.change_scene(
                    SceneManager.MENU
                )
            elif gameplay_action == "leaderboard":
                self.scene_manager.change_scene(
                    SceneManager.LEADERBOARD
                )

            return

        if current_scene == SceneManager.SETTINGS:
            if (
                event.type == pygame.MOUSEMOTION
                and self.active_settings_slider is not None
            ):
                logical_position = self._to_game_position(event.pos)
                self._set_settings_slider_from_position(
                    self.active_settings_slider,
                    logical_position[0],
                )
                return

            if (
                event.type == pygame.MOUSEBUTTONUP
                and event.button == 1
                and self.active_settings_slider is not None
            ):
                logical_position = self._to_game_position(event.pos)
                self._set_settings_slider_from_position(
                    self.active_settings_slider,
                    logical_position[0],
                )
                self.active_settings_slider = None
                self._save_current_settings()
                return

        if event.type == pygame.KEYDOWN:
            if (
                current_scene == SceneManager.MENU
                and self.confirm_new_game
            ):
                if event.key in (
                    pygame.K_y,
                    pygame.K_RETURN,
                ):
                    self._confirm_new_campaign()
                elif event.key in (
                    pygame.K_n,
                    pygame.K_ESCAPE,
                ):
                    self._cancel_new_game_confirmation()
                return

            if event.key == pygame.K_ESCAPE:
                self._handle_escape()
                return

            if (
                event.key == pygame.K_RETURN
                and current_scene == SceneManager.LEADERBOARD
            ):
                self.scene_manager.change_scene(
                    SceneManager.MENU
                )
                return

            if (
                event.key == pygame.K_RETURN
                and current_scene == SceneManager.MENU
            ):
                if (
                    self.save_manager
                    .has_campaign_progress()
                ):
                    self._continue_campaign()
                else:
                    self._start_first_campaign()
                return

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            self._handle_click(
                self._to_game_position(event.pos)
            )

    # Controlează acțiunea tastei ESC în funcție de scena curentă.
    def _handle_escape(self):
        current_scene = (
            self.scene_manager.current_scene
        )

        if current_scene == SceneManager.PAUSE:
            self.scene_manager.change_scene(
                SceneManager.GAMEPLAY
            )

        elif current_scene in (
            SceneManager.LEADERBOARD,
            SceneManager.SETTINGS,
        ):
            if (
                current_scene == SceneManager.SETTINGS
                and self.active_settings_slider is not None
            ):
                self.active_settings_slider = None
                self._save_current_settings()
            self.scene_manager.go_back()

    # Direcționează clickul către meniul, pauza sau setările active.
    def _handle_click(self, mouse_position):
        current_scene = (
            self.scene_manager.current_scene
        )

        if current_scene == SceneManager.MENU:
            self._handle_menu_click(mouse_position)

        elif current_scene == SceneManager.PAUSE:
            self._handle_pause_click(mouse_position)

        elif current_scene == SceneManager.SETTINGS:
            self._handle_settings_click(
                mouse_position
            )

        elif current_scene == SceneManager.LEADERBOARD:
            if self.leaderboard_back_button.collidepoint(
                mouse_position
            ):
                self.scene_manager.change_scene(
                    SceneManager.MENU
                )

    # Procesează butoanele PLAY, LEADERBOARD, SETTINGS și EXIT.
    def _handle_menu_click(self, mouse_position):
        if self.confirm_new_game:
            if self.confirm_new_game_timer < 14:
                return

            if (
                self.confirm_new_game_button.collidepoint(
                    mouse_position
                )
            ):
                self._confirm_new_campaign()

            elif (
                self.cancel_new_game_button.collidepoint(
                    mouse_position
                )
            ):
                self._cancel_new_game_confirmation()

            return

        for button_rect, button_text, action in (
            self._get_menu_buttons()
        ):
            if not button_rect.collidepoint(
                mouse_position
            ):
                continue

            if action == "play":
                self._start_first_campaign()

            elif action == "continue":
                self._continue_campaign()

            elif action == "new_game":
                self.confirm_new_game = True
                self.confirm_new_game_timer = 0

            elif action == "leaderboard":
                self.scene_manager.change_scene(
                    SceneManager.LEADERBOARD
                )

            elif action == "settings":
                self.scene_manager.change_scene(
                    SceneManager.SETTINGS
                )

            elif action == "exit":
                self.running = False

            break

    # Procesează butoanele RESUME, SETTINGS și MAIN MENU din pauză.
    def _handle_pause_click(self, mouse_position):
        if self.resume_button.collidepoint(
            mouse_position
        ):
            self.scene_manager.change_scene(
                SceneManager.GAMEPLAY
            )

        elif self.pause_settings_button.collidepoint(
            mouse_position
        ):
            self.scene_manager.change_scene(
                SceneManager.SETTINGS
            )

        elif self.pause_menu_button.collidepoint(
            mouse_position
        ):
            self.gameplay.stop_boss_music()
            self.scene_manager.change_scene(
                SceneManager.MENU
            )

    # Transformă poziția mouse-ului într-o valoare de volum între 0 și 100%.
    def _set_settings_slider_from_position(
        self,
        slider_name,
        mouse_x,
    ):
        slider_rect = (
            self.music_slider_rect
            if slider_name == "music"
            else self.sound_slider_rect
        )
        slider_value = max(
            0.0,
            min(
                1.0,
                (mouse_x - slider_rect.x) / slider_rect.width,
            ),
        )

        if slider_name == "music":
            self.music_volume = slider_value
            pygame.mixer.music.set_volume(self.music_volume)
            self.gameplay.sync_boss_music_volume()
        else:
            self.sound_volume = slider_value
            self._apply_sound_volume()

    # Modifică volumul, fullscreen-ul sau revine la scena anterioară.
    def _handle_settings_click(
        self,
        mouse_position,
    ):
        if self.music_slider_rect.collidepoint(mouse_position):
            self.active_settings_slider = "music"
            self._set_settings_slider_from_position(
                "music",
                mouse_position[0],
            )

        elif self.sound_slider_rect.collidepoint(mouse_position):
            self.active_settings_slider = "sound"
            self._set_settings_slider_from_position(
                "sound",
                mouse_position[0],
            )

        elif self.music_minus_button.collidepoint(
            mouse_position
        ):
            self.music_volume = max(
                0.0,
                self.music_volume - 0.1,
            )
            pygame.mixer.music.set_volume(
                self.music_volume
            )
            self.gameplay.sync_boss_music_volume()
            self._save_current_settings()

        elif self.music_plus_button.collidepoint(
            mouse_position
        ):
            self.music_volume = min(
                1.0,
                self.music_volume + 0.1,
            )
            pygame.mixer.music.set_volume(
                self.music_volume
            )
            self.gameplay.sync_boss_music_volume()
            self._save_current_settings()

        elif self.sound_minus_button.collidepoint(
            mouse_position
        ):
            self.sound_volume = max(
                0.0,
                self.sound_volume - 0.1,
            )
            self._apply_sound_volume()
            self._save_current_settings()

        elif self.sound_plus_button.collidepoint(
            mouse_position
        ):
            self.sound_volume = min(
                1.0,
                self.sound_volume + 0.1,
            )
            self._apply_sound_volume()
            self._save_current_settings()

        elif self.resolution_minus_button.collidepoint(
            mouse_position
        ):
            self._change_resolution(-1)

        elif self.resolution_plus_button.collidepoint(
            mouse_position
        ):
            self._change_resolution(1)

        elif self.fullscreen_button.collidepoint(
            mouse_position
        ):
            self._toggle_fullscreen()

        elif self.settings_back_button.collidepoint(
            mouse_position
        ):
            self.active_settings_slider = None
            self.scene_manager.go_back()

    # Resetează lupta și păstrează scorul câștigat în campanie.
    def _start_gameplay(
        self,
        starting_score=None,
    ):
        if starting_score is None:
            starting_score = (
                self.save_manager.data[
                    "campaign_score"
                ]
            )

        self.gameplay.reset(starting_score)
        self.scene_manager.change_scene(
            SceneManager.GAMEPLAY
        )

    # Pornește campania completă de la planeta natală.
    def _start_first_campaign(self):
        self.planet_scene.reset()
        self.save_manager.save_checkpoint(
            SceneManager.PLANET,
            0,
            campaign_score=0,
        )
        self.scene_manager.change_scene(
            SceneManager.PLANET
        )

    # Încheie scena planetei și intră în hangarul bazei militare.
    def _finish_planet_scene(self):
        self.hangar_scene.reset()
        self.save_manager.save_checkpoint(
            SceneManager.HANGAR,
            0,
        )
        self.scene_manager.change_scene(
            SceneManager.HANGAR
        )

    # Încheie scena Hangar și pornește lansarea navei.
    def _finish_hangar_scene(self):
        self.launch_scene.reset()
        self.save_manager.save_checkpoint(
            SceneManager.LAUNCH,
            0,
        )
        self.scene_manager.change_scene(
            SceneManager.LAUNCH
        )

    # Încheie lansarea navei și pornește apropierea de vortex.
    def _finish_launch_scene(self):
        self.vortex_scene.reset()
        self.save_manager.save_checkpoint(
            SceneManager.VORTEX,
            0,
        )
        self.scene_manager.change_scene(
            SceneManager.VORTEX
        )

    # Încheie apropierea de vortex și pornește Asteroid Ocean.
    def _finish_vortex_scene(self):
        self.asteroid_scene.reset(
            self.save_manager.data[
                "campaign_score"
            ]
        )
        self.save_manager.save_checkpoint(
            SceneManager.ASTEROIDS,
            0,
        )
        self.scene_manager.change_scene(
            SceneManager.ASTEROIDS
        )

    # Încheie Asteroid Ocean și salvează scorul înainte de anomalie.
    def _finish_asteroid_scene(self):
        campaign_score = self.asteroid_scene.score
        self.save_manager.save_checkpoint(
            SceneManager.ANOMALY,
            0,
            campaign_score=campaign_score,
        )
        self.anomaly_scene.reset()
        self.scene_manager.change_scene(
            SceneManager.ANOMALY
        )

    # Încheie avertizarea gravitațională și intră în wormhole.
    def _finish_anomaly_scene(self):
        campaign_score = (
            self.save_manager.data[
                "campaign_score"
            ]
        )
        self.save_manager.save_checkpoint(
            SceneManager.WORMHOLE,
            0,
            campaign_score=campaign_score,
        )
        self.wormhole_scene.reset()
        self.scene_manager.change_scene(
            SceneManager.WORMHOLE
        )

    # Încheie tranzitul prin wormhole și intră în sistemul Dead Star.
    def _finish_wormhole_scene(self):
        campaign_score = (
            self.save_manager.data[
                "campaign_score"
            ]
        )
        self.save_manager.save_checkpoint(
            SceneManager.DEAD_STAR,
            0,
            campaign_score=campaign_score,
        )
        self.dead_star_scene.reset()
        self.scene_manager.change_scene(
            SceneManager.DEAD_STAR
        )

    # Încheie intro-ul, salvează progresul și pornește războiul principal.
    def _finish_dead_star_scene(self):
        campaign_score = (
            self.save_manager.data[
                "campaign_score"
            ]
        )
        self.save_manager.complete_intro(
            current_scene=SceneManager.GAMEPLAY,
            checkpoint=0,
        )
        self._start_gameplay(campaign_score)

    # Continuă campania de la scena și checkpoint-ul salvate.
    # Până când scenele campaniei sunt implementate, pornește gameplay-ul.
    def _continue_campaign(self):
        saved_scene = self.save_manager.data[
            "current_scene"
        ]

        if saved_scene == SceneManager.PLANET:
            self.planet_scene.reset()
            self.scene_manager.change_scene(
                SceneManager.PLANET
            )
        elif saved_scene == SceneManager.HANGAR:
            self.hangar_scene.reset()
            self.scene_manager.change_scene(
                SceneManager.HANGAR
            )
        elif saved_scene == SceneManager.LAUNCH:
            self.launch_scene.reset()
            self.scene_manager.change_scene(
                SceneManager.LAUNCH
            )
        elif saved_scene == SceneManager.VORTEX:
            self.vortex_scene.reset()
            self.scene_manager.change_scene(
                SceneManager.VORTEX
            )
        elif saved_scene == SceneManager.ASTEROIDS:
            self.asteroid_scene.reset(
                self.save_manager.data[
                    "campaign_score"
                ]
            )
            self.scene_manager.change_scene(
                SceneManager.ASTEROIDS
            )
        elif saved_scene == SceneManager.ANOMALY:
            self.anomaly_scene.reset()
            self.scene_manager.change_scene(
                SceneManager.ANOMALY
            )
        elif saved_scene == SceneManager.WORMHOLE:
            self.wormhole_scene.reset()
            self.scene_manager.change_scene(
                SceneManager.WORMHOLE
            )
        elif saved_scene == SceneManager.DEAD_STAR:
            self.dead_star_scene.reset()
            self.scene_manager.change_scene(
                SceneManager.DEAD_STAR
            )
        else:
            self._start_gameplay()

    # Confirmă NEW GAME și resetează numai progresul campaniei.
    def _confirm_new_campaign(self):
        self.save_manager.reset_campaign()
        self.confirm_new_game = False
        self.confirm_new_game_timer = 0

        self._start_first_campaign()

    # Închide avertizarea fără să modifice progresul existent.
    def _cancel_new_game_confirmation(self):
        self.confirm_new_game = False
        self.confirm_new_game_timer = 0

    # Salvează imediat valorile curente din meniul Settings.
    def _save_current_settings(self):
        self.save_manager.save_settings(
            self.music_volume,
            self.sound_volume,
            self.fullscreen,
            self.selected_resolution,
        )
        self.settings_saved_feedback_timer = 90

    # Trimite cadrul logic către fereastra controlată de DisplayManager.
    def _present_frame(self):
        self.display_manager.present()

    # Transforma pozitia fizica a mouse-ului in coordonate de joc 1280x720.
    def _to_game_position(self, mouse_position):
        return self.display_manager.to_game_position(
            mouse_position
        )

    # Returneaza pozitia mouse-ului deja adaptata la rezolutia jocului.
    def _get_mouse_position(self):
        return self.display_manager.get_mouse_position()

    # Activează sau dezactivează fullscreen la rezoluția selectată.
    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.display_manager.set_fullscreen(
            self.fullscreen
        )
        self.selected_resolution = (
            self.display_manager.resolution
        )
        self.screen = self.display_manager.canvas
        self._sync_scene_surfaces()
        self._save_current_settings()

    # Schimbă rezoluția și reconstruiește în siguranță toate suprafețele.
    def _change_resolution(self, direction):
        self.selected_resolution = (
            self.display_manager.cycle_resolution(
                direction
            )
        )
        self.screen = self.display_manager.canvas
        self._sync_scene_surfaces()
        self._save_current_settings()

    # Scenele păstrează referința către noul canvas după schimbarea modului.
    def _sync_scene_surfaces(self):
        self.gameplay.screen = self.screen
        self.planet_scene.screen = self.screen
        self.hangar_scene.screen = self.screen
        self.launch_scene.screen = self.screen
        self.vortex_scene.screen = self.screen
        self.asteroid_scene.screen = self.screen
        self.anomaly_scene.screen = self.screen
        self.wormhole_scene.screen = self.screen
        self.dead_star_scene.screen = self.screen

    # Actualizează numai scena care este activă.
    def update(self, delta_time):
        current_scene = (
            self.scene_manager.current_scene
        )

        if current_scene == SceneManager.MENU:
            self._update_menu()

        elif current_scene == SceneManager.LEADERBOARD:
            self.leaderboard_animation_timer = min(
                self.leaderboard_animation_duration,
                self.leaderboard_animation_timer + 1,
            )

        elif current_scene == SceneManager.PAUSE:
            self.pause_animation_timer = min(
                self.pause_animation_duration,
                self.pause_animation_timer + 1,
            )

        elif current_scene == SceneManager.SETTINGS:
            self.settings_animation_timer = min(
                self.settings_animation_duration,
                self.settings_animation_timer + 1,
            )
            if self.settings_saved_feedback_timer > 0:
                self.settings_saved_feedback_timer -= 1

        elif current_scene == SceneManager.PLANET:
            planet_action = (
                self.planet_scene.update(delta_time)
            )

            if planet_action == "hangar":
                self._finish_planet_scene()

        elif current_scene == SceneManager.HANGAR:
            hangar_action = (
                self.hangar_scene.update(delta_time)
            )

            if hangar_action == "launch":
                self._finish_hangar_scene()

        elif current_scene == SceneManager.LAUNCH:
            launch_action = (
                self.launch_scene.update(delta_time)
            )

            if launch_action == "vortex":
                self._finish_launch_scene()

        elif current_scene == SceneManager.VORTEX:
            vortex_action = (
                self.vortex_scene.update(delta_time)
            )

            if vortex_action == "asteroids":
                self._finish_vortex_scene()

        elif current_scene == SceneManager.ASTEROIDS:
            asteroid_action = (
                self.asteroid_scene.update(delta_time)
            )

            if asteroid_action == "anomaly":
                self._finish_asteroid_scene()

        elif current_scene == SceneManager.ANOMALY:
            anomaly_action = (
                self.anomaly_scene.update(delta_time)
            )

            if anomaly_action == "wormhole":
                self._finish_anomaly_scene()

        elif current_scene == SceneManager.WORMHOLE:
            wormhole_action = (
                self.wormhole_scene.update(delta_time)
            )

            if wormhole_action == "dead_star":
                self._finish_wormhole_scene()

        elif current_scene == SceneManager.DEAD_STAR:
            dead_star_action = (
                self.dead_star_scene.update(delta_time)
            )

            if dead_star_action == "gameplay":
                self._finish_dead_star_scene()

        elif current_scene == SceneManager.GAMEPLAY:
            self.gameplay.update()

        if current_scene != SceneManager.LEADERBOARD:
            self.leaderboard_animation_timer = 0

        if current_scene != SceneManager.PAUSE:
            self.pause_animation_timer = 0

        if current_scene != SceneManager.SETTINGS:
            self.settings_animation_timer = 0
            self.active_settings_slider = None

        # Scenele se pot schimba in timpul update-ului; muzica se sincronizeaza dupa.
        self._sync_scene_music()
        self._sync_scene_ambience()

    # Actualizează animațiile decorative din meniul principal.
    def _update_menu(self):
        if self.confirm_new_game:
            self.confirm_new_game_timer = min(
                self.confirm_new_game_animation_duration,
                self.confirm_new_game_timer + 1,
            )

        self.menu_ship_float_timer += 0.035
        self.menu_player.x = self.menu_ship_base_x + math.sin(
            self.menu_ship_float_timer * 0.58
        ) * 2.0
        self.menu_player.y = self.menu_ship_base_y + math.sin(
            self.menu_ship_float_timer
        ) * 7.0

        self.menu_player.rect.topleft = (
            self.menu_player.x,
            self.menu_player.y,
        )
        self.menu_player.update_engine()

        self.logo_timer += 0.05

    # Alege și desenează scena activă.
    def draw(self):
        current_scene = (
            self.scene_manager.current_scene
        )

        if current_scene == SceneManager.MENU:
            self._draw_menu()

        elif current_scene == SceneManager.PLANET:
            self.planet_scene.draw()

        elif current_scene == SceneManager.HANGAR:
            self.hangar_scene.draw()

        elif current_scene == SceneManager.LAUNCH:
            self.launch_scene.draw()

        elif current_scene == SceneManager.VORTEX:
            self.vortex_scene.draw()

        elif current_scene == SceneManager.ASTEROIDS:
            self.asteroid_scene.draw()

        elif current_scene == SceneManager.ANOMALY:
            self.anomaly_scene.draw()

        elif current_scene == SceneManager.WORMHOLE:
            self.wormhole_scene.draw()

        elif current_scene == SceneManager.DEAD_STAR:
            self.dead_star_scene.draw()

        elif current_scene == SceneManager.GAMEPLAY:
            self.gameplay.set_pointer_position(
                self._get_mouse_position()
            )
            self.gameplay.draw()

        elif current_scene == SceneManager.PAUSE:
            self._draw_pause()

        elif current_scene == SceneManager.LEADERBOARD:
            self._draw_leaderboard()

        elif current_scene == SceneManager.SETTINGS:
            self._draw_settings()

    # Desenează fundalul, nava, inamicii decorativi, logo-ul și butoanele meniului.
    def _draw_menu(self):
        self.screen.blit(
            self.menu_background,
            (0, 0),
        )

        # Vignette-ul pastreaza fundalul vizibil, dar face textul lizibil.
        self.screen.blit(
            self.menu_interface_overlay,
            (0, 0),
        )

        self._draw_menu_ship_showcase()
        self.menu_player.draw(self.screen)
        self._draw_menu_ship_scan_overlay()

        self._draw_logo()
        self._draw_menu_mission_panel()
        mouse_position = self._get_mouse_position()
        menu_buttons = self._get_menu_buttons()

        self._draw_menu_navigation_panel(
            mouse_position,
            menu_buttons,
        )

        for button_rect, button_text, action in menu_buttons:
            self._draw_menu_navigation_button(
                button_rect,
                button_text,
                action,
                mouse_position,
                primary=(action in ("continue", "play")),
            )

        if self.confirm_new_game:
            self._draw_new_game_confirmation()

    @staticmethod
    def _format_menu_score(value):
        return f"{max(0, int(value)):,}".replace(",", " ")

    # Afișează progresul real al campaniei și datele salvate ale pilotului.
    def _draw_menu_mission_panel(self):
        panel_rect = pygame.Rect(
            82,
            230,
            430,
            224,
        )

        shadow = pygame.Surface(
            (panel_rect.width + 20, panel_rect.height + 20),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            shadow,
            (0, 0, 10, 115),
            shadow.get_rect(),
            border_radius=18,
        )
        self.screen.blit(
            shadow,
            (panel_rect.x - 10, panel_rect.y - 7),
        )

        panel_surface = pygame.Surface(
            panel_rect.size,
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            panel_surface,
            (4, 12, 29, 225),
            panel_surface.get_rect(),
            border_radius=15,
        )
        pygame.draw.rect(
            panel_surface,
            (55, 175, 230, 175),
            panel_surface.get_rect(),
            2,
            border_radius=15,
        )
        pygame.draw.rect(
            panel_surface,
            (20, 50, 78, 45),
            pygame.Rect(8, 8, panel_rect.width - 16, 44),
            border_radius=10,
        )
        pygame.draw.line(
            panel_surface,
            (70, 210, 255, 220),
            (18, 46),
            (214, 46),
            2,
        )
        pygame.draw.line(
            panel_surface,
            (120, 80, 205, 85),
            (214, 46),
            (panel_rect.width - 18, 46),
            1,
        )

        for corner_x, direction in (
            (16, 1),
            (panel_rect.width - 16, -1),
        ):
            pygame.draw.line(
                panel_surface,
                (80, 215, 255, 190),
                (corner_x, 1),
                (corner_x + direction * 23, 1),
                3,
            )
        self.screen.blit(panel_surface, panel_rect.topleft)

        saved_data = self.save_manager.data
        scene_order = (
            SceneManager.PLANET,
            SceneManager.HANGAR,
            SceneManager.LAUNCH,
            SceneManager.VORTEX,
            SceneManager.ASTEROIDS,
            SceneManager.ANOMALY,
            SceneManager.WORMHOLE,
            SceneManager.DEAD_STAR,
            SceneManager.GAMEPLAY,
        )
        current_scene = saved_data.get(
            "current_scene",
            SceneManager.PLANET,
        )
        scene_index = (
            scene_order.index(current_scene)
            if current_scene in scene_order
            else 0
        )
        campaign_progress = int(
            scene_index / (len(scene_order) - 1) * 100
        )
        sector_names = {
            SceneManager.PLANET: "HOMEWORLD",
            SceneManager.HANGAR: "LAUNCH BAY",
            SceneManager.LAUNCH: "ORBITAL ASCENT",
            SceneManager.VORTEX: "VORTEX EDGE",
            SceneManager.ASTEROIDS: "ASTEROID OCEAN",
            SceneManager.ANOMALY: "GRAVITY ANOMALY",
            SceneManager.WORMHOLE: "WORMHOLE",
            SceneManager.DEAD_STAR: "DEAD STAR",
            SceneManager.GAMEPLAY: "WAR ZONE",
        }

        header = self.menu_label_font.render(
            "MISSION BRIEFING",
            True,
            (100, 205, 255),
        )
        link_status = self.menu_micro_font.render(
            "CAMPAIGN // LINKED"
            if self.save_manager.has_campaign_progress()
            else "CAMPAIGN // NEW",
            True,
            (90, 230, 180)
            if self.save_manager.has_campaign_progress()
            else (255, 184, 82),
        )
        mission = self.menu_subtitle_font.render(
            "DEAD STAR CAMPAIGN",
            True,
            (235, 244, 255),
        )
        progress_label = self.menu_micro_font.render(
            "CAMPAIGN PROGRESS",
            True,
            (105, 130, 162),
        )
        progress_value = self.menu_label_font.render(
            f"{campaign_progress:02d}%",
            True,
            (100, 220, 255),
        )

        self.screen.blit(header, (panel_rect.x + 20, panel_rect.y + 16))
        self.screen.blit(
            link_status,
            (
                panel_rect.right - link_status.get_width() - 20,
                panel_rect.y + 20,
            ),
        )
        self.screen.blit(mission, (panel_rect.x + 20, panel_rect.y + 57))
        self.screen.blit(
            progress_label,
            (panel_rect.x + 20, panel_rect.y + 88),
        )
        self.screen.blit(
            progress_value,
            (
                panel_rect.right - progress_value.get_width() - 20,
                panel_rect.y + 84,
            ),
        )

        # Bara segmentată arată exact cât din călătoria cinematică a fost parcurs.
        segment_count = len(scene_order)
        segment_gap = 4
        progress_x = panel_rect.x + 20
        progress_y = panel_rect.y + 108
        progress_width = panel_rect.width - 40
        segment_width = (
            progress_width - segment_gap * (segment_count - 1)
        ) // segment_count
        active_segments = scene_index + 1
        if not self.save_manager.has_campaign_progress():
            active_segments = 0

        for segment_index in range(segment_count):
            segment_rect = pygame.Rect(
                progress_x
                + segment_index * (segment_width + segment_gap),
                progress_y,
                segment_width,
                7,
            )
            if segment_index < active_segments:
                segment_color = (
                    70 + min(70, segment_index * 8),
                    185 + min(45, segment_index * 5),
                    255,
                )
            else:
                segment_color = (28, 55, 82)
            pygame.draw.rect(
                self.screen,
                segment_color,
                segment_rect,
                border_radius=3,
            )

        card_y = panel_rect.y + 130
        card_gap = 8
        card_width = 125
        card_height = 58
        card_data = (
            (
                "CURRENT SECTOR",
                sector_names.get(current_scene, "UNKNOWN"),
            ),
            (
                "CHECKPOINT",
                f"{max(0, int(saved_data.get('checkpoint', 0))):02d}",
            ),
            (
                "BEST SCORE",
                self._format_menu_score(
                    saved_data.get("highest_score", 0)
                ),
            ),
        )
        for card_index, (card_label, card_value) in enumerate(card_data):
            card_rect = pygame.Rect(
                panel_rect.x
                + 20
                + card_index * (card_width + card_gap),
                card_y,
                card_width,
                card_height,
            )
            card_surface = pygame.Surface(
                card_rect.size,
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                card_surface,
                (8, 22, 44, 210),
                card_surface.get_rect(),
                border_radius=8,
            )
            pygame.draw.rect(
                card_surface,
                (50, 115, 160, 120),
                card_surface.get_rect(),
                1,
                border_radius=8,
            )
            self.screen.blit(card_surface, card_rect.topleft)

            card_label_surface = self.menu_micro_font.render(
                card_label,
                True,
                (92, 116, 150),
            )
            card_value_surface = self.menu_label_font.render(
                card_value,
                True,
                (205, 232, 248),
            )
            if card_value_surface.get_width() > card_width - 10:
                card_value_surface = self.menu_micro_font.render(
                    card_value,
                    True,
                    (205, 232, 248),
                )
            self.screen.blit(
                card_label_surface,
                (
                    card_rect.centerx
                    - card_label_surface.get_width() // 2,
                    card_rect.y + 9,
                ),
            )
            self.screen.blit(
                card_value_surface,
                (
                    card_rect.centerx
                    - card_value_surface.get_width() // 2,
                    card_rect.y + 29,
                ),
            )

        ship_status = self.menu_micro_font.render(
            "GF-01 DEFENDER  //  COMBAT SYSTEMS NOMINAL",
            True,
            (88, 218, 180),
        )
        self.screen.blit(
            ship_status,
            (
                panel_rect.x + 20,
                panel_rect.bottom - 18,
            ),
        )

    # Creează docul holografic din spatele navei expuse în meniu.
    def _draw_menu_ship_showcase(self):
        showcase_rect = pygame.Rect(50, 452, 325, 224)
        showcase = pygame.Surface(
            showcase_rect.size,
            pygame.SRCALPHA,
        )
        center_x = 162
        platform_y = 188
        animation_time = pygame.time.get_ticks() * 0.001

        pygame.draw.polygon(
            showcase,
            (35, 175, 255, 12),
            (
                (center_x - 42, 16),
                (center_x + 42, 16),
                (center_x + 116, platform_y),
                (center_x - 116, platform_y),
            ),
        )
        for beam_offset in (-62, -31, 0, 31, 62):
            pygame.draw.line(
                showcase,
                (70, 190, 255, 28),
                (center_x + beam_offset // 3, 25),
                (center_x + beam_offset, platform_y),
                1,
            )

        for glow_index in range(5, 0, -1):
            glow_rect = pygame.Rect(
                center_x - 123 - glow_index * 3,
                platform_y - 22 - glow_index,
                246 + glow_index * 6,
                44 + glow_index * 2,
            )
            pygame.draw.ellipse(
                showcase,
                (30, 145, 255, 7 + glow_index * 4),
                glow_rect,
            )

        pygame.draw.ellipse(
            showcase,
            (8, 24, 52, 205),
            pygame.Rect(center_x - 124, platform_y - 23, 248, 46),
        )
        pygame.draw.ellipse(
            showcase,
            (65, 195, 255, 180),
            pygame.Rect(center_x - 124, platform_y - 23, 248, 46),
            2,
        )
        pygame.draw.ellipse(
            showcase,
            (125, 230, 255, 110),
            pygame.Rect(center_x - 90, platform_y - 15, 180, 30),
            1,
        )

        arc_rect = pygame.Rect(center_x - 137, platform_y - 29, 274, 58)
        for arc_index in range(3):
            arc_start = animation_time * 0.8 + arc_index * math.tau / 3
            pygame.draw.arc(
                showcase,
                (105, 225, 255, 210),
                arc_rect,
                arc_start,
                arc_start + 0.72,
                3,
            )

        for grid_offset in range(-100, 101, 25):
            pygame.draw.line(
                showcase,
                (65, 155, 215, 38),
                (center_x + grid_offset, platform_y),
                (center_x + int(grid_offset * 0.76), platform_y + 20),
                1,
            )
        self.screen.blit(showcase, showcase_rect.topleft)

    # Desenează scanarea și eticheta tehnică peste nava din doc.
    def _draw_menu_ship_scan_overlay(self):
        ship_rect = self.menu_player.rect
        scan_progress = (
            pygame.time.get_ticks() * 0.055
        ) % max(1, ship_rect.height)
        scan_y = int(ship_rect.y + scan_progress)

        scan_glow = pygame.Surface((170, 16), pygame.SRCALPHA)
        pygame.draw.rect(
            scan_glow,
            (65, 215, 255, 24),
            scan_glow.get_rect(),
            border_radius=8,
        )
        pygame.draw.line(
            scan_glow,
            (170, 245, 255, 205),
            (12, 8),
            (158, 8),
            1,
        )
        self.screen.blit(
            scan_glow,
            (ship_rect.centerx - 85, scan_y - 8),
        )

        bracket_rect = ship_rect.inflate(30, 18)
        bracket_length = 15
        bracket_color = (75, 205, 255, 150)
        for corner_x, direction_x in (
            (bracket_rect.left, 1),
            (bracket_rect.right, -1),
        ):
            for corner_y, direction_y in (
                (bracket_rect.top, 1),
                (bracket_rect.bottom, -1),
            ):
                pygame.draw.line(
                    self.screen,
                    bracket_color,
                    (corner_x, corner_y),
                    (corner_x + direction_x * bracket_length, corner_y),
                    1,
                )
                pygame.draw.line(
                    self.screen,
                    bracket_color,
                    (corner_x, corner_y),
                    (corner_x, corner_y + direction_y * bracket_length),
                    1,
                )

        connector_start = (
            bracket_rect.right,
            bracket_rect.centery - 2,
        )
        connector_middle = (318, connector_start[1])
        connector_end = (342, connector_start[1] - 18)
        pygame.draw.line(
            self.screen,
            (70, 185, 230, 130),
            connector_start,
            connector_middle,
            1,
        )
        pygame.draw.line(
            self.screen,
            (70, 185, 230, 130),
            connector_middle,
            connector_end,
            1,
        )
        ship_label = self.menu_micro_font.render(
            "GF-01 // READY",
            True,
            (115, 220, 250),
        )
        hull_label = self.menu_micro_font.render(
            "HULL LINK NOMINAL",
            True,
            (85, 205, 165),
        )
        self.screen.blit(ship_label, (347, connector_end[1] - 7))
        self.screen.blit(hull_label, (347, connector_end[1] + 9))

    # Desenează carcasa holografică și protocolul selectat din meniul principal.
    def _draw_menu_navigation_panel(
        self,
        mouse_position,
        menu_buttons,
    ):
        navigation_panel = pygame.Rect(
            self.width - 464,
            165,
            418,
            460,
        )

        # Umbra separă panoul de nebuloasa luminoasă fără să ascundă fundalul.
        shadow_surface = pygame.Surface(
            (
                navigation_panel.width + 28,
                navigation_panel.height + 28,
            ),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            shadow_surface,
            (0, 0, 10, 125),
            shadow_surface.get_rect(),
            border_radius=25,
        )
        self.screen.blit(
            shadow_surface,
            (
                navigation_panel.x - 14,
                navigation_panel.y - 10,
            ),
        )

        panel_surface = pygame.Surface(
            navigation_panel.size,
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            panel_surface,
            (3, 9, 25, 232),
            panel_surface.get_rect(),
            border_radius=18,
        )

        # O a doua placă translucidă creează profunzime în interiorul panoului.
        pygame.draw.rect(
            panel_surface,
            (12, 29, 58, 58),
            pygame.Rect(9, 9, navigation_panel.width - 18, 64),
            border_radius=13,
        )
        pygame.draw.rect(
            panel_surface,
            (94, 75, 190, 135),
            panel_surface.get_rect(),
            2,
            border_radius=18,
        )

        # Muchiile scurte sugerează un terminal militar, nu o fereastră simplă.
        corner_color = (75, 210, 255, 205)
        corner_length = 27
        for corner_x, direction in (
            (18, 1),
            (navigation_panel.width - 18, -1),
        ):
            pygame.draw.line(
                panel_surface,
                corner_color,
                (corner_x, 1),
                (corner_x + direction * corner_length, 1),
                3,
            )
            pygame.draw.line(
                panel_surface,
                corner_color,
                (corner_x, 1),
                (corner_x, 15),
                2,
            )

        pygame.draw.line(
            panel_surface,
            (80, 205, 255, 225),
            (24, 46),
            (240, 46),
            2,
        )
        pygame.draw.line(
            panel_surface,
            (120, 75, 205, 95),
            (240, 46),
            (navigation_panel.width - 24, 46),
            1,
        )
        self.screen.blit(
            panel_surface,
            navigation_panel.topleft,
        )

        pygame.draw.circle(
            self.screen,
            (85, 225, 255),
            (
                navigation_panel.x + 26,
                navigation_panel.y + 27,
            ),
            4,
        )
        label = self.menu_label_font.render(
            "COMMAND NAVIGATION",
            True,
            (115, 205, 245),
        )
        online_label = self.menu_micro_font.render(
            "LINK // ONLINE",
            True,
            (92, 225, 178),
        )
        self.screen.blit(
            label,
            (navigation_panel.x + 40, navigation_panel.y + 20),
        )
        self.screen.blit(
            online_label,
            (
                navigation_panel.right
                - online_label.get_width()
                - 24,
                navigation_panel.y + 22,
            ),
        )

        selected_action = menu_buttons[0][2]
        for button_rect, _button_text, action in menu_buttons:
            if button_rect.collidepoint(mouse_position):
                selected_action = action
                break

        descriptions = {
            "continue": "RESUME FROM LAST SAFE CHECKPOINT",
            "play": "BEGIN THE GALAXY DEFENDER CAMPAIGN",
            "new_game": "RESTART CAMPAIGN FROM THE HOMEWORLD",
            "leaderboard": "VIEW THE TOP GALACTIC DEFENDERS",
            "settings": "CONFIGURE DISPLAY AND AUDIO SYSTEMS",
            "exit": "CLOSE THE COMMAND INTERFACE",
        }
        status_label = self.menu_micro_font.render(
            "SELECTED PROTOCOL",
            True,
            (92, 112, 146),
        )
        protocol_text = self.menu_protocol_font.render(
            descriptions[selected_action],
            True,
            (155, 205, 235),
        )
        lowest_button_bottom = max(
            button_rect.bottom
            for button_rect, _button_text, _action in menu_buttons
        )
        status_y = max(
            navigation_panel.bottom - 50,
            lowest_button_bottom + 10,
        )
        self.screen.blit(
            status_label,
            (navigation_panel.x + 41, status_y),
        )
        self.screen.blit(
            protocol_text,
            (navigation_panel.x + 41, status_y + 17),
        )

        # Punctul pulsează discret și confirmă că selecția este activă.
        pulse = (
            math.sin(pygame.time.get_ticks() * 0.006) + 1.0
        ) / 2.0
        pygame.draw.circle(
            self.screen,
            (45, 130, 175),
            (navigation_panel.x + 25, status_y + 20),
            7,
        )
        pygame.draw.circle(
            self.screen,
            (90, 225, 255),
            (navigation_panel.x + 25, status_y + 20),
            3 + int(pulse * 2),
        )

    # Desenează o pictogramă vectorială, astfel încât meniul nu cere asset-uri noi.
    def _draw_menu_action_icon(
        self,
        surface,
        action,
        center,
        color,
    ):
        center_x, center_y = center

        if action in ("continue", "play"):
            pygame.draw.polygon(
                surface,
                color,
                (
                    (center_x - 5, center_y - 8),
                    (center_x + 8, center_y),
                    (center_x - 5, center_y + 8),
                ),
            )

        elif action == "new_game":
            pygame.draw.circle(surface, color, center, 9, 2)
            pygame.draw.line(
                surface,
                color,
                (center_x - 5, center_y),
                (center_x + 5, center_y),
                2,
            )
            pygame.draw.line(
                surface,
                color,
                (center_x, center_y - 5),
                (center_x, center_y + 5),
                2,
            )

        elif action == "leaderboard":
            for bar_index, bar_height in enumerate((7, 13, 19)):
                bar_rect = pygame.Rect(
                    center_x - 11 + bar_index * 8,
                    center_y + 9 - bar_height,
                    5,
                    bar_height,
                )
                pygame.draw.rect(
                    surface,
                    color,
                    bar_rect,
                    border_radius=2,
                )

        elif action == "settings":
            pygame.draw.circle(surface, color, center, 8, 2)
            pygame.draw.circle(surface, color, center, 3, 2)
            for offset_x, offset_y in (
                (0, -12),
                (0, 12),
                (-12, 0),
                (12, 0),
            ):
                pygame.draw.line(
                    surface,
                    color,
                    (
                        center_x + int(offset_x * 0.62),
                        center_y + int(offset_y * 0.62),
                    ),
                    (center_x + offset_x, center_y + offset_y),
                    2,
                )

        elif action == "exit":
            pygame.draw.arc(
                surface,
                color,
                pygame.Rect(center_x - 10, center_y - 9, 20, 20),
                math.radians(35),
                math.radians(325),
                2,
            )
            pygame.draw.line(
                surface,
                color,
                (center_x, center_y - 12),
                (center_x, center_y + 1),
                3,
            )

    # Butonul principal are un nivel vizual distinct și reacționează la hover.
    def _draw_menu_navigation_button(
        self,
        button_rect,
        button_text,
        action,
        mouse_position,
        primary=False,
    ):
        is_hovered = button_rect.collidepoint(mouse_position)
        pulse = (
            math.sin(pygame.time.get_ticks() * 0.007) + 1.0
        ) / 2.0
        scale_amount = 6 if is_hovered else 0
        draw_rect = pygame.Rect(
            button_rect.x - scale_amount // 2,
            button_rect.y - scale_amount // 2,
            button_rect.width + scale_amount,
            button_rect.height + scale_amount,
        )

        if is_hovered:
            fill_color = (9, 67, 105, 246)
            border_color = (95, 225, 255, 245)
            text_color = (245, 252, 255)
            icon_color = (150, 240, 255)
        elif primary:
            fill_color = (7, 34, 65, 242)
            border_color = (65, 180, 225, 220)
            text_color = (220, 242, 255)
            icon_color = (85, 215, 255)
        else:
            fill_color = (7, 16, 37, 235)
            border_color = (55, 101, 145, 205)
            text_color = (190, 207, 229)
            icon_color = (100, 155, 195)

        if is_hovered:
            glow_surface = pygame.Surface(
                (draw_rect.width + 24, draw_rect.height + 24),
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                glow_surface,
                (45, 190, 255, 32 + int(pulse * 24)),
                glow_surface.get_rect(),
                border_radius=16,
            )
            self.screen.blit(
                glow_surface,
                (draw_rect.x - 12, draw_rect.y - 12),
            )

        button_surface = pygame.Surface(
            draw_rect.size,
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            button_surface,
            fill_color,
            button_surface.get_rect(),
            border_radius=10,
        )

        # Reflexia diagonală se deplasează numai peste protocolul selectat.
        if is_hovered:
            scan_x = int(
                (pygame.time.get_ticks() * 0.10)
                % (draw_rect.width + 100)
            ) - 50
            pygame.draw.polygon(
                button_surface,
                (120, 230, 255, 22),
                (
                    (scan_x - 28, 0),
                    (scan_x + 4, 0),
                    (scan_x + 34, draw_rect.height),
                    (scan_x + 2, draw_rect.height),
                ),
            )

        pygame.draw.rect(
            button_surface,
            border_color,
            button_surface.get_rect(),
            2,
            border_radius=10,
        )
        pygame.draw.line(
            button_surface,
            (*icon_color[:3], 245),
            (1, 10),
            (1, draw_rect.height - 10),
            4 if (is_hovered or primary) else 2,
        )

        icon_tile = pygame.Rect(
            12,
            draw_rect.height // 2 - 17,
            34,
            34,
        )
        pygame.draw.rect(
            button_surface,
            (12, 30, 56, 205),
            icon_tile,
            border_radius=8,
        )
        pygame.draw.rect(
            button_surface,
            (*icon_color[:3], 135),
            icon_tile,
            1,
            border_radius=8,
        )
        self._draw_menu_action_icon(
            button_surface,
            action,
            icon_tile.center,
            icon_color,
        )

        button_label = self.menu_button_font.render(
            button_text,
            True,
            text_color,
        )
        button_surface.blit(
            button_label,
            (
                59,
                draw_rect.height // 2
                - button_label.get_height() // 2,
            ),
        )

        # Chevron-ul este desenat din linii clare, fără aspectul vechiului simbol >.
        chevron_x = draw_rect.width - 24
        chevron_y = draw_rect.height // 2
        pygame.draw.line(
            button_surface,
            icon_color,
            (chevron_x - 5, chevron_y - 6),
            (chevron_x + 1, chevron_y),
            2,
        )
        pygame.draw.line(
            button_surface,
            icon_color,
            (chevron_x + 1, chevron_y),
            (chevron_x - 5, chevron_y + 6),
            2,
        )
        if is_hovered:
            pygame.draw.circle(
                button_surface,
                (170, 245, 255),
                (chevron_x + 6, chevron_y),
                2,
            )

        self.screen.blit(button_surface, draw_rect.topleft)

    # Returnează butoanele potrivite pentru progresul salvat.
    def _get_menu_buttons(self):
        if self.save_manager.has_campaign_progress():
            return [
                (
                    self.continue_button,
                    "CONTINUE",
                    "continue",
                ),
                (
                    self.new_game_button,
                    "NEW GAME",
                    "new_game",
                ),
                (
                    self.saved_leaderboard_button,
                    "LEADERBOARD",
                    "leaderboard",
                ),
                (
                    self.saved_settings_button,
                    "SETTINGS",
                    "settings",
                ),
                (
                    self.saved_exit_button,
                    "EXIT",
                    "exit",
                ),
            ]

        return [
            (self.play_button, "PLAY", "play"),
            (
                self.leaderboard_button,
                "LEADERBOARD",
                "leaderboard",
            ),
            (
                self.settings_button,
                "SETTINGS",
                "settings",
            ),
            (self.exit_button, "EXIT", "exit"),
        ]

    # Desenează unul dintre cele două protocoale ale avertizării NEW GAME.
    def _draw_new_game_choice_button(
        self,
        button_rect,
        title,
        subtitle,
        mouse_position,
        visibility,
        dangerous=False,
    ):
        is_hovered = button_rect.collidepoint(mouse_position)
        pulse = (
            math.sin(pygame.time.get_ticks() * 0.008) + 1.0
        ) / 2.0

        if dangerous:
            accent = (255, 111, 77)
            fill = (
                (118, 37, 38, 245)
                if is_hovered
                else (58, 23, 31, 235)
            )
        else:
            accent = (80, 215, 255)
            fill = (
                (15, 82, 116, 245)
                if is_hovered
                else (8, 29, 55, 235)
            )

        if is_hovered:
            glow_surface = pygame.Surface(
                (button_rect.width + 22, button_rect.height + 22),
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                glow_surface,
                (*accent, int((30 + pulse * 24) * visibility)),
                glow_surface.get_rect(),
                border_radius=16,
            )
            self.screen.blit(
                glow_surface,
                (button_rect.x - 11, button_rect.y - 11),
            )

        button_surface = pygame.Surface(
            button_rect.size,
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            button_surface,
            fill,
            button_surface.get_rect(),
            border_radius=11,
        )
        pygame.draw.rect(
            button_surface,
            (*accent, 245 if is_hovered else 175),
            button_surface.get_rect(),
            2,
            border_radius=11,
        )
        pygame.draw.line(
            button_surface,
            (*accent, 245),
            (1, 10),
            (1, button_rect.height - 10),
            4,
        )

        icon_rect = pygame.Rect(14, 13, 36, 36)
        pygame.draw.rect(
            button_surface,
            (5, 13, 30, 185),
            icon_rect,
            border_radius=9,
        )
        pygame.draw.rect(
            button_surface,
            (*accent, 145),
            icon_rect,
            1,
            border_radius=9,
        )
        icon_center = icon_rect.center
        if dangerous:
            pygame.draw.arc(
                button_surface,
                accent,
                pygame.Rect(
                    icon_center[0] - 9,
                    icon_center[1] - 9,
                    18,
                    18,
                ),
                math.radians(35),
                math.radians(315),
                2,
            )
            pygame.draw.polygon(
                button_surface,
                accent,
                (
                    (icon_center[0] + 7, icon_center[1] - 9),
                    (icon_center[0] + 12, icon_center[1] - 5),
                    (icon_center[0] + 5, icon_center[1] - 3),
                ),
            )
        else:
            pygame.draw.line(
                button_surface,
                accent,
                (icon_center[0] - 7, icon_center[1] - 7),
                (icon_center[0] + 7, icon_center[1] + 7),
                2,
            )
            pygame.draw.line(
                button_surface,
                accent,
                (icon_center[0] + 7, icon_center[1] - 7),
                (icon_center[0] - 7, icon_center[1] + 7),
                2,
            )

        title_surface = self.menu_subtitle_font.render(
            title,
            True,
            (250, 250, 255),
        )
        subtitle_surface = self.menu_micro_font.render(
            subtitle,
            True,
            accent,
        )
        button_surface.blit(title_surface, (64, 9))
        button_surface.blit(subtitle_surface, (64, 37))
        button_surface.set_alpha(int(255 * visibility))
        self.screen.blit(button_surface, button_rect.topleft)

    # Desenează avertizarea premium înainte de resetarea campaniei.
    def _draw_new_game_confirmation(self):
        entrance_progress = min(
            1.0,
            self.confirm_new_game_timer
            / self.confirm_new_game_animation_duration,
        )
        eased_progress = 1.0 - (1.0 - entrance_progress) ** 3
        content_visibility = max(
            0.0,
            min(
                1.0,
                (self.confirm_new_game_timer - 3) / 18,
            ),
        )

        overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )
        overlay.fill((1, 3, 12, int(220 * eased_progress)))
        scan_offset = self.confirm_new_game_timer * 4 % 48
        for scan_y in range(int(scan_offset) - 48, self.height, 48):
            pygame.draw.line(
                overlay,
                (255, 92, 70, int(11 * eased_progress)),
                (0, scan_y),
                (self.width, scan_y),
                1,
            )
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(270, 145, 740, 430)
        panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(
            panel_surface,
            (5, 10, 27, int(246 * eased_progress)),
            panel_surface.get_rect(),
            border_radius=20,
        )
        pygame.draw.rect(
            panel_surface,
            (130, 80, 150, int(155 * eased_progress)),
            panel_surface.get_rect(),
            2,
            border_radius=20,
        )
        pygame.draw.line(
            panel_surface,
            (255, 100, 78, int(245 * eased_progress)),
            (38, 1),
            (panel.width // 2, 1),
            4,
        )
        pygame.draw.line(
            panel_surface,
            (70, 210, 255, int(220 * eased_progress)),
            (panel.width // 2, 1),
            (panel.width - 38, 1),
            4,
        )
        self.screen.blit(panel_surface, panel.topleft)

        status = self.menu_micro_font.render(
            "GALACTIC DEFENSE COMMAND  //  SECURE CAMPAIGN CONTROL",
            True,
            (115, 175, 210),
        )
        title = self.menu_font.render(
            "REINITIALIZE CAMPAIGN?",
            True,
            (245, 249, 255),
        )
        warning = self.menu_label_font.render(
            "THIS ACTION RESTARTS THE STORY FROM THE HOMEWORLD",
            True,
            (255, 153, 92),
        )
        for text_surface in (status, title, warning):
            text_surface.set_alpha(int(255 * content_visibility))

        self.screen.blit(
            status,
            (
                self.width // 2 - status.get_width() // 2,
                panel.y + 24,
            ),
        )
        self.screen.blit(
            title,
            (
                self.width // 2 - title.get_width() // 2,
                panel.y + 50,
            ),
        )
        self.screen.blit(
            warning,
            (
                self.width // 2 - warning.get_width() // 2,
                panel.y + 108,
            ),
        )

        saved_data = self.save_manager.data
        scene_name = str(
            saved_data.get("current_scene", "planet")
        ).replace("_", " ").upper()
        checkpoint = max(
            0,
            int(saved_data.get("checkpoint", 0)),
        )
        campaign_score = self._format_menu_score(
            saved_data.get("campaign_score", 0)
        )
        best_score = self._format_menu_score(
            saved_data.get("highest_score", 0)
        )

        card_y = panel.y + 142
        left_card = pygame.Rect(panel.x + 38, card_y, 322, 126)
        right_card = pygame.Rect(panel.x + 380, card_y, 322, 126)
        card_definitions = (
            (
                left_card,
                "CAMPAIGN DATA // WILL RESET",
                (255, 111, 77),
                (
                    f"CURRENT SECTOR  //  {scene_name}",
                    f"SAFE CHECKPOINT  //  {checkpoint:02d}",
                    f"MISSION SCORE  //  {campaign_score}",
                ),
            ),
            (
                right_card,
                "PILOT DATA // WILL BE PRESERVED",
                (80, 220, 180),
                (
                    f"GALACTIC BEST  //  {best_score}",
                    "AUDIO AND DISPLAY SETTINGS",
                    "LEADERBOARD RECORDS",
                ),
            ),
        )
        for card_rect, card_title, accent, rows in card_definitions:
            card_surface = pygame.Surface(
                card_rect.size,
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                card_surface,
                (9, 18, 39, int(224 * content_visibility)),
                card_surface.get_rect(),
                border_radius=12,
            )
            pygame.draw.rect(
                card_surface,
                (*accent, int(150 * content_visibility)),
                card_surface.get_rect(),
                1,
                border_radius=12,
            )
            pygame.draw.line(
                card_surface,
                (*accent, int(220 * content_visibility)),
                (15, 38),
                (card_rect.width - 15, 38),
                2,
            )
            self.screen.blit(card_surface, card_rect.topleft)

            card_title_surface = self.menu_label_font.render(
                card_title,
                True,
                accent,
            )
            card_title_surface.set_alpha(
                int(255 * content_visibility)
            )
            self.screen.blit(
                card_title_surface,
                (card_rect.x + 16, card_rect.y + 13),
            )
            for row_index, row_text in enumerate(rows):
                row_surface = self.menu_micro_font.render(
                    row_text,
                    True,
                    (170, 193, 220),
                )
                row_surface.set_alpha(
                    int(255 * content_visibility)
                )
                self.screen.blit(
                    row_surface,
                    (
                        card_rect.x + 18,
                        card_rect.y + 50 + row_index * 23,
                    ),
                )

        mouse_position = self._get_mouse_position()
        self._draw_new_game_choice_button(
            self.confirm_new_game_button,
            "BEGIN NEW CAMPAIGN",
            "RESET CAMPAIGN DATA",
            mouse_position,
            content_visibility,
            dangerous=True,
        )
        self._draw_new_game_choice_button(
            self.cancel_new_game_button,
            "CANCEL",
            "KEEP CURRENT PROGRESS",
            mouse_position,
            content_visibility,
        )

        hint = self.menu_micro_font.render(
            "ENTER / Y  //  CONFIRM        ESC / N  //  CANCEL",
            True,
            (105, 130, 162),
        )
        hint.set_alpha(int(255 * content_visibility))
        self.screen.blit(
            hint,
            (
                self.width // 2 - hint.get_width() // 2,
                panel.bottom - 31,
            ),
        )

    # Desenează logo-ul animat GALAXY DEFENDER și efectul său de lumină.
    def _draw_logo(self):
        pulse = (
            1
            + math.sin(self.logo_timer) * 0.025
        )

        base_title = self.title_font.render(
            "GALAXY DEFENDER",
            True,
            (80, 210, 255),
        )

        title_text = pygame.transform.smoothscale(
            base_title,
            (
                int(base_title.get_width() * pulse),
                int(base_title.get_height() * pulse),
            ),
        )

        title_y = 82

        glow_text = self.title_font.render(
            "GALAXY DEFENDER",
            True,
            (0, 100, 255),
        )
        glow_surface = pygame.Surface(
            (
                glow_text.get_width() + 40,
                glow_text.get_height() + 40,
            ),
            pygame.SRCALPHA,
        )
        glow_surface.blit(glow_text, (20, 20))
        glow_surface.set_alpha(80)

        self.screen.blit(
            glow_surface,
            (
                68,
                title_y - 20,
            ),
        )
        self.screen.blit(
            title_text,
            (
                88,
                title_y,
            ),
        )

        subtitle = self.menu_subtitle_font.render(
            "TACTICAL SPACE DEFENSE // CAMPAIGN OPERATIONS",
            True,
            (155, 175, 205),
        )
        self.screen.blit(
            subtitle,
            (94, title_y + 101),
        )

        pygame.draw.line(
            self.screen,
            (75, 195, 255),
            (94, title_y + 137),
            (505, title_y + 137),
            2,
        )

    # Desenează un fundal comun pentru ecranele secundare ale meniului.
    # Acest cadru păstrează același stil vizual pe Pause, Settings și Leaderboard.
    def _draw_secondary_screen_frame(
        self,
        title,
        subtitle,
        accent_color=(75, 205, 255),
    ):
        self.screen.blit(self.menu_background, (0, 0))
        self.screen.blit(self.menu_interface_overlay, (0, 0))

        # Stratul întunecat face informația ușor de citit peste fundal.
        shade = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )
        shade.fill((2, 6, 18, 105))
        self.screen.blit(shade, (0, 0))

        title_surface = self.title_font.render(
            title,
            True,
            (232, 244, 255),
        )
        subtitle_surface = self.menu_label_font.render(
            subtitle,
            True,
            accent_color,
        )
        title_x = (
            self.width // 2
            - title_surface.get_width() // 2
        )
        self.screen.blit(title_surface, (title_x, 55))
        self.screen.blit(
            subtitle_surface,
            (
                self.width // 2
                - subtitle_surface.get_width() // 2,
                142,
            ),
        )
        pygame.draw.line(
            self.screen,
            accent_color,
            (self.width // 2 - 210, 173),
            (self.width // 2 + 210, 173),
            2,
        )

    # Desenează un panou transparent de tip „sticlă” pentru informații.
    def _draw_glass_panel(
        self,
        panel_rect,
        accent_color=(75, 205, 255),
        alpha=220,
    ):
        panel = pygame.Surface(
            panel_rect.size,
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            panel,
            (4, 10, 28, alpha),
            panel.get_rect(),
            border_radius=18,
        )
        pygame.draw.rect(
            panel,
            (*accent_color, 155),
            panel.get_rect(),
            2,
            border_radius=18,
        )
        pygame.draw.line(
            panel,
            (*accent_color, 220),
            (22, 0),
            (panel_rect.width - 22, 0),
            3,
        )
        self.screen.blit(panel, panel_rect.topleft)

    # Desenează o valoare importantă din telemetria rundei curente.
    def _draw_pause_stat_card(
        self,
        card_rect,
        label,
        value,
        accent_color,
        visibility,
    ):
        card = pygame.Surface(card_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            card,
            (7, 18, 39, int(215 * visibility)),
            card.get_rect(),
            border_radius=9,
        )
        pygame.draw.rect(
            card,
            (*accent_color, int(125 * visibility)),
            card.get_rect(),
            1,
            border_radius=9,
        )
        label_surface = self.menu_micro_font.render(
            label,
            True,
            (95, 122, 155),
        )
        value_surface = self.pause_value_font.render(
            value,
            True,
            (225, 243, 255),
        )
        if value_surface.get_width() > card_rect.width - 10:
            value_surface = self.menu_subtitle_font.render(
                value,
                True,
                (225, 243, 255),
            )
        label_surface.set_alpha(int(255 * visibility))
        value_surface.set_alpha(int(255 * visibility))
        card.blit(
            label_surface,
            (
                card_rect.width // 2 - label_surface.get_width() // 2,
                10,
            ),
        )
        card.blit(
            value_surface,
            (
                card_rect.width // 2 - value_surface.get_width() // 2,
                27,
            ),
        )
        self.screen.blit(card, card_rect.topleft)

    # Desenează una dintre comenzile disponibile în timpul pauzei.
    def _draw_pause_command_button(
        self,
        button_rect,
        title,
        subtitle,
        action,
        mouse_position,
        visibility,
    ):
        hovered = button_rect.collidepoint(mouse_position)
        accent_colors = {
            "resume": (75, 220, 255),
            "settings": (155, 115, 245),
            "menu": (255, 112, 82),
        }
        accent = accent_colors[action]
        fill = (
            (*accent, int(112 * visibility))
            if hovered
            else (7, 18, 39, int(225 * visibility))
        )

        if hovered:
            pulse = (
                math.sin(pygame.time.get_ticks() * 0.008) + 1.0
            ) / 2.0
            glow = pygame.Surface(
                (button_rect.width + 20, button_rect.height + 20),
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                glow,
                (*accent, int((28 + pulse * 22) * visibility)),
                glow.get_rect(),
                border_radius=16,
            )
            self.screen.blit(
                glow,
                (button_rect.x - 10, button_rect.y - 10),
            )

        button = pygame.Surface(button_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            button,
            fill,
            button.get_rect(),
            border_radius=10,
        )
        pygame.draw.rect(
            button,
            (*accent, int((235 if hovered else 145) * visibility)),
            button.get_rect(),
            2,
            border_radius=10,
        )
        pygame.draw.line(
            button,
            (*accent, int(240 * visibility)),
            (1, 10),
            (1, button_rect.height - 10),
            4,
        )

        icon_rect = pygame.Rect(14, 13, 36, 36)
        pygame.draw.rect(
            button,
            (5, 13, 29, int(190 * visibility)),
            icon_rect,
            border_radius=9,
        )
        pygame.draw.rect(
            button,
            (*accent, int(145 * visibility)),
            icon_rect,
            1,
            border_radius=9,
        )
        center_x, center_y = icon_rect.center
        if action == "resume":
            pygame.draw.polygon(
                button,
                accent,
                (
                    (center_x - 5, center_y - 8),
                    (center_x + 8, center_y),
                    (center_x - 5, center_y + 8),
                ),
            )
        elif action == "settings":
            pygame.draw.circle(button, accent, icon_rect.center, 8, 2)
            pygame.draw.circle(button, accent, icon_rect.center, 3, 2)
            for offset_x, offset_y in (
                (0, -12),
                (0, 12),
                (-12, 0),
                (12, 0),
            ):
                pygame.draw.line(
                    button,
                    accent,
                    (
                        center_x + int(offset_x * 0.62),
                        center_y + int(offset_y * 0.62),
                    ),
                    (center_x + offset_x, center_y + offset_y),
                    2,
                )
        else:
            pygame.draw.polygon(
                button,
                accent,
                (
                    (center_x, center_y - 10),
                    (center_x + 10, center_y + 8),
                    (center_x - 10, center_y + 8),
                ),
                2,
            )
            pygame.draw.line(
                button,
                accent,
                (center_x, center_y - 4),
                (center_x, center_y + 3),
                2,
            )
            pygame.draw.circle(
                button,
                accent,
                (center_x, center_y + 6),
                1,
            )

        title_surface = self.pause_button_font.render(
            title,
            True,
            (242, 249, 255),
        )
        subtitle_surface = self.menu_micro_font.render(
            subtitle,
            True,
            accent,
        )
        title_surface.set_alpha(int(255 * visibility))
        subtitle_surface.set_alpha(int(255 * visibility))
        button.blit(title_surface, (64, 8))
        button.blit(subtitle_surface, (64, 37))
        self.screen.blit(button, button_rect.topleft)

    # Desenează centrul de comandă peste cadrul complet înghețat al luptei.
    def _draw_pause(self):
        # Gameplay.draw nu actualizează pozițiile, deci pericolele rămân înghețate.
        self.gameplay.draw()

        entrance_visibility = min(
            1.0,
            self.pause_animation_timer / 24,
        )
        content_visibility = max(
            0.0,
            min(
                1.0,
                (self.pause_animation_timer - 4) / 22,
            ),
        )
        overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )
        overlay.fill((1, 4, 16, int(205 * entrance_visibility)))
        scan_offset = self.pause_animation_timer * 3 % 44
        for scan_y in range(int(scan_offset) - 44, self.height, 44):
            pygame.draw.line(
                overlay,
                (65, 195, 255, int(10 * entrance_visibility)),
                (0, scan_y),
                (self.width, scan_y),
                1,
            )
        self.screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(190, 92, 900, 535)
        panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            panel,
            (4, 10, 27, int(242 * entrance_visibility)),
            panel.get_rect(),
            border_radius=20,
        )
        pygame.draw.rect(
            panel,
            (75, 205, 255, int(170 * entrance_visibility)),
            panel.get_rect(),
            2,
            border_radius=20,
        )
        pygame.draw.line(
            panel,
            (75, 215, 255, int(235 * entrance_visibility)),
            (35, 1),
            (panel_rect.width - 35, 1),
            4,
        )
        self.screen.blit(panel, panel_rect.topleft)

        status = self.menu_micro_font.render(
            "GALACTIC DEFENSE COMMAND  //  LIVE COMBAT LINK",
            True,
            (90, 205, 245),
        )
        title = self.menu_font.render(
            "MISSION SUSPENDED",
            True,
            (240, 248, 255),
        )
        objective = self.menu_label_font.render(
            "TACTICAL SYSTEMS ARE FROZEN  //  HOSTILES ON STANDBY",
            True,
            (135, 160, 192),
        )
        for text_surface in (status, title, objective):
            text_surface.set_alpha(int(255 * content_visibility))
        self.screen.blit(
            status,
            (
                self.width // 2 - status.get_width() // 2,
                panel_rect.y + 23,
            ),
        )
        self.screen.blit(
            title,
            (
                self.width // 2 - title.get_width() // 2,
                panel_rect.y + 49,
            ),
        )
        self.screen.blit(
            objective,
            (
                self.width // 2 - objective.get_width() // 2,
                panel_rect.y + 105,
            ),
        )
        pygame.draw.line(
            self.screen,
            (65, 180, 225),
            (panel_rect.x + 38, panel_rect.y + 137),
            (panel_rect.right - 38, panel_rect.y + 137),
            1,
        )

        telemetry_rect = pygame.Rect(225, 252, 390, 309)
        command_rect = pygame.Rect(655, 252, 400, 309)
        for content_rect, accent in (
            (telemetry_rect, (70, 195, 240)),
            (command_rect, (135, 100, 225)),
        ):
            content_panel = pygame.Surface(
                content_rect.size,
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                content_panel,
                (6, 16, 35, int(220 * content_visibility)),
                content_panel.get_rect(),
                border_radius=14,
            )
            pygame.draw.rect(
                content_panel,
                (*accent, int(115 * content_visibility)),
                content_panel.get_rect(),
                1,
                border_radius=14,
            )
            self.screen.blit(content_panel, content_rect.topleft)

        telemetry_header = self.menu_label_font.render(
            "LIVE MISSION TELEMETRY",
            True,
            (100, 210, 250),
        )
        command_header = self.menu_label_font.render(
            "COMMAND OPTIONS",
            True,
            (175, 145, 245),
        )
        telemetry_header.set_alpha(int(255 * content_visibility))
        command_header.set_alpha(int(255 * content_visibility))
        self.screen.blit(telemetry_header, (245, 271))
        self.screen.blit(command_header, (680, 271))

        count_progress = max(
            0.0,
            min(
                1.0,
                (self.pause_animation_timer - 6) / 26,
            ),
        )
        count_progress = 1.0 - (1.0 - count_progress) ** 3
        statistic_cards = (
            (
                pygame.Rect(245, 305, 110, 66),
                "SCORE",
                self._format_menu_score(
                    int(self.gameplay.score * count_progress)
                ),
                (75, 205, 255),
            ),
            (
                pygame.Rect(365, 305, 110, 66),
                "WAVE",
                f"{max(1, int(self.gameplay.wave * count_progress)):02d}",
                (150, 115, 245),
            ),
            (
                pygame.Rect(485, 305, 110, 66),
                "HULL",
                f"{max(0, int(self.gameplay.lives * count_progress)):03d}",
                (80, 220, 180),
            ),
        )
        for card_rect, label, value, accent in statistic_cards:
            self._draw_pause_stat_card(
                card_rect,
                label,
                value,
                accent,
                content_visibility,
            )

        player = self.gameplay.player
        telemetry_rows = (
            (
                "WEAPON SYSTEM",
                f"MK {player.weapon_level} / {player.maximum_weapon_level}",
                (90, 205, 245),
            ),
            (
                "SHIELD MATRIX",
                "ONLINE" if player.shield else "STANDBY",
                (80, 220, 180) if player.shield else (135, 155, 185),
            ),
            (
                "COMBAT LINK",
                f"X{self.gameplay.multiplier}",
                (255, 190, 85),
            ),
        )
        for row_index, (label, value, color) in enumerate(telemetry_rows):
            row_y = 391 + row_index * 32
            label_surface = self.menu_micro_font.render(
                label,
                True,
                (100, 125, 156),
            )
            value_surface = self.menu_label_font.render(
                value,
                True,
                color,
            )
            label_surface.set_alpha(int(255 * content_visibility))
            value_surface.set_alpha(int(255 * content_visibility))
            self.screen.blit(label_surface, (247, row_y + 4))
            self.screen.blit(
                value_surface,
                (590 - value_surface.get_width(), row_y),
            )
            pygame.draw.line(
                self.screen,
                (34, 66, 95),
                (245, row_y + 25),
                (595, row_y + 25),
                1,
            )

        energy_ratio = max(
            0.0,
            min(
                1.0,
                player.special_energy
                / max(1, player.maximum_special_energy),
            ),
        )
        energy_label = self.menu_micro_font.render(
            "ENERGY PULSE CHARGE",
            True,
            (100, 125, 156),
        )
        energy_value = self.menu_label_font.render(
            f"{int(energy_ratio * 100):03d}%",
            True,
            (85, 220, 255),
        )
        energy_label.set_alpha(int(255 * content_visibility))
        energy_value.set_alpha(int(255 * content_visibility))
        self.screen.blit(energy_label, (245, 491))
        self.screen.blit(
            energy_value,
            (595 - energy_value.get_width(), 487),
        )
        energy_bar = pygame.Rect(245, 520, 350, 10)
        pygame.draw.rect(
            self.screen,
            (18, 42, 68),
            energy_bar,
            border_radius=5,
        )
        if energy_ratio > 0:
            pygame.draw.rect(
                self.screen,
                (65, 205, 255),
                pygame.Rect(
                    energy_bar.x,
                    energy_bar.y,
                    max(5, int(energy_bar.width * energy_ratio)),
                    energy_bar.height,
                ),
                border_radius=5,
            )

        mouse_position = self._get_mouse_position()
        button_visibility = max(
            0.0,
            min(
                1.0,
                (self.pause_animation_timer - 12) / 20,
            ),
        )
        self._draw_pause_command_button(
            self.resume_button,
            "RESUME MISSION",
            "RETURN TO LIVE COMBAT",
            "resume",
            mouse_position,
            button_visibility,
        )
        self._draw_pause_command_button(
            self.pause_settings_button,
            "SYSTEM SETTINGS",
            "AUDIO AND DISPLAY CONTROL",
            "settings",
            mouse_position,
            button_visibility,
        )
        self._draw_pause_command_button(
            self.pause_menu_button,
            "ABORT TO COMMAND",
            "CURRENT RUN WILL END",
            "menu",
            mouse_position,
            button_visibility,
        )

        warning = self.menu_micro_font.render(
            "CAUTION  //  ABORT DOES NOT ERASE CAMPAIGN PROGRESS",
            True,
            (205, 125, 105),
        )
        warning.set_alpha(int(255 * button_visibility))
        self.screen.blit(
            warning,
            (
                command_rect.centerx - warning.get_width() // 2,
                541,
            ),
        )
        hint = self.menu_micro_font.render(
            "ESC  //  RESUME MISSION",
            True,
            (95, 125, 158),
        )
        hint.set_alpha(int(255 * content_visibility))
        self.screen.blit(
            hint,
            (
                self.width // 2 - hint.get_width() // 2,
                panel_rect.bottom - 28,
            ),
        )

    # Desenează o carte premium pentru unul dintre primii trei piloți.
    def _draw_archive_podium_card(
        self,
        card_rect,
        rank,
        score,
        accent_color,
        command_label,
        visibility,
        featured=False,
    ):
        card = pygame.Surface(card_rect.size, pygame.SRCALPHA)
        fill_alpha = int((238 if featured else 220) * visibility)
        pygame.draw.rect(
            card,
            (8, 17, 39, fill_alpha),
            card.get_rect(),
            border_radius=14,
        )
        if featured:
            pygame.draw.rect(
                card,
                (*accent_color, int(34 * visibility)),
                card.get_rect().inflate(-8, -8),
                border_radius=11,
            )
        pygame.draw.rect(
            card,
            (*accent_color, int((235 if featured else 165) * visibility)),
            card.get_rect(),
            2,
            border_radius=14,
        )
        pygame.draw.line(
            card,
            (*accent_color, int(230 * visibility)),
            (18, 1),
            (card_rect.width - 18, 1),
            3,
        )

        badge_center = (34, 32)
        pygame.draw.circle(
            card,
            (*accent_color, int(52 * visibility)),
            badge_center,
            20,
        )
        pygame.draw.circle(
            card,
            (*accent_color, int(220 * visibility)),
            badge_center,
            20,
            2,
        )
        rank_text = self.archive_rank_font.render(
            f"{rank:02d}",
            True,
            accent_color,
        )
        rank_text.set_alpha(int(255 * visibility))
        card.blit(
            rank_text,
            (
                badge_center[0] - rank_text.get_width() // 2,
                badge_center[1] - rank_text.get_height() // 2,
            ),
        )

        command = self.menu_micro_font.render(
            command_label,
            True,
            accent_color,
        )
        command.set_alpha(int(255 * visibility))
        card.blit(command, (65, 18))

        score_label = (
            self._format_menu_score(score)
            if score is not None
            else "---"
        )
        score_surface = self.archive_score_font.render(
            score_label,
            True,
            (245, 249, 255) if score is not None else (90, 112, 145),
        )
        score_surface.set_alpha(int(255 * visibility))
        score_y = 57 if featured else 53
        card.blit(
            score_surface,
            (
                card_rect.width // 2 - score_surface.get_width() // 2,
                score_y,
            ),
        )
        footer = self.menu_micro_font.render(
            "COMBAT SCORE" if score is not None else "AWAITING RECORD",
            True,
            (105, 132, 165),
        )
        footer.set_alpha(int(255 * visibility))
        card.blit(
            footer,
            (
                card_rect.width // 2 - footer.get_width() // 2,
                card_rect.height - 27,
            ),
        )
        self.screen.blit(card, card_rect.topleft)

    # Desenează un rând compact pentru pozițiile patru până la zece.
    def _draw_archive_row(
        self,
        row_rect,
        rank,
        score,
        visibility,
        highlighted=False,
    ):
        row = pygame.Surface(row_rect.size, pygame.SRCALPHA)
        if highlighted:
            accent = (80, 220, 180)
            fill = (10, 47, 52, int(220 * visibility))
        else:
            accent = (65, 170, 220)
            fill = (7, 19, 40, int(205 * visibility))

        pygame.draw.rect(
            row,
            fill,
            row.get_rect(),
            border_radius=8,
        )
        pygame.draw.rect(
            row,
            (*accent, int(110 * visibility)),
            row.get_rect(),
            1,
            border_radius=8,
        )
        pygame.draw.line(
            row,
            (*accent, int(210 * visibility)),
            (1, 8),
            (1, row_rect.height - 8),
            3,
        )

        if highlighted:
            rank_label = "PILOT BEST"
        else:
            rank_label = f"RANK  {rank:02d}"
        rank_surface = self.menu_micro_font.render(
            rank_label,
            True,
            accent,
        )
        score_surface = self.archive_row_font.render(
            self._format_menu_score(score)
            if score is not None
            else "NO RECORD",
            True,
            (225, 240, 250)
            if score is not None
            else (85, 108, 140),
        )
        rank_surface.set_alpha(int(255 * visibility))
        score_surface.set_alpha(int(255 * visibility))
        row.blit(
            rank_surface,
            (
                15,
                row_rect.height // 2 - rank_surface.get_height() // 2,
            ),
        )
        row.blit(
            score_surface,
            (
                row_rect.width - score_surface.get_width() - 16,
                row_rect.height // 2 - score_surface.get_height() // 2,
            ),
        )
        self.screen.blit(row, row_rect.topleft)

    # Butonul vizibil revine direct în centrul de comandă.
    def _draw_archive_back_button(self, visibility):
        button_rect = self.leaderboard_back_button
        mouse_position = self._get_mouse_position()
        hovered = button_rect.collidepoint(mouse_position)
        accent = (90, 220, 255)
        button = pygame.Surface(button_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            button,
            (12, 75, 108, int(240 * visibility))
            if hovered
            else (7, 24, 49, int(225 * visibility)),
            button.get_rect(),
            border_radius=10,
        )
        pygame.draw.rect(
            button,
            (*accent, int((235 if hovered else 150) * visibility)),
            button.get_rect(),
            2,
            border_radius=10,
        )
        pygame.draw.line(
            button,
            accent,
            (22, button_rect.height // 2),
            (32, button_rect.height // 2 - 8),
            2,
        )
        pygame.draw.line(
            button,
            accent,
            (22, button_rect.height // 2),
            (32, button_rect.height // 2 + 8),
            2,
        )
        label = self.menu_subtitle_font.render(
            "RETURN TO COMMAND",
            True,
            (235, 248, 255),
        )
        label.set_alpha(int(255 * visibility))
        button.blit(
            label,
            (
                button_rect.width // 2 - label.get_width() // 2,
                button_rect.height // 2 - label.get_height() // 2,
            ),
        )
        self.screen.blit(button, button_rect.topleft)

    # Citește și prezintă cele mai bune zece scoruri ca arhivă de piloți.
    def _draw_leaderboard(self):
        self._draw_secondary_screen_frame(
            "PILOT ARCHIVE",
            "GALACTIC DEFENSE COMMAND  //  VERIFIED COMBAT RECORDS",
        )

        visibility = min(
            1.0,
            self.leaderboard_animation_timer / 28,
        )
        panel_rect = pygame.Rect(130, 184, 1020, 420)
        panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            panel,
            (4, 10, 28, int(234 * visibility)),
            panel.get_rect(),
            border_radius=18,
        )
        pygame.draw.rect(
            panel,
            (75, 205, 255, int(160 * visibility)),
            panel.get_rect(),
            2,
            border_radius=18,
        )
        pygame.draw.line(
            panel,
            (75, 205, 255, int(225 * visibility)),
            (24, 1),
            (panel_rect.width - 24, 1),
            3,
        )
        self.screen.blit(panel, panel_rect.topleft)

        scores = self.load_leaderboard()
        pilot_best = max(
            max(scores, default=0),
            max(
                0,
                int(self.save_manager.data.get("highest_score", 0)),
            ),
        )
        header = self.menu_label_font.render(
            "TOP DEFENDERS  //  GALACTIC RANKING",
            True,
            (105, 210, 250),
        )
        archive_status = self.menu_micro_font.render(
            f"ARCHIVED ENTRIES  //  {len(scores):02d}     "
            f"ACTIVE PILOT BEST  //  {self._format_menu_score(pilot_best)}",
            True,
            (110, 145, 180),
        )
        header.set_alpha(int(255 * visibility))
        archive_status.set_alpha(int(255 * visibility))
        self.screen.blit(header, (panel_rect.x + 32, panel_rect.y + 17))
        self.screen.blit(
            archive_status,
            (
                panel_rect.right - archive_status.get_width() - 32,
                panel_rect.y + 20,
            ),
        )

        if not scores:
            empty_center = (self.width // 2, 337)
            pulse = (
                math.sin(pygame.time.get_ticks() * 0.004) + 1.0
            ) / 2.0
            for circle_index, radius in enumerate((92, 66, 38)):
                pygame.draw.circle(
                    self.screen,
                    (
                        65,
                        175,
                        225,
                        int((42 - circle_index * 8) * visibility),
                    ),
                    empty_center,
                    radius + int(pulse * (3 - circle_index)),
                    1,
                )
            pygame.draw.line(
                self.screen,
                (75, 190, 235),
                (empty_center[0] - 112, empty_center[1]),
                (empty_center[0] - 26, empty_center[1]),
                1,
            )
            pygame.draw.line(
                self.screen,
                (75, 190, 235),
                (empty_center[0] + 26, empty_center[1]),
                (empty_center[0] + 112, empty_center[1]),
                1,
            )
            empty_title = self.font.render(
                "NO VERIFIED COMBAT RECORDS",
                True,
                (210, 232, 246),
            )
            empty_subtitle = self.menu_label_font.render(
                "COMPLETE A MISSION TO REGISTER YOUR FIRST SCORE",
                True,
                (95, 165, 205),
            )
            empty_title.set_alpha(int(255 * visibility))
            empty_subtitle.set_alpha(int(255 * visibility))
            self.screen.blit(
                empty_title,
                (
                    self.width // 2 - empty_title.get_width() // 2,
                    445,
                ),
            )
            self.screen.blit(
                empty_subtitle,
                (
                    self.width // 2 - empty_subtitle.get_width() // 2,
                    486,
                ),
            )

            button_visibility = max(
                0.0,
                min(
                    1.0,
                    (self.leaderboard_animation_timer - 18) / 18,
                ),
            )
            self._draw_archive_back_button(button_visibility)
            back_hint = self.menu_micro_font.render(
                "ENTER  //  MAIN MENU        ESC  //  PREVIOUS SCREEN",
                True,
                (90, 115, 148),
            )
            back_hint.set_alpha(int(255 * button_visibility))
            self.screen.blit(
                back_hint,
                (
                    self.width // 2 - back_hint.get_width() // 2,
                    683,
                ),
            )
            return

        count_progress = max(
            0.0,
            min(
                1.0,
                (self.leaderboard_animation_timer - 8) / 38,
            ),
        )
        count_progress = 1.0 - (1.0 - count_progress) ** 3
        podium_layout = (
            (2, pygame.Rect(165, 238, 280, 135), (185, 205, 225), "SILVER COMMAND"),
            (1, pygame.Rect(500, 226, 280, 152), (255, 196, 82), "GOLD COMMAND"),
            (3, pygame.Rect(835, 238, 280, 135), (218, 139, 86), "BRONZE COMMAND"),
        )
        for slot_index, (rank, card_rect, color, label) in enumerate(
            podium_layout
        ):
            score_index = rank - 1
            actual_score = (
                scores[score_index]
                if score_index < len(scores)
                else None
            )
            displayed_score = (
                int(actual_score * count_progress)
                if actual_score is not None
                else None
            )
            card_visibility = max(
                0.0,
                min(
                    1.0,
                    (
                        self.leaderboard_animation_timer
                        - 4
                        - slot_index * 4
                    ) / 24,
                ),
            )
            self._draw_archive_podium_card(
                card_rect,
                rank,
                displayed_score,
                color,
                label,
                card_visibility,
                featured=(rank == 1),
            )

        pygame.draw.line(
            self.screen,
            (55, 110, 150, int(135 * visibility)),
            (panel_rect.x + 35, 390),
            (panel_rect.right - 35, 390),
            1,
        )
        left_header = self.menu_micro_font.render(
            "ARCHIVE BLOCK A  //  RANKS 04-07",
            True,
            (85, 145, 185),
        )
        right_header = self.menu_micro_font.render(
            "ARCHIVE BLOCK B  //  RANKS 08-10",
            True,
            (85, 145, 185),
        )
        left_header.set_alpha(int(255 * visibility))
        right_header.set_alpha(int(255 * visibility))
        self.screen.blit(left_header, (165, 399))
        self.screen.blit(right_header, (670, 399))

        row_width = 445
        row_height = 32
        row_gap = 6
        for rank in range(4, 8):
            row_index = rank - 4
            row_visibility = max(
                0.0,
                min(
                    1.0,
                    (
                        self.leaderboard_animation_timer
                        - 18
                        - row_index * 3
                    ) / 18,
                ),
            )
            score = scores[rank - 1] if rank - 1 < len(scores) else None
            self._draw_archive_row(
                pygame.Rect(
                    165,
                    420 + row_index * (row_height + row_gap),
                    row_width,
                    row_height,
                ),
                rank,
                score,
                row_visibility,
            )

        for rank in range(8, 11):
            row_index = rank - 8
            row_visibility = max(
                0.0,
                min(
                    1.0,
                    (
                        self.leaderboard_animation_timer
                        - 21
                        - row_index * 3
                    ) / 18,
                ),
            )
            score = scores[rank - 1] if rank - 1 < len(scores) else None
            self._draw_archive_row(
                pygame.Rect(
                    670,
                    420 + row_index * (row_height + row_gap),
                    row_width,
                    row_height,
                ),
                rank,
                score,
                row_visibility,
            )

        self._draw_archive_row(
            pygame.Rect(670, 534, row_width, row_height),
            0,
            pilot_best,
            max(
                0.0,
                min(
                    1.0,
                    (self.leaderboard_animation_timer - 30) / 18,
                ),
            ),
            highlighted=True,
        )

        button_visibility = max(
            0.0,
            min(
                1.0,
                (self.leaderboard_animation_timer - 28) / 18,
            ),
        )
        self._draw_archive_back_button(button_visibility)
        back_hint = self.menu_micro_font.render(
            "ENTER  //  MAIN MENU        ESC  //  PREVIOUS SCREEN",
            True,
            (90, 115, 148),
        )
        back_hint.set_alpha(int(255 * button_visibility))
        self.screen.blit(
            back_hint,
            (
                self.width // 2 - back_hint.get_width() // 2,
                683,
            ),
        )

    # Desenează un slider care poate fi apăsat sau tras cu mouse-ul.
    def _draw_settings_slider(
        self,
        slider_rect,
        value,
        slider_name,
        mouse_position,
        visibility,
    ):
        hovered = slider_rect.inflate(0, 18).collidepoint(
            mouse_position
        )
        active = self.active_settings_slider == slider_name
        accent = (75, 215, 255) if slider_name == "music" else (155, 115, 245)

        pygame.draw.rect(
            self.screen,
            (10, 28, 51),
            slider_rect,
            border_radius=9,
        )
        pygame.draw.rect(
            self.screen,
            (52, 92, 125),
            slider_rect,
            1,
            border_radius=9,
        )
        fill_width = int(slider_rect.width * max(0.0, min(1.0, value)))
        if fill_width > 0:
            pygame.draw.rect(
                self.screen,
                accent,
                pygame.Rect(
                    slider_rect.x,
                    slider_rect.y,
                    fill_width,
                    slider_rect.height,
                ),
                border_radius=9,
            )

        for tick_index in range(1, 10):
            tick_x = slider_rect.x + int(
                slider_rect.width * tick_index / 10
            )
            pygame.draw.line(
                self.screen,
                (160, 220, 240) if tick_x <= slider_rect.x + fill_width else (45, 75, 105),
                (tick_x, slider_rect.y + 5),
                (tick_x, slider_rect.bottom - 5),
                1,
            )

        knob_x = slider_rect.x + fill_width
        if active or hovered:
            pygame.draw.circle(
                self.screen,
                (*accent, int(55 * visibility)),
                (knob_x, slider_rect.centery),
                15,
            )
        pygame.draw.circle(
            self.screen,
            (235, 250, 255),
            (knob_x, slider_rect.centery),
            8 if (active or hovered) else 7,
        )
        pygame.draw.circle(
            self.screen,
            accent,
            (knob_x, slider_rect.centery),
            8 if (active or hovered) else 7,
            2,
        )

    # Desenează butoanele compacte pentru volum și schimbarea rezoluției.
    def _draw_settings_step_button(
        self,
        button_rect,
        symbol,
        mouse_position,
        accent_color,
        visibility,
    ):
        hovered = button_rect.collidepoint(mouse_position)
        button = pygame.Surface(button_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            button,
            (*accent_color, int(95 * visibility))
            if hovered
            else (7, 20, 42, int(220 * visibility)),
            button.get_rect(),
            border_radius=9,
        )
        pygame.draw.rect(
            button,
            (*accent_color, int((230 if hovered else 135) * visibility)),
            button.get_rect(),
            2,
            border_radius=9,
        )
        symbol_surface = self.menu_subtitle_font.render(
            symbol,
            True,
            (240, 250, 255),
        )
        symbol_surface.set_alpha(int(255 * visibility))
        button.blit(
            symbol_surface,
            (
                button_rect.width // 2 - symbol_surface.get_width() // 2,
                button_rect.height // 2 - symbol_surface.get_height() // 2,
            ),
        )
        self.screen.blit(button, button_rect.topleft)

    # Desenează comutatorul vizual pentru modul fullscreen.
    def _draw_settings_fullscreen_toggle(
        self,
        visibility,
        mouse_position,
    ):
        toggle_rect = self.fullscreen_button
        hovered = toggle_rect.collidepoint(mouse_position)
        accent = (80, 220, 180) if self.fullscreen else (105, 135, 170)
        toggle = pygame.Surface(toggle_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            toggle,
            (*accent, int((105 if hovered else 65) * visibility)),
            toggle.get_rect(),
            border_radius=22,
        )
        pygame.draw.rect(
            toggle,
            (*accent, int((235 if hovered else 165) * visibility)),
            toggle.get_rect(),
            2,
            border_radius=22,
        )
        knob_x = toggle_rect.width - 23 if self.fullscreen else 23
        pygame.draw.circle(
            toggle,
            (235, 250, 255, int(255 * visibility)),
            (knob_x, toggle_rect.height // 2),
            16,
        )
        state = self.menu_micro_font.render(
            "ON" if self.fullscreen else "OFF",
            True,
            (230, 250, 245) if self.fullscreen else (165, 185, 208),
        )
        state.set_alpha(int(255 * visibility))
        state_x = 17 if self.fullscreen else toggle_rect.width - state.get_width() - 15
        toggle.blit(
            state,
            (
                state_x,
                toggle_rect.height // 2 - state.get_height() // 2,
            ),
        )
        self.screen.blit(toggle, toggle_rect.topleft)

    # Desenează butonul care revine la ecranul din care au fost deschise setările.
    def _draw_settings_back_button(self, visibility, mouse_position):
        button_rect = self.settings_back_button
        hovered = button_rect.collidepoint(mouse_position)
        button = pygame.Surface(button_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            button,
            (12, 75, 108, int(240 * visibility))
            if hovered
            else (7, 24, 49, int(225 * visibility)),
            button.get_rect(),
            border_radius=10,
        )
        pygame.draw.rect(
            button,
            (90, 220, 255, int((235 if hovered else 150) * visibility)),
            button.get_rect(),
            2,
            border_radius=10,
        )
        pygame.draw.line(
            button,
            (90, 220, 255),
            (10, button_rect.height // 2),
            (20, button_rect.height // 2 - 8),
            2,
        )
        pygame.draw.line(
            button,
            (90, 220, 255),
            (10, button_rect.height // 2),
            (20, button_rect.height // 2 + 8),
            2,
        )
        label = self.menu_subtitle_font.render(
            "RETURN TO PREVIOUS SCREEN",
            True,
            (235, 248, 255),
        )
        label.set_alpha(int(255 * visibility))
        button.blit(
            label,
            (
                button_rect.width // 2 - label.get_width() // 2,
                button_rect.height // 2 - label.get_height() // 2,
            ),
        )
        self.screen.blit(button, button_rect.topleft)

    # Desenează configurația audio, video și comenzile pilotului.
    def _draw_settings(self):
        self._draw_secondary_screen_frame(
            "SYSTEM CONFIGURATION",
            "GALACTIC DEFENSE COMMAND  //  PILOT PREFERENCES",
        )

        visibility = min(
            1.0,
            self.settings_animation_timer / 28,
        )
        content_visibility = max(
            0.0,
            min(
                1.0,
                (self.settings_animation_timer - 4) / 24,
            ),
        )
        panel_rect = pygame.Rect(110, 188, 1060, 418)
        panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            panel,
            (4, 10, 28, int(235 * visibility)),
            panel.get_rect(),
            border_radius=18,
        )
        pygame.draw.rect(
            panel,
            (75, 205, 255, int(155 * visibility)),
            panel.get_rect(),
            2,
            border_radius=18,
        )
        pygame.draw.line(
            panel,
            (75, 215, 255, int(225 * visibility)),
            (24, 1),
            (panel_rect.width - 24, 1),
            3,
        )
        self.screen.blit(panel, panel_rect.topleft)

        audio_rect = pygame.Rect(140, 218, 480, 305)
        display_rect = pygame.Rect(660, 218, 480, 305)
        for card_rect, accent in (
            (audio_rect, (75, 205, 255)),
            (display_rect, (155, 115, 245)),
        ):
            card = pygame.Surface(card_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(
                card,
                (6, 17, 37, int(220 * content_visibility)),
                card.get_rect(),
                border_radius=14,
            )
            pygame.draw.rect(
                card,
                (*accent, int(115 * content_visibility)),
                card.get_rect(),
                1,
                border_radius=14,
            )
            self.screen.blit(card, card_rect.topleft)

        mouse_position = self._get_mouse_position()
        audio_header = self.menu_label_font.render(
            "AUDIO SYSTEMS",
            True,
            (105, 215, 255),
        )
        display_header = self.menu_label_font.render(
            "DISPLAY SYSTEMS",
            True,
            (180, 150, 245),
        )
        audio_header.set_alpha(int(255 * content_visibility))
        display_header.set_alpha(int(255 * content_visibility))
        self.screen.blit(audio_header, (160, 238))
        self.screen.blit(display_header, (680, 238))

        audio_controls = (
            (
                "MUSIC OUTPUT",
                self.music_volume,
                self.music_slider_rect,
                "music",
                self.music_minus_button,
                self.music_plus_button,
                274,
                (75, 215, 255),
            ),
            (
                "COMBAT EFFECTS",
                self.sound_volume,
                self.sound_slider_rect,
                "sound",
                self.sound_minus_button,
                self.sound_plus_button,
                379,
                (155, 115, 245),
            ),
        )
        for (
            label,
            value,
            slider_rect,
            slider_name,
            minus_button,
            plus_button,
            label_y,
            accent,
        ) in audio_controls:
            label_surface = self.menu_subtitle_font.render(
                label,
                True,
                (205, 225, 242),
            )
            value_surface = self.menu_label_font.render(
                f"{round(value * 100):03d}%",
                True,
                accent,
            )
            label_surface.set_alpha(int(255 * content_visibility))
            value_surface.set_alpha(int(255 * content_visibility))
            self.screen.blit(label_surface, (160, label_y))
            self.screen.blit(
                value_surface,
                (592 - value_surface.get_width(), label_y + 3),
            )
            self._draw_settings_slider(
                slider_rect,
                value,
                slider_name,
                mouse_position,
                content_visibility,
            )
            self._draw_settings_step_button(
                minus_button,
                "-",
                mouse_position,
                accent,
                content_visibility,
            )
            self._draw_settings_step_button(
                plus_button,
                "+",
                mouse_position,
                accent,
                content_visibility,
            )

        if self.active_settings_slider is not None:
            save_status_text = "ADJUSTING OUTPUT  //  RELEASE TO SAVE"
            save_status_color = (255, 190, 90)
        elif self.settings_saved_feedback_timer > 0:
            save_status_text = "CONFIGURATION SAVED  //  PILOT PROFILE UPDATED"
            save_status_color = (80, 225, 175)
        else:
            save_status_text = "AUTO SAVE LINK  //  READY"
            save_status_color = (90, 155, 190)
        save_status = self.menu_micro_font.render(
            save_status_text,
            True,
            save_status_color,
        )
        save_status.set_alpha(int(255 * content_visibility))
        self.screen.blit(
            save_status,
            (audio_rect.centerx - save_status.get_width() // 2, 488),
        )

        resolution_label = self.menu_subtitle_font.render(
            "OUTPUT RESOLUTION",
            True,
            (205, 225, 242),
        )
        resolution_value = self.pause_value_font.render(
            self.display_manager.get_resolution_label(),
            True,
            (185, 160, 255),
        )
        resolution_label.set_alpha(int(255 * content_visibility))
        resolution_value.set_alpha(int(255 * content_visibility))
        self.screen.blit(resolution_label, (680, 274))
        self.screen.blit(
            resolution_value,
            (
                display_rect.centerx - resolution_value.get_width() // 2,
                310,
            ),
        )
        self._draw_settings_step_button(
            self.resolution_minus_button,
            "<",
            mouse_position,
            (155, 115, 245),
            content_visibility,
        )
        self._draw_settings_step_button(
            self.resolution_plus_button,
            ">",
            mouse_position,
            (155, 115, 245),
            content_visibility,
        )

        fullscreen_label = self.menu_subtitle_font.render(
            "FULLSCREEN MODE",
            True,
            (205, 225, 242),
        )
        fullscreen_label.set_alpha(int(255 * content_visibility))
        self.screen.blit(fullscreen_label, (680, 394))
        self._draw_settings_fullscreen_toggle(
            content_visibility,
            mouse_position,
        )

        display_details = (
            "LOGICAL CANVAS  //  1280 x 720",
            "ADAPTIVE SCALING  //  ENABLED",
            "RENDERER MODE  //  SAFE COMPATIBILITY",
        )
        for detail_index, detail_text in enumerate(display_details):
            detail_surface = self.menu_micro_font.render(
                detail_text,
                True,
                (105, 135, 170),
            )
            detail_surface.set_alpha(int(255 * content_visibility))
            self.screen.blit(
                detail_surface,
                (680, 452 + detail_index * 20),
            )

        controls_rect = pygame.Rect(140, 538, 1000, 50)
        controls = pygame.Surface(controls_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            controls,
            (6, 17, 37, int(215 * content_visibility)),
            controls.get_rect(),
            border_radius=11,
        )
        pygame.draw.rect(
            controls,
            (65, 145, 190, int(105 * content_visibility)),
            controls.get_rect(),
            1,
            border_radius=11,
        )
        self.screen.blit(controls, controls_rect.topleft)
        control_definitions = (
            ("WASD / ARROWS", "MOVE"),
            ("SPACE", "FIRE"),
            ("E", "ENERGY PULSE"),
            ("ESC", "PAUSE / BACK"),
        )
        control_width = controls_rect.width // len(control_definitions)
        for control_index, (key_text, action_text) in enumerate(
            control_definitions
        ):
            center_x = (
                controls_rect.x
                + control_index * control_width
                + control_width // 2
            )
            key_surface = self.menu_label_font.render(
                key_text,
                True,
                (105, 215, 255),
            )
            action_surface = self.menu_micro_font.render(
                action_text,
                True,
                (110, 135, 165),
            )
            key_surface.set_alpha(int(255 * content_visibility))
            action_surface.set_alpha(int(255 * content_visibility))
            self.screen.blit(
                key_surface,
                (center_x - key_surface.get_width() // 2, 546),
            )
            self.screen.blit(
                action_surface,
                (center_x - action_surface.get_width() // 2, 569),
            )

        back_visibility = max(
            0.0,
            min(
                1.0,
                (self.settings_animation_timer - 20) / 18,
            ),
        )
        self._draw_settings_back_button(
            back_visibility,
            mouse_position,
        )
        back_hint = self.menu_micro_font.render(
            "ESC  //  RETURN TO PREVIOUS SCREEN",
            True,
            (90, 115, 148),
        )
        back_hint.set_alpha(int(255 * back_visibility))
        self.screen.blit(
            back_hint,
            (
                self.width // 2 - back_hint.get_width() // 2,
                683,
            ),
        )

    # Desenează umplerea unei bare de volum între 0% și 100%.
    def _draw_volume_bar(self, bar_rect, value):
        pygame.draw.rect(
            self.screen,
            (7, 17, 36),
            bar_rect,
            border_radius=8,
        )
        pygame.draw.rect(
            self.screen,
            (48, 103, 145),
            bar_rect,
            2,
            border_radius=8,
        )
        fill_width = int(
            (bar_rect.width - 6)
            * max(0.0, min(1.0, value))
        )
        if fill_width > 0:
            pygame.draw.rect(
                self.screen,
                (55, 205, 255),
                (
                    bar_rect.x + 3,
                    bar_rect.y + 3,
                    fill_width,
                    bar_rect.height - 6,
                ),
                border_radius=5,
            )

    # Desenează un titlu centrat orizontal la poziția verticală primită.
    def _draw_centered_title(
        self,
        text,
        y_position,
    ):
        title = self.title_font.render(
            text,
            True,
            (80, 210, 255),
        )
        self.screen.blit(
            title,
            (
                self.width // 2
                - title.get_width() // 2,
                y_position,
            ),
        )

    # Afișează indicația prin care utilizatorul poate reveni cu ESC.
    def _draw_back_hint(self):
        back_text = self.menu_label_font.render(
            "ESC  //  RETURN TO PREVIOUS SCREEN",
            True,
            (100, 175, 215),
        )
        self.screen.blit(
            back_text,
            (
                self.width // 2
                - back_text.get_width() // 2,
                674,
            ),
        )

    # Desenează un buton și îi schimbă aspectul atunci când mouse-ul este deasupra.
    def _draw_button(
        self,
        button_rect,
        button_text,
        mouse_position,
        animated=False,
    ):
        is_hovered = button_rect.collidepoint(
            mouse_position
        )

        if is_hovered:
            button_color = (18, 112, 170)
            text_color = (255, 255, 255)
            border_color = (90, 225, 255)
            scale_amount = 10 if animated else 0
        else:
            button_color = (10, 19, 43)
            text_color = (195, 210, 232)
            border_color = (62, 110, 155)
            scale_amount = 0

        draw_rect = pygame.Rect(
            button_rect.x - scale_amount // 2,
            button_rect.y - scale_amount // 2,
            button_rect.width + scale_amount,
            button_rect.height + scale_amount,
        )

        button_surface = pygame.Surface(
            draw_rect.size,
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            button_surface,
            (*button_color, 232),
            button_surface.get_rect(),
            border_radius=9,
        )
        pygame.draw.rect(
            button_surface,
            (*border_color, 230),
            button_surface.get_rect(),
            2,
            border_radius=9,
        )
        pygame.draw.line(
            button_surface,
            (*border_color, 245),
            (0, 8),
            (0, draw_rect.height - 8),
            5,
        )

        if is_hovered:
            glow_surface = pygame.Surface(
                (draw_rect.width + 20, draw_rect.height + 20),
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                glow_surface,
                (50, 195, 255, 45),
                glow_surface.get_rect(),
                border_radius=14,
            )
            self.screen.blit(
                glow_surface,
                (draw_rect.x - 10, draw_rect.y - 10),
            )

        self.screen.blit(button_surface, draw_rect.topleft)

        text_font = (
            self.menu_button_font
            if animated
            else self.menu_font
        )
        text_surface = text_font.render(
            button_text,
            True,
            text_color,
        )
        self.screen.blit(
            text_surface,
            (
                (
                    draw_rect.x + 28
                    if animated
                    else draw_rect.centerx
                    - text_surface.get_width() // 2
                ),
                draw_rect.centery
                - text_surface.get_height() // 2,
            ),
        )

        if animated:
            arrow_surface = self.menu_button_font.render(
                ">",
                True,
                border_color,
            )
            self.screen.blit(
                arrow_surface,
                (
                    draw_rect.right
                    - arrow_surface.get_width()
                    - 22,
                    draw_rect.centery
                    - arrow_surface.get_height() // 2,
                ),
            )


# Pornește aplicația numai atunci când main.py este rulat direct.
if __name__ == "__main__":
    game = GalaxyDefender()
    game.run()
