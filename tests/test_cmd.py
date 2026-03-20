import subprocess
from pyrecracker.cmd import Command

import pytest


def test_simple_command_str():
	cmd = Command("echo").add_arg("hello")
	assert str(cmd) == "echo hello"
	

def test_complex_command_str_list_args():
	cmd = Command("ip", sudo=True).add_args(["link", "add", "name", "eth0", "type", "dummy"])
	assert str(cmd) == "sudo ip link add name eth0 type dummy"


def test_complex_command_str_string_args():
	cmd = Command("ls", sudo=True).add_args("-l -a /tmp")
	assert str(cmd) == "sudo ls -l -a /tmp"
	

def test_complex_command_method_chaining():
	cmd = Command("ip", sudo=True) \
	    .add_arg("link") \
	    .add_arg("add") \
        .add_args(["name", "eth0"]) \
	    .add_args("type dummy")
	assert str(cmd) == "sudo ip link add name eth0 type dummy"
	

def test_command_call_failure(monkeypatch):
	cmd = Command("false")
	def fake_run(*args, **kwargs):
		raise subprocess.CalledProcessError(returncode=42, cmd=args[0])

	monkeypatch.setattr("subprocess.run", fake_run)
	with pytest.raises(RuntimeError) as exc:
		cmd.run()
	assert "failed with exit code 42" in str(exc.value)
