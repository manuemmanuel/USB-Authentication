import pyudev
import subprocess
import time
import logging

class USBControlTool:
    def __init__(self):
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='usb')
        self.blocked_devices = set()
        self.logger = self.setup_logger()

    def setup_logger(self):
        logger = logging.getLogger('usb_logger')
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler = logging.FileHandler('usb_events.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger
        
    def start_monitoring(self):
        observer = pyudev.MonitorObserver(self.monitor, callback=self.handle_usb_event, name='usb-monitor')
        observer.start()

        try:
            self.logger.info("USB Device Control Tool is running.")
            while True:
                time.sleep(1)
                self.view_connected_devices()
        except KeyboardInterrupt:
            self.logger.info("USB Device Control Tool stopped by user.")
        finally:
            observer.stop()
            observer.join()

    def handle_usb_event(self, device):
        if device.action == 'add' and device not in self.blocked_devices:
            self.logger.info(f"USB Device Connected: {device}")
            if self.is_device_blocked(device):
                self.logger.info(f"Blocking USB Device: {device}")
                self.block_device(device)

        elif device.action == 'remove' and device in self.blocked_devices:
            self.logger.info(f"USB Device Disconnected: {device}")
            self.unblock_device(device)

    def is_device_blocked(self, device):
        # Add your custom logic here to determine if the device should be blocked
        return True

    def block_device(self, device):
        self.blocked_devices.add(device)
        subprocess.run(['sudo', 'echo', '0', '>', f'/sys{device.sys_path}/authorized'])

    def unblock_device(self, device):
        self.blocked_devices.remove(device)
        subprocess.run(['sudo', 'echo', '1', '>', f'/sys{device.sys_path}/authorized'])

    def view_connected_devices(self):
        self.logger.info("\nList of connected USB devices:")
        with open("usb_connections.log", "a") as connections_log:
            connections_log.write("\n------------------------\n")
            connection_count = 1
            for device in self.context.list_devices(subsystem='usb'):
                if device.get('PRODUCT') and device.get('MANUFACTURER'):
                    self.logger.info(f"Connection #{connection_count}\nManufacturer: {device.get('MANUFACTURER')}\nProduct: {device.get('PRODUCT')}")
                    connection_count += 1

def main():
    usb_tool = USBControlTool()
    usb_tool.start_monitoring()

if __name__ == '__main__':
    main()
