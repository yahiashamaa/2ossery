import hashlib
import usb.core
import usb.util
import usb.backend.libusb1

import os

from logger import log, LogLevel

from time import sleep

def find_device():
    usb_backend = None
    device_connection_attempts = 0

    log(LogLevel.INFO, "Waiting for fastboot device")

    if os.name == "nt":
        import libusb
        usb_backend = usb.backend.libusb1.get_backend(find_library=lambda x: libusb.dll._name)

    while True:

        adb_device = usb.core.find(idVendor=0x18d1, idProduct=0x4ee2, backend=usb_backend)
        if adb_device is not None:
            print()
            log(LogLevel.WARN, "Device found in ADB mode. Please run: adb shell reboot bootloader")
            sleep(1)
            continue


        fastboot_device = usb.core.find(idVendor=0x18d1, idProduct=0xdddd, backend=usb_backend)

        if fastboot_device is None:
            if device_connection_attempts == 15:
                device_connection_attempts = 0

                print()
                log(LogLevel.WARN, f"Tip: Make sure you run this program with the right permissions.")

            print(".", end="", flush=True)
            device_connection_attempts += 1
            sleep(1)
        else:
            print()
            return fastboot_device

def get_unlock_key(serialno):
    key = hashlib.md5(b"HUA" + serialno.encode() + b"MI").hexdigest()
    log(LogLevel.INFO, f"Unlock key: {key}")
    return key

def send_cmd(device, cmd):
    device.write(1, cmd.encode("ascii"))
    
    data = device.read(0x81, 64, timeout=5000)
    s = bytes(data).decode("ascii", errors="ignore")
    
    status = s[:4]
    body = s[4:]
    
    return status, body

def print_banner():
    log(LogLevel.NORMAL,
r"""
  ___   ____   _____ _____ ______ _______     __
 |__ \ / __ \ / ____/ ____|  ____|  __ \ \   / /
    ) | |  | | (___| (___ | |__  | |__) \ \_/ / 
   / /| |  | |\___ \\___ \|  __| |  _  / \   /  
  / /_| |__| |____) |___) | |____| | \ \  | |   
 |____|\____/|_____/_____/|______|_|  \_\ |_|   

""")

def main():
    print_banner()

    device = find_device()

    log(LogLevel.INFO, "Querying device info...")
    print()

    serialno = send_cmd(device, "getvar:serialno")
    bl_ver = send_cmd(device, "getvar:version-bootloader")
    

    log(LogLevel.DEVICE_INFO, f"Serial Number: {serialno[1]}")
    log(LogLevel.DEVICE_INFO, f"Bootloader Version: {bl_ver[1]}")
    print()

    key = get_unlock_key(serialno[1].strip())

    print()
    log(LogLevel.INFO, "Sending unlock key")
    
    response = send_cmd(device, f"oem unlock {key}")
    print()
    log(LogLevel.DEVICE_INFO, response[0])
    print()
    log(LogLevel.INFO, "Done sending unlock key")
    print()

    if response[0] == "ED":
        log(LogLevel.ERROR, "Unlock key was refused.")
        exit(-1)
    elif response[0] == "OKAY":
        log(LogLevel.INFO, "Sent the unlock key successfully")
    
    unlock_status = send_cmd(device, "getvar:unlocked")
    if unlock_status[1].strip() == "yes":
        log(LogLevel.INFO, "Unlock succeeded!")
    
if __name__ == "__main__":
    main()
