# ACF

Artiq Control Framework (ACF) is a framework for writing generic experimental code for the Artiq hardware system. The main purpose is to add some basic utility on top of Artiq's base capabilities to avoid boilerplate-style code and overall make common experimental workflows easy to implement. It allows users to read and write system parameters, label particular hardware devices with meaningful names, plot data live during an experiment, define and reuse subsequences, and more.

## Design Principles
Here we list some of the design principles that are kept in mind while developing this code.

### Never change Artiq source code
Artiq source code should never be changed. It would add another repository to keep track of, making managing the codebase harder. It would require other members of the lab later to potentially make changes inside of Artiq's code base as well, which can be difficult and time consuming. Users should not need to understand the internal's of Artiq's code in order to use it. Finally, if newer Artiq versions are released, they are unusable without taking all the edited code and patching it onto the newer version of Artiq, potentially creating merge conflicts and again requiring users to deal with Artiq internals.

### Separation between stored parameters and experiment parameters
Stored parameters are parameters that have been stored for use in multiple experiments. For example, after running a calibration stored parameters may include resonant frequencies, cooling frequencies, pi-times, etc. Experiment parameters are the parameters being currently used in an experiment. For example, an 866 frequency scan will use the 397 cooling frequency parameter, but in this case it is an experiment parameter since it is the version being currently used in an experiment. This principle states that these should be separate, i.e. you can change the stored value without automatically changing the value used in an experiment, and you can change the value used in an experiment without changing the stored value. This is nice because users will want to try different values in experiments without needing to change the known good value in storage. That said, this framework does allow the user to automatically pull stored parameters into experiments should that be the desired behavior.

### Artiq primitives
Base features of Artiq should be used as much as possible. For example, for storing parameters one should not use some extra external storage, when they can be stored as Artiq datasets with persist=True. Extra GUI features should not be added in external applications, but instead should be implemented as Artiq applets. This principle takes advantage of existing functionality to avoid writing extra code, as well as keeps the codebase in a more cohesive state.

### Never limit base Artiq functionality
A framework is developed in the present, and experiments are run in the future. It is often difficult to predict what will be necessary for experiments, and so this framework attempts to *add* features and *never constrain* the user. Users should be able to take advantage of the framework to simplify code, gain useful features, etc. but there should never be a scenario in which the user wants to implement something that should be possible in Artiq, but is impossible given the fact that they are using this framework. The main maifestation of this principle in this framework is the fact that for creating experiments, one derivces from `ACFExperiment` instead of `EnvExperiment`, but still has access to the standard Artiq `build()` and `run()` functions. Any code that would be placed in these functions if the framework were not being used can still be placed in the same functions and will work like normal.

## Installation
Move into your artiq working directory, i.e. the location that contains `repository`, `device_db.py`, etc.
```bash
cd {your artiq directory}
```

Clone this repository
```bash
git clone [david put in the repository url]
```

Create a folder to hold configuration files
```bash
mkdir acf_config
```

Add the location of the configuration directory to your `.bashrc`
```bash
echo 'export ACF_CONFIG_DIR=path/to/artiq_dir/acf_config' >> ~/.bashrc
```

When you run the artiq master from the artiq working directory, this repository will be accessible to experimental code.

## Usage

### Create an experiment
To create an experiment, copy the following template.
```python
from acf.experiment import ACFExperiment
from acf_sequences.sequences import sequences
from artiq.experiment import *

class MyExperiment(ACFExperiment):

    def build(self):
    	
	# ACF Setup
        self.setup(sequences)

	# Add arguments from parameters
        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("attenuation/397")

	# Call add_arguments_to_gui on sequences whos arguments/parameters should show up in
	# the experiment GUI
        self.seq.doppler_cool.add_arguments_to_gui()

	# Other experiment setup

    @kernel
    def run(self):
    	
	# ACF Setup
        self.setup_run()

	# Experimental code
```

The basic structure of an experiment in this framework is the same as a regular Artiq experiemnt. One creates an experiment class that inherits from `ACFExperiment`, which is a subclass of `EnvExperiment`, along with `build()` and `run()`, which are the same as in normal Artiq experiments.

