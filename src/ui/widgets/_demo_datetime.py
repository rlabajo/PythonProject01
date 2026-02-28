"""
Run this file directly to preview all custom datetime widgets:
    python -m src.ui.widgets._demo_datetime
"""

import sys
from datetime import datetime, date, time, timedelta

from PySide6.QtCore    import Qt
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                                QHBoxLayout, QScrollArea)

from src.ui.themes.theme import apply_dark_theme
from src.ui.widgets.labels import SectionDividerLabel, CaptionLabel
from src.ui.widgets.datetime_widgets import (
    TimePicker, DatePicker, DateRangePicker,
    DateTimeWidget, CountdownTimer, StopwatchWidget,
    TimelineWidget, TimelineEvent,
)


def main() -> None:
    app = QApplication(sys.argv)
    apply_dark_theme(app)

    content = QWidget()
    root = QVBoxLayout(content)
    root.setSpacing(18)
    root.setContentsMargins(36, 36, 36, 36)

    # ── TimePicker ────────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("TIME PICKER"))
    tp_row = QHBoxLayout()
    tp_row.setSpacing(16)

    tp1 = TimePicker(initial=time(9, 30))
    tp1.timeChanged.connect(lambda t: print(f"Time → {t}"))
    tp_row.addWidget(tp1)

    tp2 = TimePicker(show_seconds=True, initial=time(14, 45, 20))
    tp2.timeChanged.connect(lambda t: print(f"Time (s) → {t}"))
    tp_row.addWidget(tp2)
    tp_row.addStretch()
    root.addLayout(tp_row)
    root.addWidget(CaptionLabel(
        "Scroll, drag, or use ↑↓ keys on a focused drum. "
        "Right picker includes seconds."
    ))

    # ── DatePicker ────────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("DATE PICKER"))
    dp_row = QHBoxLayout()
    dp_row.setSpacing(16)

    dp = DatePicker(initial=date.today())
    dp.dateChanged.connect(lambda d: print(f"Date → {d.isoformat()}"))
    dp_row.addWidget(dp)
    dp_row.addStretch()
    root.addLayout(dp_row)

    # ── DateRangePicker ───────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("DATE RANGE PICKER"))
    drp = DateRangePicker()
    drp.rangeChanged.connect(
        lambda s, e: print(f"Range → {s.isoformat()} to {e.isoformat()}")
    )
    root.addWidget(drp)
    root.addWidget(CaptionLabel(
        "Click once for start, click again for end. "
        "Hover shows a preview of the range."
    ))

    # ── DateTimeWidget ────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("DATE + TIME WIDGET"))
    dtw = DateTimeWidget(
        initial=datetime.now().replace(second=0, microsecond=0),
        show_seconds=False,
    )
    dtw.dateTimeChanged.connect(
        lambda dt: print(f"DateTime → {dt.isoformat()}")
    )
    root.addWidget(dtw)
    root.addWidget(CaptionLabel(
        "Click either chip to open the floating picker popup."
    ))

    # ── CountdownTimer ────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("COUNTDOWN TIMER"))
    target = datetime.now() + timedelta(hours=1, minutes=23, seconds=45)
    cd = CountdownTimer(target=target, label="Next deployment in")
    cd.finished.connect(lambda: print("Countdown reached zero!"))
    root.addWidget(cd)

    # ── StopwatchWidget ───────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("STOPWATCH"))
    sw = StopwatchWidget()
    sw.lapped.connect(
        lambda n, s, e: print(f"Lap {n} — split {s}, elapsed {e}")
    )
    root.addWidget(sw)

    # ── TimelineWidget ────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("TIMELINE"))
    tl = TimelineWidget()
    tl.setMinimumHeight(240)

    for ev in [
        TimelineEvent(datetime(2026, 2, 28, 9,  0),
                      "Pipeline triggered",
                      "Commit abc1234 pushed to main", "info"),
        TimelineEvent(datetime(2026, 2, 28, 9,  1),
                      "Build started",
                      "Runner: ubuntu-latest", "info"),
        TimelineEvent(datetime(2026, 2, 28, 9,  4),
                      "Tests passed",
                      "142 tests · 0 failures · 0 skipped", "success"),
        TimelineEvent(datetime(2026, 2, 28, 9,  5),
                      "High memory usage detected",
                      "Peak RSS 1.8 GB — threshold 1.5 GB", "warning"),
        TimelineEvent(datetime(2026, 2, 28, 9,  7),
                      "Deployment failed",
                      "Health check timed out after 30 s", "error"),
        TimelineEvent(datetime(2026, 2, 28, 9, 12),
                      "Rollback completed",
                      "Reverted to v2.3.9", "success"),
    ]:
        tl.add_event(ev)

    root.addWidget(tl)
    root.addStretch()

    scroll = QScrollArea()
    scroll.setWidget(content)
    scroll.setWidgetResizable(True)
    scroll.setWindowTitle("Custom DateTime Widgets — Demo")
    scroll.resize(780, 860)
    scroll.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()