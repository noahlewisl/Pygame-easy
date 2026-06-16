"""
pygame_easy.py - A simple game library built on top of Pygame.
Made for beginners! Handles the hard stuff so you can focus on making games.

Usage:
    import pygame_easy as ge

    ge.init("My Game", 800, 600)

    player = ge.Sprite("player.png", x=100, y=100)

    def update():
        if ge.key_held("right"): player.x += 5
        if ge.key_held("left"):  player.x -= 5

    ge.run(update)
"""

import pygame
import sys
import os

pygame.init()
pygame.mixer.init()

# ─────────────────────────────────────────────
#  INTERNAL STATE
# ─────────────────────────────────────────────

_screen      = None
_clock       = pygame.time.Clock()
_fps         = 60
_bg_color    = (0, 0, 0)
_bg_image    = None
_title       = "pygame-easy"
_width       = 800
_height      = 600
_keys_down   = set()   # pressed this frame
_keys_held   = set()   # held down
_keys_up     = set()   # released this frame
_mouse_pos   = (0, 0)
_mouse_down  = set()
_mouse_up    = set()
_mouse_held  = set()
_sprites     = []
_sounds      = {}
_fonts       = {}
_running     = False
_camera_x    = 0
_camera_y    = 0
_delta_time  = 0.0     # seconds since last frame

# Key name mapping (friendly → pygame)
_KEY_MAP = {
    "up":     pygame.K_UP,    "down":  pygame.K_DOWN,
    "left":   pygame.K_LEFT,  "right": pygame.K_RIGHT,
    "space":  pygame.K_SPACE, "enter": pygame.K_RETURN,
    "escape": pygame.K_ESCAPE,"shift": pygame.K_LSHIFT,
    "ctrl":   pygame.K_LCTRL, "alt":   pygame.K_LALT,
    "w": pygame.K_w, "a": pygame.K_a, "s": pygame.K_s, "d": pygame.K_d,
    "q": pygame.K_q, "e": pygame.K_e, "r": pygame.K_r, "f": pygame.K_f,
    "z": pygame.K_z, "x": pygame.K_x, "c": pygame.K_c, "v": pygame.K_v,
    "0": pygame.K_0, "1": pygame.K_1, "2": pygame.K_2, "3": pygame.K_3,
    "4": pygame.K_4, "5": pygame.K_5, "6": pygame.K_6, "7": pygame.K_7,
    "8": pygame.K_8, "9": pygame.K_9,
}


# ─────────────────────────────────────────────
#  SETUP
# ─────────────────────────────────────────────

def init(title="pygame-easy", width=800, height=600, fps=60, bg_color=(0,0,0)):
    """
    Set up the game window. Call this first!

    Args:
        title     : Window title.
        width     : Window width in pixels.
        height    : Window height in pixels.
        fps       : Frames per second (default 60).
        bg_color  : Background color as (R, G, B). Default black.
    """
    global _screen, _fps, _bg_color, _title, _width, _height
    _title    = title
    _width    = width
    _height   = height
    _fps      = fps
    _bg_color = bg_color
    _screen   = pygame.display.set_mode((width, height))
    pygame.display.set_caption(title)


def set_background_color(r, g, b):
    """Change the background fill color."""
    global _bg_color
    _bg_color = (r, g, b)


def set_background_image(path):
    """Set an image as the background (will be stretched to fit the window)."""
    global _bg_image
    _bg_image = pygame.transform.scale(
        pygame.image.load(path).convert(), (_width, _height)
    )


def set_camera(x, y):
    """Offset the camera. All sprites/shapes will shift by (-x, -y)."""
    global _camera_x, _camera_y
    _camera_x, _camera_y = x, y


# ─────────────────────────────────────────────
#  SPRITE CLASS
# ─────────────────────────────────────────────

