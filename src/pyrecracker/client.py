from dataclasses import asdict

import requests_unixsocket

from pyrecracker.client_types import (
    MachineConfiguration, 
    BootSource, 
    Drive, 
    InstanceActionInfo
)


class FirecrackerClient:
    """
    A client for interacting with the Firecracker HTTP API via a Unix socket.
    """

    def __init__(self, socket_path: str) -> None:
        """
        Initialize the FirecrackerClient with the path to the Unix socket.

        Args:
            socket_path (str): The path to the Firecracker API Unix socket.
        """
        self.session = requests_unixsocket.Session()
        self.socket_url = f"http+unix://{socket_path.replace('/', '%2F')}"

    def __put(self, endpoint: str, data: dict) -> None:
        """
        Helper method to send a PUT request to the Firecracker API.

        Args:
            endpoint (str): The API endpoint to which the request should be sent.
            data (dict): The JSON data to be included in the PUT request.
        """
        response = self.session.put(f"{self.socket_url}/{endpoint}", json=data)
        response.raise_for_status()

    def put_machine_config(self, machine_config: MachineConfiguration) -> None:
        """
        Configure the machine with the specified number of vCPUs and memory size.

        Args:
            vcpu_count (int): The number of virtual CPUs to allocate to the machine.
            mem_size_mib (int): The amount of memory in MiB to allocate to the machine.
            ht_enabled (bool): Whether to enable hyper-threading for the machine.
        """
        self.__put("machine-config", asdict(machine_config))

    def put_boot_source(self, boot_source: BootSource) -> None:
        """
        Configure the linux kernel boot source for the machine.

        Args:
            kernel_image_path (str): The path to the kernel image to be used as the boot source.
            boot_args (str): The kernel command line arguments to be passed to the kernel on boot.
        """
        self.__put("boot-source", asdict(boot_source))

    def put_drives(self, drive: Drive) -> None:
        """
        Configure a root filesystem drive for the machine.

        Args:
            drive_id (str): The identifier inside firecracker for the drive to be configured.
            path_on_host (str): The path on the host where the drive's backing file is located.
            is_root_device (str): True if disk should be the root file drive else False
            is_read_only (bool): Whether the drive should be configured as read-only.
        """
        self.__put(f"drives/{drive.drive_id}", asdict(drive))

    def put_actions(self, instance_action_info: InstanceActionInfo) -> None:
        """
        Send an action request to the Firecracker API.

        Args:
            action_type (str): The type of action to be performed. Valid values are "InstanceStart" and "InstanceStop".
        """
        self.__put("actions", asdict(instance_action_info))
