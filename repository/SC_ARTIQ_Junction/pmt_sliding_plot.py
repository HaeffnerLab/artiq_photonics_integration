#!/usr/bin/env python3
"""Plot PMT counts against PMT_count_time in a fixed ten-second window.

The PMT_count y-axis unit follows PMT_count_is_cps. PMT_count_rate is always
shown in counts per second. Use --y and --x to select different datasets.
"""

import numpy as np
import PyQt5  # Ensure pyqtgraph uses Qt5.
import pyqtgraph

from artiq.applets.simple import SimpleApplet


WINDOW_SECONDS = 10.0


class PMTSlidingPlot(pyqtgraph.PlotWidget):
    def __init__(self, args, req):
        super().__init__()
        self.args = args
        self.setBackground("k")
        self.curve = self.plot(
            pen=pyqtgraph.mkPen(color=(0, 255, 0), width=1),
            symbol="o",
        )
        self.curve.setSymbolSize(5)
        self.curve.setSymbolBrush((255, 0, 0))
        self.setLabel("bottom", "Time", units="s")
        self.setLabel("left", "PMT count", units="counts/gate")
        self.getPlotItem().getAxis("left").enableAutoSIPrefix(False)
        self.showGrid(x=True, y=True, alpha=0.3)
        self.setTitle("Live PMT count (last 10 seconds)")
        self.enableAutoRange(axis=pyqtgraph.ViewBox.XAxis, enable=False)
        self.enableAutoRange(axis=pyqtgraph.ViewBox.YAxis, enable=True)

    def data_changed(self, value, metadata, persist, mods):
        try:
            times = np.asarray(value[self.args.x], dtype=float)
            counts = np.asarray(value[self.args.y], dtype=float)
            is_cps = self.args.y == "PMT_count_rate" or (
                self.args.y == "PMT_count"
                and bool(value.get(self.args.mode, False))
            )
        except KeyError:
            return
        except (TypeError, ValueError):
            self.setTitle("Invalid PMT plot datasets")
            return

        if is_cps:
            self.setLabel("left", "PMT count rate", units="counts/s")
            self.setTitle("Live PMT count rate (last 10 seconds)")
        else:
            self.setLabel("left", "PMT count", units="counts/gate")
            self.setTitle("Live PMT count (last 10 seconds)")

        if times.ndim != 1 or counts.ndim != 1 or len(times) != len(counts):
            self.setTitle("PMT value and time datasets must be matching 1D arrays!!!!!!!!!!!")
            return

        if not len(times):
            self.curve.setData([], [])
            return

        finite_times = times[np.isfinite(times)]
        if not len(finite_times):
            self.curve.setData([], [])
            self.setTitle("Waiting for finite PMT timestamps")
            return

        latest = np.max(finite_times)
        left_edge = latest - WINDOW_SECONDS
        visible = (
            np.isfinite(times)
            & np.isfinite(counts)
            & (times >= left_edge)
            & (times <= latest)
        )
        self.curve.setData(times[visible], counts[visible])
        self.setXRange(left_edge, latest, padding=0)


def main():
    applet = SimpleApplet(PMTSlidingPlot)
    applet.add_dataset("y", "PMT counts or count rates", required=False)
    applet.add_dataset("x", "PMT sample times in seconds", required=False)
    applet.add_dataset("mode", "PMT_count counts-per-second mode", required=False)
    applet.argparser.set_defaults(
        y="PMT_count",
        x="PMT_count_time",
        mode="PMT_count_is_cps",
    )
    applet.run()


if __name__ == "__main__":
    main()
