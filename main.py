import logging
import os
import sys
import time
import pyudev

class USBControlTool:
    def __init__(self):
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='usb')
        self.blocked_devices = set()

    def start_monitoring(self):
        logger = logging.getLogger(__name__)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        handler = logging.FileHandler('usb_control_tool.log', mode='w')
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.addHandler(stream_handler)
        logger.setLevel(logging.DEBUG)

        observer = pyudev.MonitorObserver(self.monitor, callback=lambda d: logger.info(self.format_output(d)), name='usb-monitor')
        observer.start()

        try:
            print("USB Device Control Tool is running. Press Ctrl+C to exit.", file=sys.stdout, flush=True)
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            observer.stop()
            observer.join()

    def is_device_blocked(self, device):
        # Add your custom logic to determine if the device should be blocked
        # Return True if the device should be blocked or False otherwise
        return True

    def block_device(self, device):
        # Add your custom logic to block the USB device
        self.blocked_devices.add(device)

    def unblock_device(self, device):
        # Add your custom logic to unblock the USB device
        self.blocked_devices.discard(device)

    @staticmethod
    def format_output(device):
        action = {'add': 'Connected', 'remove': 'Disconnected'}
        return f"{time.strftime('%Y-%m-%d %H:%M:%S')} - INFO - USB Device {action[device.action]}: {device}"

def main():
    usb_tool = USBControlTool()
    usb_tool.start_monitoring()

if __name__ == "__main__":
    main()
