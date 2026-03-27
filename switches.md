# RF Antenna Switches

Antenna switches let you route any antenna to any radio without physically swapping cables. Like a KVM but for RF signals.

## Types

### Manual Coax Switches
- Rotary knob, typically 2-4 positions
- $20-40 for decent quality (Daiwa, MFJ, etc.)
- Just make sure to match connector type (BNC, SMA, N, etc.)
- No power needed, purely mechanical

### Electronic RF Switches
- Relay-based or PIN diode switching
- Controllable via GPIO, USB, or serial
- Can be automated — e.g. "switch antenna based on active SDR task"
- Mini-Circuits makes solid ones but they're pricey

### RF Switch Matrices
- N inputs to M outputs, any combination
- Full crossbar switching — any antenna to any radio
- Expensive, mostly commercial/lab gear
- Overkill for hobby use but cool

## DIY Options
- Relay boards (4/8 channel) controlled by Raspberry Pi or Arduino
- Use RF-rated relays (not regular logic relays — impedance matters)
- People have built USB-controlled antenna switches for ~$30 in parts
- Search "RTL-SDR antenna switch" or "ham radio relay antenna switch"

## Practical Use Case
- Dedicate one dongle + antenna to ADS-B (runs 24/7, feeds FR24)
- Second dongle shares antennas via switch for scanning/experimentation
- Software-controlled switch could auto-select antenna based on which container is running
