import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FOLDER = PROJECT_ROOT / "release" / "steam_assets"
TRAILER_FOLDER = PROJECT_ROOT / "release" / "trailer_ai"
BACKGROUND_PATH = PROJECT_ROOT / "marketing" / "key_art_background_master.png"

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame


PLAYER_PATH = (
    PROJECT_ROOT / "assets" / "images" / "player_galaxy_defender_v2.png"
)
BOSS_PATH = (
    PROJECT_ROOT / "assets" / "images" / "bosses" /
    "final_boss_sovereign.png"
)
FIGHTER_PATH = (
    PROJECT_ROOT / "assets" / "images" / "enemies" /
    "enemy_alien_fighter_v2.png"
)
PHASE_PATH = (
    PROJECT_ROOT / "assets" / "images" / "enemies" /
    "enemy_alien_phase_hunter.png"
)
ICON_PATH = (
    PROJECT_ROOT / "assets" / "images" / "ui" / "game_icon_master.png"
)


def cover_crop(image, size, focus=(0.50, 0.43)):
    width, height = size
    source_width, source_height = image.get_size()
    scale = max(width / source_width, height / source_height)
    scaled_size = (
        max(1, round(source_width * scale)),
        max(1, round(source_height * scale)),
    )
    scaled = pygame.transform.smoothscale(image, scaled_size)
    overflow_x = max(0, scaled_size[0] - width)
    overflow_y = max(0, scaled_size[1] - height)
    crop_x = max(0, min(overflow_x, round(overflow_x * focus[0])))
    crop_y = max(0, min(overflow_y, round(overflow_y * focus[1])))
    return scaled.subsurface((crop_x, crop_y, width, height)).copy()


def scale_to_width(image, width):
    width = max(1, round(width))
    height = max(1, round(image.get_height() * width / image.get_width()))
    return pygame.transform.smoothscale(image, (width, height))


def centered_blit(surface, image, center):
    rect = image.get_rect(center=(round(center[0]), round(center[1])))
    surface.blit(image, rect)
    return rect


def add_sprite_with_glow(surface, image, center, width, glow_color):
    sprite = scale_to_width(image, width)
    for expansion, alpha in ((1.28, 28), (1.16, 44), (1.08, 62)):
        glow = pygame.transform.smoothscale(
            sprite,
            (
                max(1, round(sprite.get_width() * expansion)),
                max(1, round(sprite.get_height() * expansion)),
            ),
        )
        glow.fill((*glow_color, 255), special_flags=pygame.BLEND_RGBA_MULT)
        glow.set_alpha(alpha)
        centered_blit(surface, glow, center)
    return centered_blit(surface, sprite, center)


def add_vignette(surface, strength=150):
    width, height = surface.get_size()
    # Masca mica este marita cu interpolare pentru o umbrire perfect continua.
    # Vechile rame concentrice ramaneau vizibile sub forma de benzi verticale.
    mask_width = 320
    mask_height = max(80, round(mask_width * height / width))
    mask = pygame.Surface((mask_width, mask_height), pygame.SRCALPHA)
    for y in range(mask_height):
        normalized_y = abs(y * 2 / max(1, mask_height - 1) - 1)
        for x in range(mask_width):
            normalized_x = abs(x * 2 / max(1, mask_width - 1) - 1)
            edge_distance = max(normalized_x, normalized_y)
            alpha = round(strength * edge_distance ** 3.2)
            mask.set_at((x, y), (0, 0, 8, alpha))
    overlay = pygame.transform.smoothscale(mask, (width, height))
    surface.blit(overlay, (0, 0))


def add_energy_trail(surface, start, end, color, width):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for factor, alpha in ((4.5, 20), (2.7, 48), (1.4, 105), (0.55, 235)):
        pygame.draw.line(
            overlay,
            (*color, alpha),
            (round(start[0]), round(start[1])),
            (round(end[0]), round(end[1])),
            max(1, round(width * factor)),
        )
    surface.blit(overlay, (0, 0))


def render_gradient_text(text, font_size, top_color, bottom_color):
    font = pygame.font.Font(None, max(12, round(font_size)))
    mask = font.render(text, True, (255, 255, 255)).convert_alpha()
    gradient = pygame.Surface(mask.get_size(), pygame.SRCALPHA)
    height = max(1, mask.get_height())
    for y in range(height):
        progress = y / max(1, height - 1)
        color = tuple(
            round(top_color[channel] * (1.0 - progress) + bottom_color[channel] * progress)
            for channel in range(3)
        )
        pygame.draw.line(gradient, (*color, 255), (0, y), (mask.get_width(), y))
    gradient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return gradient


