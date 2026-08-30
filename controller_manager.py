import math

import pygame


class ControllerManager:
    """Normalizează controllerul într-un set mic de acțiuni Pygame."""

    DEADZONE = 0.22

    def __init__(self):
        pygame.joystick.init()
        self.controllers = {}
        self.axis_navigation = {0: 0, 1: 0}
        self._discover_controllers()

    def _discover_controllers(self):
        for joystick_index in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(joystick_index)
            joystick.init()
            instance_id = (
                joystick.get_instance_id()
                if hasattr(joystick, "get_instance_id")
                else joystick_index
            )
            self.controllers[instance_id] = joystick

    def _add_controller(self, device_index):
        try:
            joystick = pygame.joystick.Joystick(device_index)
            joystick.init()
            instance_id = (
                joystick.get_instance_id()
                if hasattr(joystick, "get_instance_id")
                else device_index
            )
            self.controllers[instance_id] = joystick
        except pygame.error:
            return

    @property
    def connected(self):
        return bool(self.controllers)

    @property
    def controller_name(self):
        joystick = self._primary_controller()
        return joystick.get_name() if joystick is not None else "NOT CONNECTED"

    def _primary_controller(self):
        if not self.controllers:
            return None
        return next(iter(self.controllers.values()))

    @staticmethod
    def _key_event(key):
        return pygame.event.Event(pygame.KEYDOWN, key=key)

    @classmethod
    def translate_button(cls, button):
        button_map = {
            0: pygame.K_RETURN,  # A / Cross: accept and fire
            1: pygame.K_ESCAPE,  # B / Circle: back
            2: pygame.K_e,       # X / Square: Energy Pulse
            3: pygame.K_F1,      # Y / Triangle: skip first-run training
            7: pygame.K_ESCAPE,  # Menu / Start: pause
        }
        key = button_map.get(int(button))
        return cls._key_event(key) if key is not None else None

    @classmethod
    def translate_hat(cls, hat_value):
        horizontal, vertical = hat_value
        if vertical > 0:
            return cls._key_event(pygame.K_UP)
        if vertical < 0:
            return cls._key_event(pygame.K_DOWN)
        if horizontal < 0:
            return cls._key_event(pygame.K_LEFT)
        if horizontal > 0:
            return cls._key_event(pygame.K_RIGHT)
        return None

    def handle_event(self, event):
        translated_events = []
        if event.type == getattr(pygame, "JOYDEVICEADDED", -1):
            self._add_controller(event.device_index)
            return translated_events
        if event.type == getattr(pygame, "JOYDEVICEREMOVED", -1):
            self.controllers.pop(event.instance_id, None)
            return translated_events
        if event.type == pygame.JOYBUTTONDOWN:
            translated = self.translate_button(event.button)
            if translated is not None:
                translated_events.append(translated)
            return translated_events
        if event.type == pygame.JOYHATMOTION:
            translated = self.translate_hat(event.value)
            if translated is not None:
                translated_events.append(translated)
            return translated_events
        if event.type == pygame.JOYAXISMOTION and event.axis in (0, 1):
            direction = 0
            if event.value <= -0.72:
                direction = -1
            elif event.value >= 0.72:
                direction = 1
            previous_direction = self.axis_navigation[event.axis]
            self.axis_navigation[event.axis] = direction
            if direction != 0 and direction != previous_direction:
                if event.axis == 0:
                    key = pygame.K_LEFT if direction < 0 else pygame.K_RIGHT
                else:
                    key = pygame.K_UP if direction < 0 else pygame.K_DOWN
                translated_events.append(self._key_event(key))
        return translated_events

    @classmethod
    def apply_deadzone(cls, x_value, y_value):
        magnitude = math.hypot(x_value, y_value)
        if magnitude <= cls.DEADZONE:
            return 0.0, 0.0
        normalized_magnitude = min(
            1.0,
            (magnitude - cls.DEADZONE) / (1.0 - cls.DEADZONE),
        )
        return (
            x_value / magnitude * normalized_magnitude,
            y_value / magnitude * normalized_magnitude,
        )

    def movement_vector(self):
        joystick = self._primary_controller()
        if joystick is None:
            return 0.0, 0.0

        try:
            x_value = joystick.get_axis(0) if joystick.get_numaxes() > 0 else 0.0
            y_value = joystick.get_axis(1) if joystick.get_numaxes() > 1 else 0.0
            if joystick.get_numhats() > 0:
                hat_x, hat_y = joystick.get_hat(0)
                if hat_x or hat_y:
                    x_value = float(hat_x)
                    y_value = float(-hat_y)
            return self.apply_deadzone(x_value, y_value)
        except pygame.error:
            return 0.0, 0.0

    def fire_held(self):
        joystick = self._primary_controller()
        if joystick is None:
            return False
        try:
            face_button = (
                joystick.get_numbuttons() > 0
                and joystick.get_button(0)
            )
            right_trigger = (
                joystick.get_numaxes() > 5
                and joystick.get_axis(5) > 0.35
            )
            return bool(face_button or right_trigger)
        except pygame.error:
            return False
