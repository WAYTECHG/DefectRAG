"""Draws the friendly DefectRAG robot used at the top of notification emails.

Writes frontend/public/assets/email/robot-hello.gif (served by the Space under /assets/, so email
clients can load it). Frames are drawn at 4x and downscaled for smooth edges.
Outlook desktop shows only the first frame, so frame 0 is a complete pose.
"""
from math import cos, pi, radians, sin
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'frontend/public/assets/email/robot-hello.gif'
SIZE, S, FRAMES, FRAME_MS = 200, 4, 12, 90
INK, LAVENDER, PANEL, BG = '#5b4fd6', '#d9d3fa', '#1f2147', '#f4f2ff'
EYE, AMBER, AMBER_GLOW, CHEEK, WHITE = '#7ee0ff', '#f3a64a', '#ffd38a', '#ffb3c4', '#ffffff'
FONT = Path('C:/Windows/Fonts/segoeuib.ttf')


def p(*values):
    """Scale final-size coordinates to the 4x drawing canvas."""
    return [v * S for v in values]


def limb(d, start, angle, length, width, colour):
    end = (start[0] + length * cos(radians(angle)), start[1] + length * sin(radians(angle)))
    d.line(p(*start, *end), fill=colour, width=width * S)
    for x, y in (start, end):
        r = width / 2
        d.ellipse(p(x - r, y - r, x + r, y + r), fill=colour)
    return end


def frame(i):
    phase = 2 * pi * i / FRAMES
    bob = 1.5 * sin(phase)
    img = Image.new('RGB', (SIZE * S, SIZE * S), BG)
    d = ImageDraw.Draw(img)
    # Soft floor shadow, unaffected by the bob.
    d.ellipse(p(62, 176, 138, 186), fill='#e4dffb')
    y = lambda v: v + bob  # noqa: E731  - whole robot bobs gently

    # Arm holding the magnifying glass (left of picture), drawn behind the body.
    hand = limb(d, (72, y(134)), 140, 26, 9, INK)
    d.line(p(hand[0], hand[1], hand[0] - 7, hand[1] + 9), fill=AMBER, width=5 * S)
    cx, cy = hand[0] - 13, hand[1] - 10
    d.ellipse(p(cx - 13, cy - 13, cx + 13, cy + 13), fill='#fff7e6', outline=AMBER, width=5 * S)
    d.arc(p(cx - 8, cy - 8, cx + 8, cy + 8), 200, 260, fill=WHITE, width=2 * S)

    # Body with a small status panel.
    d.rounded_rectangle(p(68, y(122), 132, y(172)), radius=14 * S, fill=WHITE, outline=INK, width=3 * S)
    d.rounded_rectangle(p(84, y(136), 116, y(156)), radius=6 * S, fill=LAVENDER)
    for k, colour in enumerate((INK, AMBER, INK)):
        lit = colour if (i // 3) % 3 == k else '#b9b0f0'
        d.ellipse(p(89 + 9 * k, y(143), 95 + 9 * k, y(149)), fill=lit)

    # Waving arm (right of picture), in front of the body and clear of the head.
    wave = -40 + 22 * sin(phase)
    hand = limb(d, (128, y(132)), wave, 30, 9, INK)
    d.ellipse(p(hand[0] - 8, hand[1] - 8, hand[0] + 8, hand[1] + 8), fill=WHITE, outline=INK, width=3 * S)

    # Neck, ears, head and face screen.
    d.rectangle(p(92, y(112), 108, y(124)), fill=LAVENDER)
    d.rounded_rectangle(p(47, y(72), 57, y(96)), radius=4 * S, fill=LAVENDER, outline=INK, width=2 * S)
    d.rounded_rectangle(p(143, y(72), 153, y(96)), radius=4 * S, fill=LAVENDER, outline=INK, width=2 * S)
    d.rounded_rectangle(p(56, y(50), 144, y(116)), radius=20 * S, fill=WHITE, outline=INK, width=3 * S)
    d.rounded_rectangle(p(66, y(61), 134, y(106)), radius=14 * S, fill=PANEL)

    # Eyes blink once per loop; a small smile and cheeks keep the tone friendly.
    if i == 8:
        for ex in (86, 114):
            d.rounded_rectangle(p(ex - 7, y(81), ex + 7, y(84)), radius=1.5 * S, fill=EYE)
    else:
        for ex in (86, 114):
            d.ellipse(p(ex - 7, y(75), ex + 7, y(89)), fill=EYE)
            d.ellipse(p(ex - 4, y(77), ex - 1, y(80)), fill=WHITE)
    d.arc(p(89, y(86), 111, y(100)), 20, 160, fill=EYE, width=3 * S)
    d.ellipse(p(70, y(93), 78, y(99)), fill=CHEEK)
    d.ellipse(p(122, y(93), 130, y(99)), fill=CHEEK)

    # Antenna light pulses.
    d.line(p(100, y(50), 100, y(36)), fill=INK, width=3 * S)
    if i % 4 < 2:
        d.ellipse(p(91, y(21), 109, y(39)), fill=AMBER_GLOW)
    d.ellipse(p(94, y(24), 106, y(36)), fill=AMBER)

    # "Hi!" speech bubble.
    d.rounded_rectangle(p(146, 18, 192, 46), radius=10 * S, fill=INK)
    d.polygon(p(154, 44, 150, 54, 164, 45), fill=INK)
    font = ImageFont.truetype(str(FONT), 16 * S)
    d.text(p(169, 32), 'Hi!', font=font, fill=WHITE, anchor='mm')

    small = img.resize((SIZE, SIZE), Image.LANCZOS)
    return small.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)


def main():
    frames = [frame(i) for i in range(FRAMES)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=FRAME_MS, loop=0, optimize=True, disposal=1)
    print(OUT, OUT.stat().st_size, 'bytes')


if __name__ == '__main__':
    main()