class Sprite:
    """
    A game object with an image, position, and helpers.

    Args:
        image_path : Path to an image file (png, jpg, etc).
        x, y       : Starting position (top-left corner).
        scale      : Resize factor. 1.0 = original, 2.0 = double, 0.5 = half.
        visible    : Whether to draw the sprite.
    """

    def __init__(self, image_path, x=0, y=0, scale=1.0, visible=True):
        self.x       = x
        self.y       = y
        self.scale   = scale
        self.visible = visible
        self.angle   = 0       # rotation in degrees
        self.opacity = 255     # 0 = invisible, 255 = fully visible
        self.speed_x = 0       # optional velocity
        self.speed_y = 0
        self.tag     = ""      # optional label for collision groups

        self._raw    = pygame.image.load(image_path).convert_alpha()
        self._update_image()
        _sprites.append(self)

    def _update_image(self):
        w = int(self._raw.get_width()  * self.scale)
        h = int(self._raw.get_height() * self.scale)
        self._image = pygame.transform.scale(self._raw, (w, h))

    @property
    def width(self):
        return self._image.get_width()

    @property
    def height(self):
        return self._image.get_height()

    @property
    def center_x(self):
        return self.x + self.width // 2

    @property
    def center_y(self):
        return self.y + self.height // 2

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    def move(self, dx, dy):
        """Move by dx, dy pixels."""
        self.x += dx
        self.y += dy

    def move_with_speed(self):
        """Apply speed_x / speed_y each frame."""
        self.x += self.speed_x
        self.y += self.speed_y

    def set_image(self, image_path):
        """Swap to a different image file."""
        self._raw = pygame.image.load(image_path).convert_alpha()
        self._update_image()

    def set_scale(self, scale):
        """Resize the sprite. 1.0 = original size."""
        self.scale = scale
        self._update_image()

    def collides_with(self, other):
        """Returns True if this sprite overlaps another Sprite."""
        r1 = pygame.Rect(self.x, self.y, self.width, self.height)
        r2 = pygame.Rect(other.x, other.y, other.width, other.height)
        return r1.colliderect(r2)

    def collides_with_any(self, tag=None):
        """
        Returns first Sprite this collides with (or None).
        Optionally filter by tag.
        """
        for s in _sprites:
            if s is self:
                continue
            if tag and s.tag != tag:
                continue
            if self.collides_with(s):
                return s
        return None

    def keep_in_bounds(self, margin=0):
        """Stop the sprite from leaving the window."""
        self.x = max(margin, min(self.x, _width  - self.width  - margin))
        self.y = max(margin, min(self.y, _height - self.height - margin))

    def distance_to(self, other):
        """Returns pixel distance to another Sprite."""
        import math
        return math.hypot(self.center_x - other.center_x,
                          self.center_y - other.center_y)

    def destroy(self):
        """Remove this sprite from the game."""
        if self in _sprites:
            _sprites.remove(self)

    def _draw(self, surface):
        if not self.visible:
            return
        img = self._image
        if self.angle != 0:
            img = pygame.transform.rotate(img, self.angle)
        if self.opacity != 255:
            img = img.copy()
            img.set_alpha(self.opacity)
        surface.blit(img, (self.x - _camera_x, self.y - _camera_y))


# ─────────────────────────────────────────────
#  SHAPES
# ─────────────────────────────────────────────

def draw_rect(x, y, w, h, color=(255,255,255), filled=True, thickness=2):
    """Draw a rectangle."""
    t = 0 if filled else thickness
    pygame.draw.rect(_screen, color, (x - _camera_x, y - _camera_y, w, h), t)


def draw_circle(x, y, radius, color=(255,255,255), filled=True, thickness=2):
    """Draw a circle. x, y = center."""
    t = 0 if filled else thickness
    pygame.draw.circle(_screen, color, (x - _camera_x, y - _camera_y), radius, t)


def draw_line(x1, y1, x2, y2, color=(255,255,255), thickness=2):
    """Draw a line between two points."""
    pygame.draw.line(_screen, color,
                     (x1 - _camera_x, y1 - _camera_y),
                     (x2 - _camera_x, y2 - _camera_y), thickness)


def draw_triangle(x1, y1, x2, y2, x3, y3, color=(255,255,255), filled=True, thickness=2):
    """Draw a triangle from three points."""
    t = 0 if filled else thickness
    pygame.draw.polygon(_screen, color,
                        [(x1-_camera_x, y1-_camera_y),
                         (x2-_camera_x, y2-_camera_y),
                         (x3-_camera_x, y3-_camera_y)], t)


# ─────────────────────────────────────────────
#  TEXT
# ─────────────────────────────────────────────

def draw_text(text, x, y, size=32, color=(255,255,255), font_path=None):
    """
    Draw text on screen.

    Args:
        text      : The string to display.
        x, y      : Position (top-left of text).
        size      : Font size.
        color     : Text color (R, G, B).
        font_path : Optional path to a .ttf font file.
    """
    key = (font_path, size)
    if key not in _fonts:
        _fonts[key] = pygame.font.Font(font_path, size)
    surf = _fonts[key].render(str(text), True, color)
    _screen.blit(surf, (x - _camera_x, y - _camera_y))


def text_size(text, size=32, font_path=None):
    """Returns (width, height) of a text string without drawing it."""
    key = (font_path, size)
    if key not in _fonts:
        _fonts[key] = pygame.font.Font(font_path, size)
    return _fonts[key].size(str(text))


# ─────────────────────────────────────────────
#  SOUND
# ─────────────────────────────────────────────

def load_sound(name, path):
    """
    Load a sound file and give it a name.

    Args:
        name : A label you choose (e.g. "jump", "coin").
        path : Path to the sound file (.wav or .ogg recommended).
    """
    _sounds[name] = pygame.mixer.Sound(path)


