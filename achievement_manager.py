import math

import pygame


ACHIEVEMENTS = {
    "FIRST_BLOOD": {
        "title": "FIRST BLOOD",
        "description": "Destroy your first hostile ship.",
    },
    "STORY_COMPLETE": {
        "title": "BEYOND THE WORMHOLE",
        "description": "Reach enemy territory.",
    },
    "UNTOUCHABLE": {
        "title": "UNTOUCHABLE",
        "description": "Reach a combat combo of 25.",
    },
    "DAREDEVIL": {
        "title": "DAREDEVIL",
        "description": "Reach a Graze Chain of 25.",
    },
    "SOVEREIGN_SLAYER": {
        "title": "SOVEREIGN SLAYER",
        "description": "Destroy the Dead Star Sovereign.",
    },
    "DEEP_SPACE": {
        "title": "DEEP SPACE",
        "description": "Reach Stage 3 in one run.",
    },
    "ACE_PILOT": {
        "title": "ACE PILOT",
        "description": "Earn 100,000 points in one run.",
    },
    "IMMORTAL_RUN": {
        "title": "IMMORTAL RUN",
        "description": "Defeat a Sovereign without taking hull damage.",
    },
}


class AchievementManager:

    def __init__(self, save_manager, platform_services):
        self.save_manager = save_manager
        self.platform_services = platform_services
        self.unlocked = set(save_manager.get_unlocked_achievements())
        self.notification_queue = []
        self.active_notification = None
        self.notification_timer = 0
        self.notification_duration = 240
        self.title_font = pygame.font.Font(None, 29)
        self.description_font = pygame.font.Font(None, 19)

    def unlock(self, achievement_id):
        if achievement_id not in ACHIEVEMENTS or achievement_id in self.unlocked:
            return False

        self.unlocked.add(achievement_id)
        self.save_manager.unlock_achievement(achievement_id)
        self.platform_services.unlock_achievement(achievement_id)
        self.notification_queue.append(achievement_id)
        if self.active_notification is None:
            self._show_next_notification()
        return True

    def _show_next_notification(self):
        if not self.notification_queue:
            self.active_notification = None
            self.notification_timer = 0
            return
        self.active_notification = self.notification_queue.pop(0)
        self.notification_timer = self.notification_duration

    def update(self):
        if self.active_notification is None:
            self._show_next_notification()
            return

        self.notification_timer -= 1
        if self.notification_timer <= 0:
            self.active_notification = None
            self._show_next_notification()

    def evaluate_gameplay(self, gameplay):
        if gameplay.enemies_killed >= 1:
            self.unlock("FIRST_BLOOD")
        if gameplay.best_combo >= 25 or gameplay.combo >= 25:
            self.unlock("UNTOUCHABLE")
        if gameplay.best_graze_chain >= 25:
            self.unlock("DAREDEVIL")
        if gameplay.boss_count >= 1:
            self.unlock("SOVEREIGN_SLAYER")
        if gameplay.stage >= 3:
            self.unlock("DEEP_SPACE")
        if gameplay.score >= 100000:
            self.unlock("ACE_PILOT")
        if getattr(gameplay, "flawless_bosses", 0) >= 1:
            self.unlock("IMMORTAL_RUN")

    def draw(self, screen):
        if self.active_notification is None:
            return

        achievement = ACHIEVEMENTS[self.active_notification]
        elapsed = self.notification_duration - self.notification_timer
        visibility = min(1.0, elapsed / 18) * min(
            1.0,
            self.notification_timer / 35,
        )
        slide = 1.0 - min(1.0, elapsed / 22)
        panel_width = 460
        panel_height = 78
        panel_x = screen.get_width() // 2 - panel_width // 2
        panel_y = int(18 - slide * 95)
        panel = pygame.Surface(
            (panel_width, panel_height),
            pygame.SRCALPHA,
        )
        pulse = (math.sin(elapsed * 0.13) + 1.0) / 2.0
        pygame.draw.rect(
            panel,
            (4, 13, 29, int(235 * visibility)),
            panel.get_rect(),
            border_radius=12,
        )
        pygame.draw.rect(
            panel,
            (75, 225, 255, int((190 + pulse * 55) * visibility)),
            panel.get_rect(),
            2,
            border_radius=12,
        )
        pygame.draw.circle(
            panel,
            (255, 202, 78, int(235 * visibility)),
            (39, 39),
            19,
            3,
        )
        pygame.draw.circle(
            panel,
            (235, 250, 255, int(230 * visibility)),
            (39, 39),
            6,
        )

        category = self.description_font.render(
            "ACHIEVEMENT UNLOCKED",
            True,
            (95, 185, 220),
        )
        title = self.title_font.render(
            achievement["title"],
            True,
            (235, 250, 255),
        )
        description = self.description_font.render(
            achievement["description"],
            True,
            (150, 175, 200),
        )
        for surface in (category, title, description):
            surface.set_alpha(int(255 * visibility))
        panel.blit(category, (73, 9))
        panel.blit(title, (72, 27))
        panel.blit(description, (73, 54))
        screen.blit(panel, (panel_x, panel_y))

