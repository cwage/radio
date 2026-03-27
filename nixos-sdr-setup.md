# NixOS SDR Setup

Changes needed in `hosts/thinkpad/configuration.nix` (cwage/nix-workstation):

## 1. Enable RTL-SDR hardware support

Handles udev rules + kernel module blacklisting (replaces manual setup on Ubuntu):

```nix
hardware.rtl-sdr.enable = true;
```

## 2. Add plugdev group to user

```nix
users.users.cwage = {
  extraGroups = [ "wheel" "audio" "video" "networkmanager" "plugdev" ];
};
```

## 3. Add SDR packages

```nix
environment.systemPackages = with pkgs; [
  # ... existing packages ...

  # SDR
  rtl-sdr
  gqrx
  gnuradio
  soapysdr-with-plugins
];
```
