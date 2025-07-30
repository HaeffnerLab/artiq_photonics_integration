"""
Parameter management applet for ARTIQ experiments.
This module provides a GUI widget for displaying and editing experiment parameters,
with support for hierarchical parameter organization and unit conversion.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import PyQt5
from PyQt5.QtWidgets import QMainWindow, QTreeView, QAbstractItemView, QPushButton, QHBoxLayout, QWidget, QVBoxLayout
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QMimeData
import PyQt5.Qt as Qt
from artiq.applets.simple import SimpleApplet
from artiq.language import units

#from acf.parameter_manager import ParameterManager


# Constants
PARAM_PREFIX = "__param__"
MODEL_COLUMNS = ["Parameter", "Value", "Actions"]


class ParameterItemModel(QStandardItemModel):
    """Custom model that supports parameter reordering."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalHeaderLabels(MODEL_COLUMNS)
        
    def move_item_up(self, item):
        """Move an item up in its parent's list."""
        parent = item.parent()
        if parent is None:
            parent = self.invisibleRootItem()
            
        row = item.row()
        if row > 0:
            # Swap with the item above
            parent.takeRow(row)
            parent.insertRow(row - 1, item)
            return True
        return False
        
    def move_item_down(self, item):
        """Move an item down in its parent's list."""
        parent = item.parent()
        if parent is None:
            parent = self.invisibleRootItem()
            
        row = item.row()
        if row < parent.rowCount() - 1:
            # Swap with the item below
            parent.takeRow(row)
            parent.insertRow(row + 1, item)
            return True
        return False


