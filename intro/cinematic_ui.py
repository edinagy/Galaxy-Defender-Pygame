import math

import pygame


_PORTRAIT_CACHE = {}


class CinematicOverlay:
    """Subtitrări și comunicații comune tuturor scenelor de poveste."""

    def __init__(self):
        self.speaker_font = pygame.font.Font(None, 22)
        self.dialogue_font = pygame.font.Font(None, 27)
        self.micro_font = pygame.font.Font(None, 17)
        self.portrait = self._load_portrait((84, 94))

    @staticmethod
    def _load_portrait(size):
        if size not in _PORTRAIT_CACHE:
            portrait = pygame.image.load(
                "assets/images/intro/commander_vale_portrait.png"
            ).convert_alpha()
            visible_bounds = portrait.get_bounding_rect(min_alpha=8)
            if visible_bounds.width and visible_bounds.height:
                portrait = portrait.subsurface(visible_bounds).copy()
            scale = min(
                size[0] / portrait.get_width(),
                size[1] / portrait.get_height(),
            )
            portrait = pygame.transform.smoothscale(
                portrait,
                (
                    max(1, int(portrait.get_width() * scale)),
                    max(1, int(portrait.get_height() * scale)),
                ),
            )
            _PORTRAIT_CACHE[size] = portrait
        return _PORTRAIT_CACHE[size]

    @staticmethod
    def _active_cue(elapsed_time, cues):
        for cue in cues:
            if cue[0] <= elapsed_time < cue[1]:
                return cue
        return None

    def draw(
        self,
        screen,
        elapsed_time,
        cues,
        chapter,
        status="CINEMATIC LINK",
        letterbox=True,
        show_skip=True,
    ):
        if letterbox:
            self._draw_letterbox(screen, chapter, status, show_skip)

        cue = self._active_cue(elapsed_time, cues)
        if cue is not None:
            self._draw_transmission(screen, elapsed_time, cue)

    def _draw_letterbox(self, screen, chapter, status, show_skip):
        width, height = screen.get_size()
        top_bar = pygame.Surface((width, 34), pygame.SRCALPHA)
        bottom_bar = pygame.Surface((width, 34), pygame.SRCALPHA)
        top_bar.fill((0, 2, 8, 238))
        bottom_bar.fill((0, 2, 8, 238))
        screen.blit(top_bar, (0, 0))
        screen.blit(bottom_bar, (0, height - 34))

        chapter_surface = self.micro_font.render(
            chapter,
            True,
            (165, 205, 230),
        )
        status_surface = self.micro_font.render(
            f"LINK // {status}",
            True,
            (85, 225, 190),
        )
        screen.blit(chapter_surface, (22, 10))
        screen.blit(
            status_surface,
            (width - status_surface.get_width() - 22, 10),
        )

        if show_skip:
            skip_surface = self.micro_font.render(
                "A / ENTER / SPACE  //  CONTINUE",
                True,
                (105, 135, 165),
            )
            screen.blit(
                skip_surface,
                (
                    width - skip_surface.get_width() - 22,
                    height - 24,
                ),
            )

    def _draw_transmission(self, screen, elapsed_time, cue):
        start_time, end_time, speaker, dialogue, channel = cue
        local_time = elapsed_time - start_time
        fade_in = min(1.0, local_time / 0.22)
        fade_out = min(1.0, (end_time - elapsed_time) / 0.30)
        visibility = max(0.0, min(fade_in, fade_out))
        if visibility <= 0:
            return

        width, height = screen.get_size()
        panel_rect = pygame.Rect(34, height - 164, width - 68, 116)
        panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        emergency = channel == "EMERGENCY"
        accent = (255, 103, 82) if emergency else (73, 215, 255)
        pygame.draw.rect(
            panel,
            (3, 10, 24, int(228 * visibility)),
            panel.get_rect(),
            border_radius=11,
        )
        pygame.draw.rect(
            panel,
            (*accent, int(205 * visibility)),
            panel.get_rect(),
            2,
            border_radius=11,
        )
        pygame.draw.line(
            panel,
            (*accent, int(245 * visibility)),
            (2, 12),
            (2, panel_rect.height - 12),
            4,
        )

        portrait_width = 100
        portrait_rect = pygame.Rect(10, 10, portrait_width, 96)
        pygame.draw.rect(
            panel,
            (7, 20, 38, int(215 * visibility)),
            portrait_rect,
            border_radius=8,
        )

        if speaker == "COMMANDER VALE":
            portrait = self.portrait.copy()
            portrait.set_alpha(int(235 * visibility))
            portrait_x = portrait_rect.centerx - portrait.get_width() // 2
            portrait_y = portrait_rect.bottom - portrait.get_height() - 1
            panel.blit(portrait, (portrait_x, portrait_y))
            scan_y = int((elapsed_time * 41) % portrait_rect.height)
            pygame.draw.line(
                panel,
                (*accent, int(80 * visibility)),
                (portrait_rect.x + 5, portrait_rect.y + scan_y),
                (portrait_rect.right - 5, portrait_rect.y + scan_y),
                1,
            )
        else:
            center = portrait_rect.center
            pulse = 0.5 + math.sin(elapsed_time * 7.0) * 0.5
            pygame.draw.circle(
                panel,
                (*accent, int((110 + pulse * 80) * visibility)),
                center,
                27,
                2,
            )
            for line_index in range(7):
                bar_height = 7 + int(
                    15
                    * abs(
                        math.sin(
                            elapsed_time * 5.2 + line_index * 0.9
                        )
                    )
                )
                bar_x = center[0] - 24 + line_index * 8
                pygame.draw.line(
                    panel,
                    (*accent, int(220 * visibility)),
                    (bar_x, center[1] - bar_height // 2),
                    (bar_x, center[1] + bar_height // 2),
                    3,
                )

        pygame.draw.rect(
            panel,
            (*accent, int(150 * visibility)),
            portrait_rect,
            1,
            border_radius=8,
        )

        speaker_surface = self.speaker_font.render(
            speaker,
            True,
            accent,
        )
        channel_surface = self.micro_font.render(
            channel,
            True,
            (115, 145, 175),
        )
        text_x = 126
        panel.blit(speaker_surface, (text_x, 15))
        panel.blit(
            channel_surface,
            (
                panel_rect.width - channel_surface.get_width() - 18,
                18,
            ),
        )

        visible_character_count = max(1, int(local_time * 72))
        visible_dialogue = dialogue[:visible_character_count]
        lines = self._wrap_text(
            visible_dialogue,
            self.dialogue_font,
            panel_rect.width - text_x - 30,
        )
        for line_index, line in enumerate(lines[:2]):
            line_surface = self.dialogue_font.render(
                line,
                True,
                (224, 238, 248),
            )
            panel.blit(line_surface, (text_x, 47 + line_index * 29))

        panel.set_alpha(int(255 * visibility))
        screen.blit(panel, panel_rect.topleft)

    @staticmethod
    def _wrap_text(text, font, maximum_width):
        words = text.split(" ")
        lines = []
        current_line = ""
        for word in words:
            candidate = word if not current_line else f"{current_line} {word}"
            if font.size(candidate)[0] <= maximum_width:
                current_line = candidate
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines


def draw_camera_noise(screen, elapsed_time, strength=1.0):
    """Linii discrete de interferență, fără a aloca texturi mari."""
    if strength <= 0:
        return
    width, height = screen.get_size()
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    base_alpha = max(0, min(18, int(9 * strength)))
    offset = int(elapsed_time * 37) % 29
    for y_position in range(offset, height, 29):
        pygame.draw.line(
            overlay,
            (120, 200, 255, base_alpha),
            (0, y_position),
            (width, y_position),
            1,
        )
    screen.blit(overlay, (0, 0))
