import pygame


# Rezoluția în care au fost construite meniurile, scenele și gameplay-ul.
DESIGN_WIDTH = 1280
DESIGN_HEIGHT = 720


# Managerul central al ferestrei și al modului fullscreen.
# Restul jocului continuă să lucreze în coordonate 1280x720, iar această clasă
# se ocupă de afișare, proporții, margini și coordonatele mouse-ului.
class DisplayManager:

    COMMON_RESOLUTIONS = (
        (1280, 720),
        (1366, 768),
        (1600, 900),
        (1920, 1080),
        (2560, 1440),
        (3840, 2160),
    )

    def __init__(
        self,
        resolution=(1280, 720),
        fullscreen=False,
    ):
        self.logical_size = (
            DESIGN_WIDTH,
            DESIGN_HEIGHT,
        )
        self.fullscreen = bool(fullscreen)

        self.desktop_size = self._get_desktop_size()
        self.available_resolutions = (
            self._detect_resolutions()
        )
        self.resolution = self._validate_resolution(
            resolution
        )

        self.display_surface = None
        self.canvas = None
        self.scaled_frame = None
        self.viewport_size = self.logical_size
        self.viewport_offset = (0, 0)
        self._integer_scaling = False

        self.recreate_display()

    # Citește rezoluția fizică a monitorului principal.
    @staticmethod
    def _get_desktop_size():
        desktop_sizes = pygame.display.get_desktop_sizes()
        if desktop_sizes:
            return tuple(desktop_sizes[0])

        display_info = pygame.display.Info()
        return (
            max(DESIGN_WIDTH, display_info.current_w),
            max(DESIGN_HEIGHT, display_info.current_h),
        )

    # Construiește lista de rezoluții disponibile pe calculatorul jucătorului.
    def _detect_resolutions(self):
        desktop_width, desktop_height = self.desktop_size
        detected = set()

        for width, height in self.COMMON_RESOLUTIONS:
            if (
                width <= desktop_width
                and height <= desktop_height
            ):
                detected.add((width, height))

        display_modes = pygame.display.list_modes()
        if display_modes not in (-1, None):
            for width, height in display_modes:
                aspect_ratio = width / max(1, height)
                if (
                    width >= 1280
                    and height >= 720
                    and width <= desktop_width
                    and height <= desktop_height
                    and 1.25 <= aspect_ratio <= 2.40
                ):
                    detected.add((width, height))

        # Rezoluția nativă apare întotdeauna, inclusiv pe 16:10/ultrawide.
        detected.add(self.desktop_size)
        detected.add((DESIGN_WIDTH, DESIGN_HEIGHT))

        return sorted(
            detected,
            key=lambda size: (
                size[0] * size[1],
                size[0],
            ),
        )

    # Corectează o valoare lipsă sau incompatibilă din save.json.
    def _validate_resolution(self, resolution):
        try:
            requested = (
                int(resolution[0]),
                int(resolution[1]),
            )
        except (TypeError, ValueError, IndexError):
            requested = (DESIGN_WIDTH, DESIGN_HEIGHT)

        if requested in self.available_resolutions:
            return requested

        # Alege modul disponibil cel mai apropiat ca număr de pixeli.
        requested_pixels = requested[0] * requested[1]
        return min(
            self.available_resolutions,
            key=lambda size: abs(
                size[0] * size[1] - requested_pixels
            ),
        )

    # Creează fereastra sau modul fullscreen la rezoluția selectată.
    def recreate_display(self):
        display_flags = (
            pygame.FULLSCREEN | pygame.DOUBLEBUF
            if self.fullscreen
            else 0
        )

        try:
            self.display_surface = pygame.display.set_mode(
                self.resolution,
                display_flags,
            )
        except pygame.error:
            # DOUBLEBUF poate lipsi pe anumite drivere; fullscreen rămâne activ.
            fallback_flags = (
                pygame.FULLSCREEN
                if self.fullscreen
                else 0
            )
            try:
                self.display_surface = pygame.display.set_mode(
                    self.resolution,
                    fallback_flags,
                )
            except pygame.error:
                # Ultima rezervă: modul nativ este acceptat de monitor sigur.
                self.resolution = self.desktop_size
                self.display_surface = pygame.display.set_mode(
                    self.resolution,
                    fallback_flags,
                )

        actual_width, actual_height = (
            self.display_surface.get_size()
        )
        logical_width, logical_height = self.logical_size

        scale_factor = min(
            actual_width / logical_width,
            actual_height / logical_height,
        )
        viewport_width = max(
            1,
            round(logical_width * scale_factor),
        )
        viewport_height = max(
            1,
            round(logical_height * scale_factor),
        )

        self.viewport_size = (
            viewport_width,
            viewport_height,
        )
        self.viewport_offset = (
            (actual_width - viewport_width) // 2,
            (actual_height - viewport_height) // 2,
        )

        horizontal_scale = viewport_width / logical_width
        vertical_scale = viewport_height / logical_height
        self._integer_scaling = (
            abs(horizontal_scale - round(horizontal_scale)) < 0.001
            and abs(vertical_scale - round(vertical_scale)) < 0.001
        )

        # Canvasul este mereu separat de fereastră, pentru comportament identic
        # în toate modurile și pentru schimbarea sigură a rezoluției în mers.
        self.canvas = pygame.Surface(
            self.logical_size
        ).convert()
        self.scaled_frame = pygame.Surface(
            self.viewport_size
        ).convert()

    # Afișează cadrul jocului în zona corectă a ferestrei fizice.
    def present(self):
        self.display_surface.fill((0, 0, 0))

        if self.viewport_size == self.logical_size:
            self.scaled_frame.blit(
                self.canvas,
                (0, 0),
            )
        elif self._integer_scaling:
            # La 2x/3x/4x păstrăm pixelii exacți și evităm blurul.
            pygame.transform.scale(
                self.canvas,
                self.viewport_size,
                self.scaled_frame,
            )
        else:
            # Pentru 1366x768, 1600x900 sau 1920x1080 este necesară
            # interpolarea, fiindcă factorul nu este un număr întreg.
            pygame.transform.smoothscale(
                self.canvas,
                self.viewport_size,
                self.scaled_frame,
            )

        self.display_surface.blit(
            self.scaled_frame,
            self.viewport_offset,
        )

    # Transformă poziția fizică a mouse-ului în coordonate 1280x720.
    def to_game_position(self, mouse_position):
        mouse_x, mouse_y = mouse_position
        offset_x, offset_y = self.viewport_offset
        viewport_width, viewport_height = self.viewport_size

        if not (
            offset_x <= mouse_x < offset_x + viewport_width
            and offset_y <= mouse_y < offset_y + viewport_height
        ):
            return (-10000, -10000)

        return (
            int(
                (mouse_x - offset_x)
                * DESIGN_WIDTH
                / viewport_width
            ),
            int(
                (mouse_y - offset_y)
                * DESIGN_HEIGHT
                / viewport_height
            ),
        )

    def get_mouse_position(self):
        return self.to_game_position(
            pygame.mouse.get_pos()
        )

    # Selectează următoarea sau precedenta rezoluție disponibilă.
    def cycle_resolution(self, direction):
        current_index = self.available_resolutions.index(
            self.resolution
        )
        new_index = (
            current_index + int(direction)
        ) % len(self.available_resolutions)
        self.resolution = self.available_resolutions[
            new_index
        ]
        self.recreate_display()
        return self.resolution

    # Activează/dezactivează fullscreen fără să piardă rezoluția selectată.
    def set_fullscreen(self, fullscreen):
        self.fullscreen = bool(fullscreen)
        self.recreate_display()

    # Textul afișat în meniul Settings.
    def get_resolution_label(self):
        width, height = self.resolution
        native_suffix = (
            "  //  NATIVE"
            if self.resolution == self.desktop_size
            else ""
        )
        return f"{width} x {height}{native_suffix}"