def play_sound(name, volume=1.0):
    """Play a loaded sound by name."""
    if name in _sounds:
        _sounds[name].set_volume(volume)
        _sounds[name].play()


def play_music(path, loop=True, volume=0.5):
    """
    Play background music.

    Args:
        path   : Path to music file (.mp3, .ogg, .wav).
        loop   : If True, music loops forever.
        volume : Volume from 0.0 to 1.0.
    """
    pygame.mixer.music.load(path)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(-1 if loop else 0)


def stop_music():
    """Stop background music."""
    pygame.mixer.music.stop()


def set_music_volume(volume):
    """Set music volume (0.0 to 1.0)."""
    pygame.mixer.music.set_volume(volume)


# ─────────────────────────────────────────────
#  INPUT — KEYBOARD
# ─────────────────────────────────────────────

def key_pressed(key):
    """Returns True on the frame the key was first pressed."""
    k = _KEY_MAP.get(key.lower(), None)
    if k is None:
        k = getattr(pygame, f"K_{key.lower()}", None)
    return k in _keys_down


def key_held(key):
    """Returns True while a key is held down."""
    k = _KEY_MAP.get(key.lower(), None)
    if k is None:
        k = getattr(pygame, f"K_{key.lower()}", None)
    return k in _keys_held


def key_released(key):
    """Returns True on the frame the key was released."""
    k = _KEY_MAP.get(key.lower(), None)
    if k is None:
        k = getattr(pygame, f"K_{key.lower()}", None)
    return k in _keys_up


# ─────────────────────────────────────────────
#  INPUT — MOUSE
# ─────────────────────────────────────────────

def mouse_pos():
    """Returns (x, y) of the mouse cursor."""
    return _mouse_pos


def mouse_x():
    return _mouse_pos[0]


def mouse_y():
    return _mouse_pos[1]


def mouse_clicked(button="left"):
    """Returns True on the frame a mouse button was clicked."""
    b = {"left": 1, "middle": 2, "right": 3}.get(button, 1)
    return b in _mouse_down


def mouse_held(button="left"):
    """Returns True while a mouse button is held."""
    b = {"left": 1, "middle": 2, "right": 3}.get(button, 1)
    return b in _mouse_held


def mouse_released(button="left"):
    """Returns True on the frame a mouse button was released."""
    b = {"left": 1, "middle": 2, "right": 3}.get(button, 1)
    return b in _mouse_up


def mouse_over_sprite(sprite):
    """Returns True if the mouse is hovering over a sprite."""
    mx, my = _mouse_pos
    return (sprite.x <= mx <= sprite.x + sprite.width and
            sprite.y <= my <= sprite.y + sprite.height)


# ─────────────────────────────────────────────
#  UTILITIES
# ─────────────────────────────────────────────

def screen_width():
    return _width

def screen_height():
    return _height

def delta_time():
    """Seconds since the last frame. Useful for frame-rate independent movement."""
    return _delta_time

def get_fps():
    """Returns current FPS."""
    return _clock.get_fps()

def quit_game():
    """Exit the game."""
    global _running
    _running = False


# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────

def run(update_fn=None, draw_fn=None):
    """
    Start the game loop.

    Args:
        update_fn : A function called every frame for your game logic.
        draw_fn   : An optional function called every frame for custom drawing.
                    (Sprites are drawn automatically — use this for extra shapes/text.)

    Example:
        def update():
            if ge.key_held("right"):
                player.x += 5

        ge.run(update)
    """
    global _running, _keys_down, _keys_up, _keys_held
    global _mouse_pos, _mouse_down, _mouse_up, _mouse_held
    global _delta_time

    _running = True

    while _running:
        # ── Events ──────────────────────────────
        _keys_down.clear()
        _keys_up.clear()
        _mouse_down.clear()
        _mouse_up.clear()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                _running = False

            elif event.type == pygame.KEYDOWN:
                _keys_down.add(event.key)
                _keys_held.add(event.key)

            elif event.type == pygame.KEYUP:
                _keys_up.add(event.key)
                _keys_held.discard(event.key)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                _mouse_down.add(event.button)
                _mouse_held.add(event.button)

            elif event.type == pygame.MOUSEBUTTONUP:
                _mouse_up.add(event.button)
                _mouse_held.discard(event.button)

        _mouse_pos = pygame.mouse.get_pos()

        # ── Update ───────────────────────────────
        if update_fn:
            update_fn()

        # ── Draw ─────────────────────────────────
        if _bg_image:
            _screen.blit(_bg_image, (0, 0))
        else:
            _screen.fill(_bg_color)

        for sprite in _sprites:
            sprite._draw(_screen)

        if draw_fn:
            draw_fn()

        pygame.display.flip()
        _delta_time = _clock.tick(_fps) / 1000.0

    pygame.quit()
    sys.exit()
