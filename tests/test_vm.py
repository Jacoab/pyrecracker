import pytest
from unittest.mock import MagicMock, patch
from requests.exceptions import HTTPError, ConnectionError

from pyrecracker.client_types import ActionType, VMState
from pyrecracker.vm import VMManager, VMError


@pytest.fixture
def mock_host_env(monkeypatch):
	mock_env = MagicMock()
	mock_env.firecracker.return_value = mock_env
	mock_env.exec.return_value = mock_env
	mock_env.batch_exec.return_value = mock_env
	monkeypatch.setattr("pyrecracker.vm.HostEnvironment", lambda: mock_env)
	return mock_env


@pytest.fixture
def mock_client(monkeypatch):
	mock = MagicMock()
	mock.socket_path = "/tmp/firecracker.sock"
	monkeypatch.setattr("pyrecracker.vm.FirecrackerClient", lambda socket_path: mock)
	return mock


@pytest.fixture
def vm_manager(mock_host_env, mock_client):
	return VMManager(
		socket_path="/tmp/firecracker.sock",
		kernel_image_path="/path/to/kernel",
		firecracker_logs_path="logs/firecracker.log"
	)


class TestVMManagerInitialization:

	def test_init_creates_host_environment(self, mock_host_env, mock_client):
		vm = VMManager(
			socket_path="/tmp/firecracker.sock",
			kernel_image_path="/path/to/kernel",
			firecracker_logs_path="logs/firecracker.log"
		)

		mock_host_env.firecracker.assert_called_once()
		args, kwargs = mock_host_env.firecracker.call_args
		assert kwargs["api_socket"] == "/tmp/firecracker.sock"
		assert kwargs["logs_path"] == "logs/firecracker.log"
		mock_host_env.batch_exec.assert_called_once()

	def test_init_creates_firecracker_client(self, mock_host_env):
		with patch("pyrecracker.vm.FirecrackerClient") as mock_client_class:
			vm = VMManager(
				socket_path="/custom/socket/path.sock",
				kernel_image_path="/path/to/kernel"
			)
			mock_client_class.assert_called_once_with("/custom/socket/path.sock")

	def test_init_sets_default_boot_source(self, vm_manager):
		assert vm_manager.kernel_image_path == "/path/to/kernel"
		assert "console=ttyS0" in vm_manager.boot_args
		assert "reboot=k" in vm_manager.boot_args

	def test_init_sets_default_machine_config(self, vm_manager):
		assert vm_manager.vcpu_count == 1
		assert vm_manager.mem_size_mib == 128

	def test_init_sets_default_drive_config(self, vm_manager):
		assert vm_manager.drive_id == "rootfs"
		assert vm_manager.is_root_device is True

	def test_init_sets_default_network_interface_config(self, vm_manager):
		assert vm_manager.iface_id == "eth0"
		assert vm_manager.host_dev_name == "tap0"


class TestSetupHostNetworking:

	def test_setup_host_networking_with_both_ips(self, mock_host_env, mock_client):
		# Create fresh mock for this test
		mock_host_env.reset_mock()
		mock_host_env.add_tap_device.return_value = mock_host_env
		mock_host_env.add_tap_address.return_value = mock_host_env
		mock_host_env.set_tap_up.return_value = mock_host_env
		
		vm = VMManager(
			socket_path="/tmp/firecracker.sock",
			kernel_image_path="/path/to/kernel"
		)
		vm.host_ip = "192.168.1.1"
		vm.guest_ip = "192.168.1.2"
		mock_host_env.reset_mock()

		vm.setup_host_networking()

		mock_host_env.add_tap_device.assert_called_once_with("tap0")
		mock_host_env.add_tap_address.assert_called_once_with("192.168.1.1", "tap0")
		mock_host_env.set_tap_up.assert_called_once_with("tap0")
		mock_host_env.batch_exec.assert_called_once()

	def test_setup_host_networking_without_host_ip(self, vm_manager):
		vm_manager.host_ip = None
		vm_manager.guest_ip = "192.168.1.2"

		with pytest.raises(VMError):
			vm_manager.setup_host_networking()

	def test_setup_host_networking_without_guest_ip(self, vm_manager):
		vm_manager.host_ip = "192.168.1.1"
		vm_manager.guest_ip = None

		with pytest.raises(VMError):
			vm_manager.setup_host_networking()

	def test_setup_host_networking_without_any_ip(self, vm_manager):
		vm_manager.host_ip = None
		vm_manager.guest_ip = None

		with pytest.raises(VMError):
			vm_manager.setup_host_networking()