class ParameterWidget(QMainWindow):
    """A widget for displaying and editing experiment parameters.
    
    This widget provides a tree view interface for parameters, supporting:
    - Multi-level hierarchical parameter organization
    - Unit conversion and display
    - Two-way synchronization with ARTIQ datasets
    - Parameter value editing
    """

    def __init__(self, args: Any, req: Any) -> None:
        """Initialize the parameter widget.
        
        Args:
            args: Command line arguments
            req: Request object for dataset operations
        """
        super().__init__()
        self.setup()
        self.req = req
        
        # Flags to prevent update loops
        self.updating_item_from_datasets = False
        self.updating_datasets_from_item = False
        
        # Track existing parameters to handle name changes
        self.param_items = {}  # Maps parameter names to their UI items
        # Track group items to handle empty groups
        self.group_items = {}  # Maps group paths to their UI items

    def setup(self) -> None:
        """Set up the widget's UI components and data model."""
        # Create and configure the tree view
        self.view = QTreeView()
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setCentralWidget(self.view)

        # Create and configure the item model
        self.model = ParameterItemModel()
        self.model.itemChanged.connect(self.param_changed)
        self.view.setModel(self.model)
        
        # Set column widths
        self.view.setColumnWidth(0, 200)  # Parameter name
        self.view.setColumnWidth(1, 250)  # Value
        self.view.setColumnWidth(2, 20)  # Actions - wider than the buttons

    def handle_rows_moved(self, parent: QStandardItem, start: int, end: int, destination: QStandardItem, row: int) -> None:
        """Handle rows being moved via drag and drop.
        
        This method updates the tracking dictionaries when items are moved.
        
        Args:
            parent: The parent item of the moved rows
            start: The starting row index
            end: The ending row index
            destination: The destination parent item
            row: The destination row index
        """
        # This is a UI-only operation, no need to update the dataset
        # Just update our tracking dictionaries if needed
        
        # Get the moved item
        moved_item = parent.child(start, 0)
        if moved_item is None:
            return
            
        # If it's a parameter (has a value item)
        if parent.child(start, 1) is not None:
            param_name = parent.child(start, 1).data()
            if param_name in self.param_items:
                # Update the tracking
                self.param_items[param_name] = parent.child(start, 1)
        
        # If it's a group
        elif moved_item.hasChildren():
            group_path = self._get_item_path(moved_item)
            if group_path in self.group_items:
                # Update the tracking
                self.group_items[group_path] = moved_item
                
        # Ensure the model is updated
        self.model.layoutChanged.emit()

    def param_changed(self, item: QStandardItem) -> None:
        """Handle parameter value changes from the UI.
        
        Args:
            item: The item that was changed
        """
        if self.updating_item_from_datasets:
            self.updating_item_from_datasets = False
            return

        param_name = item.data()
        dataset_name = f"{PARAM_PREFIX}{param_name}"

        value, unit_str = self.get_value_from_display_text(item.text())
        self.updating_datasets_from_item = True
        self.req.set_dataset(dataset_name, value, unit=unit_str)

    def value_with_unit(self, value: float, unit_str: str) -> float:
        """Convert a value to the specified units.
        
        Args:
            value: The value to convert
            unit_str: The target unit string (e.g., "MHz")
            
        Returns:
            The converted value
        """
        if unit_str == "": 
            scale=1
        else:
            scale = getattr(units, unit_str)
        return value / scale

    def data_changed(self, value: Dict, metadata: Any, persist: bool, mod_buffer: List[Dict]) -> None:
        """Handle dataset changes from ARTIQ.
        
        Args:
            value: The new dataset values
            metadata: Dataset metadata
            persist: Whether to persist the changes
            mod_buffer: List of modifications
        """
        if self.updating_datasets_from_item:
            self.updating_datasets_from_item = False
            return

        mod = mod_buffer[0]

        if mod["action"] == "init":
            # Initialize the parameter tree
            self.param_items.clear()  # Clear existing parameter tracking
            self.group_items.clear()  # Clear existing group tracking
            for dataset_name, dataset_value in value.items():
                param_name = dataset_name.removeprefix(PARAM_PREFIX)
                param_unit = mod["struct"][dataset_name][2].get("unit", None)
                self.add_param_to_model(param_name, dataset_value, unit_str=param_unit)

        elif mod["action"] == "setitem":
            param_name = mod["key"].removeprefix(PARAM_PREFIX)
            param_value = mod["value"][1]
            param_unit = mod["value"][2].get("unit", None)

            # Check if this is a new parameter or an existing one
            if param_name in self.param_items:
                # Update existing parameter
                item = self.param_items[param_name]
                self.updating_item_from_datasets = True
                item.setText(self.make_value_display_text(param_value, param_unit))
            else:
                # Add new parameter
                self.add_param_to_model(param_name, param_value, unit_str=param_unit)

        elif mod["action"] == "delitem":
            param_name = mod["key"].removeprefix(PARAM_PREFIX)
            if param_name in self.param_items:
                item = self.param_items[param_name]
                parent = item.parent()
                if parent is None:
                    self.model.takeRow(item.row())
                else:
                    item.parent().takeRow(item.row())
                del self.param_items[param_name]
                
                # Check if we need to remove empty parent groups
                self.cleanup_empty_groups()

    def cleanup_empty_groups(self) -> None:
        """Remove any empty parent groups from the model."""
        # Start from the root and work down
        root = self.model.invisibleRootItem()
        self._cleanup_empty_groups_recursive(root)
    
    def _cleanup_empty_groups_recursive(self, parent: QStandardItem) -> None:
        """Recursively remove empty groups.
        
        Args:
            parent: The parent item to check
        """
        # Process children from bottom to top to avoid index issues
        for row in range(parent.rowCount() - 1, -1, -1):
            child = parent.child(row, 0)
            
            # If this is a group (has children)
            if child.hasChildren():
                # Recursively clean up its children first
                self._cleanup_empty_groups_recursive(child)
                
                # If the group is now empty (no children or only empty children)
                if child.rowCount() == 0:
                    # Remove the group
                    parent.takeRow(row)
                    
                    # Remove from tracking
                    group_path = self._get_item_path(child)
                    if group_path in self.group_items:
                        del self.group_items[group_path]
    
    def _get_item_path(self, item: QStandardItem) -> str:
        """Get the full path of an item in the tree.
        
        Args:
            item: The item to get the path for
            
        Returns:
            The full path as a string with '/' separators
        """
        path = [item.text()]
        parent = item.parent()
        
        while parent is not None and parent != self.model.invisibleRootItem():
            path.insert(0, parent.text())
            parent = parent.parent()
            
        return "/".join(path)

    def find_matching_item(self, data: str) -> Optional[QStandardItem]:
        """Find an item in the model tree matching the given data.
        
        Args:
            data: The data to match against
            
        Returns:
            The matching item or None if not found
        """
        # First check if we have this parameter tracked
        if data in self.param_items:
            return self.param_items[data]
            
        # If not found in our tracking, search the tree
        def recurse(item: QStandardItem) -> Optional[QStandardItem]:
            for row in range(item.rowCount()):
                if item.child(row, 1) is None:
                    recurse_result = recurse(item.child(row, 0))
                    if recurse_result is not None:
                        return recurse_result
                elif item.child(row, 1).data() == data:
                    result = item.child(row, 1)
                    # Add to our tracking
                    self.param_items[data] = result
                    return result
            return None

        return recurse(self.model.invisibleRootItem())

    def make_value_display_text(self, value: Any, unit_str: Optional[str] = None) -> str:
        """Create display text for a value with optional units.
        
        Args:
            value: The value to display
            unit_str: Optional unit string
            
        Returns:
            Formatted display text
        """
        if unit_str is not None:
            return f"{self.value_with_unit(value, unit_str)} {unit_str}"
        return str(value)

    def get_value_from_display_text(self, display_text: str) -> Tuple[Union[float, str], Optional[str]]:
        """Parse a display text into a value and unit.
        
        Args:
            display_text: The text to parse
            
        Returns:
            Tuple of (value, unit_str)
        """
        split = display_text.split()
        value_in_units = split[0]
        if value_in_units.replace(".", "").isnumeric():
            value_in_units = float(value_in_units)

        if len(split) == 1:
            return value_in_units, None
        
        unit_str = split[1]
        scale = getattr(units, unit_str)
        return value_in_units * scale, unit_str

    def add_param_to_model(self, name: str, value: Any, unit_str: Optional[str] = None) -> None:
        """Add a parameter to the model tree.
        
        Args:
            name: Parameter name (can include multiple levels with '/')
            value: Parameter value
            unit_str: Optional unit string
        """
        levels = name.split("/")
        value_item = QStandardItem(self.make_value_display_text(value, unit_str))
        value_item.setData(name)
        value_item.setEditable(True)

        if len(levels) == 1:
            # Single level parameter
            name_item = QStandardItem(name)
            name_item.setEditable(False)
            
            # Create action buttons
            action_item = QStandardItem("")
            action_item.setEditable(False)
            
            # Add the row
            self.model.appendRow([name_item, value_item, action_item])
            
            # Track this parameter
            self.param_items[name] = value_item
            
            # Create and connect the buttons
            self._create_action_buttons(name_item)
        else:
            # Multi-level parameter
            curr_item = self.model.invisibleRootItem()
            group_path = ""
            
            # Create or navigate through the hierarchy
            for i, level in enumerate(levels[:-1]):  # Process all but the last level
                found = False
                group_path = "/".join(levels[:i+1]) if i > 0 else level
                
                # Look for existing level
                for row in range(curr_item.rowCount()):
                    if curr_item.child(row, 0).text() == level:
                        curr_item = curr_item.child(row, 0)
                        found = True
                        break
                
                # Create new level if not found
                if not found:
                    new_item = QStandardItem(level)
                    new_item.setEditable(False)
                    action_item = QStandardItem("")
                    action_item.setEditable(False)
                    curr_item.appendRow([new_item, QStandardItem(""), action_item])
                    curr_item = new_item
                    # Track this group
                    self.group_items[group_path] = new_item
                    # Create and connect the buttons for the group
                    self._create_action_buttons(new_item)
            
            # Add the final parameter
            name_item = QStandardItem(levels[-1])
            name_item.setEditable(False)
            
            # Create action buttons
            action_item = QStandardItem("")
            action_item.setEditable(False)
            
            # Add the row
            curr_item.appendRow([name_item, value_item, action_item])
            
            # Track this parameter
            self.param_items[name] = value_item
            
            # Create and connect the buttons
            self._create_action_buttons(name_item)
            
    def _create_action_buttons(self, name_item: QStandardItem) -> None:
        """Create up/down buttons for a parameter or group.
        
        Args:
            name_item: The name item for the parameter or group
        """
        try:
            # Get the parent item
            parent = name_item.parent()
            if parent is None:
                parent = self.model.invisibleRootItem()
                
            # Get the row
            row = name_item.row()
            
            # Create a widget to hold the buttons
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(0, 0, 0, 0)
            
            # Create up button
            up_button = QPushButton("↑")
            up_button.setFixedSize(20, 20)
            up_button.clicked.connect(lambda: self._move_item_up(name_item))
            button_layout.addWidget(up_button)
            
            # Create down button
            down_button = QPushButton("↓")
            down_button.setFixedSize(20, 20)
            down_button.clicked.connect(lambda: self._move_item_down(name_item))
            button_layout.addWidget(down_button)
            
            # Make sure the action column exists
            if parent.child(row, 2) is None:
                action_item = QStandardItem("")
                action_item.setEditable(False)
                parent.setChild(row, 2, action_item)
            
            # Set the widget in the action column
            self.view.setIndexWidget(self.model.indexFromItem(parent.child(row, 2)), button_widget)
        except Exception as e:
            print(f"Error creating action buttons: {e}")
            # Continue without buttons if there's an error
            
    def _move_item_up(self, name_item: QStandardItem) -> None:
        """Move a parameter or group up in its parent's list.
        
        Args:
            name_item: The name item for the parameter or group
        """
        # Get the parent item
        parent = name_item.parent()
        if parent is None:
            parent = self.model.invisibleRootItem()
            
        # Get the row
        row = name_item.row()
        
        # Move the item up
        if row > 0:
            # Get all items in the row
            name_item = parent.child(row, 0)
            value_item = parent.child(row, 1)
            action_item = parent.child(row, 2)
            
            # Remove the row
            parent.takeRow(row)
            
            # Insert the row above
            parent.insertRow(row - 1, [name_item, value_item, action_item])
            
            # Recreate the action buttons
            self._create_action_buttons(name_item)
            
            # Update the model
            self.model.layoutChanged.emit()
            
    def _move_item_down(self, name_item: QStandardItem) -> None:
        """Move a parameter or group down in its parent's list.
        
        Args:
            name_item: The name item for the parameter or group
        """
        # Get the parent item
        parent = name_item.parent()
        if parent is None:
            parent = self.model.invisibleRootItem()
            
        # Get the row
        row = name_item.row()
        
        # Move the item down
        if row < parent.rowCount() - 1:
            # Get all items in the row
            name_item = parent.child(row, 0)
            value_item = parent.child(row, 1)
            action_item = parent.child(row, 2)
            
            # Remove the row
            parent.takeRow(row)
            
            # Insert the row below
            parent.insertRow(row + 1, [name_item, value_item, action_item])
            
            # Recreate the action buttons
            self._create_action_buttons(name_item)
            
            # Update the model
            self.model.layoutChanged.emit()


class GetParametersApplet(SimpleApplet):
    """Applet for parameter management in ARTIQ experiments."""
    
    def args_init(self) -> None:
        """Initialize command line arguments."""
        super().args_init()
        self.dataset_prefixes.append(PARAM_PREFIX)

        # TODO: Figure out how to import ACF so the above line can be replaced with this
        # so that dataset_prefix is only defined in 1 location
        #self.dataset_prefixes.append(ParameterManager.dataset_prefix)

def main():
    applet = GetParametersApplet(ParameterWidget)
    applet.run()


if __name__ == "__main__":
    main()
