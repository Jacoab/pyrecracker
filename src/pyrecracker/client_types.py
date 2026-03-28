from typing import Optional
from dataclasses import dataclass
from enum import StrEnum


@dataclass
class BootSource:
    """
    Represents the request body for the Firecracker BootSource API.
    Maps 1-to-1 with the BootSource definition in the Firecracker Swagger spec.
    
    Attributes:
        kernel_image_path (str): Path to the kernel image on the host.
        boot_args (Optional[str]): Kernel boot arguments.
        initrd_path (Optional[str]): Path to the initrd image on the host.
    """
    kernel_image_path: str
    boot_args: Optional[str] = None
    initrd_path: Optional[str] = None


class HugePages(StrEnum):
    NONE = "None"
    TWO_MIB = "2M"


@dataclass
class MachineConfiguration:
    """
    Represents the request body for the Firecracker Machine Configuration API.
    Maps 1-to-1 with the MachineConfiguration definition in the Firecracker Swagger spec.
    
    Attributes:
        mem_size_mib (int): Memory size in MiB.
        vcpu_count (int): Number of vCPUs (1-32).
        smt (Optional[bool]): Simultaneous multithreading enabled.
        track_dirty_pages (Optional[bool]): Track dirty pages for live migration.
        huge_pages (Optional[HugePages]): Use huge pages.
    """
    mem_size_mib: int
    vcpu_count: int
    #cpu_template: Optional[CPUTemplate] = None will have to be a ref to another dataclass
    smt: Optional[bool] = None
    track_dirty_pages: Optional[bool] = None
    huge_pages: Optional[HugePages] = None

    def __post__init__(self):
        if self.vcpu_count < 1 or self.vcpu_count > 32:
            raise ValueError("vcpu_count must be between 1 and 32")
        if self.huge_pages is not None:
            if self.huge_pages not in [HugePages.NONE, HugePages.TWO_MIB]:
                raise ValueError(
                    "MachineConfiguration.huge_pages must be either"
                    f" '{HugePages.NONE}' or '{HugePages.TWO_MIB}'"
                )


class CacheType(StrEnum):
    UNSAFE = "Unsafe"
    WRITEBACK = "Writeback"


class IOEngine(StrEnum):
    SYNC = "Sync"
    ASYNC = "Async"


@dataclass
class Drive:
    """
    Represents the request body for the Firecracker Drive API.
    Maps 1-to-1 with the Drive definition in the Firecracker Swagger spec.
    
    Attributes:
        drive_id (str): Unique identifier for the drive.
        is_root_device (bool): Whether this drive is the root device.
        partuuid (Optional[str]): Partition UUID.
        cache_type (Optional[CacheType]): Cache type.
        is_read_only (Optional[bool]): If the drive is read-only.
        path_on_host (Optional[str]): Path to the drive on the host.
        io_engine (Optional[IOEngine]): IO engine.
        socket (Optional[str]): Path to the drive's socket.
    """
    drive_id: str
    is_root_device: bool
    partuuid: Optional[str] = None
    cache_type: Optional[CacheType] = None
    is_read_only: Optional[bool] = None
    path_on_host: Optional[str] = None
    #rate_limiter: Optional[RateLimiter] = None This needs to be a ref to another dataclass
    io_engine: Optional[IOEngine] = None
    socket: Optional[str] = None

    def __post__init__(self):
        if self.cache_type is not None:
            if self.cache_type not in [CacheType.UNSAFE, CacheType.WRITEBACK]:
                raise ValueError(
                    f"DriveBody.cache_type must be either '{CacheType.UNSAFE}' or '{CacheType.WRITEBACK}'"
                )
        if self.io_engine is not None:
            if self.io_engine not in [IOEngine.SYNC, IOEngine.ASYNC]:
                raise ValueError(
                    f"DriveBody.io_engine must be either '{IOEngine.SYNC}' or '{IOEngine.ASYNC}'"
                )