def render_logo(max_width, compact=False):
    if compact:
        font_size = max(24, round(max_width / 8.6))
        title = render_gradient_text(
            "GALAXY DEFENDER",
            font_size,
            (245, 252, 255),
            (74, 186, 255),
        )
        while title.get_width() > max_width and font_size > 18:
            font_size -= 1
            title = render_gradient_text(
                "GALAXY DEFENDER",
                font_size,
                (245, 252, 255),
                (74, 186, 255),
            )
        logo = pygame.Surface(
            (title.get_width() + 14, title.get_height() + 14),
            pygame.SRCALPHA,
        )
        position = (7, 7)
        for offset_x, offset_y in ((-3, 0), (3, 0), (0, -3), (0, 3)):
            shadow = title.copy()
            shadow.fill((2, 12, 28, 255), special_flags=pygame.BLEND_RGBA_MULT)
            logo.blit(shadow, (position[0] + offset_x, position[1] + offset_y))
        logo.blit(title, position)
        return logo

    galaxy = render_gradient_text(
        "GALAXY",
        max_width * 0.115,
        (176, 231, 255),
        (53, 153, 233),
    )
    defender = render_gradient_text(
        "DEFENDER",
        max_width * 0.195,
        (255, 255, 255),
        (79, 187, 255),
    )
    content_width = max(galaxy.get_width(), defender.get_width())
    content_height = galaxy.get_height() + defender.get_height() * 0.82
    logo = pygame.Surface(
        (round(content_width + max_width * 0.055), round(content_height + 18)),
        pygame.SRCALPHA,
    )
    galaxy_position = (
        round((logo.get_width() - galaxy.get_width()) / 2),
        2,
    )
    defender_position = (
        round((logo.get_width() - defender.get_width()) / 2),
        round(galaxy.get_height() * 0.74),
    )

    for image, position in ((galaxy, galaxy_position), (defender, defender_position)):
        for offset_x, offset_y in ((-4, 0), (4, 0), (0, -4), (0, 4)):
            outline = image.copy()
            outline.fill((1, 8, 24, 255), special_flags=pygame.BLEND_RGBA_MULT)
            logo.blit(outline, (position[0] + offset_x, position[1] + offset_y))
        logo.blit(image, position)

    accent_y = min(logo.get_height() - 3, defender_position[1] + defender.get_height())
    pygame.draw.line(
        logo,
        (65, 210, 255, 230),
        (round(logo.get_width() * 0.13), accent_y),
        (round(logo.get_width() * 0.87), accent_y),
        max(1, round(max_width * 0.006)),
    )
    return logo


def add_combat_scene(surface, player, boss, fighter, phase, layout):
    width, height = surface.get_size()
    if layout == "wide_hero":
        boss_center = (width * 0.72, height * 0.39)
        boss_width = width * 0.28
        player_center = (width * 0.47, height * 0.72)
        player_width = width * 0.075
    elif layout == "vertical":
        boss_center = (width * 0.50, height * 0.28)
        boss_width = width * 0.72
        player_center = (width * 0.50, height * 0.70)
        player_width = width * 0.25
    else:
        boss_center = (width * 0.68, height * 0.38)
        boss_width = width * 0.40
        player_center = (width * 0.48, height * 0.77)
        player_width = width * 0.14

    add_energy_trail(
        surface,
        (player_center[0], player_center[1] + height * 0.20),
        (player_center[0], player_center[1] + height * 0.03),
        (35, 173, 255),
        max(2, width * 0.0025),
    )
    add_sprite_with_glow(
        surface,
        boss,
        boss_center,
        boss_width,
        (255, 38, 82),
    )

    if layout != "wide_hero":
        enemy_width = width * (0.105 if layout == "horizontal" else 0.18)
        enemy_y = height * (0.44 if layout == "horizontal" else 0.46)
        add_sprite_with_glow(
            surface,
            fighter,
            (width * 0.18, enemy_y),
            enemy_width,
            (255, 45, 72),
        )
        add_sprite_with_glow(
            surface,
            phase,
            (width * 0.86, enemy_y * 1.04),
            enemy_width,
            (140, 72, 255),
        )

    add_sprite_with_glow(
        surface,
        player,
        player_center,
        player_width,
        (47, 188, 255),
    )


def build_capsule(background, sprites, size, layout, logo=True):
    focus = (0.50, 0.37 if layout == "vertical" else 0.43)
    surface = cover_crop(background, size, focus)
    add_combat_scene(surface, *sprites, layout)
    add_vignette(surface, 135)

    width, height = size
    if logo:
        if layout == "vertical":
            title = render_logo(width * 0.89)
            center = (width * 0.50, height * 0.88)
        else:
            title = render_logo(width * 0.44)
            center = (width * 0.25, height * 0.26)
        centered_blit(surface, title, center)
    return surface


