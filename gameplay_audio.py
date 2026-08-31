"""Layered, rate-limited sound design for the endless combat loop."""

from dataclasses import dataclass

import pygame


SOUND_ROOT = "assets/sounds/cinematic"


def _path(pack, file_name):
    return f"{SOUND_ROOT}/{pack}/{file_name}"


SOUND_PATHS = {
    # Player and enemy weapons.
    "laser_large_0": _path("kenney_sci_fi", "laserLarge_000.ogg"),
    "laser_large_1": _path("kenney_sci_fi", "laserLarge_001.ogg"),
    "laser_large_2": _path("kenney_sci_fi", "laserLarge_002.ogg"),
    "laser_large_3": _path("kenney_sci_fi", "laserLarge_003.ogg"),
    "laser_large_4": _path("kenney_sci_fi", "laserLarge_004.ogg"),
    "laser_small_0": _path("kenney_sci_fi", "laserSmall_000.ogg"),
    "laser_small_1": _path("kenney_sci_fi", "laserSmall_001.ogg"),
    "laser_small_2": _path("kenney_sci_fi", "laserSmall_002.ogg"),
    "laser_small_3": _path("kenney_sci_fi", "laserSmall_003.ogg"),
    "laser_small_4": _path("kenney_sci_fi", "laserSmall_004.ogg"),
    # Destruction and physical impacts.
    "explosion_0": _path("kenney_sci_fi", "explosionCrunch_000.ogg"),
    "explosion_1": _path("kenney_sci_fi", "explosionCrunch_001.ogg"),
    "explosion_2": _path("kenney_sci_fi", "explosionCrunch_002.ogg"),
    "explosion_3": _path("kenney_sci_fi", "explosionCrunch_003.ogg"),
    "explosion_4": _path("kenney_sci_fi", "explosionCrunch_004.ogg"),
    "sub_boom_0": _path(
        "kenney_sci_fi",
        "lowFrequency_explosion_000.ogg",
    ),
    "sub_boom_1": _path(
        "kenney_sci_fi",
        "lowFrequency_explosion_001.ogg",
    ),
    "metal_0": _path("kenney_sci_fi", "impactMetal_000.ogg"),
    "metal_1": _path("kenney_sci_fi", "impactMetal_001.ogg"),
    "metal_2": _path("kenney_sci_fi", "impactMetal_002.ogg"),
    "metal_3": _path("kenney_sci_fi", "impactMetal_003.ogg"),
    "metal_4": _path("kenney_sci_fi", "impactMetal_004.ogg"),
    "rock_impact": _path("kenney_impact", "impactMining_003.ogg"),
    "hull_light": _path("kenney_impact", "impactMetal_light_001.ogg"),
    "hull_medium": _path("kenney_impact", "impactMetal_medium_002.ogg"),
    "hull_heavy": _path("kenney_impact", "impactPunch_heavy_001.ogg"),
    # Shields, phase technology, rewards and warnings.
    "field_0": _path("kenney_sci_fi", "forceField_000.ogg"),
    "field_1": _path("kenney_sci_fi", "forceField_001.ogg"),
    "field_2": _path("kenney_sci_fi", "forceField_002.ogg"),
    "field_3": _path("kenney_sci_fi", "forceField_003.ogg"),
    "field_4": _path("kenney_sci_fi", "forceField_004.ogg"),
    "phase_jump": _path("kenney_digital", "phaseJump3.ogg"),
    "zap_0": _path("kenney_digital", "zap1.ogg"),
    "zap_1": _path("kenney_digital", "zap2.ogg"),
    "power_0": _path("kenney_digital", "powerUp1.ogg"),
    "power_1": _path("kenney_digital", "powerUp4.ogg"),
    "power_2": _path("kenney_digital", "powerUp10.ogg"),
    "tone_high": _path("kenney_digital", "highUp.ogg"),
    "tone_low": _path("kenney_digital", "lowDown.ogg"),
    "tone_three": _path("kenney_digital", "threeTone1.ogg"),
    "tone_two": _path("kenney_digital", "twoTone1.ogg"),
    "warning_low": _path("kenney_digital", "lowThreeTone.ogg"),
    "warning": _path("kenney_interface", "error_003.ogg"),
    "warning_short": _path("kenney_interface", "error_004.ogg"),
    "confirm_0": _path("kenney_interface", "confirmation_001.ogg"),
    "confirm_1": _path("kenney_interface", "confirmation_002.ogg"),
    "confirm_2": _path("kenney_interface", "confirmation_003.ogg"),
    "confirm_3": _path("kenney_interface", "confirmation_004.ogg"),
    "glass": _path("kenney_interface", "glass_004.ogg"),
    "switch": _path("kenney_interface", "switch_004.ogg"),
}


@dataclass(frozen=True)
class AudioEvent:
    variants: tuple
    gain: float
    group: str
    cooldown: int = 0
    layers: tuple = ()