At the beginning of `build()`, `self.setup(sequences)` is called. This performs the necessary background setup for an experiment such as initializing devices, defining some arguments, and initializing sequences. The `sequences` object must be created in the user's code using a `SequencesContainer` (see more on sequences below). Next, call `add_arg_from_param(param_name)` to create arguments in the GUI for any parameters required by the experiment. The default value for the argument will be pulled from the globally stored parameter, and when running the experiment the user can change the value of the argument independent of the stored parameter. Next, `add_arguments_to_gui()` should be called on any sequences with arguments that the user would like to see in the experiment GUI (again, see more on sequences below). After this, add any other standard Artiq code you would like in the build method, such as `setattr_argument`, or initializing variables used in `run()`.

> [!NOTE]
> Arguments v. Parameters
> Throughout this documentation and codebase, there is a specific destinction between **parameters** and **arguments**. **Arguments** refers to an input value to an experiment that can be changed. When you open an experiment all the arguments are displayed for you to change, as input to the experiment. **Parameters** are stored values that can be written and read by experiments. The function `add_arg_from_param(param_name)` creates an editable **argument** in the GUI from a **parameter** which has been stored.

In `run()`, call `self.setup_run()`. This calls kernal setup required for all scripts, such as `self.core.reset()` and `init()` on all the dds channels`. Now write all of your experimental code, just as you would in artiq. You have access to all the hardware devices through names defined in the hardware setup (see below), as well as to all the arguments defined manually and from parameters.

## Parameters
Parameters are stored values that can be created, read, and written to by experiments, or directly from the Artiq dashboard. Parameters are handled through the `ParameterManager` class. This class uses Artiq datasets to store parameters.

### Naming
Parameters can be named using forward slashes to create a heirarchy, for example `frequency/397_double_pass`. When displayed in the parameters widget, they will be displayed in a tree structure that respects this heirarchy, so `397_double_pass` will be displayed under `frequency`. In scenarios where the parameter name needs to be made into a valid python identifier, all forward slashes are replaced with underscores. In this example the variable containing the value of the parameter would be `frequency_397_double_pass`.

### Using from the Dashboard
To see parameters, add the parameter widget to Artiq. Open the Applets tab in the dashboard, right click and select 'New applet', set the name to 'Parameters', and set the command to `$python acf/applets/parameters.py`. Select the checkbox next to the applet name to display it. Parameters will now show up in a tree structure in this applet.

To edit parameters, double click the value and change it. Make sure that it is a number, optionally followed by a space and a unit. This unit should come from the standard Artiq units, like MHz, dB, etc. At this time you cannot create or delete parameters from the applet.

To create new parameters in the dashboard, use the Datasets tab. Right click in the Datasets tab and select 'New dataset'. For the name, first enter the text __param__, then add the parameter name using forward slashes to define a heirarchy. For example, to define the parameter from above the name would be `__param__frequency/397_double_pass`. Set the value to the desired value, and enter the units if required. Check the box next to 'Persist:' to ensure that the parameter stays between Artiq restarts. Select 'Ok' and the parameter should show up in the parameters applet.

To delete a parameter, delete it from the Datasets tab. Right click and select 'Delete dataset'.

Ideally the parameters applet will gain the ability to create and delete parameters, but at the moment this is not implemented. The `__param__` prefix is used to distinguish parameters from other datasets. Ideally the user should not need to know this fact, but until adding parameters from the applet is supported it is necessary for defining them.

### Using from code
Parameters can be used from the code using the ParameterManager. From code inside an experiment class that subclasses `ACFExperiment`, read a parameter using
```python
self.parameter_manager.get_param(name)
```

Write to a parameter using
```python
self.parameter_manager.set_param(name, value, units=None)
```
Give the name of the parameter, desired value, and optionally a unit string. When providing units, the value should be the full value, for example if setting something to 5 MHz value should be 5000000 and units should be 'MHz'.

## Hardware Setup
When writing experimental code we want to reference hardware devices with meaningful names like `dds_397_dp` instead of `urukul0_ch2`. This is handled by writing a file `hardware.json` in the `acf_config` folder in the following format.

```
{
"ttl": [
  {
    "name": "ttl_pmt_input",
    "channel": 0
  },
  {
    "name": "ttl_awg_trigger",
    "channel": 7
  },
],

"dds": [
  {
    "name": "dds_397_dp",
    "board": 1,
    "channel": 0
  },
  {
    "name": "dds_866_dp",
    "board": 1,
    "channel": 1
  },
]

}
```

In the 'name' fields put a valid python identifier that represents the purpose of the input/output device. In channel and board, put the numbers that correspond to which output on Artiq is used. In experiment classes that inherit from `ACFExperiment`, the hardware devices are automatically made available under the given name (this is why they must be valid python identifiers).

One may wonder why an extra hardware definition file is necessary in addition to the `device_db.py` file. The reason is a mapping between physical hardware devices (ttl0, etc.) and names that describe their use in an experiment. This also could be accomplished just by editing the `device_db.py` file to have more meaningful names. We choose to avoid this method since that file is given by Artiq so along with Artiq source code we avoid editing it.

## Sequences
To build up complicated experiments it is a common strategy to write compact groupings of code that do a predefined task and then compose them to create more complex logic; here we call these sequences. Sequences define their inputs using parameters (from parameter storage) and arguments (inputs that may not have an associated parameter). Sequences may use default values for the inputs, or can be configured to present their parameters as arguments in the experiment GUI.

### Write a sequence
To create a sequence, first create a class that derives from Sequence, using the following template.
```python
from acf.sequence import Sequence

