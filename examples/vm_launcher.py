import signal
from time import sleep
import argparse

from pyrecracker.vm import VMManager


def main():
    parser = argparse.ArgumentParser(description="Launch a Firecracker VM with custom rootfs and kernel.")
    parser.add_argument('--base-rootfs', type=str, help='Path to the base rootfs image')
    parser.add_argument('--work-rootfs', type=str, help='Path to the working rootfs image')
    parser.add_argument('--kernel', type=str, default="../firecracker/vmlinux-6.1.155", help='Path to the kernel image')
    args = parser.parse_args()

    vm = VMManager("/tmp/firecracker.sock", args.kernel)
    vm.vcpu_count = 1
    vm.mem_size_mib = 512
    vm.boot_args = "console=ttyS0 reboot=k panic=1 pci=off"
    vm.drive_id = "rootfs"
    vm.is_root_device = True
    vm.path_on_host = args.work_rootfs
    vm.is_read_only = False
    vm.iface_id = "eth0"
    vm.host_dev_name = "tap0"
    vm.guest_mac = "AA:FC:00:00:00:01"
    vm.host_ip = "172.16.0.1"
    vm.guest_ip = "172.16.0.2"

    vm.configure()
    vm.start()

    print("VM launched successfully!")

    def sigterm_handler(signum, frame):
        print("SIGINT received, stopping the VM...")
        vm.stop()
        print("VM stopped successfully!")
        print("Exiting.")
        exit(0)

    signal.signal(signal.SIGINT, sigterm_handler)
    while True:
        pass

if __name__ == "__main__":
    main()
