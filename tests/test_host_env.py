

from pyrecracker.host_env import HostEnvironment
from pyrecracker.cmd import Command, CommandError

import pytest
from unittest.mock import Mock

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


def test_add_tap_device(mock_command_run):
	executed = mock_command_run
	env = HostEnvironment() \
		.add_tap_device("tap0") \
		.exec()
	assert any("sudo ip tuntap add dev tap0 mode tap" in cmd for cmd in executed)

def test_del_tap_device(mock_command_run):
	executed = mock_command_run
	env = HostEnvironment() \
		.del_tap_device("tap0") \
		.exec()
	assert any("sudo ip tuntap del dev tap0 mode tap" in cmd for cmd in executed)

def test_add_tap_address(mock_command_run):
	executed = mock_command_run
	env = HostEnvironment() \
		.add_tap_address("192.168.1.10", "tap0") \
		.exec()
	assert any("sudo ip addr add 192.168.1.10/24 dev tap0" in cmd for cmd in executed)

def test_set_tap_up(mock_command_run):
	executed = mock_command_run
	env = HostEnvironment() \
		.set_tap_up("tap0") \
		.exec()
	assert any("sudo ip link set tap0 up" in cmd for cmd in executed)

def test_mkdir(mock_command_run):
	executed = mock_command_run
	env = HostEnvironment() \
		.mkdir("/tmp/testdir") \
		.exec()
	assert any("mkdir /tmp/testdir" in cmd for cmd in executed)

def test_mount(mock_command_run):
	executed = mock_command_run
	env = HostEnvironment() \
		.mount("/dev/sda1", "/mnt/test") \
		.exec()
	assert any("sudo mount /dev/sda1 /mnt/test" in cmd for cmd in executed)

def test_unmount(mock_command_run):
	executed = mock_command_run
	env = HostEnvironment() \
		.unmount("/mnt/test") \
		.exec()
	assert any("sudo umount /mnt/test" in cmd for cmd in executed)

def test_copy(mock_command_run):
	executed = mock_command_run
	env = HostEnvironment() \
		.copy("/tmp/source", "/tmp/target") \
		.exec()
	assert any("sudo cp /tmp/source /tmp/target" in cmd for cmd in executed)


def test_multiple_commands(mock_command_run):
	executed = mock_command_run
	env = HostEnvironment() \
		.add_tap_device("tap1") \
		.add_tap_address("192.168.1.10", "tap1") \
		.set_tap_up("tap1") \
		.exec()
	assert any("sudo ip tuntap add dev tap1 mode tap" in cmd for cmd in executed)
	assert any("sudo ip addr add 192.168.1.10/24 dev tap1" in cmd for cmd in executed)
	assert any("sudo ip link set tap1 up" in cmd for cmd in executed)


def test_cleanup_handler_on_failure(monkeypatch):
	cleanup_called = []
	call_count = [0]
	
	def fake_run(self):
		call_count[0] += 1
		# Fail on the third call (after two successful commands)
		if call_count[0] == 3:
			raise CommandError("Simulated failure")
	
	monkeypatch.setattr(Command, "run", fake_run)	
	cleanup_called = []
	
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
		.exec()

	
	assert "del_tap_device(tap0)" in cleanup_called
	assert cleanup_called.index("del_tap_device(tap0)") > 0 or len(cleanup_called) > 0


def test_add_tap_device_has_cleanup():
	env = HostEnvironment().add_tap_device("tap0")
	
	assert len(env.exec_stack) == 1
	assert env.exec_stack[0].cleanup is not None


def test_set_tap_up_has_cleanup():
	env = HostEnvironment().set_tap_up("tap0")
	
	assert len(env.exec_stack) == 1
	assert env.exec_stack[0].cleanup is not None


def test_modprobe(mock_command_run):
	executed = mock_command_run
	env = HostEnvironment() \
		.modprobe("vhost_net") \
		.exec()
	assert any("sudo modprobe vhost_net" in cmd for cmd in executed)


def test_rmmod(mock_command_run):
	executed = mock_command_run
	env = HostEnvironment() \
		.rmmod("vhost_net") \
		.exec()
	assert any("sudo rmmod vhost_net" in cmd for cmd in executed)


def test_modprobe_has_cleanup():
	env = HostEnvironment().modprobe("vhost_net")
	
	assert len(env.exec_stack) == 1
	assert env.exec_stack[0].cleanup is not None


def test_mkdir_has_cleanup():
	env = HostEnvironment().mkdir("/tmp/testdir")
	
	assert len(env.exec_stack) == 1
	assert env.exec_stack[0].cleanup is not None


def test_mount_has_cleanup():
	env = HostEnvironment().mount("/dev/sda1", "/mnt/test")
	
	assert len(env.exec_stack) == 1
	assert env.exec_stack[0].cleanup is not None


def test_rm_file(mock_command_run):
	executed = mock_command_run
	env = HostEnvironment() \
		.rm("/tmp/firecracker.sock") \
		.exec()
	assert any("rm -f /tmp/firecracker.sock" in cmd for cmd in executed)


def test_firecracker(mock_command_popen):
	executed = mock_command_popen
	env = HostEnvironment() \
		.firecracker(api_socket="/path/to/socket") \
		.exec()
	assert any("firecracker --api-sock /path/to/socket" in cmd for cmd in executed)


def test_stop_processes(mock_command_popen):
	env = HostEnvironment() \
		.firecracker(api_socket="/path/to/socket") \
		.exec()
	
	process_stack = env.process_stack
	assert len(process_stack) > 0
	
	env.stop_processes()
	
	mock_process = process_stack[0]
	mock_process.terminate.assert_called_once()


def test_stop_processes_handles_already_terminated(mock_command_popen):
	env = HostEnvironment() \
		.firecracker(api_socket="/path/to/socket") \
		.exec()
	
	process_stack = env.process_stack
	mock_process = process_stack[0]
	mock_process.poll.return_value = 0  # Return code 0 (already terminated)

	env.stop_processes()
	
	mock_process.terminate.assert_not_called()



def test_mount_overlay_fs(mock_command_run):
	executed = mock_command_run
	env = HostEnvironment()
	env.mount_overlay_fs(
		"/path/to/rootfs",
		"/path/to/upper_dir",
		"/path/to/work_dir",
		"/path/to/merge_dir",
	)
	env.exec()
	assert any("sudo mount -t overlay overlay -o lowerdir=/path/to/rootfs,upperdir=/path/to/upper_dir,workdir=/path/to/work_dir /path/to/merge_dir")


def test_dd(mock_command_run):
	executed = mock_command_run
	env = HostEnvironment() \
		.dd(if_="/dev/zero", of="rootfs.img", bs="4M", count=256) \
		.exec()
	assert any("sudo dd if=/dev/zero of=rootfs.img bs=4M count=256" in cmd for cmd in executed)


def test_dd_has_cleanup():
	env = HostEnvironment().dd(if_="/dev/zero", of="base-rootfs.ext4")
	
	assert len(env.exec_stack) == 1
	assert env.exec_stack[0].cleanup is not None
