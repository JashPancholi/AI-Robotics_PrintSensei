"""Run PrintSensei with temporary public QR sharing through TryCloudflare."""

from __future__ import annotations

import os
import queue
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import TextIO
from urllib.error import URLError
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parent
PRIVATE_PORT = 8000
PUBLIC_SHARE_PORT = 8001
TUNNEL_URL_PATTERN = re.compile(
    r"https://[a-z0-9-]+\.trycloudflare\.com",
    re.IGNORECASE,
)


class LauncherError(RuntimeError):
    pass


def find_cloudflared() -> str:
    executable = shutil.which("cloudflared")
    if executable is None:
        raise LauncherError(
            "cloudflared is not installed or is not on PATH. "
            "See Documentation/public-qr-tunnel.md."
        )
    return executable


def extract_tunnel_url(line: str) -> str | None:
    match = TUNNEL_URL_PATTERN.search(line)
    return match.group(0).lower() if match else None


def build_backend_environment(public_url: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment["QR_SHARE_BASE_URL"] = public_url.rstrip("/")
    return environment


def port_is_available(host: str, port: int) -> bool:
    # Windows can allow a provisional bind even when a wildcard listener owns
    # the port, then reject the later Uvicorn bind. Probe for a listener first.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.25)
        if probe.connect_ex((host, port)) == 0:
            return False

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        try:
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                listener.setsockopt(
                    socket.SOL_SOCKET,
                    socket.SO_EXCLUSIVEADDRUSE,
                    1,
                )
            listener.bind((host, port))
        except OSError:
            return False
    return True


def require_available_ports() -> None:
    occupied = [
        port
        for host, port in (
            ("127.0.0.1", PRIVATE_PORT),
            ("127.0.0.1", PUBLIC_SHARE_PORT),
        )
        if not port_is_available(host, port)
    ]
    if occupied:
        values = ", ".join(str(port) for port in occupied)
        raise LauncherError(
            f"Port(s) {values} are already in use. Stop the existing backend and try again."
        )


def _start_process(
    command: list[str],
    *,
    environment: dict[str, str] | None = None,
) -> subprocess.Popen[str]:
    return subprocess.Popen(
        command,
        cwd=PROJECT_ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )


def _forward_output(
    process: subprocess.Popen[str],
    label: str,
    output_queue: queue.Queue[str] | None = None,
) -> threading.Thread:
    def read_output(stream: TextIO) -> None:
        for line in stream:
            cleaned = line.rstrip()
            if cleaned:
                print(f"[{label}] {cleaned}", flush=True)
            if output_queue is not None:
                output_queue.put(line)

    if process.stdout is None:
        raise LauncherError(f"Could not capture {label} process output.")
    thread = threading.Thread(
        target=read_output,
        args=(process.stdout,),
        daemon=True,
    )
    thread.start()
    return thread


def _wait_for_http(
    url: str,
    process: subprocess.Popen[str],
    timeout_seconds: float = 20,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise LauncherError(f"Server exited before becoming ready: {url}")
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (OSError, URLError):
            time.sleep(0.2)
    raise LauncherError(f"Timed out waiting for server: {url}")


def _wait_for_tunnel_url(
    process: subprocess.Popen[str],
    output_queue: queue.Queue[str],
    timeout_seconds: float = 30,
) -> str:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise LauncherError("Cloudflare tunnel exited before providing a public URL.")
        try:
            line = output_queue.get(timeout=0.25)
        except queue.Empty:
            continue
        public_url = extract_tunnel_url(line)
        if public_url:
            return public_url
    raise LauncherError("Timed out waiting for Cloudflare to provide a public URL.")


def _stop_processes(processes: list[subprocess.Popen[str]]) -> None:
    for process in reversed(processes):
        if process.poll() is None:
            process.terminate()
    for process in reversed(processes):
        if process.poll() is not None:
            continue
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def run() -> None:
    cloudflared = find_cloudflared()
    require_available_ports()
    processes: list[subprocess.Popen[str]] = []
    try:
        public_server = _start_process(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.public_main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(PUBLIC_SHARE_PORT),
            ]
        )
        processes.append(public_server)
        _forward_output(public_server, "public")
        _wait_for_http(
            f"http://127.0.0.1:{PUBLIC_SHARE_PORT}/health",
            public_server,
        )

        tunnel = _start_process(
            [
                cloudflared,
                "tunnel",
                "--url",
                f"http://127.0.0.1:{PUBLIC_SHARE_PORT}",
                "--no-autoupdate",
            ]
        )
        processes.append(tunnel)
        tunnel_output: queue.Queue[str] = queue.Queue()
        _forward_output(tunnel, "tunnel", tunnel_output)
        public_url = _wait_for_tunnel_url(tunnel, tunnel_output)

        backend = _start_process(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                str(PRIVATE_PORT),
            ],
            environment=build_backend_environment(public_url),
        )
        processes.append(backend)
        _forward_output(backend, "backend")
        _wait_for_http(f"http://127.0.0.1:{PRIVATE_PORT}/health", backend)

        print("\nPrintSensei public QR demo is ready.", flush=True)
        print(f"Public share URL: {public_url}", flush=True)
        print("Start the frontend separately with: cd frontend; npm run dev", flush=True)
        print("Press Ctrl+C to stop the backend and invalidate public access.\n", flush=True)

        while True:
            for name, process in (
                ("public share server", public_server),
                ("Cloudflare tunnel", tunnel),
                ("private backend", backend),
            ):
                if process.poll() is not None:
                    raise LauncherError(f"The {name} stopped unexpectedly.")
            time.sleep(0.5)
    finally:
        _stop_processes(processes)


def main() -> int:
    try:
        run()
    except KeyboardInterrupt:
        print("\nStopping PrintSensei public QR demo...", flush=True)
        return 0
    except LauncherError as exc:
        print(f"Launcher error: {exc}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
