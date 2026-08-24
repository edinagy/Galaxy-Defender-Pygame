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
            370,
            430,
            250,
            60,
        )
        self.cancel_new_game_button = pygame.Rect(
            660,
            430,
            250,
            60,
        )

        self.resume_button = pygame.Rect(
            500,
            280,
            280,
            60,
        )
        self.pause_settings_button = pygame.Rect(
            500,
            370,
            280,
            60,
        )
        self.pause_menu_button = pygame.Rect(
            500,
            460,
            280,
            60,
        )

        self.music_minus_button = pygame.Rect(
            370,
            240,
            60,
            50,
        )
        self.music_plus_button = pygame.Rect(
            850,
            240,
            60,
            50,
        )
        self.sound_minus_button = pygame.Rect(
            370,
            335,
            60,
            50,
        )
        self.sound_plus_button = pygame.Rect(
            850,
            335,
            60,
            50,
        )
        self.resolution_minus_button = pygame.Rect(
            370,
            430,
            60,
            50,
        )
        self.resolution_plus_button = pygame.Rect(
            850,
            430,
            60,
            50,
        )
        self.fullscreen_button = pygame.Rect(
            500,
            500,
            280,
            55,
        )
        self.settings_back_button = pygame.Rect(
            500,
            570,
            280,
            55,
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

        if event.type == pygame.KEYDOWN:
            if (
                current_scene == SceneManager.MENU
                and self.confirm_new_game
            ):
                if event.key == pygame.K_y:
                    self._confirm_new_campaign()
                elif event.key in (
                    pygame.K_n,
                    pygame.K_ESCAPE,
                ):
                    self.confirm_new_game = False
                return

            if event.key == pygame.K_ESCAPE:
                self._handle_escape()
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

    # Procesează butoanele PLAY, LEADERBOARD, SETTINGS și EXIT.
    def _handle_menu_click(self, mouse_position):
        if self.confirm_new_game:
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
                self.confirm_new_game = False

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

    # Modifică volumul, fullscreen-ul sau revine la scena anterioară.
    def _handle_settings_click(
        self,
        mouse_position,
    ):
        if self.music_minus_button.collidepoint(
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

        self._start_first_campaign()

    # Salvează imediat valorile curente din meniul Settings.
    def _save_current_settings(self):
        self.save_manager.save_settings(
            self.music_volume,
            self.sound_volume,
            self.fullscreen,
            self.selected_resolution,
        )

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

        # Scenele se pot schimba in timpul update-ului; muzica se sincronizeaza dupa.
        self._sync_scene_music()
        self._sync_scene_ambience()

    # Actualizează animațiile decorative din meniul principal.
    def _update_menu(self):
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

    # Desenează confirmarea necesară înainte de resetarea campaniei.
    def _draw_new_game_confirmation(self):
        overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(
            250,
            210,
            780,
            330,
        )
        pygame.draw.rect(
            self.screen,
            (20, 25, 55),
            panel,
            border_radius=20,
        )
        pygame.draw.rect(
            self.screen,
            (100, 180, 255),
            panel,
            3,
            border_radius=20,
        )

        title = self.menu_font.render(
            "START A NEW CAMPAIGN?",
            True,
            (255, 255, 255),
        )
        warning = self.font.render(
            "Campaign progress will be reset.",
            True,
            (255, 180, 100),
        )
        preserved = self.font.render(
            "High score and settings will be kept.",
            True,
            (180, 220, 255),
        )

        self.screen.blit(
            title,
            (
                self.width // 2
                - title.get_width() // 2,
                260,
            ),
        )
        self.screen.blit(
            warning,
            (
                self.width // 2
                - warning.get_width() // 2,
                335,
            ),
        )
        self.screen.blit(
            preserved,
            (
                self.width // 2
                - preserved.get_width() // 2,
                375,
            ),
        )

        mouse_position = self._get_mouse_position()
        self._draw_button(
            self.confirm_new_game_button,
            "YES",
            mouse_position,
        )
        self._draw_button(
            self.cancel_new_game_button,
            "NO",
            mouse_position,
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

    # Desenează ecranul de pauză peste cadrul înghețat al luptei.
    def _draw_pause(self):
        # Gameplay.draw doar desenează; nu actualizează pozițiile obiectelor.
        # Astfel, lupta rămâne vizibilă și complet înghețată în spate.
        self.gameplay.draw()

        dark_overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )
        dark_overlay.fill((1, 5, 18, 188))
        self.screen.blit(dark_overlay, (0, 0))

        panel_rect = pygame.Rect(430, 92, 420, 535)
        self._draw_glass_panel(panel_rect)

        status = self.menu_label_font.render(
            "MISSION STATUS  //  STANDBY",
            True,
            (85, 215, 255),
        )
        title = self.title_font.render(
            "PAUSED",
            True,
            (235, 246, 255),
        )
        objective = self.menu_label_font.render(
            "COMBAT SIMULATION SUSPENDED",
            True,
            (145, 165, 195),
        )
        self.screen.blit(
            status,
            (self.width // 2 - status.get_width() // 2, 122),
        )
        self.screen.blit(
            title,
            (self.width // 2 - title.get_width() // 2, 157),
        )
        self.screen.blit(
            objective,
            (self.width // 2 - objective.get_width() // 2, 242),
        )
        pygame.draw.line(
            self.screen,
            (75, 205, 255),
            (500, 272),
            (780, 272),
            2,
        )

        buttons = [
            (self.resume_button, "RESUME"),
            (
                self.pause_settings_button,
                "SETTINGS",
            ),
            (
                self.pause_menu_button,
                "MAIN MENU",
            ),
        ]

        mouse_position = self._get_mouse_position()

        for button_rect, button_text in buttons:
            self._draw_button(
                button_rect,
                button_text,
                mouse_position,
                animated=True,
            )

        hint = self.menu_label_font.render(
            "ESC  //  RESUME MISSION",
            True,
            (115, 135, 165),
        )
        self.screen.blit(
            hint,
            (self.width // 2 - hint.get_width() // 2, 584),
        )

    # Citește și afișează cele mai bune zece scoruri.
    def _draw_leaderboard(self):
        self._draw_secondary_screen_frame(
            "LEADERBOARD",
            "GALACTIC DEFENSE COMMAND  //  PILOT ARCHIVE",
        )

        scores = self.load_leaderboard()
        panel_rect = pygame.Rect(330, 195, 620, 425)
        self._draw_glass_panel(panel_rect)

        rank_header = self.menu_label_font.render(
            "RANK",
            True,
            (110, 205, 250),
        )
        score_header = self.menu_label_font.render(
            "COMBAT SCORE",
            True,
            (110, 205, 250),
        )
        self.screen.blit(rank_header, (panel_rect.x + 42, 222))
        self.screen.blit(score_header, (panel_rect.right - 190, 222))
        pygame.draw.line(
            self.screen,
            (50, 105, 150),
            (panel_rect.x + 28, 253),
            (panel_rect.right - 28, 253),
            1,
        )

        y_position = 270

        if not scores:
            no_scores_text = self.font.render(
                "NO COMBAT RECORDS YET",
                True,
                (155, 175, 205),
            )
            self.screen.blit(
                no_scores_text,
                (
                    self.width // 2
                    - no_scores_text.get_width() // 2,
                    y_position,
                ),
            )

        for index, score_value in enumerate(scores):
            row_rect = pygame.Rect(
                panel_rect.x + 24,
                y_position - 5,
                panel_rect.width - 48,
                31,
            )
            if index % 2 == 0:
                pygame.draw.rect(
                    self.screen,
                    (12, 29, 55),
                    row_rect,
                    border_radius=5,
                )

            rank_color = (
                (255, 195, 85)
                if index == 0
                else (205, 220, 238)
            )
            rank_text = self.menu_subtitle_font.render(
                f"#{index + 1:02d}",
                True,
                rank_color,
            )
            score_text = self.menu_subtitle_font.render(
                f"{score_value:,}".replace(",", " "),
                True,
                (235, 245, 255),
            )
            self.screen.blit(rank_text, (panel_rect.x + 43, y_position))
            self.screen.blit(
                score_text,
                (panel_rect.right - 48 - score_text.get_width(), y_position),
            )
            y_position += 34

        self._draw_back_hint()

    # Desenează valorile și butoanele disponibile în meniul Settings.
    def _draw_settings(self):
        self._draw_secondary_screen_frame(
            "SETTINGS",
            "SYSTEM CONFIGURATION  //  PILOT PREFERENCES",
        )

        panel_rect = pygame.Rect(330, 175, 620, 485)
        self._draw_glass_panel(panel_rect)

        music_text = self.menu_subtitle_font.render(
            "MUSIC VOLUME",
            True,
            (205, 222, 242),
        )
        self.screen.blit(
            music_text,
            (455, 252),
        )

        sound_text = self.menu_subtitle_font.render(
            "SOUND EFFECTS",
            True,
            (205, 222, 242),
        )
        self.screen.blit(
            sound_text,
            (455, 347),
        )

        # Barele oferă feedback vizual imediat pentru nivelul volumului.
        self._draw_volume_bar(
            pygame.Rect(595, 253, 225, 20),
            self.music_volume,
        )
        self._draw_volume_bar(
            pygame.Rect(595, 348, 225, 20),
            self.sound_volume,
        )

        music_value = self.menu_label_font.render(
            f"{round(self.music_volume * 100):03d}%",
            True,
            (105, 220, 255),
        )
        sound_value = self.menu_label_font.render(
            f"{round(self.sound_volume * 100):03d}%",
            True,
            (105, 220, 255),
        )
        self.screen.blit(music_value, (742, 280))
        self.screen.blit(sound_value, (742, 375))

        resolution_text = self.menu_subtitle_font.render(
            "DISPLAY RESOLUTION",
            True,
            (205, 222, 242),
        )
        self.screen.blit(
            resolution_text,
            (
                self.width // 2
                - resolution_text.get_width() // 2,
                405,
            ),
        )

        resolution_value = self.menu_label_font.render(
            self.display_manager.get_resolution_label(),
            True,
            (105, 220, 255),
        )
        self.screen.blit(
            resolution_value,
            (
                self.width // 2
                - resolution_value.get_width() // 2,
                450,
            ),
        )

        settings_buttons = [
            (self.music_minus_button, "-"),
            (self.music_plus_button, "+"),
            (self.sound_minus_button, "-"),
            (self.sound_plus_button, "+"),
            (self.resolution_minus_button, "<"),
            (self.resolution_plus_button, ">"),
            (
                self.fullscreen_button,
                (
                    "FULLSCREEN  //  ON"
                    if self.fullscreen
                    else "FULLSCREEN  //  OFF"
                ),
            ),
            (self.settings_back_button, "BACK"),
        ]

        mouse_position = self._get_mouse_position()

        for button_rect, button_text in (
            settings_buttons
        ):
            self._draw_button(
                button_rect,
                button_text,
                mouse_position,
                animated=(button_rect.width > 100),
            )

        self._draw_back_hint()

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