EVENTS = {
    "player_fire_1": AudioEvent(("laser_small_0", "laser_small_1"), 0.075, "player_fire", 2),
    "player_fire_2": AudioEvent(("laser_small_2", "laser_small_3"), 0.085, "player_fire", 2),
    "player_fire_3": AudioEvent(("laser_large_0", "laser_large_1"), 0.095, "player_fire", 2),
    "player_fire_4": AudioEvent(("laser_large_3", "laser_large_4"), 0.115, "player_fire", 2),
    "enemy_fire_scout": AudioEvent(("laser_small_4",), 0.075, "enemy_fire", 5),
    "enemy_fire_fighter": AudioEvent(("laser_small_2",), 0.085, "enemy_fire", 6),
    "enemy_fire_tank": AudioEvent(("laser_large_2",), 0.13, "enemy_fire", 9),
    "enemy_fire_shield": AudioEvent(("field_0",), 0.11, "enemy_fire", 10),
    "enemy_fire_phase": AudioEvent(("phase_jump",), 0.14, "enemy_fire", 12, (("laser_large_4", 0.07),)),
    "enemy_fire_elite": AudioEvent(("laser_large_3",), 0.16, "enemy_fire", 14, (("warning_short", 0.06),)),
    "elite_charge": AudioEvent(("warning_short",), 0.09, "enemy_fire", 24, (("field_3", 0.05),)),
    "boss_fire": AudioEvent(("laser_large_2", "laser_large_4"), 0.13, "enemy_fire", 10),
    "enemy_hit": AudioEvent(("metal_0", "metal_1", "metal_2"), 0.055, "impact", 3),
    "shield_hit": AudioEvent(("field_1", "field_2"), 0.12, "impact", 5),
    "player_shield_absorb": AudioEvent(("field_3",), 0.22, "priority", 7, (("glass", 0.08),)),
    "player_damage": AudioEvent(("hull_heavy",), 0.27, "priority", 8, (("sub_boom_1", 0.12),)),
    "breach": AudioEvent(("warning",), 0.16, "priority", 20),
    "player_destroyed": AudioEvent(("explosion_4",), 0.40, "priority", 25, (("sub_boom_0", 0.30), ("hull_heavy", 0.18))),
    "destroy_scout": AudioEvent(("explosion_0", "explosion_1"), 0.10, "impact", 3),
    "destroy_fighter": AudioEvent(("explosion_1", "explosion_2"), 0.14, "impact", 3),
    "destroy_tank": AudioEvent(("explosion_2", "explosion_3"), 0.21, "impact", 5, (("sub_boom_1", 0.08),)),
    "destroy_shield_carrier": AudioEvent(("explosion_3",), 0.25, "impact", 7, (("field_4", 0.13),)),
    "destroy_phase_hunter": AudioEvent(("explosion_2",), 0.22, "impact", 6, (("phase_jump", 0.12),)),
    "destroy_elite": AudioEvent(("explosion_4",), 0.34, "priority", 12, (("sub_boom_0", 0.22),)),
    "destroy_drone": AudioEvent(("explosion_0", "explosion_1"), 0.12, "impact", 3),
    "destroy_asteroid": AudioEvent(("rock_impact",), 0.16, "impact", 4, (("explosion_1", 0.08),)),
    "destroy_crossfire": AudioEvent(("explosion_2",), 0.19, "impact", 5, (("metal_4", 0.08),)),
    "destroy_ally": AudioEvent(("explosion_3",), 0.24, "priority", 8, (("sub_boom_1", 0.09),)),
    "missile_explosion": AudioEvent(("explosion_3", "explosion_4"), 0.24, "priority", 8, (("sub_boom_1", 0.13),)),
    "energy_pulse": AudioEvent(("power_2",), 0.20, "priority", 15, (("field_4", 0.15), ("sub_boom_1", 0.10))),
    "energy_ready": AudioEvent(("tone_high",), 0.10, "ui", 30, (("confirm_3", 0.06),)),
    "graze": AudioEvent(("zap_0", "zap_1"), 0.045, "ui", 5),
    "combo_milestone": AudioEvent(("tone_three",), 0.11, "ui", 15),
    "combo_break": AudioEvent(("tone_low",), 0.09, "ui", 12),
    "powerup_weapon": AudioEvent(("power_0",), 0.14, "ui", 8),
    "powerup_shield": AudioEvent(("power_1",), 0.14, "ui", 8, (("field_0", 0.06),)),
    "powerup_life": AudioEvent(("tone_high",), 0.14, "ui", 8),
    "powerup_score": AudioEvent(("confirm_0", "confirm_1"), 0.10, "ui", 6),
    "boss_phase": AudioEvent(("warning_low",), 0.24, "priority", 25, (("sub_boom_0", 0.18), ("switch", 0.08))),
    "boss_generator": AudioEvent(("explosion_3",), 0.26, "priority", 12, (("metal_3", 0.10),)),
    "boss_explosion": AudioEvent(("explosion_4",), 0.30, "priority", 12, (("sub_boom_1", 0.17),)),
    "boss_destroyed": AudioEvent(("explosion_4",), 0.42, "priority", 30, (("sub_boom_0", 0.31), ("tone_low", 0.10))),
    "event_solar_storm": AudioEvent(("field_4",), 0.20, "event", 30, (("sub_boom_1", 0.10),)),
    "event_gravity_wave": AudioEvent(("phase_jump",), 0.18, "event", 30, (("sub_boom_0", 0.15),)),
    "event_reinforcements": AudioEvent(("confirm_2",), 0.15, "event", 30, (("power_0", 0.09),)),
    "event_drone_swarm": AudioEvent(("switch",), 0.14, "event", 30, (("laser_small_3", 0.07),)),
    "event_radiation_cloud": AudioEvent(("warning",), 0.17, "event", 30, (("field_2", 0.11),)),
    "event_black_hole": AudioEvent(("sub_boom_0",), 0.24, "event", 30, (("phase_jump", 0.12),)),
    "event_asteroid_storm": AudioEvent(("warning_low",), 0.15, "event", 30, (("rock_impact", 0.10),)),
    "event_crossfire": AudioEvent(("switch",), 0.15, "event", 30, (("laser_large_0", 0.10),)),
    "event_missile_barrage": AudioEvent(("warning",), 0.18, "event", 30, (("tone_two", 0.10),)),
    "event_phase_storm": AudioEvent(("phase_jump",), 0.22, "event", 30, (("field_3", 0.14), ("sub_boom_1", 0.12))),
}


