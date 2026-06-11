"""Central theme for the FinTrack desktop GUI.

Keeping all colours and the Qt stylesheet (QSS) in one place gives the app a
consistent, intentional visual identity and makes re-skinning a one-file job.
The palette is a modern "fintech" look: slate sidebar, soft off-white canvas,
emerald accent.
"""

from __future__ import annotations


class Palette:
    # Brand / accent
    ACCENT = "#10b981"          # emerald 500
    ACCENT_DARK = "#059669"     # emerald 600
    ACCENT_SOFT = "#d1fae5"     # emerald 100

    # Sidebar
    SIDEBAR = "#0f172a"         # slate 900
    SIDEBAR_HOVER = "#1e293b"   # slate 800
    SIDEBAR_TEXT = "#cbd5e1"    # slate 300

    # Canvas / surfaces
    CANVAS = "#f1f5f9"          # slate 100
    CARD = "#ffffff"
    BORDER = "#e2e8f0"          # slate 200

    # Text
    TEXT = "#0f172a"            # slate 900
    TEXT_MUTED = "#64748b"      # slate 500

    # Semantic
    INCOME = "#16a34a"          # green 600
    EXPENSE = "#dc2626"         # red 600
    WARNING = "#f59e0b"         # amber 500
    DANGER = "#dc2626"
    INFO = "#2563eb"            # blue 600

    # Chart series (categorical)
    SERIES = [
        "#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6",
        "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16",
    ]


def stylesheet() -> str:
    p = Palette
    return f"""
    QWidget {{
        font-family: 'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif;
        font-size: 14px;
        color: {p.TEXT};
    }}
    QMainWindow, QDialog {{ background: {p.CANVAS}; }}

    /* Sidebar container */
    #Sidebar {{ background: {p.SIDEBAR}; }}
    #BrandLabel {{
        color: white; font-size: 20px; font-weight: 700;
        padding: 20px 18px 6px 18px;
    }}
    #BrandSub {{ color: {p.SIDEBAR_TEXT}; padding: 0 18px 16px 18px; font-size: 12px; }}

    #NavButton {{
        background: transparent; color: {p.SIDEBAR_TEXT};
        text-align: left; border: none; padding: 12px 18px;
        border-radius: 8px; margin: 2px 10px; font-size: 14px;
    }}
    #NavButton:hover {{ background: {p.SIDEBAR_HOVER}; color: white; }}
    #NavButton:checked {{ background: {p.ACCENT}; color: white; font-weight: 600; }}

    #UserChip {{ color: {p.SIDEBAR_TEXT}; padding: 14px 18px; font-size: 12px; }}

    /* Cards */
    #Card {{
        background: {p.CARD}; border: 1px solid {p.BORDER};
        border-radius: 14px;
    }}
    #CardTitle {{ color: {p.TEXT_MUTED}; font-size: 12px; font-weight: 600;
                  text-transform: uppercase; letter-spacing: 0.5px; }}
    #StatValue {{ font-size: 26px; font-weight: 700; }}
    #PageTitle {{ font-size: 24px; font-weight: 700; padding: 4px 0; }}
    #PageSub {{ color: {p.TEXT_MUTED}; font-size: 13px; }}
    #SectionTitle {{ font-size: 16px; font-weight: 700; padding: 6px 0; }}

    /* Inputs */
    QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox, QTextEdit {{
        background: white; border: 1px solid {p.BORDER};
        border-radius: 8px; padding: 8px 10px; selection-background-color: {p.ACCENT_SOFT};
    }}
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {{
        border: 1px solid {p.ACCENT};
    }}
    QComboBox::drop-down {{ border: none; width: 24px; }}
    QComboBox QAbstractItemView {{
        background: white; border: 1px solid {p.BORDER};
        selection-background-color: {p.ACCENT_SOFT}; selection-color: {p.TEXT};
        outline: none;
    }}

    /* Buttons */
    QPushButton {{
        background: {p.ACCENT}; color: white; border: none;
        border-radius: 8px; padding: 9px 16px; font-weight: 600;
    }}
    QPushButton:hover {{ background: {p.ACCENT_DARK}; }}
    QPushButton:disabled {{ background: #94a3b8; }}
    QPushButton#Ghost {{
        background: transparent; color: {p.TEXT};
        border: 1px solid {p.BORDER};
    }}
    QPushButton#Ghost:hover {{ background: {p.CANVAS}; }}
    QPushButton#Danger {{ background: {p.DANGER}; }}
    QPushButton#Danger:hover {{ background: #b91c1c; }}

    /* Tables */
    QTableWidget {{
        background: white; border: 1px solid {p.BORDER};
        border-radius: 12px; gridline-color: {p.BORDER};
        selection-background-color: {p.ACCENT_SOFT}; selection-color: {p.TEXT};
    }}
    QHeaderView::section {{
        background: {p.CANVAS}; color: {p.TEXT_MUTED};
        padding: 10px; border: none; border-bottom: 1px solid {p.BORDER};
        font-weight: 600;
    }}
    QTableWidget::item {{ padding: 6px; }}

    /* Progress bars */
    QProgressBar {{
        background: {p.CANVAS}; border: none; border-radius: 6px;
        height: 10px; text-align: center; color: transparent;
    }}
    QProgressBar::chunk {{ background: {p.ACCENT}; border-radius: 6px; }}

    /* Tabs / misc */
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: #cbd5e1; border-radius: 5px; min-height: 30px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
    QLabel#Pill {{ border-radius: 10px; padding: 3px 10px; font-size: 12px; font-weight: 600; }}
    """
