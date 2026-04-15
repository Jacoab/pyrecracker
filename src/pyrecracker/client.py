import logging
from dataclasses import asdict
from typing import Any

import requests_unixsocket
from requests.exceptions import HTTPError

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


log = logging.getLogger(__name__)


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
        self.__session = requests_unixsocket.Session()
        self.__socket_path = socket_path
        self.__socket_url = f"http+unix://{socket_path.replace('/', '%2F')}"

    @property
    def socket_path(self) -> str:
        """
        Get the socket path for the Firecracker API.
        """
        return self.__socket_path

    def __put(self, endpoint: str, data: dict) -> None:
        """
        Helper method to send a PUT request to the Firecracker API.

        Args:
            endpoint (str): The API endpoint to which the request should be sent.
            data (dict): The JSON data to be included in the PUT request.
        Raises:
            HTTPError: If the PUT request receives with an HTTP error response.
        """
        try:
            response = self.__session.put(f"{self.__socket_url}/{endpoint}", json=data)
            response.raise_for_status()
        except HTTPError as err:
            log.error(f"Error occurred while sending PUT request to {endpoint}: {err}")
            raise

    def __patch(self, endpoint: str, data: dict) -> None:
        """
        Helper method to send a PATCH request to the Firecracker API.

        Args:
            endpoint (str): The API endpoint to which the request should be sent.
            data (dict): The JSON data to be included in the PATCH request.
        Raises:
            HTTPError: If the PATCH request receives with an HTTP error response.
        """
        try:
            response = self.__session.patch(f"{self.__socket_url}/{endpoint}", json=data)
            response.raise_for_status()
        except HTTPError as err:
            log.error(f"Error occurred while sending PATCH request to {endpoint}: {err}")
            raise

    def __body_to_dict(self, body: Any) -> dict:
        """
        Helper method to convert a dataclass instance to a dictionary.

        Args:
            body (Any): The dataclass instance to be converted.

        Returns:
            dict: The dictionary representation of the dataclass instance.
        """
        return asdict(
            body, 
            dict_factory=lambda x: {k: v for (k, v) in x if v is not None}
        )

    def put_machine_config(self, machine_config: MachineConfiguration) -> None:
        """
        Configure the machine with the specified number of vCPUs and memory size.

        Args:
            machine_config (MachineConfiguration): The machine configuration to be applied.
        """
        data = self.__body_to_dict(machine_config)
        self.__put("machine-config", data)

    def put_boot_source(self, boot_source: BootSource) -> None:
        """
        Configure the linux kernel boot source for the machine.

        Args:
            boot_source (BootSource): The boot source configuration for the machine, including kernel 
                image path and boot arguments.
        """
        data = self.__body_to_dict(boot_source)
        self.__put("boot-source", data)

    def put_drives(self, drive: Drive) -> None:
        """
        Configure a root filesystem drive for the machine.

        Args:
            drive (Drive): The drive configuration for the root filesystem.
        """
        data = self.__body_to_dict(drive)
        self.__put(f"drives/{drive.drive_id}", data)

    def put_network_interfaces(self, network_interface: NetworkInterface) -> None:
        """
        Configure a network interface for the machine.

        Args:
            network_interface (NetworkInterface): The network interface configuration.
        """
        data = self.__body_to_dict(network_interface)
        self.__put(f"network-interfaces/{network_interface.iface_id}", data)   

    def put_actions(self, instance_action_info: InstanceActionInfo) -> None:
        """
        Send an action request to the Firecracker API.

        Args:
            action_type (str): The type of action to be performed. Valid values are "InstanceStart" and "InstanceStop".
        """
        self.__put("actions", self.__body_to_dict(instance_action_info))

    def patch_vm(self, vm: VM) -> None:
        """
        Configure the VM with the specified configuration.

        Args:
            vm (VM): The VM configuration to be applied.
        """
        self.__patch("vm", self.__body_to_dict(vm))

    def put_snapshot_create(self, snapshot_create_params: SnapshotCreateParams) -> None:
        """
        Create a snapshot of the VM.

        Args:
            snapshot_create_params (SnapshotCreateParams): The parameters for creating the snapshot.
        """
        self.__put("snapshot/create", self.__body_to_dict(snapshot_create_params))

    def put_snapshot_load(self, snapshot_load_params: SnapshotLoadParams) -> None:
        """
        Load a snapshot of the VM.

        Args:
            snapshot_load_params (SnapshotLoadParams): The parameters for loading the snapshot.
        """
        self.__put("snapshot/load", self.__body_to_dict(snapshot_load_params))
