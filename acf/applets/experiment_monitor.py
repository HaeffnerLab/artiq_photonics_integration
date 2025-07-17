"""
Experiment Monitor applet for ARTIQ.
This module provides a real-time plotting interface for monitoring experiment data.
"""

import numpy as np
import PyQt5
import pyqtgraph as pg
from PyQt5.QtGui import QColor
from typing import Optional, Dict, Any, Tuple
from artiq.applets.simple import TitleApplet, SimpleApplet
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExperimentMonitor(pg.PlotWidget):
    """
    A PyQtGraph-based widget for real-time experiment data monitoring.
    
    This class provides functionality to plot experiment data with optional
    x-axis values, error bars, and fitted curves. It supports both regular
    plotting and region-based plotting for Ca-44 experiments.
    """
    
    def __init__(self, args: Any, req: Any) -> None:
        """
        Initialize the Experiment Monitor.
        
        Args:
            args: Command line arguments containing configuration
            req: Request object from ARTIQ
        """
        try:
            pg.PlotWidget.__init__(self)
            self.args = args

            # Dataset names
            self.y_dataset_name = self.args.y
            self.has_x_dataset = self.args.x is not None
            self.has_fit_dataset = self.args.fit is not None
            self.has_err_dataset = self.args.y_err is not None
            self.has_pos_dataset = self.args.pos is not None

            # Initialize dataset names with defaults if not provided
            self.x_dataset_name = self.args.x if self.has_x_dataset else "No X Dataset"
            self.fit_dataset_name = self.args.fit if self.has_fit_dataset else "No Fit Dataset"
            self.err_dataset_name = self.args.y_err if self.has_err_dataset else "No Error Dataset"

            # Validate axis limits
            if self.args.xmax is not None and not self.has_x_dataset:
                raise RuntimeError("xmax given, but no x dataset given.")
            if self.args.xmin != 0 and self.args.xmax is None:
                raise RuntimeError("xmin given but no xmax given.")
            if self.args.ymin != 0 and self.args.ymax is None:
                raise RuntimeError("ymin given but no ymax given.")

            # Set axis ranges if provided
            if self.args.xmax is not None:
                self.setXRange(self.args.xmin, self.args.xmax)
            if self.args.ymax is not None:
                self.setYRange(self.args.ymin, self.args.ymax)
            
            # Set up plot styling
            self.pen = pg.mkPen(color=(0, 255, 0)) if self.args.pen else None

            # Set up plot labels and title
            title = "Experiment Monitor"
            if self.args.exp_label is not None:
                title += f"<br>({self.args.exp_label})"

            self.setLabel("bottom", self.x_dataset_name)
            self.setLabel("left", self.y_dataset_name)
            self.setTitle(title)
            self.setBackground('k')
            
            self.waiting_for_size_update = False
        except Exception as e:
            logger.error(f"Error initializing ExperimentMonitor: {str(e)}")
            raise

    def data_changed(self, value: Dict[str, np.ndarray], 
                    metadata: Dict[str, Any], 
                    persist: Dict[str, Any], 
                    mod_buffer: Dict[str, Any]) -> None:
        """
        Handle data updates from the experiment.
        
        Args:
            value: Dictionary containing the latest dataset values
            metadata: Dictionary containing metadata about the datasets
            persist: Dictionary for persistent data
            mod_buffer: Dictionary containing modified buffer data
            
        Raises:
            RuntimeError: If required datasets are missing or have size mismatches
        """
        try:
            # Validate required datasets
            if self.y_dataset_name not in value:
                raise RuntimeError(f"Y Dataset name '{self.y_dataset_name}' not in value.")
            if self.has_x_dataset and self.x_dataset_name not in value:
                raise RuntimeError(f"X Dataset name '{self.x_dataset_name}' not in value.")
            if self.has_fit_dataset and self.fit_dataset_name not in value:
                raise RuntimeError(f"Fit Dataset name '{self.fit_dataset_name}' not in value.")

            # Extract data with error handling
            try:
                y_data = value[self.y_dataset_name]
                if not isinstance(y_data, np.ndarray):
                    y_data = np.array(y_data)
            except Exception as e:
                logger.error(f"Error processing y_data: {str(e)}")
                return

            try:
                x_data = (value[self.x_dataset_name] if self.has_x_dataset 
                         else np.arange(len(y_data)))
                if not isinstance(x_data, np.ndarray):
                    x_data = np.array(x_data)
            except Exception as e:
                logger.error(f"Error processing x_data: {str(e)}")
                return

            try:
                fit_data = (value[self.fit_dataset_name] if self.has_fit_dataset 
                          else None)
                if fit_data is not None and not isinstance(fit_data, np.ndarray):
                    fit_data = np.array(fit_data)
            except Exception as e:
                logger.error(f"Error processing fit_data: {str(e)}")
                fit_data = None

            try:
                err_data = (value[self.err_dataset_name] if self.has_err_dataset 
                          else None)
                if err_data is not None and not isinstance(err_data, np.ndarray):
                    err_data = np.array(err_data)
            except Exception as e:
                logger.error(f"Error processing err_data: {str(e)}")
                err_data = None

            try:
                pos_data = (value[self.args.pos] if self.has_pos_dataset 
                          else None)
                if pos_data is not None and not isinstance(pos_data, np.ndarray):
                    pos_data = np.array(pos_data)
            except Exception as e:
                logger.error(f"Error processing pos_data: {str(e)}")
                pos_data = None

            # Handle size mismatches
            if x_data.size != y_data.size:
                if not self.waiting_for_size_update:
                    self.waiting_for_size_update = True
                    return
                else:
                    raise RuntimeError(
                        f"Size mismatch between x_data ({x_data.size}) "
                        f"and y_data ({y_data.size})."
                    )
            elif self.waiting_for_size_update:
                self.waiting_for_size_update = False

            self.clear()

            # Plot data based on whether position data is available
            if not self.has_pos_dataset:
                try:
                    plot = self.plot(x_data, y_data, pen=self.pen, symbol="o")
                    plot.setSymbolSize(5)
                    plot.setSymbolBrush((255, 0, 0))  # Fluorescent pink
                except Exception as e:
                    logger.error(f"Error plotting regular data: {str(e)}")
            else:
                try:
                    self._plot_regional_data(x_data, y_data, pos_data)
                except Exception as e:
                    logger.error(f"Error plotting regional data: {str(e)}")

            # Plot fit data if available
            if self.has_fit_dataset and fit_data is not None:
                try:
                    self.plot(x_data, fit_data, pen='r')
                except Exception as e:
                    logger.error(f"Error plotting fit data: {str(e)}")

        except Exception as e:
            logger.error(f"Error in data_changed: {str(e)}")
            # Don't raise the exception to prevent applet from crashing
            return

    def _plot_regional_data(self, x_data: np.ndarray, 
                          y_data: np.ndarray, 
                          pos_data: np.ndarray) -> None:
        """
        Plot data with different regions based on position data.
        
        Args:
            x_data: X-axis values
            y_data: Y-axis values
            pos_data: Position/region data
        """
        try:
            valid_mask = ~np.isnan(pos_data)
            x_data_tmp = x_data[valid_mask]
            y_data_tmp = y_data[valid_mask]
            pos_data_tmp = pos_data[valid_mask]

            self.addLegend()
            category_info = {
                1: {'color': 'r', 'label': 'Region 1'},
                2: {'color': 'b', 'label': 'Region 2'}
            }

            if len(pos_data_tmp) > 0:
                segments = self._get_segments(x_data_tmp, y_data_tmp, pos_data_tmp)
                self._plot_segments(segments, category_info)
        except Exception as e:
            logger.error(f"Error in _plot_regional_data: {str(e)}")
            raise

    def _get_segments(self, x_data: np.ndarray, 
                     y_data: np.ndarray, 
                     pos_data: np.ndarray) -> list:
        """
        Get contiguous segments of data based on position changes.
        
        Args:
            x_data: X-axis values
            y_data: Y-axis values
            pos_data: Position/region data
            
        Returns:
            List of tuples containing (category, x_segment, y_segment)
        """
        try:
            segments = []
            current_category = pos_data[0]
            start_index = 0

            for i in range(1, len(pos_data)):
                if pos_data[i] != current_category:
                    segments.append((current_category, x_data[start_index:i], y_data[start_index:i]))
                    start_index = i
                    current_category = pos_data[i]
            
            segments.append((current_category, x_data[start_index:], y_data[start_index:]))
            return segments
        except Exception as e:
            logger.error(f"Error in _get_segments: {str(e)}")
            raise

    def _plot_segments(self, segments: list, category_info: dict) -> None:
        """
        Plot segments with appropriate colors and legend entries.
        
        Args:
            segments: List of data segments
            category_info: Dictionary containing color and label information for each category
        """
        try:
            category_plotted = set()
            previous_end = None

            for cat, x_seg, y_seg in segments:
                try:
                    color = category_info[cat]['color']
                    label = category_info[cat]['label']

                    if cat not in category_plotted:
                        self.plot(
                            x_seg, y_seg, 
                            pen=self.pen, 
                            symbol='o', 
                            symbolSize=5, 
                            symbolBrush=color, 
                            name=label
                        )
                        category_plotted.add(cat)
                    else:
                        self.plot(
                            x_seg, y_seg, 
                            pen=self.pen, 
                            symbolSize=5, 
                            symbol='o', 
                            symbolBrush=color
                        )
                    
                    if previous_end is not None:
                        self.plot(
                            [previous_end[0], x_seg[0]],
                            [previous_end[1], y_seg[0]],
                            pen=self.pen
                        )
                    previous_end = (x_seg[-1], y_seg[-1])
                except Exception as e:
                    logger.error(f"Error plotting segment for category {cat}: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"Error in _plot_segments: {str(e)}")
            raise

def main() -> None:
    """Set up and run the experiment monitor applet."""
    try:
        applet = SimpleApplet(ExperimentMonitor)
        
        # Add datasets
        applet.add_dataset("y", "Y values")
        applet.add_dataset("y_err", "Y values uncertainty", required=False)
        applet.add_dataset("x", "X values", required=False)
        applet.add_dataset("fit", "The fitted values", required=False)
        applet.add_dataset("pos", "position of the data point", required=False)

        # Add command line arguments
        applet.argparser.add_argument("--xmin", type=float, default=0,
                                    help="Min value of the x axis")
        applet.argparser.add_argument("--xmax", type=float, default=None,
                                    help="Max value of the x axis")
        applet.argparser.add_argument("--ymin", type=float, default=0,
                                    help="Min value of the y axis")
        applet.argparser.add_argument("--ymax", type=float, default=None,
                                    help="Max value of the y axis")
        applet.argparser.add_argument("--pen", type=bool, default=False,
                                    help="Set to true to draw lines between points.")
        applet.argparser.add_argument("--exp-label", type=str, default=None)
        
        applet.run()
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main()
