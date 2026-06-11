"""Regenerate the bundled app icons (assets/icon.png, assets/icon.ico) from
the brand mark in ``fintrack.gui.icons``.

Run after changing the logo:

    python scripts/make_icons.py

Runs headless (offscreen Qt platform), so it works in CI too. The .ico embeds
the standard Windows sizes; the .png is 512x512 and is what PyInstaller uses
to derive platform icons (it converts via Pillow on macOS/Linux).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QByteArray, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QGuiApplication, QImage, QPainter  # noqa: E402
from PySide6.QtSvg import QSvgRenderer  # noqa: E402

from fintrack.gui.icons import LOGO_SVG  # noqa: E402


def render(size: int) -> QImage:
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    QSvgRenderer(QByteArray(LOGO_SVG)).render(painter, QRectF(0, 0, size, size))
    painter.end()
    return image


def main() -> int:
    QGuiApplication(sys.argv)
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)

    render(512).save(str(assets / "icon.png"))
    print(f"wrote {assets / 'icon.png'}")

    # Multi-size .ico for the Windows executable and installer.
    ico_path = assets / "icon.ico"
    _write_ico(ico_path, [render(s) for s in (16, 24, 32, 48, 64, 128, 256)])
    print(f"wrote {ico_path}")
    return 0


def _write_ico(path: Path, images: list[QImage]) -> None:
    """Pack PNG-encoded frames into a .ico container (no Pillow needed)."""
    import struct
    from PySide6.QtCore import QBuffer, QIODevice

    frames = []
    for img in images:
        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        img.save(buf, "PNG")
        frames.append((img.width(), bytes(buf.data())))
        buf.close()

    header = struct.pack("<HHH", 0, 1, len(frames))
    entries, blobs = b"", b""
    offset = len(header) + 16 * len(frames)
    for width, blob in frames:
        size_byte = 0 if width >= 256 else width
        entries += struct.pack("<BBBBHHII", size_byte, size_byte, 0, 0,
                               1, 32, len(blob), offset)
        blobs += blob
        offset += len(blob)
    path.write_bytes(header + entries + blobs)


if __name__ == "__main__":
    sys.exit(main())