def build_small_capsule(background, player, size):
    width, height = size
    surface = cover_crop(background, size, (0.53, 0.42))
    shade = pygame.Surface(size, pygame.SRCALPHA)
    shade.fill((0, 3, 16, 115))
    surface.blit(shade, (0, 0))
    add_sprite_with_glow(
        surface,
        player,
        (width * 0.86, height * 0.55),
        width * 0.17,
        (48, 194, 255),
    )
    title = render_logo(width * 0.76, compact=True)
    centered_blit(surface, title, (width * 0.41, height * 0.52))
    add_vignette(surface, 100)
    return surface


def build_page_background(background, size):
    surface = cover_crop(background, size, (0.50, 0.43))
    darkness = pygame.Surface(size, pygame.SRCALPHA)
    darkness.fill((2, 4, 16, 118))
    surface.blit(darkness, (0, 0))
    add_vignette(surface, 185)
    return surface


def save_png(surface, filename):
    pygame.image.save(surface, OUTPUT_FOLDER / filename)


def build_icons(icon):
    shortcut = pygame.transform.smoothscale(icon, (256, 256))
    save_png(shortcut, "shortcut_icon_256.png")
    app_icon = pygame.transform.smoothscale(icon, (184, 184)).convert()
    pygame.image.save(app_icon, OUTPUT_FOLDER / "app_icon_184.jpg")


def upscale_store_screenshots():
    source_folder = PROJECT_ROOT / "release" / "screenshots"
    target_folder = OUTPUT_FOLDER / "screenshots"
    target_folder.mkdir(parents=True, exist_ok=True)
    screenshot_names = (
        "03_stage_two_gameplay.png",
        "03_first_run_tutorial.png",
        "04_energy_ready_feedback.png",
        "05_critical_hull_feedback.png",
        "06_stage_two_sovereign.png",
    )
    for index, filename in enumerate(screenshot_names, start=1):
        image = pygame.image.load(source_folder / filename).convert()
        scaled = pygame.transform.smoothscale(image, (1920, 1080))
        pygame.image.save(
            scaled,
            target_folder / f"{index:02d}_{Path(filename).stem}.png",
        )


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    TRAILER_FOLDER.mkdir(parents=True, exist_ok=True)

    background = pygame.image.load(BACKGROUND_PATH).convert()
    pygame.image.save(
        background,
        OUTPUT_FOLDER / "key_art_background_master.png",
    )
    player = pygame.image.load(PLAYER_PATH).convert_alpha()
    boss = pygame.image.load(BOSS_PATH).convert_alpha()
    fighter = pygame.image.load(FIGHTER_PATH).convert_alpha()
    phase = pygame.image.load(PHASE_PATH).convert_alpha()
    icon = pygame.image.load(ICON_PATH).convert_alpha()
    sprites = (player, boss, fighter, phase)

    assets = {
        "store_header_920x430.png": build_capsule(
            background, sprites, (920, 430), "horizontal"
        ),
        "store_main_1232x706.png": build_capsule(
            background, sprites, (1232, 706), "horizontal"
        ),
        "store_vertical_748x896.png": build_capsule(
            background, sprites, (748, 896), "vertical"
        ),
        "library_capsule_600x900.png": build_capsule(
            background, sprites, (600, 900), "vertical"
        ),
        "library_header_920x430.png": build_capsule(
            background, sprites, (920, 430), "horizontal"
        ),
        "library_hero_3840x1240.png": build_capsule(
            background, sprites, (3840, 1240), "wide_hero", logo=False
        ),
        "page_background_1438x810.png": build_page_background(
            background, (1438, 810)
        ),
        "store_small_462x174.png": build_small_capsule(
            background, player, (462, 174)
        ),
    }
    for filename, surface in assets.items():
        save_png(surface, filename)

    logo = render_logo(1180)
    logo_canvas = pygame.Surface((1280, 360), pygame.SRCALPHA)
    centered_blit(logo_canvas, logo, logo_canvas.get_rect().center)
    save_png(logo_canvas, "library_logo_1280x360.png")

    build_icons(icon)
    upscale_store_screenshots()
    pygame.image.save(
        build_capsule(
            background,
            sprites,
            (1920, 1080),
            "horizontal",
            logo=False,
        ),
        TRAILER_FOLDER / "shot_01_sovereign_reference_1920x1080.png",
    )
    pygame.quit()


if __name__ == "__main__":
    main()
