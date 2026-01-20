"""This class provides a single place to make all hardware definitions,
which can then be used in all experiments."""
from artiq.experiment import kernel
from acf.utils import get_config_dir
import json

class HardwareSetup:

    def __init__(self):
        """Create a HardwareSetup instance for a given hardware setup.

        """
        self.hardware = {}
        self.urukul_boards = []
        self.init_from_file()

    def init_from_file(self):
        """Create the hardware definition from json file."""
        config_file = get_config_dir() / "hardware.json"

        with config_file.open() as fh:
            data = json.load(fh)

        for ttl_device in data["ttl"]:
            self.add_ttl(ttl_device["name"], ttl_device["channel"])
 
        for dds_device in data["dds"]:
            self.add_dds(dds_device["name"], dds_device["board"], dds_device["channel"])
        
        # self.add_cam()
        # self.add_sampler()
        self.add_dac()

    def add_dac(self):
        self.hardware['dac'] = {
            "type": "dac",
            "device_str": "zotino0",
        }

    # def add_sampler(self):
    #     self.hardware['sampler'] = {
    #         "type": "sampler",
    #         "device_str": "sampler0",
    #     }
    # def add_cam(self):
    #     self.hardware['cam'] = {
    #         "type": "camera",
    #         "device_str": "grabber0",
    #     }

    def add_ttl(self, name, channel):
        """Add a ttl type device.

        Args:
            name (str): The name of the device.
            channel (int): Which ttl channel the device is connected to.
        """
        if not name.isidentifier():
            raise RuntimeError(f"ttl name '{name}' is not a valid python identifier.")

        self.hardware[name] = {
            "type": "ttl",
            "device_str": f"ttl{channel}",
        }

    def add_dds(self, name, board_num, channel):
        """Add a dds type device.

        Args:
            name (str): The name of the device.
            board_num (int): Which DDS board the device is on.
            channel (int): Which channel on the DDS board the device is on.
        """
        if not name.isidentifier():
            raise RuntimeError(f"dds name '{name}' is not a valid python identifier.")

        self.hardware[name] = {
            "type": "dds",
            "device_str": f"urukul{board_num}_ch{channel}",
        }
        if board_num not in self.urukul_boards:
            self.urukul_boards.append(board_num)

    def initialize(self, exp):
        """Initialize all of the hardware and set names in the calling exp class.

        Must be called in the build method, before any other method is called.

        Args:
            exp (EnvExperiment): The calling EnvExperiment class.
        """
        self.exp = exp
        self.dds_devices = []
        self.cpld_devices = []

        self.exp.setattr_device("core")
        self.exp.setattr_device("scheduler")
        for board_num in sorted(self.urukul_boards):
            cpld_name = f"urukul{board_num}_cpld"
            self.exp.setattr_device(cpld_name)
            self.cpld_devices.append(getattr(self.exp, cpld_name))
        for device_name in self.hardware:

            # Register device with Artiq
            self.exp.setattr_device(self.hardware[device_name]["device_str"])

            # Inject device labels into calling environment
            setattr(exp, device_name, self.get_device(device_name))

            if self.hardware[device_name]["type"] == "dds":
                self.dds_devices.append(self.get_device(device_name))


    def get_device(self, name):
        """Get a particular device.

        Args:
            name (str): The name of the device.

        Returns: The device object from the EnvExperiment object.
        """
        return getattr(self.exp, self.hardware[name]["device_str"])

    def add_device_attributes(self, obj):
        """Add all of the device objects as attributes to another object.

        Args:
            obj: The object to add device attributes to.
        """
        for device_name in self.hardware.keys():
            setattr(obj, device_name, self.get_device(device_name))
        

    @kernel
    def get_all_dds(self):
        """Get all dds type devices.

        Returns: List of dds devices.
        """
        return self.dds_devices

    @kernel
    def get_all_cpld(self):
        """Get all CPLD devices for Urukul boards."""
        return self.cpld_devices

    def shutdown(self):
        """Turn off output on all of the hardware."""
        pass

