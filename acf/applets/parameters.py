import numpy as np
import PyQt5
from PyQt5.QtWidgets import QMainWindow, QTreeView, QAbstractItemView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import PyQt5.Qt as Qt
from artiq.applets.simple import SimpleApplet
from artiq.language import units

#from acf.parameter_manager import ParameterManager


class ParameterWidget(QMainWindow):

    def __init__(self, args, req):
        super().__init__()
        self.setup()

        self.req = req

        # Set this to true before updating item text from dataset to avoid triggering
        # dataset update from item changed event
        self.updating_item_from_datasets = False

        # Same but the opposite direction
        self.updating_datasets_from_item = False

    def setup(self):

        # Create the Tree View as the main display for the widget
        self.view = QTreeView()
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setCentralWidget(self.view)

        # Create the item model and import data from the parameter manager
        self.model = QStandardItemModel(0, 2)
        self.model.itemChanged.connect(self.param_changed)
        self.model.setHorizontalHeaderLabels(["Parameter", "Value"])
        """for i in range(5):
            #item = QStandardItem()
            #item.insertRow(0, [QStandardItem("hi"), QStandardItem("there")])
            #item.setText([f"hi {i}", "lol"])
            #item.setData(["hi", "there"])
            itemitem = QStandardItem(f"value {i}")
            itemitem.setData(f"item parameter value {i}")
            items = [QStandardItem("name"), itemitem]
            self.model.appendRow(items)
        for i in range(5):
            nameitem = QStandardItem("name")
            nameitem.setEditable(False)
            subnameitem = QStandardItem("subname")
            subnameitem.setEditable(False)
            nameitem.appendRow([subnameitem, QStandardItem(f"subvalue {2*i}")])
            self.model.appendRow(nameitem)"""
        #parent_item.appendRow(item)

        #self.model = QStandardItemModel()
        #parentItem = self.model.invisibleRootItem()
        #for i in range(0, 4):
            #item = QStandardItem("hi hi")
            #parentItem.appendRow(item)
            #parentItem = item

        self.view.setModel(self.model)
        #self.view.expandAll()
        #for column in range(self.model.columnCount()):
            #self.view.resizeColumnToContents(column)

        #self.update_actions()

    def param_changed(self, item):

        # Don't update artiq dataset if the item was updated to reflect a change in the
        # artiq dataset
        if self.updating_item_from_datasets:
            self.updating_item_from_datasets = False
            return

        param_name = item.data()
        dataset_name = f"__param__{param_name}"

        value, unit_str = self.get_value_from_display_text(item.text())
        self.updating_datasets_from_item = True
        self.req.set_dataset(dataset_name, value, unit=unit_str)

    def value_with_unit(self, value, unit_str):
        """Given an absolute value, return it in units described by unit_str.

        Ex. if `value` is 200,000,000 and unit_str is "MHz", this would return 200.

        Args:
            value (float): The value to convert.
            unit_str (str): The artiq unit string.

        Returns: The converted value with given units.
        """
        scale = getattr(units, unit_str)
        return value / scale

    def data_changed(self, value, metadata, persist, mod_buffer):

        # Don't update value if the dataset update was from a manual parameter update
        # This techinically causes a race condition if the flag is set and then another
        # dataset is changed before the dataset changed for this parameter is handled here,
        # but this is unlikely enough that this should be fine.
        if self.updating_datasets_from_item:
            self.updating_datasets_from_item = False
            return

        mod = mod_buffer[0]
        print(mod)

        if mod["action"] == "init":
            # Initialize the table
            print(value)
            for dataset_name, dataset_value in value.items():
                # TODO Replace __param__ with dataset_prefix from ParameterManger
                # See lower TODO
                param_name = dataset_name.removeprefix("__param__")
                param_unit = mod["struct"][dataset_name][2].get("unit", None)
                self.add_param_to_model(param_name, dataset_value, unit_str=param_unit)

        elif mod["action"] == "setitem":
            param_name = mod["key"].removeprefix("__param__")
            param_value = mod["value"][1]
            param_unit = mod["value"][2].get("unit", None)

            # Find item who's data matches the parameter name
            item = self.find_matching_item(param_name)

            if item is None:
                self.add_param_to_model(param_name, param_value, unit_str=param_unit)
            else:
                self.updating_item_from_datasets = True
                item.setText(self.make_value_display_text(param_value, param_unit))

        elif mod["action"] == "delitem":
            param_name = mod["key"].removeprefix("__param__")
            item = self.find_matching_item(param_name)
            if item is not None:
                parent = item.parent()
                if parent is None:
                    # Top level elements have parent as None, so remove from the model
                    self.model.takeRow(item.row())
                else:
                    item.parent().takeRow(item.row())

    def find_matching_item(self, data):
        """Find the first item in the model tree who's item data matches `data`.

        Since parameters can be nested to arbitraty levels, this works recursively.

        Args:
            data (?): The data to compare to model leaves.

        Returns: The first item that matches, or None if there are no matches.
        """

        def recurse(item):

            for row in range(item.rowCount()):

                if item.child(row, 1) is None:
                    recurse_result = recurse(item.child(row, 0))
                    if recurse_result is None:
                        continue
                    else:
                        return recurse_result

                elif item.child(row, 1).data() == data:
                    return item.child(row, 1)

                else:
                    continue

            return None

        return recurse(self.model.invisibleRootItem())    
    
    def make_value_display_text(self, value, unit_str=None):
        """Create the display text for a value and unit.

        Args:
            value (?): The value being displayed.
            unit_str (str): The string units. Should be an artiq unit.

        Returns: String representing the value and units.
        """
        if unit_str is not None:
            return f"{self.value_with_unit(value, unit_str)} {unit_str}"
        else:
            return str(value)

    def get_value_from_display_text(self, display_text):
        """Get the full value represented by display text.

        Args:
            display_text (str): The text displaying a parameter.

        Returns: (value, unit_str) The value and unit string represented by the text.
        """
        split = display_text.split()
        value_in_units = split[0]
        if value_in_units.replace(".", "").isnumeric():
            value_in_units = float(value_in_units)

        if len(split) == 1:
            return value_in_units, None
        else:
            unit_str = split[1]
            scale = getattr(units, unit_str)
            return value_in_units * scale, unit_str

    def add_param_to_model(self, name, value, unit_str=None):
        """Add a parameter to the model to be displayed.

        Args:
            name (str): The name of the parameter Should not include the parameter manager prefix.
            value (?): The value of the parameter.
            unit_str (str): String representing the artiq units of the value.
        """
        levels = name.split("/")
        value_item = QStandardItem(self.make_value_display_text(value, unit_str))
        value_item.setData(name)
        print()
        print(f"Adding param: '{name}'")

        if len(levels) == 1:
            name_item = QStandardItem(name)
            name_item.setEditable(False)
            self.model.appendRow([name_item, value_item])

        else:

            # Parameter has sublevels, so nest them in the model

            # First find the level (where in a/b/c) the parameter name is different
            # from a tree that already exists
            #curr_level = 1
            #while levels[curr_level] == curr_existing

            curr_level = 0
            curr_item = self.model.invisibleRootItem()
            while True:
                """print("Item text")
                print(curr_item.text())
                if not curr_item.hasChildren():
                    break"""

                print(f"rowCount: {curr_item.rowCount()}")
                found_item = False
                for row in range(curr_item.rowCount()):
                    item = curr_item.child(row, 0)
                    print(f"item text: {item.text()}")
                    if item.text() == levels[curr_level]:
                        curr_level += 1
                        curr_item = item
                        found_item = True
                        break

                # If we didn't find the item, exit the while loop
                if not found_item:
                    break

            # curr_level is now set to the level in the nested parameter name that does
            # not match an existing nested parameter in the model
            print("curr_level")
            print(curr_level)

            # Start inserting where the parameter nested structure differed
            previous_item = curr_item
            for level_name in levels[curr_level:-1]:
                level_item = QStandardItem(level_name)
                level_item.setEditable(False)
                previous_item.appendRow(level_item)
                previous_item = level_item

            last_name_item = QStandardItem(levels[-1])
            last_name_item.setEditable(False)
            previous_item.appendRow([last_name_item, value_item])


            """top_level_item = QStandardItem(levels[0])
            previous_item = top_level_item
            for level_name in levels[1:-1]:
                level_item = QStandardItem(level_name)
                level_item.setEditable(False)
                previous_item.appendRow(level_item)
                previous_item = level_item
            last_name_item = QStandardItem(levels[-1])
            last_name_item.setEditable(False)
            previous_item.appendRow([last_name_item, value_item])
            self.model.appendRow(top_level_item)"""


class GetParametersApplet(SimpleApplet):
    """A simple applet that adds __param__ to dataset prefixes so that it gets
    updates to all the datasets being used as system parameters. Note that this
    prefix __param__ comes from ParameterManager in acf."""

    def args_init(self):
        super().args_init()
        self.dataset_prefixes.append("__param__")

        # TODO: Figure out how to import ACF so the above line can be replaced with this
        # so that dataset_prefix is only defined in 1 location
        #self.dataset_prefixes.append(ParameterManager.dataset_prefix)

def main():
    applet = GetParametersApplet(ParameterWidget)
    applet.run()


if __name__ == "__main__":
    main()
