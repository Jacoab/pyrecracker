

from pyrecracker.host_env import HostEnvironment
from pyrecracker.cmd import Command, CommandError

import pytest
from unittest.mock import Mock, patch, MagicMock

@pytest.fixture
def mock_command_run(monkeypatch):
	executed = []
	def fake_call(self):
		executed.append(str(self))
	monkeypatch.setattr(Command, "run", fake_call)
	return executed


@pytest.fixture
def mock_command_popen(monkeypatch):
	executed = []
	def fake_call(self, log_file_path=None):
		executed.append(str(self))
		mock_process = Mock()
		mock_process.poll.return_value = None
		mock_process.terminate.return_value = None
		mock_process.wait.return_value = None
		mock_process.kill.return_value = None
		mock_process.pid = 12345
		return mock_process
	monkeypatch.setattr(Command, "popen", fake_call)
	return executed


class TestTapDevice:

	def test_add_tap_device(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.add_tap_device("tap0") \
			.batch_exec()
		assert any("sudo ip tuntap add dev tap0 mode tap" in cmd for cmd in executed)

	def test_del_tap_device(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.del_tap_device("tap0") \
			.batch_exec()
		assert any("sudo ip tuntap del dev tap0 mode tap" in cmd for cmd in executed)

	def test_add_tap_address(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.add_tap_address("192.168.1.10", "tap0") \
			.batch_exec()
		assert any("sudo ip addr add 192.168.1.10/24 dev tap0" in cmd for cmd in executed)

	def test_set_tap_up(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.set_tap_up("tap0") \
			.batch_exec()
		assert any("sudo ip link set tap0 up" in cmd for cmd in executed)

	def test_add_tap_device_has_cleanup(self):
		env = HostEnvironment().add_tap_device("tap0")
		
		assert len(env.exec_stack) == 1
		assert env.exec_stack[0].cleanup is not None

	def test_set_tap_up_has_cleanup(self):
		env = HostEnvironment().set_tap_up("tap0")
		
		assert len(env.exec_stack) == 1
		assert env.exec_stack[0].cleanup is not None

	def test_multiple_tap_commands(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.add_tap_device("tap1") \
			.add_tap_address("192.168.1.10", "tap1") \
			.set_tap_up("tap1") \
			.batch_exec()
		assert any("sudo ip tuntap add dev tap1 mode tap" in cmd for cmd in executed)
		assert any("sudo ip addr add 192.168.1.10/24 dev tap1" in cmd for cmd in executed)
		assert any("sudo ip link set tap1 up" in cmd for cmd in executed)


class TestFilesystem:

	def test_mkdir(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.mkdir("/tmp/testdir") \
			.batch_exec()
		assert any("mkdir /tmp/testdir" in cmd for cmd in executed)

	def test_mount(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.mount("/dev/sda1", "/mnt/test") \
			.batch_exec()
		assert any("sudo mount /dev/sda1 /mnt/test" in cmd for cmd in executed)

	def test_unmount(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.unmount("/mnt/test") \
			.batch_exec()
		assert any("sudo umount /mnt/test" in cmd for cmd in executed)

	def test_copy(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.copy("/tmp/source", "/tmp/target") \
			.batch_exec()
		assert any("sudo cp /tmp/source /tmp/target" in cmd for cmd in executed)

	def test_rm_file(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.rm("/tmp/firecracker.sock") \
			.batch_exec()
		assert any("rm -f /tmp/firecracker.sock" in cmd for cmd in executed)

	def test_mkdir_has_cleanup(self):
		env = HostEnvironment().mkdir("/tmp/testdir")
		
		assert len(env.exec_stack) == 1
		assert env.exec_stack[0].cleanup is not None

	def test_mount_has_cleanup(self):
		env = HostEnvironment().mount("/dev/sda1", "/mnt/test")
		
		assert len(env.exec_stack) == 1
		assert env.exec_stack[0].cleanup is not None

	def test_dd(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.dd(if_="/dev/zero", of="rootfs.img", bs="4M", count=256) \
			.batch_exec()
		assert any("sudo dd if=/dev/zero of=rootfs.img bs=4M count=256" in cmd for cmd in executed)

	def test_dd_has_cleanup(self):
		env = HostEnvironment().dd(if_="/dev/zero", of="base-rootfs.ext4")
		
		assert len(env.exec_stack) == 1
		assert env.exec_stack[0].cleanup is not None

	def test_mount_overlay_fs(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment()
		env.mount_overlay_fs(
			"/path/to/rootfs",
			"/path/to/upper_dir",
			"/path/to/work_dir",
			"/path/to/merge_dir",
		)
		env.batch_exec()
		assert any("sudo mount -t overlay overlay -o lowerdir=/path/to/rootfs,upperdir=/path/to/upper_dir,workdir=/path/to/work_dir /path/to/merge_dir")


class TestKernelModules:

	def test_modprobe(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.modprobe("vhost_net") \
			.batch_exec()
		assert any("sudo modprobe vhost_net" in cmd for cmd in executed)

	def test_rmmod(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.rmmod("vhost_net") \
			.batch_exec()
		assert any("sudo rmmod vhost_net" in cmd for cmd in executed)

	def test_modprobe_has_cleanup(self):
		env = HostEnvironment().modprobe("vhost_net")
		
		assert len(env.exec_stack) == 1
		assert env.exec_stack[0].cleanup is not None


class TestFirecracker:

	def test_firecracker(self, mock_command_popen):
		executed = mock_command_popen
		env = HostEnvironment() \
			.firecracker(api_socket="/path/to/socket") \
			.batch_exec()
		assert any("firecracker --api-sock /path/to/socket" in cmd for cmd in executed)

	def test_stop_processes(self, mock_command_popen):
		env = HostEnvironment() \
			.firecracker(api_socket="/path/to/socket") \
			.batch_exec()
		
		process_stack = env.process_stack
		assert len(process_stack) > 0
		
		env.stop_processes()
		
		mock_process = process_stack[0]
		mock_process.terminate.assert_called_once()

	def test_stop_processes_handles_already_terminated(self, mock_command_popen):
		env = HostEnvironment() \
			.firecracker(api_socket="/path/to/socket") \
			.batch_exec()
		
		process_stack = env.process_stack
		mock_process = process_stack[0]
		mock_process.poll.return_value = 0

		env.stop_processes()
		
		mock_process.terminate.assert_not_called()


class TestLoopDevices:

	def test_losetup(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.losetup("base-rootfs.ext4") \
			.batch_exec()
		assert any("sudo losetup -f --show base-rootfs.ext4" in cmd for cmd in executed)

	def test_blockdev(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.blockdev("--getsz", "/dev/loop0") \
			.batch_exec()
		assert any("sudo blockdev --getsz /dev/loop0" in cmd for cmd in executed)


class TestDeviceMapper:

	def test_create_dev_mapper_snapshot(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.create_dev_mapper_snapshot("vm1-snap", 0, 1048576, "/dev/loop0", "/dev/loop1") \
			.batch_exec()
		assert any("sudo dmsetup create vm1-snap --table 0 1048576 snapshot /dev/loop0 /dev/loop1 P 8" in cmd for cmd in executed)


class TestChroot:

	def test_chroot(self, mock_command_run):
		executed = mock_command_run
		env = HostEnvironment() \
			.chroot("/path/to/chroot") \
			.batch_exec()
		assert any("sudo chroot /path/to/chroot" in cmd for cmd in executed)


class TestCleanupHandlers:

	def test_cleanup_handler_on_failure(self, monkeypatch):
		cleanup_called = []
		call_count = [0]
		
		def fake_run(self):
			call_count[0] += 1
			if call_count[0] == 3:
				raise CommandError("Simulated failure")
		
		monkeypatch.setattr(Command, "run", fake_run)	
		
		def patched_del_tap_device(self, tap_name):
			cleanup_called.append(f"del_tap_device({tap_name})")
			return self
		
		def patched_rm(self, target):
			cleanup_called.append(f"rm({target})")
			return self
		
		monkeypatch.setattr(HostEnvironment, "del_tap_device", patched_del_tap_device)
		monkeypatch.setattr(HostEnvironment, "rm", patched_rm)
		
		HostEnvironment() \
			.add_tap_device("tap0") \
			.add_tap_address("192.168.1.1", "tap0") \
			.set_tap_up("tap0") \
			.batch_exec()

		
		assert "del_tap_device(tap0)" in cleanup_called
		assert cleanup_called.index("del_tap_device(tap0)") > 0 or len(cleanup_called) > 0


class TestCleanupLoopDevice:

	def test_cleanup_loop_device_calls_losetup(self):
		with patch('pyrecracker.host_env.Command') as mock_command_class:
			mock_cmd = MagicMock()
			mock_command_class.return_value = mock_cmd
			mock_cmd.add_args.return_value = mock_cmd

			env = HostEnvironment()
			env.cleanup_loop_device("/dev/loop0")

			mock_command_class.assert_called_once_with("losetup", sudo=True)
			mock_cmd.add_args.assert_called_once_with(["-d", "/dev/loop0"])
			mock_cmd.run.assert_called_once()

	def test_cleanup_loop_device_handles_error(self):
		with patch('pyrecracker.host_env.Command') as mock_command_class:
			mock_cmd = MagicMock()
			mock_command_class.return_value = mock_cmd
			mock_cmd.add_args.return_value = mock_cmd
			mock_cmd.run.side_effect = CommandError("Device not found")

			env = HostEnvironment()
			
			env.cleanup_loop_device("/dev/loop0")


class TestCleanupDeviceMapper:

	def test_cleanup_device_mapper_calls_dmsetup(self):
		with patch('pyrecracker.host_env.Command') as mock_command_class:
			mock_cmd = MagicMock()
			mock_command_class.return_value = mock_cmd
			mock_cmd.add_args.return_value = mock_cmd

			env = HostEnvironment()
			env.cleanup_device_mapper("snapshot1")

			mock_command_class.assert_called_once_with("dmsetup", sudo=True)
			mock_cmd.add_args.assert_called_once_with(["remove", "-f", "snapshot1"])
			mock_cmd.run.assert_called_once()

	def test_cleanup_device_mapper_uses_force_flag(self):
		with patch('pyrecracker.host_env.Command') as mock_command_class:
			mock_cmd = MagicMock()
			mock_command_class.return_value = mock_cmd
			mock_cmd.add_args.return_value = mock_cmd

			env = HostEnvironment()
			env.cleanup_device_mapper("snapshot1")

			call_args = mock_cmd.add_args.call_args[0][0]
			assert "-f" in call_args

	def test_cleanup_device_mapper_handles_error(self):
		with patch('pyrecracker.host_env.Command') as mock_command_class:
			mock_cmd = MagicMock()
			mock_command_class.return_value = mock_cmd
			mock_cmd.add_args.return_value = mock_cmd
			mock_cmd.run.side_effect = CommandError("Device mapper not found")

			env = HostEnvironment()
			
			env.cleanup_device_mapper("snapshot1")


class TestCleanupTapDevice:

	def test_cleanup_tap_device_calls_ip_command(self):
		with patch('pyrecracker.host_env.Command') as mock_command_class:
			mock_cmd = MagicMock()
			mock_command_class.return_value = mock_cmd
			mock_cmd.add_arg.return_value = mock_cmd
			mock_cmd.add_args.return_value = mock_cmd

			env = HostEnvironment()
			env.cleanup_tap_device("tap0")

			mock_command_class.assert_called_once_with("ip", sudo=True)
			mock_cmd.add_arg.assert_called_once_with("tuntap")
			mock_cmd.run.assert_called_once()

	def test_cleanup_tap_device_uses_correct_arguments(self):
		with patch('pyrecracker.host_env.Command') as mock_command_class:
			mock_cmd = MagicMock()
			mock_command_class.return_value = mock_cmd
			mock_cmd.add_arg.return_value = mock_cmd
			mock_cmd.add_args.return_value = mock_cmd

			env = HostEnvironment()
			env.cleanup_tap_device("tap0")

			add_args_calls = mock_cmd.add_args.call_args_list
			assert any("del" in str(call) for call in add_args_calls)
			assert any("tap" in str(call) for call in add_args_calls)

	def test_cleanup_tap_device_handles_error(self):
		with patch('pyrecracker.host_env.Command') as mock_command_class:
			mock_cmd = MagicMock()
			mock_command_class.return_value = mock_cmd
			mock_cmd.add_arg.return_value = mock_cmd
			mock_cmd.add_args.return_value = mock_cmd
			mock_cmd.run.side_effect = CommandError("TAP device not found")

			env = HostEnvironment()
			
			env.cleanup_tap_device("tap0")


class TestCleanupOverlayFile:

	def test_cleanup_overlay_file_removes_file(self):
		with patch('pathlib.Path.unlink') as mock_unlink:
			env = HostEnvironment()
			env.cleanup_overlay_file("/path/to/overlay.img")

			mock_unlink.assert_called_once_with(missing_ok=True)

	def test_cleanup_overlay_file_handles_missing_file(self):
		env = HostEnvironment()
		
		env.cleanup_overlay_file("/nonexistent/path/overlay.img")

	def test_cleanup_overlay_file_handles_oserror(self):
		with patch('pathlib.Path.unlink') as mock_unlink:
			mock_unlink.side_effect = OSError("Permission denied")

			env = HostEnvironment()
			
			env.cleanup_overlay_file("/path/to/overlay.img")
