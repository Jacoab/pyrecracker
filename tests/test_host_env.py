from pyrecracker.host_env import HostEnvironment
from pyrecracker.cmd import Command


def test_single_successful_command(monkeypatch):
	executed = []

	def fake_call(self):
		executed.append(str(self))

	monkeypatch.setattr(Command, "call", fake_call)
	env = HostEnvironment()
	env.add_tap_device("tap0")
	env.exec()
	assert executed == ["sudo ip tuntap add tap0 mode tap"]


def test_all_commands_success(monkeypatch):
	executed = []

	def fake_call(self):
		executed.append(str(self))

	monkeypatch.setattr(Command, "call", fake_call)
	env = HostEnvironment()
	env.add_tap_device("tap1")
	env.add_tap_address("192.168.1.10", "tap1")
	env.set_tap_up("tap1")
	env.exec()
	assert executed == [
		"sudo ip tuntap add tap1 mode tap",
		"sudo ip addr add 192.168.1.10/24 dev tap1",
		"sudo ip link set tap1 up"
	]


def test_failing_command(monkeypatch):
	calls = []

	def fake_call(self):
		calls.append(str(self))
		if "fail" in str(self):
			raise RuntimeError("Simulated failure")

	monkeypatch.setattr(Command, "call", fake_call)
	env = HostEnvironment()
	env.add_tap_device("failtap")
	env.add_tap_device("tap2")
	env.exec()
	assert calls == ["sudo ip tuntap add failtap mode tap"]