class TestConfigure:

	def test_configure_with_ips(self, mock_client, mock_host_env):
		# Create fresh mock for this test
		mock_host_env.reset_mock()
		mock_host_env.add_tap_device.return_value = mock_host_env
		mock_host_env.add_tap_address.return_value = mock_host_env
		mock_host_env.set_tap_up.return_value = mock_host_env
		
		vm = VMManager(
			socket_path="/tmp/firecracker.sock",
			kernel_image_path="/path/to/kernel"
		)
		vm.host_ip = "192.168.1.1"
		vm.guest_ip = "192.168.1.2"
		mock_host_env.reset_mock()
		mock_client.reset_mock()

		vm.configure()

		mock_host_env.add_tap_device.assert_called_once()
		mock_host_env.batch_exec.assert_called()

		mock_client.put_machine_config.assert_called_once()
		mock_client.put_boot_source.assert_called_once()
		mock_client.put_drives.assert_called_once()
		mock_client.put_network_interfaces.assert_called_once()

	def test_configure_without_ips_skips_networking(self, vm_manager, mock_client, mock_host_env):
		vm_manager.host_ip = None
		vm_manager.guest_ip = None
		mock_host_env.reset_mock()
		mock_client.reset_mock()

		with pytest.raises(VMError):
			vm_manager.configure()

		mock_client.put_machine_config.assert_not_called()

	def test_configure_client_http_error(self, vm_manager, mock_client):
		mock_client.put_machine_config.side_effect = HTTPError("HTTP 400 Bad Request")
		vm_manager.host_ip = "192.168.1.1"
		vm_manager.guest_ip = "192.168.1.2"

		with pytest.raises(VMError):
			vm_manager.configure()

	def test_configure_client_connection_error(self, vm_manager, mock_client):
		mock_client.put_boot_source.side_effect = ConnectionError("Connection refused")
		vm_manager.host_ip = "192.168.1.1"
		vm_manager.guest_ip = "192.168.1.2"

		with pytest.raises(VMError):
			vm_manager.configure()

	def test_configure_passes_correct_config_objects(self, vm_manager, mock_client):
		vm_manager.host_ip = "192.168.1.1"
		vm_manager.guest_ip = "192.168.1.2"
		vm_manager.vcpu_count = 2
		vm_manager.mem_size_mib = 256

		vm_manager.configure()

		machine_config_call = mock_client.put_machine_config.call_args[0][0]
		assert machine_config_call.vcpu_count == 2
		assert machine_config_call.mem_size_mib == 256

		boot_source_call = mock_client.put_boot_source.call_args[0][0]
		assert boot_source_call.kernel_image_path == "/path/to/kernel"

		drive_call = mock_client.put_drives.call_args[0][0]
		assert drive_call.drive_id == "rootfs"
		assert drive_call.is_root_device is True

		iface_call = mock_client.put_network_interfaces.call_args[0][0]
		assert iface_call.iface_id == "eth0"
		assert iface_call.host_dev_name == "tap0"


class TestCreateSnapshot:

	def test_create_snapshot_calls_client(self, vm_manager, mock_client):
		vm_manager.create_snapshot(
			snapshot_path="/path/to/snapshot",
			mem_file_path="/path/to/memory",
		)

		mock_client.put_snapshot_create.assert_called_once()
		snapshot_params = mock_client.put_snapshot_create.call_args[0][0]
		assert snapshot_params.snapshot_path == "/path/to/snapshot"
		assert snapshot_params.mem_file_path == "/path/to/memory"
		assert snapshot_params.snapshot_type == "Full"

	def test_create_snapshot_default_type(self, vm_manager, mock_client):
		vm_manager.create_snapshot(
			snapshot_path="/path/to/snapshot",
			mem_file_path="/path/to/memory"
		)

		snapshot_params = mock_client.put_snapshot_create.call_args[0][0]
		assert snapshot_params.snapshot_type == "Full"

	def test_create_snapshot_http_error(self, vm_manager, mock_client):
		mock_client.put_snapshot_create.side_effect = HTTPError("HTTP error")

		with pytest.raises(VMError):
			vm_manager.create_snapshot("/path/to/snapshot", "/path/to/memory")

	def test_create_snapshot_connection_error(self, vm_manager, mock_client):
		mock_client.put_snapshot_create.side_effect = ConnectionError("Connection error")

		with pytest.raises(VMError):
			vm_manager.create_snapshot("/path/to/snapshot", "/path/to/memory")


