"""Cue-based sound design for the opening campaign cinematic."""

from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class AudioCue:
    time: float
    sound: str
    gain: float
    role: str = "one_shot"


SOUND_ROOT = "assets/sounds/cinematic"

SOUND_PATHS = {
    "computer_noise": f"{SOUND_ROOT}/kenney_sci_fi/computerNoise_001.ogg",
    "door_close": f"{SOUND_ROOT}/kenney_sci_fi/doorClose_001.ogg",
    "door_open": f"{SOUND_ROOT}/kenney_sci_fi/doorOpen_001.ogg",
    "gravity_engine_a": f"{SOUND_ROOT}/kenney_sci_fi/engineCircular_001.ogg",
    "gravity_engine_b": f"{SOUND_ROOT}/kenney_sci_fi/engineCircular_002.ogg",
    "explosion_light": f"{SOUND_ROOT}/kenney_sci_fi/explosionCrunch_002.ogg",
    "explosion_heavy": f"{SOUND_ROOT}/kenney_sci_fi/explosionCrunch_004.ogg",
    "force_field_a": f"{SOUND_ROOT}/kenney_sci_fi/forceField_002.ogg",
    "force_field_b": f"{SOUND_ROOT}/kenney_sci_fi/forceField_004.ogg",
    "metal_hit": f"{SOUND_ROOT}/kenney_sci_fi/impactMetal_000.ogg",
    "laser": f"{SOUND_ROOT}/kenney_sci_fi/laserLarge_001.ogg",
    "sub_boom": f"{SOUND_ROOT}/kenney_sci_fi/lowFrequency_explosion_000.ogg",
    "engine_large": f"{SOUND_ROOT}/kenney_sci_fi/spaceEngineLarge_002.ogg",
    "engine_low": f"{SOUND_ROOT}/kenney_sci_fi/spaceEngineLow_001.ogg",
    "engine_small": f"{SOUND_ROOT}/kenney_sci_fi/spaceEngineSmall_003.ogg",
    "thruster": f"{SOUND_ROOT}/kenney_sci_fi/thrusterFire_002.ogg",
    "warning_low": f"{SOUND_ROOT}/kenney_digital/lowThreeTone.ogg",
    "phase_jump": f"{SOUND_ROOT}/kenney_digital/phaseJump3.ogg",
    "signal_fall": f"{SOUND_ROOT}/kenney_digital/zapThreeToneDown.ogg",
    "confirmation": f"{SOUND_ROOT}/kenney_interface/confirmation_003.ogg",
    "warning": f"{SOUND_ROOT}/kenney_interface/error_003.ogg",
    "lock_ping": f"{SOUND_ROOT}/kenney_interface/error_007.ogg",
    "switch": f"{SOUND_ROOT}/kenney_interface/switch_003.ogg",
    "bell_impact": f"{SOUND_ROOT}/kenney_impact/impactBell_heavy_001.ogg",
    "hull_impact": f"{SOUND_ROOT}/kenney_impact/impactMetal_heavy_001.ogg",
    "rock_impact": f"{SOUND_ROOT}/kenney_impact/impactMining_003.ogg",
    "clamp_impact": f"{SOUND_ROOT}/kenney_impact/impactPlate_heavy_004.ogg",
}


# Continuous textures stay deliberately quiet. The cinematic music remains the
# emotional layer, while these sounds provide a physical location and motion.
SCENE_TEXTURES = {
    "planet": None,
    "hangar": ("computer_noise", 0.10),
    "launch": ("engine_large", 0.14),
    "vortex": ("gravity_engine_a", 0.12),
    "asteroids": ("engine_small", 0.10),
    "anomaly": ("engine_low", 0.11),
    "wormhole": ("gravity_engine_b", 0.14),
    "dead_star": ("computer_noise", 0.065),
}


