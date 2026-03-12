import signal
from time import sleep

from pyrecracker.host_env import HostEnvironment
from pyrecracker.client import FirecrackerClient
from pyrecracker.client_types import (
    BootSource,
    Drive,
    MachineConfiguration,
    InstanceActionInfo,
    NetworkInterface,
)


SOCKET_PATH = "/tmp/firecracker.sock"
API = "http+unix://%2Ftmp%2Ffirecracker.sock"

BASE_ROOTFS = "./rootfs.ext4"
WORK_ROOTFS = "../firecracker/ubuntu-24.04.ext4"
KERNEL = "../firecracker/vmlinux-6.1.155"

TAP_DEV = "tap0"
HOST_IP = "172.16.0.1"
GUEST_IP = "172.16.0.2"


def main():
    # Create a host environment and Firecracker client
    host_env = HostEnvironment()
    
    # Setup the TAP device for networking
    host_env.add_tap_device(TAP_DEV)
    host_env.add_tap_address(HOST_IP, TAP_DEV)
    host_env.set_tap_up(TAP_DEV)
    host_env.exec()

    client = FirecrackerClient(SOCKET_PATH)

    #
    # CONFIGURING THE VM
    #

    # Define the machine configuration
    machine_config = MachineConfiguration(
        vcpu_count=1,
        mem_size_mib=512,
    )
    client.put_machine_config(machine_config)

    # Define the boot source
    boot_source = BootSource(
        kernel_image_path=KERNEL,
        boot_args="console=ttyS0 reboot=k panic=1 pci=off"
    )
    client.put_boot_source(boot_source)

    # Define the drive
    drive = Drive(
        drive_id="rootfs",
        is_root_device=True,
        path_on_host=WORK_ROOTFS,
        is_read_only=False,
    )
    client.put_drives(drive)

    network_interface = NetworkInterface(
        iface_id="eth0",
        host_dev_name=TAP_DEV,
        guest_mac="AA:FC:00:00:00:01",
    )
    client.put_network_interfaces(network_interface)

    #
    # Start the microVM
    #
    action_info = InstanceActionInfo(action_type="InstanceStart")
    client.put_actions(action_info)

    print("VM launched successfully!")

    def sigterm_handler(signum, frame):
        print("SIGINT received, stopping the VM...")
        action_info = InstanceActionInfo(action_type="SendCtrlAltDel")
        client.put_actions(action_info)
        print("VM stopped successfully!")
        print("Cleaning up host environment...")
        sleep(5)
        host_env.rm(SOCKET_PATH)
        host_env.del_tap_device(TAP_DEV)
        host_env.exec()
        print("Exiting.")
        exit(0)
        
    signal.signal(signal.SIGINT, sigterm_handler)
    while True:
        pass

if __name__ == "__main__":
    main()
