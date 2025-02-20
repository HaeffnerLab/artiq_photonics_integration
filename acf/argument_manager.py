"""The purpose of this class is to provide a location for the experimentor to
define common arguments for scripts in one place."""

from artiq.language.environment import NumberValue

from acf.parameter_manager import ParameterManager

class ArgumentManager:

	def __init__(self):
		self.exp = None
		self.param_mgr = None
		self.arguments = {}

	def add_argument(self,
					name,
					default_value=None,
					default_parameter=None,
					param_mod_func=None,
					unit="",
					min=None,
					max=None,
					tooltip=""):
		"""Add a NumberValue argument to the list of saved arguments.

		Either `value` or `parameter` must be provided.

		Args:
			name (str): The name of the argument.
			default_value (Artiq Value): The default value of the argument.
			default_param (str): The name of the parameter to use as the default value.
			param_mod_func (Function): A function to apply to the parameter that
				returns the value for the argument.
			tooltip (str): A tooltip to set on the argument.
		"""
		if default_value is None and default_parameter is None:
			raise RuntimeError("default_value or default_parameter must be given.")

		if default_value is not None and default_parameter is not None:
			raise RuntimeError("Only one of default_value and default_parameter should be given.")

		if param_mod_func is not None and default_parameter is None:
			raise RuntimeError("param_mod_func given but no default_parameter provided.")

		self.arguments[name] = {
			"default_value": default_value,
			"default_parameter": default_parameter,
			"param_mod_func": param_mod_func,
			"unit": unit,
			"min": min,
			"max": max,
			"tooltip": tooltip,
		}

	def set_arguments(self, names):
		"""Set a list of arguments on the current experiment.

		Args:
			names (List[str]): List of names of desired arguments.
		"""
		for name in names:
			self.set_argument(name)

	def set_argument(self, name, default_value=None):
		"""Set an argument on the current experiment.

		Args:
			name (str): The name of the argument.
			default_value (Artiq Value): Set this to override the defined default value / parameter.
		"""
		if name not in self.arguments:
			raise RuntimeError(f"Argument '{name}' not in saved arguments.")

		saved_arg = self.arguments[name]
		if default_value is not None:
			default = default_value
		elif saved_arg["default_value"] is not None:
			default = saved_arg["default_value"]
		elif saved_arg["default_parameter"] is not None:
			param_value = self.param_mgr.get_param(saved_arg["default_parameter"])

			if saved_arg["param_mod_func"] is not None:
				default = saved_arg["param_mod_func"](param_value)
			else:
				default = param_value

		self.exp.setattr_argument(
			name,
			NumberValue(
				default=default,
				unit=saved_arg["unit"],
				min=saved_arg["min"],
				max=saved_arg["max"]
			),
			tooltip=saved_arg["tooltip"]
		)

	def initialize(self, exp):
		"""Initialize the argument manager with the calling experiment class."""
		self.exp = exp
		self.param_mgr = ParameterManager(exp)
