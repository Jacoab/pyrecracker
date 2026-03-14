from typing import Optional
from time import sleep

from pyrecracker.client import FirecrackerClient
from pyrecracker.client_types import (
    VM,
    MachineConfiguration, 
    BootSource, 
    Drive, 
    InstanceActionInfo,
    NetworkInterface,
    SnapshotCreateParams,
    SnapshotLoadParams
)
from pyrecracker.host_env import HostEnvironment


class VMManager:
    """
    Class for managing a Firecracker MicroVM instance.  All settings for 
    Firecracker VMs that are normally set via the Firecracker API are exposed 
    as properties of this class.  Methods for controlling a VM's lifecycle 
    are also provided.

    Attributes:
        __host_env: HostEnvironment - Host environment manager
        __client: FirecrackerClient - Client for interacting with the Firecracker API
        __boot_source: BootSource - Boot source configuration for the VM
        __machine_config: MachineConfiguration - Machine configuration for the VM
        __drive: Drive - Drive configuration for the VM
        __network_interface: NetworkInterface - Network interface configuration for the VM
        __host_ip: Optional[str] - Host IP address for the network interface
        __guest_ip: Optional[str] - Guest IP address for the network interface
    """
    def __init__(self, socket_path: str, kernel_image_path: str) -> None:
        self.__host_env = HostEnvironment()
        self.__client = FirecrackerClient(socket_path)
        
        self.__boot_source = BootSource(
            kernel_image_path=kernel_image_path,
            boot_args="console=ttyS0 reboot=k panic=1 pci=off"
        )
        self.__machine_config = MachineConfiguration(
            vcpu_count=1, 
            mem_size_mib=128
        )
        self.__drive = Drive(drive_id="rootfs", is_root_device=True)
        self.__network_interface = NetworkInterface(iface_id="eth0", host_dev_name="tap0")

        self.__host_ip: Optional[str] = None
        self.__guest_ip: Optional[str] = None

        self.__host_env_cleanup_pause: int = 2

    @property
    def socket_path(self) -> str:
        """
        Socket path for the Firecracker API.
        """
        return self.__client.socket_path

    @property
    def kernel_image_path(self) -> str:
        """
        Get or set the path to the kernel image for the VM.
        """
        return self.__boot_source.kernel_image_path

    @kernel_image_path.setter
    def kernel_image_path(self, kernel_image_path: str) -> None:
        self.__boot_source.kernel_image_path = kernel_image_path

    @property
    def boot_args(self) -> Optional[str]:
        """
        Get or set the boot arguments for the VM.
        """
        return self.__boot_source.boot_args

    @boot_args.setter
    def boot_args(self, boot_args: str) -> None:
        self.__boot_source.boot_args = boot_args

    @property
    def initrd_path(self) -> Optional[str]:
        """
        Path to the initrd image for the VM.
        """
        return self.__boot_source.initrd_path

    @initrd_path.setter
    def initrd_path(self, initrd_path: str) -> None:
        self.__boot_source.initrd_path = initrd_path

    @property
    def mem_size_mib(self) -> int:
        """
        Memory size in MiB for the VM.
        """
        return self.__machine_config.mem_size_mib

    @mem_size_mib.setter
    def mem_size_mib(self, mem_size_mib: int) -> None:
        self.__machine_config.mem_size_mib = mem_size_mib

    @property
    def vcpu_count(self) -> int:
        """
        Number of vCPUs for the VM.
        """
        return self.__machine_config.vcpu_count

    @vcpu_count.setter
    def vcpu_count(self, vcpu_count: int) -> None:
        self.__machine_config.vcpu_count = vcpu_count

    @property
    def smt(self) -> Optional[bool]:
        """
        Simultaneous multithreading (SMT) for the VM.
        """
        return self.__machine_config.smt

    @smt.setter
    def smt(self, smt: bool) -> None:
        self.__machine_config.smt = smt

    @property
    def track_dirty_pages(self) -> Optional[bool]:
        """
        Dirty page tracking for the VM.
        """
        return self.__machine_config.track_dirty_pages

    @track_dirty_pages.setter
    def track_dirty_pages(self, track_dirty_pages:bool) -> None:
        self.__machine_config.track_dirty_pages = track_dirty_pages

    @property
    def huge_pages(self) -> Optional[str]:
        """
        Huge pages setting for the VM.
        """
        return self.__machine_config.huge_pages

    @huge_pages.setter
    def huge_pages(self, huge_pages: str) -> None:
        self.__machine_config.huge_pages = huge_pages

    @property
    def drive_id(self) -> str:
        """
        Drive ID for the VM's root device.
        """
        return self.__drive.drive_id

    @drive_id.setter
    def drive_id(self, drive_id: str) -> None:
        self.__drive.drive_id = drive_id

    @property
    def is_root_device(self) -> bool:
        """
        Whether the drive is the root device.
        """
        return self.__drive.is_root_device

    @is_root_device.setter
    def is_root_device(self, is_root_device: bool) -> None:
        self.__drive.is_root_device = is_root_device

    @property
    def partuuid(self) -> Optional[str]:
        """
        Partition UUID for the drive.
        """
        return self.__drive.partuuid

    @partuuid.setter
    def partuuid(self, partuuid: str) -> None:
        self.__drive.partuuid = partuuid

    @property
    def cache_type(self) -> Optional[str]:
        """
        Cache type for the drive.
        """
        return self.__drive.cache_type

    @cache_type.setter
    def cache_type(self, cache_type: str) -> None:
        self.__drive.cache_type = cache_type

    @property
    def is_read_only(self) -> Optional[bool]:
        """
        Whether the drive is read-only.
        """
        return self.__drive.is_read_only

    @is_read_only.setter
    def is_read_only(self, is_read_only: bool) -> None:
        self.__drive.is_read_only = is_read_only

    @property
    def path_on_host(self) -> Optional[str]:
        """
        Path to the drive on the host.
        """
        return self.__drive.path_on_host

    @path_on_host.setter
    def path_on_host(self, path_on_host: str) -> None:
        self.__drive.path_on_host = path_on_host

    @property
    def io_engine(self) -> Optional[str]:
        """
        IO engine for the drive.
        """
        return self.__drive.io_engine

    @io_engine.setter
    def io_engine(self, io_engine: str) -> None:
        self.__drive.io_engine = io_engine

    @property
    def socket(self) -> Optional[str]:
        """
        Socket path for the drive.
        """
        return self.__drive.socket

    @socket.setter
    def socket(self, socket: str) -> None:
        self.__drive.socket = socket

    @property
    def host_dev_name(self) -> str:
        """
        Host device name for the network interface.
        """
        return self.__network_interface.host_dev_name

    @host_dev_name.setter
    def host_dev_name(self, host_dev_name: str) -> None:
        self.__network_interface.host_dev_name = host_dev_name

    @property
    def iface_id(self) -> str:
        """
        Network interface ID for the VM.
        """
        return self.__network_interface.iface_id

    @iface_id.setter
    def iface_id(self, iface_id: str) -> None:
        self.__network_interface.iface_id = iface_id

    @property
    def guest_mac(self) -> Optional[str]:
        """
        Guest MAC address for the network interface.
        """
        return self.__network_interface.guest_mac

    @guest_mac.setter
    def guest_mac(self, guest_mac: str) -> None:
        self.__network_interface.guest_mac = guest_mac

    @property
    def host_ip(self) -> Optional[str]:
        """
        Host IP address for the network interface.
        """
        return self.__host_ip
    
    @host_ip.setter
    def host_ip(self, host_ip: str) -> None:
        self.__host_ip = host_ip

    @property
    def guest_ip(self) -> Optional[str]:
        """
        Guest IP address for the network interface.
        """
        return self.__guest_ip
    
    @guest_ip.setter
    def guest_ip(self, guest_ip: str) -> None:
        self.__guest_ip = guest_ip

    @property
    def host_env_cleanup_pause(self) -> int:
        """
        Time in seconds to pause before cleaning up the host environment after stopping the VM.
        """
        return self.__host_env_cleanup_pause
    
    @host_env_cleanup_pause.setter
    def host_env_cleanup_pause(self, host_env_cleanup_pause: int) -> None:
        self.__host_env_cleanup_pause = host_env_cleanup_pause
    
    def configure(self) -> None:
        """
        Configure the VM with the current settings.  This will 
        do the following:
        - set up the TAP device for networking if host and guest IPs are provided
        - set the machine configuration
        - set the boot source
        - set the drive configuration
        - set the network interface configuration
        """

        # Set up the TAP device for networking if host and guest IPs are provided
        if self.host_ip is not None and self.guest_ip is not None:
            self.__host_env.add_tap_device(self.host_dev_name)
            self.__host_env.add_tap_address(self.host_ip, self.host_dev_name)
            self.__host_env.set_tap_up(self.host_dev_name)
            self.__host_env.exec()

        # Configure the VM with the specified settings
        self.__client.put_machine_config(self.__machine_config)
        self.__client.put_boot_source(self.__boot_source)
        self.__client.put_drives(self.__drive)
        self.__client.put_network_interfaces(self.__network_interface)

    def create_snapshot(
        self, 
        snapshot_path: str, 
        mem_file_path: str, 
        snapshot_type: str = "Full"
    ) -> None:
        """
        Create a snapshot of the VM.

        Args:
            mem_file_path (str): The path on the host where the memory file will be stored.
        snapshot_path (str): The path on the host where the snapshot will be stored.
        snapshot_type (str): The type of snapshot to create ('Full' or 'Diff').
        """
        snapshot_params = SnapshotCreateParams(
            snapshot_path=snapshot_path,
            mem_file_path=mem_file_path,
            snapshot_type=snapshot_type
        )
        self.__client.put_snapshot_create(snapshot_params)

    def load_snapshot(
        self, 
        snapshot_path: str, 
        mem_file_path: Optional[str] = None,
        resume_vm: bool = False
    ) -> None:
        """
        Load a snapshot of the VM.

        Args:
            snapshot_path (str): Path to the file that contains the microVM state to be loaded.
            mem_file_path (Optional[str]): The path on the host that contains the guest memory to be loaded.
            resume_vm (bool): Whether to resume the VM immediately after loading the snapshot.
        """
        snapshot_load_params = SnapshotLoadParams(
            snapshot_path=snapshot_path,
            track_dirty_pages=self.track_dirty_pages,
            mem_file_path=mem_file_path,
            resume_vm=resume_vm
        )
        self.__client.put_snapshot_load(snapshot_load_params)

    def pause(self):
        """
        Pause the VM.
        """
        vm = VM(state="Paused")
        self.__client.put_vm(vm)

    def resume(self):
        """
        Resume the VM.
        """
        vm = VM(state="Resume")
        self.__client.put_vm(vm)

    def start(self) -> None:
        """
        Starts the microVM.
        """
        action_info = InstanceActionInfo(action_type="InstanceStart")
        self.__client.put_actions(action_info)

    def stop(self) -> None:
        """
        Stops the microVM.
        """
        action_info = InstanceActionInfo(action_type="SendCtrlAltDel")
        self.__client.put_actions(action_info)
        sleep(self.host_env_cleanup_pause)

        self.__host_env.rm(self.socket_path)
        self.__host_env.del_tap_device(self.host_dev_name)
        self.__host_env.exec()
