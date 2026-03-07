import usb.core
import usb.util
import usb.backend.libusb1

import os

from logger import log, LogLevel

from time import sleep

UNLOCK_KEY = b"MAYO" * 20

def find_device():
    usb_backend = None
    device_connection_attempts = 0

    log(LogLevel.INFO, "Waiting for fastboot device")

    if os.name == "nt":
        usb_backend = usb.backend.libusb1.get_backend(find_library=lambda x: libusb.dll._name)

    while True:
        device = usb.core.find(idVendor=0x0e8d, idProduct=0x201c, backend=usb_backend)

        if device is None:
            if device_connection_attempts == 15:
                device_connection_attempts = 0

                print()
                log(LogLevel.WARN, f"Tip: Make sure you run this program with the right permissions.")

            print(".", end="", flush=True)
            device_connection_attempts += 1
            sleep(1)
        else:
            print()
            return device

def send_cmd(device, cmd):
    # Hack cause the USB stack on wasp does not play nice
    while True:
        ret = device.write(1, cmd.encode("ascii"))
        response = []

        while True:
            data = device.read(0x81, 64, timeout=0)
            s = bytes(data).decode("ascii", errors="ignore")

            if len(s) < 4:
                status = "UNKNOWN"
            else:
                status = s[:4]

            body = s[4:]
            response.append(body)

            if status != "INFO":
                break

        rsp = "".join(response)
        rsp = rsp.replace("\r", "").replace("\x00", "")

        # If you actually send an unknown command, RIP
        if rsp == "unknown command":
            log(LogLevel.WARN, "Retrying...")
            continue
        else:
            return rsp

def send_data(device, data):
    send_cmd(device, f"download:{len(data):08X}")
    device.write(1, data)

    while True:
        data = device.read(0x81, 64, timeout=0)
        s = bytes(data).decode("ascii", errors="ignore")

        if len(s) < 4:
            status = "UNKNOWN"
        else:
            status = s[:4]

            if status == "OKAY":
                return True

        return False

def print_banner():
    log(LogLevel.NORMAL,
r"""
  _______ ____   _____ _____ ______ _______     __
 |__   __/ __ \ / ____/ ____|  ____|  __ \ \   / /
    | | | |  | | (___| (___ | |__  | |__) \ \_/ /
    | | | |  | |\___ \\___ \|  __| |  _  / \   /
    | | | |__| |____) |___) | |____| | \ \  | |
    |_|  \____/|_____/_____/|______|_|  \_\ |_|


""")

def main():
    print_banner()

    device = find_device()

    log(LogLevel.INFO, "Querying device info...")
    print()

    codename = send_cmd(device, "getvar:product")
    bl_ver = send_cmd(device, "getvar:version-bootloader")
    security_ver = int(send_cmd(device, "oem getsecurityversion"))

    log(LogLevel.DEVICE_INFO, f"Codename: {codename}")
    log(LogLevel.DEVICE_INFO, f"Bootloader Version: {bl_ver}")
    log(LogLevel.DEVICE_INFO, f"Security Version: {security_ver}")
    print()

    if codename != "wasp":
        log(LogLevel.ERROR, "Unsupported device.")
        exit(-1)

    if security_ver != 2:
        log(LogLevel.ERROR, "Unsupported security version, Android 11 is not supported.")
        exit(-1)

    log(LogLevel.INFO, "Starting unlock")
    log(LogLevel.INFO, "Sending unlock data")

    if send_data(device, UNLOCK_KEY) == True:
        response = send_cmd(device, "flash:unlock")
        log(LogLevel.INFO, "Done sending unlock key")
        print()

        if response == "flash unlock key failed":
            log(LogLevel.ERROR, "Failed to flash unlock key, maybe this version is patched.")
            exit(-1)

        log(LogLevel.INFO, "Flashed unlock key successfully, starting unlock")
        log(LogLevel.INFO, "Please press the volume up key to comfirm the unlock")
        response = send_cmd(device, "oem unlock")

        if response != "Start unlock flow\n":
            log(LogLevel.ERROR, "Failed to unlock bootloader.")
            exit(-1)

        log(LogLevel.INFO, "Rebooting device")
        print()
        send_cmd(device, "reboot")
    else:
        log(LogLevel.ERROR, "Failed to send unlock data")
        exit(-1)

    log(LogLevel.INFO, "Unlock succeeded!")

if __name__ == "__main__":
    main()
