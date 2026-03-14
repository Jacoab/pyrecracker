import pytest
from unittest.mock import patch, MagicMock
from pyrecracker.client import FirecrackerClient
from pyrecracker.client_types import (
    VM, 
    MachineConfiguration, 
    BootSource, 
    Drive, 
    InstanceActionInfo, 
    SnapshotCreateParams,
    SnapshotLoadParams, 
)


@pytest.fixture
def mock_session():
	with patch("requests_unixsocket.Session", autospec=True) as mock_cls:
		mock_instance = MagicMock()
		mock_cls.return_value = mock_instance
		yield mock_instance


def test_put_machine_config(mock_session):
	client = FirecrackerClient("/tmp/firecracker.socket")
	config = MachineConfiguration(mem_size_mib=512, vcpu_count=2)
	client.put_machine_config(config)
	mock_session.put.assert_called_once()
	args, kwargs = mock_session.put.call_args
	assert "machine-config" in args[0]
	assert kwargs["json"]["mem_size_mib"] == 512
	assert kwargs["json"]["vcpu_count"] == 2


def test_put_boot_source(mock_session):
	client = FirecrackerClient("/tmp/firecracker.socket")
	boot = BootSource(kernel_image_path="/path/to/kernel", boot_args="console=ttyS0")
	client.put_boot_source(boot)
	mock_session.put.assert_called_once()
	args, kwargs = mock_session.put.call_args
	assert "boot-source" in args[0]
	assert kwargs["json"]["kernel_image_path"] == "/path/to/kernel"
	assert kwargs["json"]["boot_args"] == "console=ttyS0"


def test_put_drives(mock_session):
	client = FirecrackerClient("/tmp/firecracker.socket")
	drive = Drive(drive_id="root", is_root_device=True, path_on_host="/path/to/root.img")
	client.put_drives(drive)
	mock_session.put.assert_called_once()
	args, kwargs = mock_session.put.call_args
	assert "drives/root" in args[0]
	assert kwargs["json"]["drive_id"] == "root"
	assert kwargs["json"]["is_root_device"] is True
	assert kwargs["json"]["path_on_host"] == "/path/to/root.img"


def test_put_actions(mock_session):
	client = FirecrackerClient("/tmp/firecracker.socket")
	action = InstanceActionInfo(action_type="InstanceStart")
	client.put_actions(action)
	mock_session.put.assert_called_once()
	args, kwargs = mock_session.put.call_args
	assert "actions" in args[0]
	assert kwargs["json"]["action_type"] == "InstanceStart"


def test_put_vm(mock_session):
	client = FirecrackerClient("/tmp/firecracker.socket")
	vm = VM(state="Running")
	client.put_vm(vm)
	mock_session.put.assert_called_once()
	args, kwargs = mock_session.put.call_args
	assert "vm" in args[0]
	assert kwargs["json"]["state"] == "Running"


def test_put_snapshot_create(mock_session):
	client = FirecrackerClient("/tmp/firecracker.socket")
	snapshot_params = SnapshotCreateParams(snapshot_path="/path/to/snapshot", mem_file_path="/path/to/memfile")
	client.put_snapshot_create(snapshot_params)
	mock_session.put.assert_called_once()
	args, kwargs = mock_session.put.call_args
	assert "snapshot/create" in args[0]
	assert kwargs["json"]["snapshot_path"] == "/path/to/snapshot"
	assert kwargs["json"]["mem_file_path"] == "/path/to/memfile"


def test_put_snapshot_load(mock_session):
	client = FirecrackerClient("/tmp/firecracker.socket")
	snapshot_load_params = SnapshotLoadParams(snapshot_path="/path/to/snapshot", resume_vm=True)
	client.put_snapshot_load(snapshot_load_params)
	mock_session.put.assert_called_once()
	args, kwargs = mock_session.put.call_args
	assert "snapshot/load" in args[0]
	assert kwargs["json"]["snapshot_path"] == "/path/to/snapshot"
	assert kwargs["json"]["resume_vm"] is True
