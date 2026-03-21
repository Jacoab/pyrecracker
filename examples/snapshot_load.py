import signal
import argparse
from time import sleep
from pyrecracker.vm import VMManager


def main():
    parser = argparse.ArgumentParser(description="Launch a Firecracker VM, take a snapshot, and load from it.")
    parser.add_argument('--work-rootfs', type=str, required=True, help='Path to the working rootfs image')
    parser.add_argument('--kernel', type=str, required=True, help='Path to the kernel image')
    parser.add_argument('--snapshot-path', type=str, required=True, help='Path to save/load the snapshot file')
    parser.add_argument('--mem-file-path', type=str, required=True, help='Path to save/load the memory file')
    args = parser.parse_args()

    vm = VMManager("/tmp/firecracker.sock", args.kernel)
    vm.vcpu_count = 1
    vm.mem_size_mib = 512
    vm.boot_args = "console=ttyS0 reboot=k panic=1 pci=off ip=172.16.0.2::172.16.0.1:255.255.255.0::eth0:off"
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
    print("VM launched successfully! Running for 5 seconds...")
    sleep(20)

    print(f"Creating snapshot at {args.snapshot_path} and memory file at {args.mem_file_path}...")
    vm.pause()
    sleep(2)
    vm.create_snapshot(args.snapshot_path, args.mem_file_path)
    print("Snapshot created. Stopping VM...")
    sleep(2)
    vm.stop()

    print("Loading VM from snapshot...")
    vm = VMManager("/tmp/firecracker.sock", args.kernel)
    vm.iface_id = "eth0"
    vm.host_dev_name = "tap0"
    vm.guest_mac = "AA:FC:00:00:00:01"
    vm.host_ip = "172.16.0.1"
    vm.guest_ip = "172.16.0.2"
    
    # Set up the TAP device on the host side
    vm.setup_host_networking()
    
    # Load the snapshot (network interface config is restored from snapshot)
    vm.load_snapshot(args.snapshot_path, args.mem_file_path, resume_vm=True)
    print("VM loaded from snapshot and resumed!")
    sleep(5)  # Give the network time to come up

    def sigterm_handler(signum, frame):
        print("\nSIGINT received, stopping the VM...")
        vm.stop()
        print("VM stopped successfully!")
        print("Exiting.")
        exit(0)

    signal.signal(signal.SIGINT, sigterm_handler)
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        sigterm_handler(None, None)

if __name__ == "__main__":
    main()
