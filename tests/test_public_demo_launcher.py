import os
import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import run_public_demo


def test_extract_tunnel_url_from_cloudflared_output():
    line = "INF Your quick Tunnel has been created! Visit https://Bright-Tree.trycloudflare.com"

    assert run_public_demo.extract_tunnel_url(line) == (
        "https://bright-tree.trycloudflare.com"
    )
    assert run_public_demo.extract_tunnel_url("no URL yet") is None


def test_backend_environment_contains_session_url_without_mutating_parent():
    os.environ.pop("QR_SHARE_BASE_URL", None)

    environment = run_public_demo.build_backend_environment(
        "https://demo.trycloudflare.com/"
    )

    assert environment["QR_SHARE_BASE_URL"] == "https://demo.trycloudflare.com"
    assert "QR_SHARE_BASE_URL" not in os.environ


def test_find_cloudflared_reports_missing_command(monkeypatch):
    monkeypatch.setattr(run_public_demo.shutil, "which", lambda _: None)

    with pytest.raises(run_public_demo.LauncherError, match="not installed"):
        run_public_demo.find_cloudflared()


def test_port_check_detects_an_existing_server(monkeypatch):
    monkeypatch.setattr(
        run_public_demo,
        "port_is_available",
        lambda host, port: port != run_public_demo.PRIVATE_PORT,
    )

    with pytest.raises(run_public_demo.LauncherError, match="8000"):
        run_public_demo.require_available_ports()


def test_port_is_available_detects_bound_socket():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        assert not run_public_demo.port_is_available("127.0.0.1", port)


def test_port_is_available_accepts_unused_socket():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temporary:
        temporary.bind(("127.0.0.1", 0))
        port = temporary.getsockname()[1]
    assert run_public_demo.port_is_available("127.0.0.1", port)


def test_wait_for_tunnel_url_reports_early_process_exit():
    class ExitedProcess:
        def poll(self):
            return 1

    with pytest.raises(run_public_demo.LauncherError, match="exited"):
        run_public_demo._wait_for_tunnel_url(
            ExitedProcess(),
            run_public_demo.queue.Queue(),
        )


def test_stop_processes_terminates_live_children_and_kills_timeout():
    class FakeProcess:
        def __init__(self, times_out=False):
            self.running = True
            self.times_out = times_out
            self.terminated = False
            self.killed = False

        def poll(self):
            return None if self.running else 0

        def terminate(self):
            self.terminated = True

        def wait(self, timeout):
            if self.times_out and not self.killed:
                raise run_public_demo.subprocess.TimeoutExpired("fake", timeout)
            self.running = False
            return 0

        def kill(self):
            self.killed = True

    normal = FakeProcess()
    stuck = FakeProcess(times_out=True)

    run_public_demo._stop_processes([normal, stuck])

    assert normal.terminated and not normal.killed
    assert stuck.terminated and stuck.killed
