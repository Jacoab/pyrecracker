from dataclasses import dataclass
from typing import Callable, Optional, Self
from logging import getLogger
import subprocess

from pyrecracker.cmd import Command, CommandError


logger = getLogger(__name__)

@dataclass
class EnvironmentCall:
    """
    A dataclass to represent a call to be made in the host environment. This class
    encapsulates the command to be executed and an optional callback function that
    can be used to perform cleanup actions if the command execution fails.

    Attributes:
        command (Command): The Command instance representing the command to be executed.
        popen (bool): Determines whether the environment call should be spawned as a
            subprocess or not (default False)
        process_log_path (Optional[str]): An optional file path to log the output of the
            command if it is spawned as a subprocess.
        cleanup (Optional[Callable[[], None]]): An optional cleanup function to be called
            if the command execution fails.
    """
    command: Command
    popen: bool = False
    process_log_path: Optional[str] = None
    cleanup: Optional[Callable[[], None]] = None


class HostEnvironment:
    """
    Interface for managing the host environment setup needed for firecracker
    MicroVMs.  This class can be used to safely execute series of Unix commands
    and control command execution flow based on success or failure of individual 
    commands.

    Attributes:
        __continue_on_error (bool): True if command execution should continue on failure
            else false.
        __exec_stack (list[EnvironmentCall]): The Command call stack.
        __process_stack (list[subprocess.Popen]): The list of subprocesses spawned by 
            the environment.
        __process_stop_timeout (int): The number of seconds to wait for a process to stop before
            force killing it.
    """

    def __init__(self, continue_on_error: bool = False, process_stop_timeout: int = 5) -> None:
        self.__continue_on_error: bool = continue_on_error
        self.__exec_stack: list[EnvironmentCall] = []
        self.__process_stack: list[subprocess.Popen] = []
        self.__process_stop_timeout: int = process_stop_timeout

    @property
    def exec_stack(self) -> list[EnvironmentCall]:
        """
        Returns the list of Command instances that are scheduled for execution.

        Returns:
            list[Command]: The list of Command instances to be executed.
        """
        return self.__exec_stack
    
    @property
    def process_stack(self) -> list[subprocess.Popen]:
        """
        Returns the list of subprocess.Popen instances that have been spawned by the environment.

        Returns:
            list[subprocess.Popen]: The list of subprocess.Popen instances representing
                the spawned processes.
        """
        return self.__process_stack

    def add_tap_device(self, tap_name: str) -> Self:
        """
        Add a TAP virtual network device to the host environment.

        Args:
            tap_name (str): The name of the TAP device to be added.   
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        cmd = Command("ip", sudo=True) \
            .add_arg("tuntap") \
            .add_args(["add", "dev", tap_name]) \
            .add_args(["mode", "tap"])
        
        def cleanup() -> None:
            self.del_tap_device(tap_name).exec()

        self.__exec_stack.append(EnvironmentCall(cmd, cleanup=cleanup))
        return self

    def del_tap_device(self, tap_name: str) -> Self:
        """
        Delete a TAP virtual network device on the host environment.

        Args:
            tap_name (str): The name of the TAP device to be added.
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        cmd = Command("ip", sudo=True) \
            .add_arg("tuntap") \
            .add_args(["del", "dev", tap_name]) \
            .add_args(["mode", "tap"])
        self.__exec_stack.append(EnvironmentCall(cmd))
        return self

    def add_tap_address(self, address: str, tap_name: str) -> Self:
        """
        Add an IP address to a TAP virtual network device in the host environment.

        Args:
            address (str): The IP address to be added to the TAP device.
            tap_name (str): The name of the TAP device to which the IP address should be added.
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        cmd = Command("ip", sudo=True) \
            .add_arg("addr") \
            .add_args(["add", f"{address}/24"]) \
            .add_args(["dev", tap_name])
        self.__exec_stack.append(EnvironmentCall(cmd))
        return self

    def set_tap_up(self, tap_name: str) -> Self:
        """
        Set the TAP virtual network device status to up in the host environment.

        Args:
            tap_name (str): The name of the TAP device.
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        cmd = Command("ip", sudo=True) \
            .add_arg("link") \
            .add_args(["set", tap_name, "up"])
        
        def cleanup() -> None:
            self.del_tap_device(tap_name).exec()

        self.__exec_stack.append(EnvironmentCall(cmd, cleanup=cleanup))
        return self

    def mkdir(self, path: str) -> Self:
        """
        Create a directory at the specified path in the host environment.

        Args:
            path (str): The path where the directory should be created.
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        cmd = Command("mkdir").add_arg(path)

        def cleanup() -> None:
            self.rm(path).exec()

        self.__exec_stack.append(EnvironmentCall(cmd, cleanup=cleanup))
        return self

    def mount(self, source: str, target: str) -> Self:
        """
        Mount a filesystem at the specified target path in the host environment.

        Args:
            source (str): The source of the filesystem to be mounted.
            target (str): The target path where the filesystem should be mounted.
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        cmd = Command("mount", sudo=True).add_args([source, target])

        def cleanup() -> None:
            self.unmount(target).exec()

        self.__exec_stack.append(EnvironmentCall(cmd, cleanup=cleanup))
        return self

    def unmount(self, path: str) -> Self:
        """
        Unmount a filesystem at the specified target path in the host environment.

        Args:
            path (str): The path of the filesystem to be unmounted.
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        cmd = Command("umount", sudo=True).add_arg(path)
        self.__exec_stack.append(EnvironmentCall(cmd))
        return self

    def copy(self, source: str, target: str) -> Self:
        """
        Copy a file from source to target path in the host environment.

        Args:
            source (str): The path of the file to be copied.
            target (str): The destination path where the file should be copied.
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        cmd = Command("cp", sudo=True).add_args([source, target])
        self.__exec_stack.append(EnvironmentCall(cmd)) # NOTE: Might need a cleanup function
        return self

    def rm(self, target: str) -> Self:
        """
        Remove the directory or file from the host environment.

        Args:
            target (str): The path of the directory or file to be deleted
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        cmd = Command("rm", sudo=True).add_args(["-f", target])
        self.__exec_stack.append(EnvironmentCall(cmd))
        return self

    def firecracker(
        self, 
        api_socket: str = "/tmp/firecracker.sock",
        logs_path: Optional[str] = None
    ) -> Self:
        """
        Run the Firecracker virtual machine manager and make the Firecracker API
        availble on the provided unix socket path.

        Args:
            api_socket (str): Path the the unix socket to run the Firecracker API on
                (default is '/tmp/firecracker.sock')
            logs_path (Optional[str]): An optional file path to log the output of the
                Firecracker process.
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        cmd = Command("firecracker", sudo=True).add_args(["--api-sock", api_socket])

        def cleanup() -> None:
            self.rm(api_socket).exec()

        self.__exec_stack.append(
            EnvironmentCall(
                cmd, 
                popen=True, 
                process_log_path=logs_path, 
                cleanup=cleanup
            )
        )
        return self

    def mount_overlay_fs(
        self, 
        base_root_fs: str,
        upper_dir: str,
        work_dir: str,
        merge_dir: str
    ) -> Self:
        """
        Mount an overlay filesystem at the specified target path in the host environment.

        Args:
            base_root_fs (str): The root file system to base the overlay off of.
            upper_dir (str): The writable layer where all modifications will appear.
            work_dir (str): An empty directory for internal filesystem operations.
            merge_dir (str): Final mount point for the overlay filesystem.
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        cmd = Command("mount", sudo=True).add_args([
            "-t", "overlay", "overlay", 
            "-o", f"lowerdir={base_root_fs},upperdir={upper_dir},workdir={work_dir}", 
            merge_dir
        ])

        def cleanup() -> None:
            self.unmount(merge_dir).exec()

        self.__exec_stack.append(EnvironmentCall(cmd, cleanup=cleanup))
        return self
    
    def modprobe(self, module_name: str) -> Self:
        """
        Load a kernel module into the host environment.

        Args:
            module_name (str): The name of the kernel module to be loaded.
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        cmd = Command("modprobe", sudo=True).add_arg(module_name)

        def cleanup() -> None:
            self.rmmod(module_name).exec()

        self.__exec_stack.append(EnvironmentCall(cmd, cleanup=cleanup))
        return self

    def rmmod(self, module_name: str) -> Self:
        """
        Remove a kernel module from the host environment.

        Args:
            module_name (str): The name of the kernel module to be removed.
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        cmd = Command("rmmod", sudo=True).add_arg(module_name)
        self.__exec_stack.append(EnvironmentCall(cmd))
        return self

    def dd(
        self, 
        if_: str, 
        of: str, 
        bs: str = "1M", 
        count: int = 512
    ) -> Self:
        """
        Use the dd command to create a file in the host environment.

        Args:
            if_ (str): The input file path.
            of (str): The output file path.
            bs (str): The block size to use for copying (default is '1M').
            count (int): The number of blocks to copy (default is 512).
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        cmd = Command("dd", sudo=True) \
            .add_args([f"if={if_}", f"of={of}", f"bs={bs}", f"count={count}"])
        
        def cleanup() -> None:
            self.rm(of).exec()

        self.__exec_stack.append(EnvironmentCall(cmd, cleanup=cleanup))
        return self

    def loosetup(self, file: str) -> Self:
        """
        Associate a file with a loop device in the host environment.

        Args:
            file (str): The file to be associated with a loop device.
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        cmd = Command("losetup", sudo=True).add_args(["-f", file])
        
        # TODO: Need some way to clean up the created device.  The problem right now is
        # that I cant get the output of losetup whic is needed to know which device to 
        # delete in the cleanup unil the command is ran.  Think of a way to handle this.
        self.__exec_stack.append(EnvironmentCall(cmd))
        return self

    def blockdev(self, operation: str, device: str) -> Self:
        """
        Execute the blockdev command on a block device in the host environment.

        Args:
            operation (str): The blockdev operation to perform (e.g., '--getsz').
            device (str): The block device path (e.g., '/dev/loop0').
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        cmd = Command("blockdev", sudo=True).add_args([operation, device])
        self.__exec_stack.append(EnvironmentCall(cmd))
        return self

    def stop_processes(self) -> Self:
        """
        Stops all running processes that were spawned with popen.
        Handles cases where processes have already terminated.
        
        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        for process in self.__process_stack:
            try:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=self.__process_stop_timeout)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Process {process.pid} did not terminate gracefully, killing it")
                        process.kill()
                        process.wait()
            except (ProcessLookupError, OSError) as e:
                logger.debug(f"Error stopping process: {e}")
        return self

    def exec(self) -> Self:
        """
        Executes all commands in the execution stack. Command execution can stop
        on command failure or continue based on the value of __continue_on_error.
        If commands are stopped on failure, cleanup functions for executed commands are called.

        Returns:
            Self: The HostEnvironment instance for method chaining.
        """
        intermediary_stack: list[EnvironmentCall] = []
        for env_call in self.__exec_stack:
            try:
                logger.debug(f"Executing environment command: {env_call.command}")
                intermediary_stack.append(env_call)
                if env_call.popen:
                    process = env_call.command.popen(log_file_path=env_call.process_log_path)
                    self.__process_stack.append(process)
                else:
                    env_call.command.run()
            except CommandError as e:
                logger.error(f"Environment execution error: {e}")
                if not self.__continue_on_error:
                    for error_env_call in reversed(intermediary_stack):
                        if error_env_call.cleanup is not None:
                            logger.debug("Executing cleanup function for failed command")
                            error_env_call.cleanup()
                    break

        self.__exec_stack = []
        return self