# Every cue is tied to a visible beat or to the start of a transmission. This
# replaces the old baked tracks that drifted away from the extended timelines.
SCENE_CUES = {
    "planet": (
        AudioCue(0.70, "switch", 0.10),
        AudioCue(2.22, "explosion_heavy", 0.34),
        AudioCue(2.22, "sub_boom", 0.25),
        AudioCue(2.45, "warning", 0.15),
        AudioCue(6.00, "confirmation", 0.08),
        AudioCue(8.00, "engine_large", 0.17, "propulsion"),
        AudioCue(9.90, "switch", 0.07),
    ),
    "hangar": (
        AudioCue(0.80, "switch", 0.08),
        AudioCue(3.80, "confirmation", 0.07),
        AudioCue(5.00, "door_close", 0.15),
        AudioCue(5.00, "clamp_impact", 0.19),
        AudioCue(5.15, "engine_small", 0.12, "propulsion"),
        AudioCue(7.40, "warning_low", 0.07),
        AudioCue(10.85, "door_open", 0.13),
    ),
    "launch": (
        AudioCue(0.18, "door_open", 0.12),
        AudioCue(0.25, "clamp_impact", 0.17),
        AudioCue(0.35, "thruster", 0.16, "propulsion"),
        AudioCue(3.70, "switch", 0.06),
        AudioCue(7.50, "warning", 0.14),
        AudioCue(7.62, "force_field_a", 0.18),
        AudioCue(10.42, "phase_jump", 0.17),
    ),
    "vortex": (
        AudioCue(0.60, "force_field_b", 0.15),
        AudioCue(3.50, "warning_low", 0.09),
        AudioCue(6.70, "warning", 0.14),
        AudioCue(6.78, "engine_large", 0.15, "propulsion"),
        AudioCue(9.70, "signal_fall", 0.14),
        AudioCue(11.02, "sub_boom", 0.20),
        AudioCue(11.06, "force_field_a", 0.18),
    ),
    "asteroids": (
        AudioCue(0.35, "warning_low", 0.10),
        AudioCue(3.35, "signal_fall", 0.10),
    ),
    "anomaly": (
        AudioCue(0.40, "hull_impact", 0.08),
        AudioCue(3.00, "force_field_b", 0.19),
        AudioCue(5.80, "warning_low", 0.08),
        AudioCue(7.80, "signal_fall", 0.15),
        AudioCue(7.82, "warning", 0.10),
        AudioCue(8.66, "sub_boom", 0.19),
        AudioCue(8.72, "phase_jump", 0.16),
    ),
    "wormhole": (
        AudioCue(0.40, "force_field_a", 0.13),
        AudioCue(3.20, "force_field_b", 0.16),
        AudioCue(6.00, "switch", 0.07),
        AudioCue(8.80, "phase_jump", 0.21),
        AudioCue(8.82, "sub_boom", 0.18),
        AudioCue(10.92, "explosion_light", 0.27),
        AudioCue(10.92, "sub_boom", 0.23),
    ),
    "dead_star": (
        AudioCue(0.50, "switch", 0.07),
        AudioCue(3.30, "sub_boom", 0.13),
        AudioCue(3.34, "confirmation", 0.07),
        AudioCue(5.80, "signal_fall", 0.07),
        AudioCue(8.00, "warning_low", 0.10),
        AudioCue(8.30, "lock_ping", 0.10),
        AudioCue(8.62, "lock_ping", 0.11),
        AudioCue(8.94, "lock_ping", 0.12),
        AudioCue(9.28, "lock_ping", 0.13),
        AudioCue(10.30, "confirmation", 0.12),
        AudioCue(10.34, "metal_hit", 0.08),
    ),
}


ASTEROID_EVENT_SOUNDS = {
    "shot": (("laser",), 0.17),
    "asteroid_hit": (("rock_impact", "metal_hit"), 0.12),
    "asteroid_destroyed": (
        ("explosion_light", "explosion_heavy"),
        0.23,
    ),
    "ship_hit": (("hull_impact", "bell_impact"), 0.25),
    "ship_destroyed": (("explosion_heavy",), 0.34),
}


