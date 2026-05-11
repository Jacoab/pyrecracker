from typing import Optional


class SnapshotResourceTracker:
    def __init__(self):
        """
        Initializes a new instance of the SnapshotResourceTracker class.
        """
        self.__loop_devices: list[str] = []
        self.__device_mapper_name: Optional[str] = None
        self.__overlay_file: Optional[str] = None

    def add_loop_device(self, device_path: str) -> None:
        """
        Adds a loop device to the tracker.

        Args:
            device_path (str): The path to the loop device to add.
        """
        self.__loop_devices.append(device_path)

    def add_device_mapper(self, mapper_name: str) -> None:
        """
        Adds a device mapper to the tracker.

        Args:
            mapper_name (str): The name of the device mapper to add.
        """
        self.__device_mapper_name = mapper_name

    def add_overlay_file(self, file_path: str) -> None:
        """
        Adds an overlay file to the tracker.

        Args:
            file_path (str): The path to the overlay file to add.
        """
        self.__overlay_file = file_path

    def get_loop_devices(self) -> list[str]:
        """
        Returns a copy of the list of loop devices.

        Returns:
            list[str]: A copy of the list of loop devices.
        """
        return self.__loop_devices.copy()

    def get_device_mapper_name(self) -> Optional[str]:
        """
        Returns the name of the device mapper.

        Returns:
            Optional[str]: The name of the device mapper, or None if not set.
        """
        return self.__device_mapper_name

    def get_overlay_file(self) -> Optional[str]:
        """
        Returns the path to the overlay file.

        Returns:
            Optional[str]: The path to the overlay file, or None if not set.
        """
        return self.__overlay_file
