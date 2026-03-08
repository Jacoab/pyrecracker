

from pyrecracker.host_env import HostEnvironment
from pyrecracker.cmd import Command

import pytest

@pytest.fixture
def executed_and_fake_call(monkeypatch):
	executed = []
	def fake_call(self):
		executed.append(str(self))
	monkeypatch.setattr(Command, "call", fake_call)
	return executed

def test_add_tap_device(executed_and_fake_call):
	executed = executed_and_fake_call
	env = HostEnvironment()
	env.add_tap_device("tap0")
	env.exec()
	assert any("sudo ip tuntap add tap0 mode tap" in cmd for cmd in executed)

def test_add_tap_address(executed_and_fake_call):
	executed = executed_and_fake_call
	env = HostEnvironment()
	env.add_tap_address("192.168.1.10", "tap0")
	env.exec()
	assert any("sudo ip addr add 192.168.1.10/24 dev tap0" in cmd for cmd in executed)

def test_set_tap_up(executed_and_fake_call):
	executed = executed_and_fake_call
	env = HostEnvironment()
	env.set_tap_up("tap0")
	env.exec()
	assert any("sudo ip link set tap0 up" in cmd for cmd in executed)

def test_mkdir(executed_and_fake_call):
	executed = executed_and_fake_call
	env = HostEnvironment()
	env.mkdir("/tmp/testdir")
	env.exec()
	assert any("mkdir /tmp/testdir" in cmd for cmd in executed)

def test_mount(executed_and_fake_call):
	executed = executed_and_fake_call
	env = HostEnvironment()
	env.mount("/dev/sda1", "/mnt/test")
	env.exec()
	assert any("sudo mount /dev/sda1 /mnt/test" in cmd for cmd in executed)

def test_unmount(executed_and_fake_call):
	executed = executed_and_fake_call
	env = HostEnvironment()
	env.unmount("/mnt/test")
	env.exec()
	assert any("sudo umount /mnt/test" in cmd for cmd in executed)

def test_copy(executed_and_fake_call):
	executed = executed_and_fake_call
	env = HostEnvironment()
	env.copy("/tmp/source", "/tmp/target")
	env.exec()
	assert any("sudo cp /tmp/source /tmp/target" in cmd for cmd in executed)


def test_multiple_commands(executed_and_fake_call):
	executed = executed_and_fake_call
	env = HostEnvironment()
	env.add_tap_device("tap1")
	env.add_tap_address("192.168.1.10", "tap1")
	env.set_tap_up("tap1")
	env.exec()
	assert any("sudo ip tuntap add tap1 mode tap" in cmd for cmd in executed)
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