class CinematicAudioDirector:
    """Synchronizes quiet beds and discrete effects with cinematic time."""

    def __init__(self, master_volume=1.0):
        self.master_volume = max(0.0, min(1.0, float(master_volume)))
        self.sounds = {
            name: pygame.mixer.Sound(path)
            for name, path in SOUND_PATHS.items()
        }

        self.texture_channel = pygame.mixer.Channel(0)
        self.propulsion_channel = pygame.mixer.Channel(1)
        self.one_shot_channels = [
            pygame.mixer.Channel(index)
            for index in range(2, 7)
        ]
        self._channel_gains = {
            self.texture_channel: 0.0,
            self.propulsion_channel: 0.0,
        }
        self._one_shot_index = 0
        self._event_variant_index = {}
        self.current_scene = None
        self.last_elapsed = 0.0
        self.next_cue_index = 0

    def set_master_volume(self, volume):
        self.master_volume = max(0.0, min(1.0, float(volume)))
        for channel, gain in self._channel_gains.items():
            channel.set_volume(self.master_volume * gain)

    def update(self, scene_name, elapsed_time):
        if scene_name not in SCENE_CUES:
            if self.current_scene is not None:
                self.stop()
            return

        elapsed_time = max(0.0, float(elapsed_time))
        restarted = elapsed_time + 0.08 < self.last_elapsed
        if scene_name != self.current_scene or restarted:
            self._enter_scene(scene_name, elapsed_time)

        cues = SCENE_CUES[scene_name]
        while self.next_cue_index < len(cues):
            cue = cues[self.next_cue_index]
            if cue.time > elapsed_time:
                break
            self._play_cue(cue)
            self.next_cue_index += 1

        self.last_elapsed = elapsed_time

    def play_asteroid_event(self, event_name):
        event = ASTEROID_EVENT_SOUNDS.get(event_name)
        if event is None or self.current_scene != "asteroids":
            return

        variants, gain = event
        variant_index = self._event_variant_index.get(event_name, 0)
        sound_name = variants[variant_index % len(variants)]
        self._event_variant_index[event_name] = variant_index + 1
        self._play_one_shot(sound_name, gain)

        if event_name == "ship_destroyed":
            self._play_one_shot("sub_boom", 0.24)

    def stop(self):
        self.texture_channel.fadeout(280)
        self.propulsion_channel.fadeout(220)
        for channel in self.one_shot_channels:
            channel.fadeout(120)
        self.current_scene = None
        self.last_elapsed = 0.0
        self.next_cue_index = 0

    def _enter_scene(self, scene_name, elapsed_time):
        self.texture_channel.fadeout(180)
        self.propulsion_channel.fadeout(160)
        for channel in self.one_shot_channels:
            channel.stop()

        self.current_scene = scene_name
        self.last_elapsed = elapsed_time
        self.next_cue_index = 0
        self._event_variant_index.clear()

        texture = SCENE_TEXTURES.get(scene_name)
        if texture is not None:
            sound_name, gain = texture
            self._play_loop(
                self.texture_channel,
                sound_name,
                gain,
                fade_ms=450,
            )

        # Loading a checkpoint never fires every missed sound at once.
        cues = SCENE_CUES[scene_name]
        while (
            self.next_cue_index < len(cues)
            and cues[self.next_cue_index].time < elapsed_time - 0.12
        ):
            self.next_cue_index += 1

    def _play_cue(self, cue):
        if cue.role == "propulsion":
            self._play_loop(
                self.propulsion_channel,
                cue.sound,
                cue.gain,
                fade_ms=240,
            )
            return
        self._play_one_shot(cue.sound, cue.gain)

    def _play_loop(self, channel, sound_name, gain, fade_ms):
        gain = max(0.0, min(1.0, float(gain)))
        self._channel_gains[channel] = gain
        channel.set_volume(self.master_volume * gain)
        channel.play(
            self.sounds[sound_name],
            loops=-1,
            fade_ms=fade_ms,
        )

    def _play_one_shot(self, sound_name, gain):
        channel = self.one_shot_channels[
            self._one_shot_index % len(self.one_shot_channels)
        ]
        self._one_shot_index += 1
        gain = max(0.0, min(1.0, float(gain)))
        self._channel_gains[channel] = gain
        channel.set_volume(self.master_volume * gain)
        channel.play(self.sounds[sound_name])
