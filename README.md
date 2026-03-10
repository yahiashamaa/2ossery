# 2ossery

Bootloader unlock PoC for Amazfit Verge (qogir), Stratos (everest) and Pace (huanghe)

## Why does this work

Huami locked the bootloader in a later update, but left the `fastboot oem unlock` mechanism in place, and the key generation is embarrassingly simple.

## How to run

1. Install dependencies: `pip3 install -r requirements.txt`
2. Boot your device into fastboot mode
3. Run `python3 2ossery.py`

## Credits

- [halal-beef](https://github.com/halal-beef) for [Tossery](https://github.com/halal-beef/tossery)
- Mayo Al-Tossery