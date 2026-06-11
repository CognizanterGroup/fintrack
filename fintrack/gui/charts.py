"""QtCharts builders for the analytics views.

Thin factory functions that turn analytics dictionaries into themed
``QChartView`` widgets. Native QtCharts is used (rather than embedding
matplotlib) so charts render crisply, animate, and match the app palette.
"""

from __future__ import annotations

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import QMargins, Qt
from PySide6.QtGui import QColor, QPainter

from .theme import Palette


def _frame(chart: QChart) -> QChartView:
    chart.setBackgroundVisible(False)
    chart.setMargins(QMargins(0, 0, 0, 0))
    chart.legend().setVisible(True)
    chart.legend().setAlignment(Qt.AlignBottom)
    view = QChartView(chart)
    view.setRenderHint(QPainter.Antialiasing)
    view.setStyleSheet("background: transparent;")
    view.setMinimumHeight(260)
    return view


def category_donut(by_category: dict[str, float], currency: str = "") -> QChartView:
    """Donut chart of spending share by category."""
    series = QPieSeries()
    series.setHoleSize(0.45)
    for i, (cat, amt) in enumerate(by_category.items()):
        slc = series.append(f"{cat}", amt)
        slc.setColor(QColor(Palette.SERIES[i % len(Palette.SERIES)]))
        slc.setLabelVisible(False)
        slc.setBorderColor(QColor("white"))
        slc.setBorderWidth(2)

    chart = QChart()
    chart.addSeries(series)
    chart.setTitle("Spending by category")
    chart.setAnimationOptions(QChart.SeriesAnimations)
    return _frame(chart)


def monthly_bars(trends: dict[str, dict]) -> QChartView:
    """Grouped income vs expense bars per month."""
    income_set = QBarSet("Income")
    expense_set = QBarSet("Expense")
    income_set.setColor(QColor(Palette.INCOME))
    expense_set.setColor(QColor(Palette.EXPENSE))

    months = list(trends.keys())
    for m in months:
        income_set.append(trends[m]["income"])
        expense_set.append(trends[m]["expense"])

    series = QBarSeries()
    series.append(income_set)
    series.append(expense_set)

    chart = QChart()
    chart.addSeries(series)
    chart.setTitle("Monthly income vs expense")
    chart.setAnimationOptions(QChart.SeriesAnimations)

    axis_x = QBarCategoryAxis()
    axis_x.append(months)
    chart.addAxis(axis_x, Qt.AlignBottom)
    series.attachAxis(axis_x)

    axis_y = QValueAxis()
    peak = max(
        [trends[m]["income"] for m in months] +
        [trends[m]["expense"] for m in months] + [1]
    )
    axis_y.setRange(0, peak * 1.1)
    axis_y.setLabelFormat("%.0f")
    chart.addAxis(axis_y, Qt.AlignLeft)
    series.attachAxis(axis_y)

    return _frame(chart)
