# Clasa care păstrează scena activă și scena vizitată anterior.
class SceneManager:
    """
    Controlează scena curentă a jocului.

    Scene disponibile:
    - menu
    - planet
    - hangar
    - launch
    - vortex
    - asteroids
    - anomaly
    - wormhole
    - dead_star
    - gameplay
    - pause
    - game_over
    - leaderboard
    - settings
    """

    # Ecranele meniului.
    MENU = "menu"
    LEADERBOARD = "leaderboard"
    SETTINGS = "settings"

    # Scenele campaniei cinematice.
    PLANET = "planet"
    HANGAR = "hangar"
    LAUNCH = "launch"
    VORTEX = "vortex"
    ASTEROIDS = "asteroids"
    ANOMALY = "anomaly"
    WORMHOLE = "wormhole"
    DEAD_STAR = "dead_star"

    # Scenele luptei principale.
    GAMEPLAY = "gameplay"
    PAUSE = "pause"
    GAME_OVER = "game_over"

    # Pornește managerul cu scena primită sau cu meniul principal.
    def __init__(self, starting_scene=MENU):
        self.current_scene = starting_scene
        self.previous_scene = None

    # Schimbă scena și memorează scena care era activă înainte.
    def change_scene(self, new_scene):
        if new_scene == self.current_scene:
            return

        self.previous_scene = self.current_scene
        self.current_scene = new_scene

    # Revine la scena anterioară, dacă aceasta există.
    def go_back(self):
        if self.previous_scene is None:
            return

        old_scene = self.current_scene
        self.current_scene = self.previous_scene
        self.previous_scene = old_scene

    # Returnează True dacă numele primit este scena activă.
    def is_scene(self, scene_name):
        return self.current_scene == scene_name