class GameplayAudioDirector:
    """Plays semantic combat events without allowing an audio wall."""

    CHANNEL_GROUPS = {
        "player_fire": tuple(range(7, 9)),
        "enemy_fire": tuple(range(9, 11)),
        "impact": tuple(range(11, 15)),
        "priority": tuple(range(15, 19)),
        "ui": tuple(range(19, 21)),
        "event": tuple(range(21, 24)),
    }

    GROUP_COOLDOWNS = {
        "player_fire": 0,
        "enemy_fire": 2,
        "impact": 1,
        "priority": 0,
        "ui": 1,
        "event": 0,
    }

    def __init__(self, master_volume=1.0):
        self.master_volume = max(0.0, min(1.0, float(master_volume)))
        self.sounds = {
            name: pygame.mixer.Sound(path)
            for name, path in SOUND_PATHS.items()
        }
        self.channels = {
            group: [
                pygame.mixer.Channel(index)
                for index in indexes
            ]
            for group, indexes in self.CHANNEL_GROUPS.items()
        }
        self.channel_gains = {}
        self.channel_indexes = {
            group: 0 for group in self.channels
        }
        self.variant_indexes = {}
        self.event_cooldowns = {}
        self.group_cooldowns = {}

    def update(self):
        self.event_cooldowns = {
            name: remaining - 1
            for name, remaining in self.event_cooldowns.items()
            if remaining > 1
        }
        self.group_cooldowns = {
            name: remaining - 1
            for name, remaining in self.group_cooldowns.items()
            if remaining > 1
        }

    def reset(self):
        for channels in self.channels.values():
            for channel in channels:
                channel.fadeout(100)
        self.event_cooldowns.clear()
        self.group_cooldowns.clear()
        self.variant_indexes.clear()

    def set_master_volume(self, volume):
        self.master_volume = max(0.0, min(1.0, float(volume)))
        for channel, gain in self.channel_gains.items():
            channel.set_volume(self.master_volume * gain)

    def play(self, event_name, strength=1.0):
        event = EVENTS.get(event_name)
        if event is None:
            return False
        if self.event_cooldowns.get(event_name, 0) > 0:
            return False
        if self.group_cooldowns.get(event.group, 0) > 0:
            return False

        variant_index = self.variant_indexes.get(event_name, 0)
        sound_name = event.variants[variant_index % len(event.variants)]
        self.variant_indexes[event_name] = variant_index + 1
        self._play_sound(
            event.group,
            sound_name,
            event.gain * max(0.0, min(1.35, float(strength))),
        )

        for layer_name, layer_gain in event.layers:
            self._play_sound(
                event.group,
                layer_name,
                layer_gain * max(0.0, min(1.35, float(strength))),
            )

        if event.cooldown > 0:
            self.event_cooldowns[event_name] = event.cooldown
        group_cooldown = self.GROUP_COOLDOWNS[event.group]
        if group_cooldown > 0:
            self.group_cooldowns[event.group] = group_cooldown
        return True

    def _play_sound(self, group, sound_name, gain):
        channels = self.channels[group]
        index = self.channel_indexes[group] % len(channels)
        self.channel_indexes[group] += 1
        channel = channels[index]
        gain = max(0.0, min(1.0, gain))
        self.channel_gains[channel] = gain
        channel.set_volume(self.master_volume * gain)
        channel.play(self.sounds[sound_name])
