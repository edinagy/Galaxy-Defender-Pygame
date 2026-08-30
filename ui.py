import math

import pygame


# Cache-ul evita recrearea fonturilor in fiecare cadru al jocului.
_FONT_CACHE = {}


def _get_font(size):
    if size not in _FONT_CACHE:
        _FONT_CACHE[size] = pygame.font.Font(None, size)

    return _FONT_CACHE[size]


# Deseneaza un panou translucid cu margine si accent luminos.
def _draw_glass_panel(
    screen,
    panel_rect,
    accent_color,
    fill_color=(7, 13, 30, 205),
):
    shadow_surface = pygame.Surface(
        (panel_rect.width + 18, panel_rect.height + 18),
        pygame.SRCALPHA,
    )
    pygame.draw.rect(
        shadow_surface,
        (0, 0, 0, 95),
        (8, 8, panel_rect.width, panel_rect.height),
        border_radius=14,
    )
    screen.blit(
        shadow_surface,
        (panel_rect.x - 4, panel_rect.y - 4),
    )

    panel_surface = pygame.Surface(
        panel_rect.size,
        pygame.SRCALPHA,
    )
    pygame.draw.rect(
        panel_surface,
        fill_color,
        panel_surface.get_rect(),
        border_radius=12,
    )
    pygame.draw.rect(
        panel_surface,
        (*accent_color, 155),
        panel_surface.get_rect(),
        2,
        border_radius=12,
    )
    pygame.draw.line(
        panel_surface,
        (*accent_color, 235),
        (14, 3),
        (panel_rect.width // 2, 3),
        3,
    )
    screen.blit(panel_surface, panel_rect.topleft)


# Deseneaza o eticheta mica pentru shield si double shot.
def _draw_status_chip(
    screen,
    x,
    y,
    label,
    active,
    active_color,
):
    chip_rect = pygame.Rect(x, y, 96, 26)
    fill_color = (
        (*active_color, 205)
        if active
        else (20, 27, 43, 190)
    )
    border_color = (
        active_color
        if active
        else (75, 88, 108)
    )

    chip_surface = pygame.Surface(
        chip_rect.size,
        pygame.SRCALPHA,
    )
    pygame.draw.rect(
        chip_surface,
        fill_color,
        chip_surface.get_rect(),
        border_radius=7,
    )
    pygame.draw.rect(
        chip_surface,
        (*border_color, 210),
        chip_surface.get_rect(),
        1,
        border_radius=7,
    )
    text_surface = _get_font(18).render(
        label,
        True,
        (255, 255, 255) if active else (115, 128, 148),
    )
    chip_surface.blit(
        text_surface,
        (
            chip_rect.width // 2 - text_surface.get_width() // 2,
            chip_rect.height // 2 - text_surface.get_height() // 2,
        ),
    )
    screen.blit(chip_surface, chip_rect.topleft)


# Desenează cele patru trepte ale armei sub panoul de integritate.
def _draw_weapon_bar(
    screen,
    x,
    y,
    player,
    pulse,
):
    weapon_level = max(
        1,
        min(
            getattr(player, "maximum_weapon_level", 4),
            getattr(player, "weapon_level", 1),
        ),
    )
    maximum_level = getattr(
        player,
        "maximum_weapon_level",
        4,
    )

    level_colors = (
        (55, 175, 255),
        (45, 235, 210),
        (195, 85, 255),
        (255, 200, 55),
    )
    accent_color = level_colors[weapon_level - 1]

    if (
        getattr(player, "weapon_feedback_type", None)
        == "downgrade"
        and player.weapon_feedback_timer % 12 < 6
    ):
        accent_color = (255, 70, 90)

    panel_rect = pygame.Rect(x, y, 244, 48)
    _draw_glass_panel(
        screen,
        panel_rect,
        accent_color,
        fill_color=(7, 13, 30, 220),
    )

    label_font = _get_font(16)
    weapon_label = label_font.render(
        "WEAPON SYSTEM",
        True,
        (145, 180, 210),
    )
    level_label = label_font.render(
        (
            "MAXIMUM"
            if weapon_level >= maximum_level
            else f"LEVEL {weapon_level}"
        ),
        True,
        accent_color,
    )
    screen.blit(
        weapon_label,
        (panel_rect.x + 14, panel_rect.y + 8),
    )
    screen.blit(
        level_label,
        (
            panel_rect.right
            - level_label.get_width()
            - 14,
            panel_rect.y + 8,
        ),
    )

    segment_gap = 5
    segment_width = 49
    segment_y = panel_rect.y + 31
    for segment_index in range(maximum_level):
        segment_rect = pygame.Rect(
            panel_rect.x + 14
            + segment_index * (segment_width + segment_gap),
            segment_y,
            segment_width,
            7,
        )
        is_active = segment_index < weapon_level
        segment_color = (
            level_colors[segment_index]
            if is_active
            else (40, 49, 66)
        )
        pygame.draw.rect(
            screen,
            segment_color,
            segment_rect,
            border_radius=3,
        )

    # Upgrade-ul proaspăt produce o lumină scurtă în jurul barei.
    if (
        getattr(player, "weapon_feedback_type", None)
        in ("upgrade", "maximum")
        and player.weapon_feedback_timer > 0
    ):
        glow_surface = pygame.Surface(
            panel_rect.size,
            pygame.SRCALPHA,
        )
        glow_alpha = int(55 + pulse * 70)
        pygame.draw.rect(
            glow_surface,
            (*accent_color, glow_alpha),
            glow_surface.get_rect(),
            3,
            border_radius=12,
        )
        screen.blit(
            glow_surface,
            panel_rect.topleft,
        )


# Desenează energia abilității speciale și indică tasta doar când este gata.
def _draw_energy_pulse_bar(
    screen,
    x,
    y,
    player,
    pulse,
):
    maximum_energy = max(
        1,
        getattr(player, "maximum_special_energy", 100),
    )
    current_energy = max(
        0,
        min(
            maximum_energy,
            getattr(player, "special_energy", 0),
        ),
    )
    energy_ratio = current_energy / maximum_energy
    ability_ready = current_energy >= maximum_energy
    accent_color = (
        (225, 105, 255)
        if ability_ready
        else (55, 195, 245)
    )

    panel_rect = pygame.Rect(x, y, 208, 48)
    _draw_glass_panel(
        screen,
        panel_rect,
        accent_color,
        fill_color=(7, 13, 30, 220),
    )

    label_font = _get_font(16)
    title_surface = label_font.render(
        "ENERGY PULSE",
        True,
        (145, 180, 210),
    )
    value_surface = label_font.render(
        (
            "READY  [E]"
            if ability_ready
            else f"{current_energy:03d}%"
        ),
        True,
        accent_color,
    )
    screen.blit(
        title_surface,
        (panel_rect.x + 14, panel_rect.y + 8),
    )
    screen.blit(
        value_surface,
        (
            panel_rect.right - value_surface.get_width() - 14,
            panel_rect.y + 8,
        ),
    )

    bar_background = pygame.Rect(
        panel_rect.x + 14,
        panel_rect.y + 31,
        panel_rect.width - 28,
        7,
    )
    pygame.draw.rect(
        screen,
        (35, 44, 62),
        bar_background,
        border_radius=3,
    )
    if energy_ratio > 0:
        energy_fill = pygame.Rect(
            bar_background.x,
            bar_background.y,
            max(3, int(bar_background.width * energy_ratio)),
            bar_background.height,
        )
        pygame.draw.rect(
            screen,
            accent_color,
            energy_fill,
            border_radius=3,
        )

    if ability_ready:
        ready_glow = pygame.Surface(
            panel_rect.size,
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            ready_glow,
            (*accent_color, int(55 + pulse * 85)),
            ready_glow.get_rect(),
            3,
            border_radius=12,
        )
        screen.blit(ready_glow, panel_rect.topleft)


def _draw_graze_chain(
    screen,
    x,
    y,
    graze_chain,
    total_grazes,
    flash_timer,
    pulse,
):
    graze_tier = min(5, 1 + max(0, graze_chain) // 10)
    active = graze_chain > 0
    accent_color = (75, 235, 255) if active else (85, 120, 145)
    panel_rect = pygame.Rect(x, y, 208, 40)
    _draw_glass_panel(
        screen,
        panel_rect,
        accent_color,
        fill_color=(5, 15, 29, 215),
    )

    label = _get_font(15).render(
        f"GRAZE CHAIN  //  {total_grazes} EVADED",
        True,
        (130, 185, 210),
    )
    value = _get_font(23).render(
        f"G{graze_chain:03d}   RISK x{graze_tier}",
        True,
        accent_color,
    )
    screen.blit(label, (panel_rect.x + 12, panel_rect.y + 5))
    screen.blit(
        value,
        (
            panel_rect.right - value.get_width() - 12,
            panel_rect.y + 18,
        ),
    )

    if flash_timer > 0:
        flash = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        flash_alpha = min(170, 45 + flash_timer * 5 + int(pulse * 20))
        pygame.draw.rect(
            flash,
            (*accent_color, flash_alpha),
            flash.get_rect(),
            2,
            border_radius=12,
        )
        screen.blit(flash, panel_rect.topleft)


# Deseneaza HUD-ul principal fara sa acopere centrul arenei.
def draw_game_ui(
    screen,
    font,
    score,
    lives,
    wave,
    multiplier,
    player=None,
    stage=1,
    combo=0,
    graze_chain=0,
    total_grazes=0,
    graze_flash_timer=0,
):
    screen_width = screen.get_width()
    pulse = (
        math.sin(pygame.time.get_ticks() * 0.004) + 1
    ) / 2
    critical_integrity = 0 < lives <= 2

    # Panoul din stanga contine scorul si integritatea navei.
    left_panel = pygame.Rect(18, 18, 244, 124)
    left_accent = (
        (255, 65, 90)
        if critical_integrity
        else (65, 195, 255)
    )
    _draw_glass_panel(
        screen,
        left_panel,
        left_accent,
    )

    # La maximum doua vieti, panoul pulseaza pentru a avertiza jucatorul.
    if critical_integrity:
        warning_glow = pygame.Surface(
            left_panel.size,
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            warning_glow,
            (255, 35, 65, int(35 + pulse * 75)),
            warning_glow.get_rect(),
            3,
            border_radius=12,
        )
        screen.blit(warning_glow, left_panel.topleft)

    label_font = _get_font(18)
    value_font = _get_font(34)
    small_value_font = _get_font(27)

    score_label = label_font.render(
        "MISSION SCORE",
        True,
        (120, 175, 210),
    )
    score_value = value_font.render(
        f"{score:07d}",
        True,
        (235, 248, 255),
    )
    screen.blit(score_label, (36, 34))
    screen.blit(score_value, (34, 52))

    pygame.draw.line(
        screen,
        (50, 90, 125),
        (34, 91),
        (244, 91),
        1,
    )

    lives_label = label_font.render(
        "HULL INTEGRITY",
        True,
        (205, 105, 120),
    )
    lives_value = small_value_font.render(
        f"{lives:02d}",
        True,
        (255, 100, 115),
    )
    screen.blit(lives_label, (36, 103))
    screen.blit(lives_value, (205, 99))

    # Cele cinci segmente vor fi utile cand revenim la cinci vieti.
    maximum_segments = 5
    active_segments = min(maximum_segments, max(0, lives))
    for segment_index in range(maximum_segments):
        segment_rect = pygame.Rect(
            36 + segment_index * 31,
            127,
            24,
            4,
        )
        segment_color = (
            (255, 75, 95)
            if segment_index < active_segments
            else (55, 35, 50)
        )
        pygame.draw.rect(
            screen,
            segment_color,
            segment_rect,
            border_radius=2,
        )

    if player is not None:
        _draw_weapon_bar(
            screen,
            left_panel.x,
            left_panel.bottom + 9,
            player,
            pulse,
        )

    # Mesajul este plasat sub HUD, astfel incat sa nu acopere arena centrala.
    if critical_integrity:
        warning_y = (
            left_panel.bottom + 66
            if player is not None
            else 151
        )
        warning_rect = pygame.Rect(
            18,
            warning_y,
            244,
            34,
        )
        warning_surface = pygame.Surface(
            warning_rect.size,
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            warning_surface,
            (80, 5, 20, int(190 + pulse * 45)),
            warning_surface.get_rect(),
            border_radius=8,
        )
        pygame.draw.rect(
            warning_surface,
            (255, 65, 90, 235),
            warning_surface.get_rect(),
            2,
            border_radius=8,
        )
        warning_text = _get_font(18).render(
            "CRITICAL INTEGRITY",
            True,
            (255, 225, 230),
        )
        warning_surface.blit(
            warning_text,
            (
                warning_rect.width // 2
                - warning_text.get_width() // 2,
                warning_rect.height // 2
                - warning_text.get_height() // 2,
            ),
        )
        screen.blit(warning_surface, warning_rect.topleft)

    # Panoul din dreapta afiseaza wave-ul si multiplicatorul.
    right_panel = pygame.Rect(
        screen_width - 226,
        18,
        208,
        124,
    )
    if combo >= 100:
        combo_tier = "GODLIKE"
        combo_color = (70, 240, 225)
    elif combo >= 50:
        combo_tier = "LEGENDARY"
        combo_color = (255, 195, 65)
    elif combo >= 25:
        combo_tier = "UNTOUCHABLE"
        combo_color = (205, 95, 255)
    else:
        combo_tier = "COMBAT LINK"
        combo_color = (
            (255, 195, 65)
            if combo >= 10
            else (75, 190, 235)
        )
    _draw_glass_panel(
        screen,
        right_panel,
        combo_color,
    )

    wave_label = label_font.render(
        f"STAGE {stage:02d}  //  WAVE",
        True,
        (125, 180, 215),
    )
    wave_value = value_font.render(
        f"{wave:02d}",
        True,
        (215, 242, 255),
    )
    screen.blit(
        wave_label,
        (right_panel.x + 18, right_panel.y + 16),
    )
    screen.blit(
        wave_value,
        (right_panel.right - wave_value.get_width() - 18, right_panel.y + 31),
    )

    combo_label = label_font.render(
        combo_tier,
        True,
        combo_color if combo >= 10 else (145, 150, 175),
    )
    combo_value = small_value_font.render(
        f"C{combo:03d}  x{multiplier}",
        True,
        combo_color,
    )
    screen.blit(
        combo_label,
        (right_panel.x + 18, right_panel.y + 82),
    )
    screen.blit(
        combo_value,
        (
            right_panel.right - combo_value.get_width() - 18,
            right_panel.y + 78,
        ),
    )

    if combo >= 10:
        tier_intensity = 1.45 if combo >= 100 else 1.0
        glow_alpha = int((45 + pulse * 65) * tier_intensity)
        glow_alpha = min(175, glow_alpha)
        glow_surface = pygame.Surface(
            (right_panel.width, right_panel.height),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            glow_surface,
            (*combo_color, glow_alpha),
            glow_surface.get_rect(),
            2,
            border_radius=12,
        )
        screen.blit(glow_surface, right_panel.topleft)

    # Power-up-urile sunt afisate separat si discret sub panoul drept.
    if player is not None:
        _draw_status_chip(
            screen,
            right_panel.x,
            right_panel.bottom + 9,
            "SHIELD",
            bool(player.shield),
            (65, 160, 255),
        )
        _draw_status_chip(
            screen,
            right_panel.x + 108,
            right_panel.bottom + 9,
            f"WEAPON L{getattr(player, 'weapon_level', 1)}",
            getattr(player, "weapon_level", 1) > 1,
            (220, 85, 255),
        )
        _draw_energy_pulse_bar(
            screen,
            right_panel.x,
            right_panel.bottom + 43,
            player,
            pulse,
        )
        _draw_graze_chain(
            screen,
            right_panel.x,
            right_panel.bottom + 96,
            graze_chain,
            total_grazes,
            graze_flash_timer,
            pulse,
        )
