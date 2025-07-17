# Utility functions

import os
from pathlib import Path

def get_config_dir():
    config_dir = "C:/msys64/home/artiq/repos/artiq_photonics_integration/acf_config"
    #os.environ.get("ACF_CONFIG_DIR")
    if config_dir is None or config_dir == "":
        raise RuntimeError("ACF_CONFIG_DIR environment variable not set.")
    
    return Path(config_dir)
