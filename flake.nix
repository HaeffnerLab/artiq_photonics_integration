{
  inputs.extrapkg.url = "git+https://git.m-labs.hk/M-Labs/artiq-extrapkg.git?ref=release-8";
  outputs = { self, extrapkg }:
    let
      pkgs = extrapkg.pkgs;
      artiq = extrapkg.packages.x86_64-linux;
    in {
      defaultPackage.x86_64-linux = pkgs.buildEnv {
        name = "artiq-env";
        paths = [
          # ========================================
          # EDIT BELOW
          # ========================================
          (pkgs.python3.withPackages(ps: [
            # List desired Python packages here.
            artiq.artiq
            pyserial
            #ps.paramiko  # needed if and only if flashing boards remotely (artiq_flash -H)
            #artiq.flake8-artiq
            #artiq.dax
            #artiq.dax-applets

            # The NixOS package collection contains many other packages that you may find
            # interesting. Here are some examples:
            ps.pandas
            ps.pyvisa
            #ps.pyvisa-sim
            ps.pyvisa-py
            #ps.psutil
            #ps.zeroconf
            ps.numpy
            ps.scipy
            #ps.numba
            ps.matplotlib
            # or if you need Qt (will recompile):
            #(ps.matplotlib.override { enableQt = true; })
            #ps.bokeh
            #ps.cirq
            #ps.qiskit
            ps.opencv4
            
            ps.gpib-ctypes
            ps.pyusb
            ps.zeroconf
            ps.psutil
          ]))
          #artiq.korad_ka3005p
          #artiq.novatech409b
          # List desired non-Python packages here
          #artiq.openocd-bscanspi  # needed if and only if flashing boards
          # Other potentially interesting non-Python packages from the NixOS package collection:
          #pkgs.gtkwave
          #pkgs.spyder
          #pkgs.R
          #pkgs.julia
          #pkgs.linuxPackages.linux-gpib
          #pkgs.linuxPackages.linux-gpib\
          #pkgs.linux-gpib
          # ========================================
          # EDIT ABOVE
          # ========================================
        ];
      };
    };
  nixConfig = {  # work around https://github.com/NixOS/nix/issues/6771
    extra-trusted-public-keys = "nixbld.m-labs.hk-1:5aSRVA5b320xbNvu30tqxVPXpld73bhtOeH6uAjRyHc=";
    extra-substituters = "https://nixbld.m-labs.hk";
  };
}
