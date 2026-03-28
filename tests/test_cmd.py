import subprocess
from pyrecracker.cmd import Command, CommandError

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


def test_command_run_non_zero_exit_code_raises_command_error(monkeypatch):
	cmd = Command("false")
	
	class FakeResult:
		returncode = 1
		stdout = ""
	
	def fake_run(*args, **kwargs):
		return FakeResult()
	
	monkeypatch.setattr("subprocess.run", fake_run)
	with pytest.raises(CommandError) as exc:
		cmd.run()
	assert "failed with exit code 1" in str(exc.value)
	assert "false" in str(exc.value)


def test_command_run_called_process_error_raises_command_error(monkeypatch):
	cmd = Command("failing_command")
	
	def fake_run(*args, **kwargs):
		raise subprocess.CalledProcessError(returncode=42, cmd=args[0])
	
	monkeypatch.setattr("subprocess.run", fake_run)
	with pytest.raises(CommandError) as exc:
		cmd.run()
	assert "failed with exit code 42" in str(exc.value)
	assert "failing_command" in str(exc.value)


def test_command_popen_called_process_error_raises_command_error(monkeypatch):
	cmd = Command("failing_popen_command")
	
	def fake_popen(*args, **kwargs):
		raise subprocess.CalledProcessError(returncode=99, cmd=args[0])
	
	monkeypatch.setattr("subprocess.Popen", fake_popen)
	with pytest.raises(CommandError) as exc:
		cmd.popen()
	assert "failed with exit code 99" in str(exc.value)
	assert "failing_popen_command" in str(exc.value)


def test_command_popen_with_log_file_called_process_error_raises_command_error(monkeypatch):
	cmd = Command("failing_popen_with_log")
	
	def fake_popen(*args, **kwargs):
		raise subprocess.CalledProcessError(returncode=55, cmd=args[0])
	
	monkeypatch.setattr("subprocess.Popen", fake_popen)
	with pytest.raises(CommandError) as exc:
		cmd.popen(log_file_path="/tmp/test.log")
	assert "failed with exit code 55" in str(exc.value)
	assert "failing_popen_with_log" in str(exc.value)
