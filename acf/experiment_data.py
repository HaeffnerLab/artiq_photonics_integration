"""This class manages data collected during an experiment.

It uses artiq's datasets to implement data storage.
"""

import numpy as np
from datetime import datetime

class ExperimentData:

    def __init__(self, exp):
        """Initialize the experiment.

        Args:
            exp (EnvExperiment): The calling experiment class.
        """
        self.exp = exp

        self.ccb = self.exp.get_device("ccb")
        self.exp.setattr_device("scheduler")
        self.scheduler = self.exp.scheduler

        # Create path from results folder to data that will be saved for this experiment
        self.exp_label = None

        # Only create an experiment label if the RID is defined
        if hasattr(self.exp.scheduler, "rid"):
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            hour_str = now.strftime("%H")
            rid = self.exp.scheduler.rid
            self.exp_label = f"{date_str}/{hour_str}/{rid}"

        # Dictionary to keep track of dataset metadata
        # Keys are dataset names, values are dictionaries of
        # metadata related to the dataset.
        #   curr_loc: The next spot data will be input to the dataset
        #   broadcast: True if the data is being broadcasted, False otherwise.
        # datasets = {
        #               "pmt_counts": {
        #                   curr_loc: 4,
        #                   broadcast: True
        #               },
        #               "frequency": {
        #                   curr_loc: 4,
        #                   broadcast: True
        #               }
        #            }
        self.datasets = {}

    def set_list_dataset(self, name, length, broadcast=False):
        """Add a list dataset to the experiment.

        Args:
            name (str): The name of the list.
            length (int): Length of the list.
            broadcast (int): Set to true to broadcast the dataset. Required for live plotting.
        """
        self.exp.set_dataset(name, np.full(length, np.nan), broadcast=broadcast)
        self.datasets[name] = { "curr_loc": 0, "broadcast": broadcast }
    
    def set_nd_dataset(self, name, shape, broadcast=False):
        """Add a n-dimensional dataset to the experiment.

        Args:
            name (str): The name of the list.
            shape (array[int]): Array of lengths of axes. Ex. [50, 10, 5]
            broadcast (int): Set to true to broadcast the dataset. Required for live plotting.
        """
        self.exp.set_dataset(name, np.full(shape, np.nan), broadcast=broadcast)
        self.datasets[name] = { 
            "curr_loc": 0, 
            "broadcast": broadcast 
        }
        # TODO: How will current_loc work for this? Column/row major ordering?

    def append_list_dataset(self, name, data):
        """Append a datapoint to a list.

        Args:
            name (str): The name of the list.
            data (?): The datapoint to add to the list. Must be the
                      same type as the list was initialized with.
        """
        if name not in self.datasets:
            raise RuntimeError(f"Dataset {name} has not been created.")

        self.exp.mutate_dataset(name, self.datasets[name]["curr_loc"], data)
        self.datasets[name]["curr_loc"] += 1
    
    def insert_nd_dataset(self, name, index, data):
        """Insert a single value into a n-dimensional dataset.
        
        Args:
            name (str): The name of the dataset.
            index (array[int]): The index at which to insert the data. The length
                of this index should match the shape with which the dataset was
                defined. Ex. for a dataset with shape [50, 10, 5], this index could
                be [10, 0, 0], but not [10, 0] (not enough indices) or [10, 0, 10]
                (the last index would be out of range). (Issue !!! This is not verified API)
            data (?): The datapoint to insert.
        """
        if type(index) in [int, np.int32]: #1D dataset insertion: verified! 
            index_mut = index
        elif type(index) is list:
            #index_mut = tuple(index)
            assert len(index) == 2, "Only 2D dataset insertion is supported for now"

            index_mut = ((index[0],index[0]+1),(index[1],index[1]+1))
        else:
            raise RuntimeError("index must be int or list.")
        
        self.exp.mutate_dataset(name, index_mut, data)
    '''
    def enable_experiment_monitor(self,
            y_data_name,
            x_data_name=None,
            xmin=None,
            xmax=None,
            ymin=None,
            ymax=None,
            pen=None):
        """Start the Experiment Monitor applet.

        Args:
            y_data_name (str): The name of the dataset for the y-axis.
            x_data_name (str): The name of the corresponding data for the  x-axis. Not required.
            xmin (float): Minimum x value.
            xmax (float): Maximum x value.
            ymin (float): Minimum y value.
            ymax (float): Maximum y value.
            pen (bool): Set to True to enable lines between sequential points.
        """
        if not self.datasets[y_data_name]["broadcast"]:
            raise RuntimeError(f"Dataset {y_data_name} must have broadcast=True to display.")

        if x_data_name is not None and not self.datasets[x_data_name]["broadcast"]:
            raise RuntimeError(f"Dataset {x_data_name} must have broadcast=True to display.")

        x_data_applet_str = ""
        if x_data_name is not None:
            x_data_applet_str = f" --x {x_data_name}"

        bounds_str = ""
        if xmin is not None:
            bounds_str += f" --xmin {xmin}"
        if xmax is not None:
            bounds_str += f" --xmax {xmax}"
        if ymin is not None:
            bounds_str += f" --ymin {ymin}"
        if ymax is not None:
            bounds_str += f" --ymax {ymax}"

        if pen is not None:
            bounds_str += f" --pen {pen}"
        
        if self.exp_label is not None:
            bounds_str += f" --exp-label {self.exp_label}"

        applet_cmd = (
                "$python acf/applets/experiment_monitor.py "
               f"{y_data_name}{x_data_applet_str}{bounds_str}"
        )
        self.ccb.issue("create_applet", "Experiment Monitor", applet_cmd)
'''


    def enable_experiment_monitor(self,
            y_data_name,
            x_data_name=None,
            fit_data_name=None,
            pos_data_name=None,
            xmin=None,
            xmax=None,
            ymin=None,
            ymax=None,
            pen=None):
        """Start the Experiment Monitor applet.

        Args:
            y_data_name (str): The name of the dataset for the y-axis.
            x_data_name (str): The name of the corresponding data for the  x-axis. Not required.
            fit_data_name (str): The name of the corresponding data for the fitting.  Not required.
            xmin (float): Minimum x value.
            xmax (float): Maximum x value.
            ymin (float): Minimum y value.
            ymax (float): Maximum y value.
            pen (bool): Set to True to enable lines between sequential points.
        """
        if not self.datasets[y_data_name]["broadcast"]:
            raise RuntimeError(f"Dataset {y_data_name} must have broadcast=True to display.")

        if x_data_name is not None and not self.datasets[x_data_name]["broadcast"]:
            raise RuntimeError(f"Dataset {x_data_name} must have broadcast=True to display.")

        x_data_applet_str = ""
        if x_data_name is not None:
            x_data_applet_str = f" --x {x_data_name}"

        fit_data_applet_str = ""
        if fit_data_name is not None:
            fit_data_applet_str = f" --fit {fit_data_name}"
        
        #Ca 44 exp
        pos_data_applet_str = ""
        if pos_data_name is not None:
            pos_data_applet_str = f" --pos {pos_data_name}"


        bounds_str = ""
        if xmin is not None:
            bounds_str += f" --xmin {xmin}"
        if xmax is not None:
            bounds_str += f" --xmax {xmax}"
        if ymin is not None:
            bounds_str += f" --ymin {ymin}"
        if ymax is not None:
            bounds_str += f" --ymax {ymax}"

        if pen is not None:
            bounds_str += f" --pen {pen}"
        
        if self.exp_label is not None:
            bounds_str += f" --exp-label {self.exp_label}"

        applet_cmd = (
                "$python acf/applets/experiment_monitor.py "
               f"{y_data_name}{x_data_applet_str}{bounds_str}{fit_data_applet_str}{pos_data_applet_str}"
        )
        self.ccb.issue("create_applet", "Experiment Monitor", applet_cmd)


