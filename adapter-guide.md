# RF Adapter Coupling Guide

Kit: ConnectoRF Universal Coaxial Adapter Kit
SDR: RTL-SDR Blog V4 (SMA female port)

## How the kit works

The kit has **universal couplers** (barrel cylinders) and **typed end pieces** (plugs and jacks). Screw a typed piece onto each end of a coupler to build any adapter combo.

Terminology:
- **Plug** = male (center pin)
- **Jack** = female (center socket)

## Current setup: Whip antenna → dongle (direct)

```
[Whip antenna (BNC male)] → [BNC jack + coupler + SMA plug] → [RTL-SDR V4 (SMA female)]
```

Pieces needed from kit:
- 1x universal coupler
- 1x BNC jack
- 1x SMA plug

## Outdoor antenna via coax cable

The coax cable has **N-type male** connectors on both ends.

### Dongle end (inside)

```
[Coax cable (N male)] → [N jack + coupler + SMA plug] → [RTL-SDR V4 (SMA female)]
```

Pieces:
- 1x universal coupler
- 1x N jack
- 1x SMA plug

### Antenna end (outside window)

Depends on which antenna:

**Whip antenna (BNC male):**
```
[Whip (BNC male)] → [BNC jack + coupler + N jack] → [Coax cable (N male)]
```

Pieces:
- 1x universal coupler
- 1x BNC jack
- 1x N jack

**V-dipole antenna (SMA male):**
```
[V-dipole (SMA male)] → [SMA jack + coupler + N jack] → [Coax cable (N male)]
```

Pieces:
- 1x universal coupler
- 1x SMA jack
- 1x N jack

**Bare wire / speaker wire (via pigtail):**
```
[Speaker wire] → soldered/twisted to [SMA pigtail (SMA female)] → [SMA plug + coupler + N jack] → [Coax cable (N male)]
```

Or skip the coax and plug the pigtail directly into the dongle.

## Full chain example: whip out window

```
[RTL-SDR V4]  ←SMA→  [SMA plug + coupler + N jack]  ←N→  [coax cable]  ←N→  [N jack + coupler + BNC jack]  ←BNC→  [whip antenna]
   inside                    inside adapter                   through window        outside adapter                    outside
```

## Tips

- Each coupling (adapter + coupler) introduces a tiny amount of signal loss — keep the chain short
- For short coax runs (<20 feet) at VHF frequencies, loss is negligible with any coax type
- The coax cable is your friend for getting the antenna outside while keeping the dongle at your desk
- Make sure all connections are snug — loose couplings kill signal quality
