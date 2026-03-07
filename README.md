# Tossery

Bootloader unlock PoC for the Nokia 2.2 (wasp)

## Vulnerable versions

Android 9 works, Android 10 should, Android 11 is not supported.

## Why does this work

Improper checks done on the encrypted unlock key blob makes the device accept any binary as an unlock key and allows for unlock.

## How to run

Install all needed packages via ```pip3 install -r requirements.txt```

Run ```python3 tossery.py``` and follow the instructions
