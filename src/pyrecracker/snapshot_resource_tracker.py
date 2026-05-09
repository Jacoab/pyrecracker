from typing import Optional


class SnapshotResourceTracker:
    def __init__(self):
        self.__loop_devices: list[str] = []
        self.__device_mapper_name: Optional[str] = None
        self.__overlay_file: Optional[str] = None

    def add_loop_device(self, device_path: str) -> None:
        self.__loop_devices.append(device_path)

    def add_device_mapper(self, mapper_name: str) -> None:
        self.__device_mapper_name = mapper_name

    def add_overlay_file(self, file_path: str) -> None:
        self.__overlay_file = file_path

    def get_loop_devices(self) -> list[str]:
        return self.__loop_devices.copy()

    def get_device_mapper_name(self) -> Optional[str]:
        return self.__device_mapper_name

    def get_overlay_file(self) -> Optional[str]:
        return self.__overlay_file