class ActionType(StrEnum):
    FLUSH_METRICS = "FlushMetrics"
    INSTANCE_START = "InstanceStart"
    SEND_CTRL_ALT_DEL = "SendCtrlAltDel"


@dataclass
class InstanceActionInfo:
    """
    Represents the request body for the Firecracker Instance Action API.
    Maps 1-to-1 with the InstanceActionInfo definition in the Firecracker Swagger spec.
    
    Attributes:
        action_type (ActionType): Action type to execute.
    """
    action_type: ActionType

    def __post__init__(self):
        if self.action_type not in [
            ActionType.FLUSH_METRICS,
            ActionType.INSTANCE_START,
            ActionType.SEND_CTRL_ALT_DEL
        ]:
            raise ValueError(
                f"InstanceActionInfo.action_type must be one of '{ActionType.FLUSH_METRICS}', "
                f"'{ActionType.INSTANCE_START}', or '{ActionType.SEND_CTRL_ALT_DEL}'"
            )
        

@dataclass
class NetworkInterface:
    """
    Represents the request body for the Firecracker Network Interface API.

    Attributes:
        host_dev_name (str): Host level path for the guest network interface (e.g. tap0).
        iface_id (str): Unique identifier for the network interface within Firecracker.
        guest_mac (Optional[str]): MAC address to be assigned to the guest network interface.
    """
    host_dev_name: str
    iface_id: str
    guest_mac: Optional[str] = None
    #rx_rate_limiter: Optional[RateLimiter] = None This needs to be a ref
    #tx_rate_limiter: Optional[RateLimiter] = None This needs to be a ref


class VMState(StrEnum):
    PAUSED = "Paused"
    RESUMED = "Resumed"


@dataclass
class VM:
    """
    Represents the state of a Firecracker microVM.

    Attributes:
        state (VMState): The current state of the microVM
    """
    state: VMState

    def __post__init__(self):
        if self.state not in [VMState.PAUSED, VMState.RESUMED]:
            raise ValueError(
                f"VM.state must be one of '{VMState.PAUSED}' or '{VMState.RESUMED}'"
            )


class SnapshotType(StrEnum):
    FULL = "Full"
    DIFF = "Diff"


@dataclass
class SnapshotCreateParams:
    """
    Represents the request body for the Firecracker Create Snapshot API.

    Attributes:
        mem_file_path (str): The path on the host where the memory file will be stored.
        snapshot_path (str): The path on the host where the snapshot will be stored.
        snapshot_type (Optional[SnapshotType]): The type of snapshot to create ('Full' or 'Diff').
    """
    snapshot_path: str
    mem_file_path: str
    snapshot_type: Optional[SnapshotType] = None

    def __post__init__(self):
        if self.snapshot_type not in [SnapshotType.FULL, SnapshotType.DIFF]:
            raise ValueError(
                f"SnapshotCreateParams.snapshot_type must be either '{SnapshotType.FULL}' or '{SnapshotType.DIFF}'"
            )


@dataclass
class SnapshotLoadParams:
    """
    Represents the request body for the Firecracker Load Snapshot API.

    Attributes:
        snapshot_path (str): Path to the file that contains the microVM state to be loaded.
        track_dirty_pages (Optional[bool]): Whether to track dirty pages after loading the snapshot.
        mem_file_path (Optional[str]): The path on the host that contains the guest memory to be loaded.
        resume_vm (Optional[bool]): Whether to resume the VM immediately after loading the snapshot.
    """
    snapshot_path: str
    track_dirty_pages: Optional[bool] = None
    mem_file_path: Optional[str] = None
    # mem_backend: Optional[MemoryBackend] = None This needs to be a ref to another dataclass
    resume_vm: Optional[bool] = None
    # network_overrides: Optional[List[NetworkOverride]] = None This needs to be a ref to a list of dataclasses
    # vsock_override: Optional[VsockOverride] = None This needs to be a ref to another dataclass