class TestLoadSnapshot:

	def test_load_snapshot_calls_client(self, vm_manager, mock_client):
		vm_manager.load_snapshot(
			snapshot_path="/path/to/snapshot",
			mem_file_path="/path/to/memory",
			resume_vm=True
		)

		mock_client.put_snapshot_load.assert_called_once()
		snapshot_params = mock_client.put_snapshot_load.call_args[0][0]
		assert snapshot_params.snapshot_path == "/path/to/snapshot"
		assert snapshot_params.mem_file_path == "/path/to/memory"
		assert snapshot_params.resume_vm is True

	def test_load_snapshot_optional_memory_file(self, vm_manager, mock_client):
		vm_manager.load_snapshot(snapshot_path="/path/to/snapshot")

		snapshot_params = mock_client.put_snapshot_load.call_args[0][0]
		assert snapshot_params.snapshot_path == "/path/to/snapshot"
		assert snapshot_params.mem_file_path is None

	def test_load_snapshot_uses_track_dirty_pages_setting(self, vm_manager, mock_client):
		vm_manager.track_dirty_pages = True
		vm_manager.load_snapshot(snapshot_path="/path/to/snapshot")

		snapshot_params = mock_client.put_snapshot_load.call_args[0][0]
		assert snapshot_params.track_dirty_pages is True

	def test_load_snapshot_http_error(self, vm_manager, mock_client):
		mock_client.put_snapshot_load.side_effect = HTTPError("HTTP error")

		with pytest.raises(VMError):
			vm_manager.load_snapshot("/path/to/snapshot")

	def test_load_snapshot_connection_error(self, vm_manager, mock_client):
		mock_client.put_snapshot_load.side_effect = ConnectionError("Connection error")

		with pytest.raises(VMError):
			vm_manager.load_snapshot("/path/to/snapshot")


class TestVMLifecycle:

	def test_start_calls_client(self, vm_manager, mock_client):
		vm_manager.start()

		mock_client.put_actions.assert_called_once()
		action_info = mock_client.put_actions.call_args[0][0]
		assert action_info.action_type == "InstanceStart"

	def test_start_http_error(self, vm_manager, mock_client):
		mock_client.put_actions.side_effect = HTTPError("HTTP error")

		with pytest.raises(VMError):
			vm_manager.start()

	def test_start_connection_error(self, vm_manager, mock_client):
		mock_client.put_actions.side_effect = ConnectionError("Connection error")

		with pytest.raises(VMError):
			vm_manager.start()

	def test_pause_calls_client(self, vm_manager, mock_client):
		vm_manager.pause()

		mock_client.patch_vm.assert_called_once()
		vm_obj = mock_client.patch_vm.call_args[0][0]
		assert vm_obj.state == "Paused"

	def test_pause_http_error(self, vm_manager, mock_client):
		mock_client.patch_vm.side_effect = HTTPError("HTTP error")

		with pytest.raises(VMError):
			vm_manager.pause()

	def test_pause_connection_error(self, vm_manager, mock_client):
		mock_client.patch_vm.side_effect = ConnectionError("Connection error")

		with pytest.raises(VMError):
			vm_manager.pause()

	def test_resume_calls_client(self, vm_manager, mock_client):
		vm_manager.resume()

		mock_client.patch_vm.assert_called_once()
		vm_obj = mock_client.patch_vm.call_args[0][0]
		assert vm_obj.state == VMState.RESUMED

	def test_resume_http_error(self, vm_manager, mock_client):
		mock_client.patch_vm.side_effect = HTTPError("HTTP error")

		with pytest.raises(VMError):
			vm_manager.resume()

	def test_resume_connection_error(self, vm_manager, mock_client):
		mock_client.patch_vm.side_effect = ConnectionError("Connection error")

		with pytest.raises(VMError):
			vm_manager.resume()

	def test_stop_calls_client(self, vm_manager, mock_client):
		vm_manager.stop()

		mock_client.put_actions.assert_called_once()
		action_info = mock_client.put_actions.call_args[0][0]
		assert action_info.action_type == ActionType.SEND_CTRL_ALT_DEL

	def test_stop_http_error(self, vm_manager, mock_client):
		mock_client.put_actions.side_effect = HTTPError("HTTP error")

		with pytest.raises(VMError):
			vm_manager.stop()

	def test_stop_ignores_connection_error(self, vm_manager, mock_client):
		mock_client.put_actions.side_effect = ConnectionError("Connection closed")

		vm_manager.stop()

	def test_stop_pauses_before_cleanup(self, vm_manager, mock_client):
		with patch("pyrecracker.vm.sleep") as mock_sleep:
			vm_manager.host_env_cleanup_pause = 3
			vm_manager.stop()

			mock_sleep.assert_called_once_with(3)

	def test_stop_uses_custom_cleanup_pause(self, vm_manager, mock_client):
		with patch("pyrecracker.vm.sleep") as mock_sleep:
			vm_manager.host_env_cleanup_pause = 5
			vm_manager.stop()

			mock_sleep.assert_called_once_with(5)


