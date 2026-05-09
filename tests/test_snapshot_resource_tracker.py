import pytest
from pyrecracker.snapshot_resource_tracker import SnapshotResourceTracker


class TestSnapshotResourceTracker:

    def test_add_loop_device(self):
        tracker = SnapshotResourceTracker()
        tracker.add_loop_device("/dev/loop0")
        
        assert "/dev/loop0" in tracker.get_loop_devices()

    def test_add_multiple_loop_devices(self):
        tracker = SnapshotResourceTracker()
        tracker.add_loop_device("/dev/loop0")
        tracker.add_loop_device("/dev/loop1")
        
        devices = tracker.get_loop_devices()
        assert len(devices) == 2
        assert "/dev/loop0" in devices
        assert "/dev/loop1" in devices

    def test_get_loop_devices_returns_copy(self):
        tracker = SnapshotResourceTracker()
        tracker.add_loop_device("/dev/loop0")
        
        devices = tracker.get_loop_devices()
        devices.append("/dev/loop999")
        
        assert len(tracker.get_loop_devices()) == 1

    def test_add_device_mapper(self):
        tracker = SnapshotResourceTracker()
        tracker.add_device_mapper("snapshot1")
        
        assert tracker.get_device_mapper_name() == "snapshot1"

    def test_add_overlay_file(self):
        tracker = SnapshotResourceTracker()
        tracker.add_overlay_file("/path/to/overlay.img")
        
        assert tracker.get_overlay_file() == "/path/to/overlay.img"

    def test_get_unset_device_mapper_returns_none(self):
        tracker = SnapshotResourceTracker()
        
        assert tracker.get_device_mapper_name() is None

    def test_get_unset_overlay_file_returns_none(self):
        tracker = SnapshotResourceTracker()
        
        assert tracker.get_overlay_file() is None

    def test_get_empty_loop_devices(self):
        tracker = SnapshotResourceTracker()
        
        assert tracker.get_loop_devices() == []

    def test_all_resources_tracked(self):
        tracker = SnapshotResourceTracker()
        tracker.add_loop_device("/dev/loop0")
        tracker.add_loop_device("/dev/loop1")
        tracker.add_device_mapper("snapshot1")
        tracker.add_overlay_file("/path/to/overlay.img")
        
        assert len(tracker.get_loop_devices()) == 2
        assert tracker.get_device_mapper_name() == "snapshot1"
        assert tracker.get_overlay_file() == "/path/to/overlay.img"
