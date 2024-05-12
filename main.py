import json
import logging
import os
import sys
import time
import pyudev
import argparse
from pathlib import Path
import yaml
import smtplib
from email.message import EmailMessage

class USBControlTool:
    def __init__(self, config_file="config.yaml", custom_block_reason=""):
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='usb')
        self.blocked_devices = set()
        self.load_configuration(config_file)
        self.custom_block_reason = custom_block_reason

    def load_configuration(self, config_file):
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file '{config_file}' does not exist.")
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        self.whitelisted_devices = set([entry["id"] for entry in config['Whitelist']])
        self.blacklisted_devices = set([entry["id"] for entry in config['Blacklist']])
        self.log_rotation_enabled = config.get('LogRotationEnabled', True)
        self.email_notifications = config.get('EmailNotifications', {})

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
        id_vendor = hex(device.get('ID_VENDOR_ID'))
        id_product = hex(device.get('ID_MODEL_ID'))
        device_id = f"{id_vendor}_{id_product}"

        if device_id in self.whitelisted_devices:
            return False

        if device_id in self.blacklisted_devices:
            return True

        # If the device isn't either whitelisted nor blacklisted, treat it as unknown and block it
        self.block_device(device)
        return True

    def block_device(self, device):
        self.blocked_devices.add(device)
        self._save_blocked_devices()
        message = f"Device with ID {device} was automatically blocked due to security reasons ({self.custom_block_reason}).\n"
        print(message, flush=True)
        if self.email_notifications:
            self._send_notification_email(message)

    def unblock_device(self, device):
        self.blocked_devices.discard(device)
        self._save_blocked_devices()

    def _save_blocked_devices(self):
        if self.log_rotation_enabled:
            current_log_filename = 'usb_control_tool.log'
            backup_log_filenames = [f"usb_control_tool_{i}.log" for i in range(1, 6)]
            Path(current_log_filename).rename(Path(*backup_log_filenames[-1]))
            for i in reversed(range(len(backup_log_filenames)-1)):
                Path(backup_log_filenames[i]).rename(Path(backup_log_filenames[i + 1]))

        with open('usb_control_tool.log', 'a') as f:
            f.write('\n'.join(self.format_output(dev) for dev in self.blocked_devices))
            f.write("\n")

    def _send_notification_email(self, message):
        msg = EmailMessage()
        msg.set_content(message)

        msg['Subject'] = "Security Alert: Unauthorized USB Device Connected"
        msg['From'] = self.email_notifications['sender']
        msg['To'] = ', '.join(self.email_notifications['recipients'])

        server = smtplib.SMTP(self.email_notifications['host'], self.email_notifications['port'])
        server.starttls()
        server.login(self.email_notifications['username'], self.email_notifications['password'])
        server.send_message(msg)
        server.quit()

    @staticmethod
    def format_output(device):
        action = {'add': 'Connected', 'remove': 'Disconnected'}
        return f"{time.strftime('%Y-%m-%d %H:%M:%S')} - INFO - USB Device {action[device.action]}: {device}"

def main():
    parser = argparse.ArgumentParser(description="A tool to manage USB connections safely and securely.")
    parser.add_argument("-c", "--config", type=str, default="config.yaml", help="The configuration file (default: config.yaml)")
    args = parser.parse_args()
    
    usb_tool = USBControlTool(args.config)
    usb_tool.start_monitoring()

if __name__ == "__main__":
    main()