class TestCreateCowDevSnapshot:

	def test_create_cow_dev_snapshot_calls_host_env_methods(self, mock_host_env, mock_client):
		# Configure batch_exec to return mock_host_env so the initialization chain works
		mock_host_env.batch_exec.return_value = mock_host_env
		mock_host_env.modprobe.return_value = mock_host_env
		mock_host_env.dd.return_value = mock_host_env
		mock_host_env.losetup.return_value = mock_host_env
		mock_host_env.blockdev.return_value = mock_host_env
		mock_host_env.exec.return_value = "8192"  # blockdev returns size as numeric string

		vm = VMManager(
			socket_path="/tmp/firecracker.sock",
			kernel_image_path="/path/to/kernel"
		)
		mock_host_env.reset_mock()
		mock_host_env.modprobe.return_value = mock_host_env
		mock_host_env.dd.return_value = mock_host_env
		mock_host_env.losetup.return_value = mock_host_env
		mock_host_env.blockdev.return_value = mock_host_env
		mock_host_env.exec.return_value = "8192"

		vm.create_cow_dev_snapshot(
			snapshot_name="test_snapshot",
			base_root_fs="/path/to/rootfs.img"
		)

		mock_host_env.modprobe.assert_called_once_with("dm_snapshot")
		assert mock_host_env.dd.call_count >= 2
		assert mock_host_env.losetup.call_count >= 2
		mock_host_env.blockdev.assert_called_once()
		mock_host_env.create_dev_mapper_snapshot.assert_called_once()

	def test_create_cow_dev_snapshot_creates_dev_mapper_snapshot(self, mock_host_env, mock_client):
		mock_host_env.batch_exec.return_value = mock_host_env
		mock_host_env.modprobe.return_value = mock_host_env
		mock_host_env.dd.return_value = mock_host_env
		mock_host_env.losetup.return_value = mock_host_env
		mock_host_env.blockdev.return_value = mock_host_env
		mock_host_env.exec.return_value = "8192"

		vm = VMManager(
			socket_path="/tmp/firecracker.sock",
			kernel_image_path="/path/to/kernel"
		)
		mock_host_env.reset_mock()
		mock_host_env.modprobe.return_value = mock_host_env
		mock_host_env.dd.return_value = mock_host_env
		mock_host_env.losetup.return_value = mock_host_env
		mock_host_env.blockdev.return_value = mock_host_env
		mock_host_env.exec.return_value = "8192"

		vm.create_cow_dev_snapshot(
			snapshot_name="test_snapshot",
			base_root_fs="/path/to/rootfs.img"
		)

		mock_host_env.create_dev_mapper_snapshot.assert_called_once()
		call_args = mock_host_env.create_dev_mapper_snapshot.call_args[0]
		assert call_args[0] == "test_snapshot"
		assert call_args[1] == 0
		assert call_args[2] == 8192
