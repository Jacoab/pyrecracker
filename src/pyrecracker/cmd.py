import subprocess
from functools import singledispatchmethod
from typing import Optional, Self
from pathlib import Path


class CommandError(Exception):
    """Custom exception for command execution errors."""
    pass


class Command:
    """
    A class to build and execute shell commands. This class supports
    adding arguments by chaining calls to `add_arg` or `add_args`.

    Attributes:
        __name (str): The base command to execute.
        __command_list (list[str]): The list of command components to be executed.
    """
    def __init__(self, name: str, sudo: bool = False) -> None:
        self.__name: str = name
        self.__command_list: list[str] = ["sudo", self.__name] if sudo else [self.__name]

    def __str__(self) -> str:
        """
        Returns the full command as a string.

        Returns:
            str: The full command string.
        """
        return " ".join(self.__command_list)
    
    def add_arg(self, arg: str) -> Self:
        """
        Adds a single argument to the command's command list.  This method
        can be chained to add multiple arguments.

        Returns:
            Command: The Command instance with the added argument.
        """
        self.__command_list.append(arg)
        return self

    @singledispatchmethod
    def add_args(self, args) -> Self:
        """
        Adds multiple arguments to the command's command list. This method 
        can be chained to add multiple arguments.
        """
        raise NotImplementedError("Unsupported type for add_args")
    
    @add_args.register
    def _(self, args: list) -> Self:
        """
        Adds a list of arguments to the command's command list. This method 
        can be chained to add multiple arguments.

        Args: 
            args (list[str]): A list of arguments to add to the command.
        Returns:
            Command: The Command instance with the added arguments.
        """
        self.__command_list.extend(args)
        return self

    @add_args.register
    def _(self, args: str) -> Self:
        """
        Adds a string of arguments to the command's command list. The string 
        is split into individual arguments based on whitespace. This method can 
        be chained to add multiple arguments.

        Args:
            args (str): A string of arguments to add to the command.
        Returns:
            Command: The Command instance with the added arguments.
        """
        args_list = args.split()
        self.__command_list.extend(args_list)
        return self
    
    def run(self) -> None:
        """
        Executes the command using subprocess.run.

        Raises:
            RuntimeError: If the command execution fails, a RuntimeError is raised with the command error code.
        """
        try:
            result = subprocess.run(self.__command_list, check=True)
            if result.returncode != 0:
                error_message = f"Command '{str(self)}' failed with exit code {result.returncode} and output: {result.stdout}"
                raise CommandError(error_message)
        except subprocess.CalledProcessError as e:
            error_message = f"Command '{str(self)}' failed with exit code {e.returncode}"
            raise CommandError(error_message) from e

    def popen(self, log_file_path: Optional[str] = None) -> subprocess.Popen:
        """
        Executes the command by spawning a background process using subprocess.Popen.
        Returns the Popen object to allow the caller to maintain a reference to the process.

        Returns:
            subprocess.Popen: The Popen object representing the spawned process.
            log_file_path (str): The path to the log file where the command's 
                output will be written.

        Raises:
            RuntimeError: If the command execution fails, a RuntimeError is raised with the command error code.
        """
        try:
            if log_file_path is None:
                process = subprocess.Popen(
                    self.__command_list, 
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL
                )
                return process
            path = Path(log_file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as log_file:
                process = subprocess.Popen(
                    self.__command_list, 
                    stdin=subprocess.DEVNULL,
                    stdout=log_file,
                    stderr=log_file
                )
                return process
        except subprocess.CalledProcessError as e:
            error_message = f"Command '{str(self)}' failed with exit code {e.returncode}"
            raise CommandError(error_message) from e