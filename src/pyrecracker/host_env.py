import shutil
from logging import getLogger

from pyrecracker.cmd import Command


logger = getLogger(__name__)


class HostEnvironment:
    """
    Interface for managing the host environment setup needed for firecracker
    MicroVMs.  This class can be used to safely execute series of Unix commands
    and control command execution flow based on success or failure of individual 
    commands.

    Attributes:
        __continue_on_error (bool): True if command execution should continue on failure
            else false.
        __exec_stack (list[Command]): The list of Command instances to be called.
    """

    def __init__(self, continue_on_error: bool = False) -> None:
        self.__continue_on_error: bool = continue_on_error
        self.__exec_stack: list[Command] = []

    @property
    def exec_stack(self) -> list[Command]:
        """
        Returns the list of Command instances that are scheduled for execution.

        Returns:
            list[Command]: The list of Command instances to be executed.
        """
        return self.__exec_stack

    def add_tap_device(self, tap_name: str) -> None:
        """
        Add a TAP virtual network device to the host environment.
        """
        cmd = Command("ip", sudo=True) \
            .add_arg("tuntap") \
            .add_args(["add", tap_name]) \
            .add_args(["mode", "tap"])
        self.__exec_stack.append(cmd)

    def add_tap_address(self, address: str, tap_name: str) -> None:
        """
        Add an IP address to a TAP virtual network device in the host environment.
        """
        cmd = Command("ip", sudo=True) \
            .add_arg("addr") \
            .add_args(["add", f"{address}/24"]) \
            .add_args(["dev", tap_name])
        self.__exec_stack.append(cmd)

    def set_tap_up(self, tap_name: str) -> None:
        """
        Set the TAP virtual network device status to up in the host environment.
        """
        cmd = Command("ip", sudo=True) \
            .add_arg("link") \
            .add_args(["set", tap_name, "up"])
        self.__exec_stack.append(cmd)

    def mkdir(self, path: str) -> None:
        """
        Create a directory at the specified path in the host environment.

        Args:
            path (str): The path where the directory should be created.
        """
        cmd = Command("mkdir").add_arg(path)
        self.__exec_stack.append(cmd)

    def mount(self, source: str, target: str) -> None:
        """
        Mount a filesystem at the specified target path in the host environment.

        Args:
            source (str): The source of the filesystem to be mounted.
            target (str): The target path where the filesystem should be mounted.
        """
        cmd = Command("mount", sudo=True).add_args([source, target])
        self.__exec_stack.append(cmd)

    def unmount(self, path: str) -> None:
        """
        Unmount a filesystem at the specified target path in the host environment.

        Args:
            path (str): The path of the filesystem to be unmounted.
        """
        cmd = Command("umount", sudo=True).add_arg(path)
        self.__exec_stack.append(cmd)

    def copy(self, source: str, target: str) -> None:
        """
        Copy a file from source to target path in the host environment.

        Args:
            source (str): The path of the file to be copied.
            target (str): The destination path where the file should be copied.
        """
        cmd = Command("cp", sudo=True).add_args([source, target])
        self.__exec_stack.append(cmd)

    def exec(self) -> None:
        """
        Executes all commands in the execution stack.  Commands execution can stop
        on command failure or continue based on the value of the __continue_on_error.
        """
        for cmd in self.__exec_stack:
            try:
                logger.debug(f"Executing environment command: {cmd}")
                cmd.call()
            except RuntimeError as e:
                logger.error(f"Environment execution error: {e}")
                if not self.__continue_on_error:
                    break
