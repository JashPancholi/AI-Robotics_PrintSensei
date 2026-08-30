# Temporary public QR sharing

This development setup uses a Cloudflare Quick Tunnel to make only QR share
pages available outside the local network. History, generation, and printing
APIs remain on the private backend and are not exposed by the tunnel.

Quick Tunnel hostnames change every time the launcher runs. Previously printed
QR codes therefore stop working after the launcher exits, even if their local
seven-day retention period has not ended.

## Install cloudflared

Install Cloudflare's `cloudflared` command and ensure it is available on `PATH`.

On Windows with WinGet:

```powershell
winget install --id Cloudflare.cloudflared
```

For Raspberry Pi OS and other Linux distributions, follow Cloudflare's package
installation instructions:

<https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/>

Confirm the installation:

```text
cloudflared --version
```

No Cloudflare account or domain is required for a Quick Tunnel.

## Start the public demo

Stop any backend already using port 8000, then run from the project root:

```powershell
.\venv\Scripts\python.exe run_public_demo.py
```

The launcher starts:

- The share-only server on local port 8001.
- A temporary Cloudflare HTTPS tunnel to port 8001.
- The private PrintSensei backend on port 8000 using the generated public URL.

Keep that terminal open. In another terminal, start the frontend:

```powershell
cd frontend
npm run dev
```

QR codes created during this session can be scanned from any network. Press
Ctrl+C in the launcher terminal to stop both servers and the tunnel.

## Limitations

- PrintSensei and the launcher must remain running.
- The public hostname and all QR codes using it become invalid after restart.
- Quick Tunnels are intended for testing and have no uptime guarantee.
- Anyone possessing a random share URL can view that share until the tunnel
  stops or its seven-day local expiry is reached.