from artiq.experiment import kernel, NumberValue, MHz

class MySequence(Sequence):

    def __init__(self):
        super().__init__()

        self.add_parameter("frequency/397_cooling")
        self.add_parameter("attenuation/397")

        self.add_argument("interesting_arg", NumberValue(default=5*MHz, unit="MHz"))

    @kernel
    def run(self):
        self.sequence(self.frequency_397_cooling, self.attenuation_397, self.interesting_arg)

    @kernel
    def sequence(self, freq_397_cooling, freq_866_cooling, interesting_arg):
    	pass
```

First create a class inheriting from Sequence. The first line should be `super().__init__()` which performs necessary setup for sequences. Next, call `add_parameter(name)` with the parameters that should be used as inputs to the sequence. Call `add_argument(name, processor)` to add inputs that do not have an associated parameter.

Implement the `sequence()` function. This should be a kernel function containing the Artiq code that runs the sequence. Its inputs should be the values required to call it, aligning with the parameters and arguments defined in `__init__()`. Next, fill in `run()`. This is also a kernel function. All it does is call `sequence()` with all of the parameter names. Attributes of the class are automatically set to appropriate values for parameters and arguments.

Sequences can either be run with no GUI input, or by setting arguments in the GUI corresponding to the parameters and arguments defined in `__init__()`. If run with no GUI input, the attributes in the class are set to default values, where for parameters these are pulled from the current value of the parameter in storage, and for arguments are pulled from the default value set in the processor. In the example above, `self.frequency_397_cooling` and `self.attenuation_397` would be automatically set to the current values in parameter storage, and `self.interesting_arg` would be set to 5 MHz. If GUI input is desired, then arguments would be created in the experiment GUI for each of the parameters and arguments defined, and the class attributes are set to those selected by the user in the GUI. The default values set inside the GUI for parameters are pulled from parameter storage, but then can be changed independently.

### Collect defined sequences
This framework uses the `SequencesContainer` object to collect user defined sequences. Create a file in your respository, and place in it code like the following.
```
from acf.sequences_container import SequencesContainer
from acf_sequences.cooling.doppler import DopplerCool
from acf_sequences.misc.print_hi import PrintHi

sequences = SequencesContainer()

sequences.add_sequence("doppler_cool", DopplerCool())
sequences.add_sequence("print_hi", PrintHi())
```

First import the `SequencesContainer` object, along with any defined sequences. Create the SequencesContainer object, and call `add_sequence(name, sequence)` with each sequence. For the name, put a valid python identifier, since this is how the sequence will be referenced in the experiment.

### Using sequences
Sequences are used in the following way.

```python
from acf.experiment import ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

class MyExperiment(ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()

    @kernel
    def run(self):
        self.setup_run()
        self.seq.doppler_cool.run()
```

First import the sequences object that was created in the previous step, and call `self.setup(sequences)` using that object in `build()`. All defined sequences will now be available through the `self.seq` object. If you want to configure arguments to that sequence, then call `add_arguments_to_gui()` on the sequence. To call the sequence, call `run()` on the sequence. If you want to pass values into the sequence that change between calls (in this case setting arguments in the GUI is not enough) then call `self.seq.sequence_name.sequence(values)`. This use case is the reason that sequences are implemented with seperate `run()` and `sequence()` functions.







Things to put in
[x] Parameters, parameter displayer widget, naming with slashes
[x] Adding parameter / other applets to GUI
[x] Parameters v Arguments
[x] Design principles
[ ] Code summary - what are the different classes etc.
[x] Installation instructions
[x] How to create an experiment
[x] How to create a sequence
[x] Why need extra hardware def file
    - Could add constraints into the file on output attenuation etc.?
