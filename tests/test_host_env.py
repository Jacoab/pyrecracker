

from pyrecracker.host_env import HostEnvironment
from pyrecracker.cmd import Command

import pytest

@pytest.fixture
def mock_command_call(monkeypatch):
	executed = []
	def fake_call(self):
		executed.append(str(self))
	monkeypatch.setattr(Command, "call", fake_call)
	return executed

def test_add_tap_device(mock_command_call):
	executed = mock_command_call
	env = HostEnvironment()
	env.add_tap_device("tap0")
	env.exec()
	assert any("sudo ip tuntap add dev tap0 mode tap" in cmd for cmd in executed)

def test_del_tap_device(mock_command_call):
	executed = mock_command_call
	env = HostEnvironment()
	env.del_tap_device("tap0")
	env.exec()
	assert any("sudo ip tuntap del dev tap0 mode tap" in cmd for cmd in executed)

def test_add_tap_address(mock_command_call):
	executed = mock_command_call
	env = HostEnvironment()
	env.add_tap_address("192.168.1.10", "tap0")
	env.exec()
	assert any("sudo ip addr add 192.168.1.10/24 dev tap0" in cmd for cmd in executed)

def test_set_tap_up(mock_command_call):
	executed = mock_command_call
	env = HostEnvironment()
	env.set_tap_up("tap0")
	env.exec()
	assert any("sudo ip link set tap0 up" in cmd for cmd in executed)

def test_mkdir(mock_command_call):
	executed = mock_command_call
	env = HostEnvironment()
	env.mkdir("/tmp/testdir")
	env.exec()
	assert any("mkdir /tmp/testdir" in cmd for cmd in executed)

def test_mount(mock_command_call):
	executed = mock_command_call
	env = HostEnvironment()
	env.mount("/dev/sda1", "/mnt/test")
	env.exec()
	assert any("sudo mount /dev/sda1 /mnt/test" in cmd for cmd in executed)

def test_unmount(mock_command_call):
	executed = mock_command_call
	env = HostEnvironment()
	env.unmount("/mnt/test")
	env.exec()
	assert any("sudo umount /mnt/test" in cmd for cmd in executed)

def test_copy(mock_command_call):
	executed = mock_command_call
	env = HostEnvironment()
	env.copy("/tmp/source", "/tmp/target")
	env.exec()
	assert any("sudo cp /tmp/source /tmp/target" in cmd for cmd in executed)


def test_multiple_commands(mock_command_call):
	executed = mock_command_call
	env = HostEnvironment()
	env.add_tap_device("tap1")
	env.add_tap_address("192.168.1.10", "tap1")
	env.set_tap_up("tap1")
	env.exec()
	assert any("sudo ip tuntap add dev tap1 mode tap" in cmd for cmd in executed)
	assert any("sudo ip addr add 192.168.1.10/24 dev tap1" in cmd for cmd in executed)
	assert any("sudo ip link set tap1 up" in cmd for cmd in executed)


def test_cleanup_handler_on_failure(monkeypatch):
	cleanup_called = []
	def fake_call(self):
		raise RuntimeError("Simulated failure")
	monkeypatch.setattr(Command, "call", fake_call)
	env = HostEnvironment()
	env.add_tap_device("tap_fail", cleanup=lambda: cleanup_called.append(True))
	env.exec()
	assert cleanup_called == [True]


def test_rm_file(mock_command_call):
	executed = mock_command_call
	env = HostEnvironment()
	env.rm("/tmp/firecracker.sock")
	env.exec()
	assert any("rm -f /tmp/firecracker.sock" in cmd for cmd in executed)
