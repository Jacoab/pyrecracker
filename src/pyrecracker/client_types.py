from typing import Optional
from dataclasses import dataclass


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
        huge_pages (Optional[str]): Use huge pages ('None' or '2M').
    """
    mem_size_mib: int
    vcpu_count: int
    #cpu_template: Optional[CPUTemplate] = None will have to be a ref to another dataclass
    smt: Optional[bool] = None
    track_dirty_pages: Optional[bool] = None
    huge_pages: Optional[str] = None

    def __post__init__(self):
        if self.vcpu_count < 1 or self.vcpu_count > 32:
            raise ValueError("vcpu_count must be between 1 and 32")
        if self.huge_pages is not None:
            if self.huge_pages not in ["None", "2M"]:
                raise ValueError(
                    "MachineConfiguration.huge_pages must be either"
                    " 'None' or '2M'"
                )


@dataclass
class Drive:
    """
    Represents the request body for the Firecracker Drive API.
    Maps 1-to-1 with the Drive definition in the Firecracker Swagger spec.
    
    Attributes:
        drive_id (str): Unique identifier for the drive.
        is_root_device (bool): Whether this drive is the root device.
        partuuid (Optional[str]): Partition UUID.
        cache_type (Optional[str]): Cache type ('Unsafe' or 'Writeback').
        is_read_only (Optional[bool]): If the drive is read-only.
        path_on_host (Optional[str]): Path to the drive on the host.
        io_engine (Optional[str]): IO engine ('Sync' or 'Async').
        socket (Optional[str]): Path to the drive's socket.
    """
    drive_id: str
    is_root_device: bool
    partuuid: Optional[str] = None
    cache_type: Optional[str] = None
    is_read_only: Optional[bool] = None
    path_on_host: Optional[str] = None
    #rate_limiter: Optional[RateLimiter] = None This needs to be a ref to another dataclass
    io_engine: Optional[str] = None
    socket: Optional[str] = None

    def __post__init__(self):
        if self.cache_type is not None:
            if self.cache_type not in ["Unsafe", "Writeback"]:
                raise ValueError(
                    "DriveBody.cache_type must be either 'Unsafe' or 'Writeback'"
                )
        if self.io_engine is not None:
            if self.io_engine not in ["Sync", "Async"]:
                raise ValueError(
                    "DriveBody.io_engine must be either 'Sync' or 'Async'"
                )


@dataclass
class InstanceActionInfo:
    """
    Represents the request body for the Firecracker Instance Action API.
    Maps 1-to-1 with the InstanceActionInfo definition in the Firecracker Swagger spec.
    
    Attributes:
        action_type (str): Action type ('FlushMetrics', 'InstanceStart', 'SendCtrlAltDel').
    """
    action_type: str

    def __post__init__(self):
        if self.action_type not in [
            "FlushMetrics", 
            "InstanceStart", 
            "SendCtrlAltDel"
        ]:
            raise ValueError(
                "InstanceActionInfo.action_type must be one of 'FlushMetrics', "
                "'InstanceStart', or 'SendCtrlAltDel'"
            )
