# Local setup for QR sharing

QR shares are stored on the PrintSensei device under `shared_content/shares`.
They can be opened by phones on the same network while the device and backend
are running.

## Configure the device address

Give the PrintSensei device a stable private IP address, preferably by creating
a DHCP reservation in the router. On Windows, run `ipconfig`; on Raspberry Pi
OS, run `hostname -I` to find the current address.

Put that address in the root `.env` file:

```dotenv
HOST=0.0.0.0
PORT=8000
QR_SHARE_BASE_URL=http://192.168.1.50:8000
QR_SHARE_TTL_DAYS=7
```

Replace `192.168.1.50` with the device's actual LAN address, then restart the
FastAPI backend. Do not use `127.0.0.1` or `localhost`; those addresses would
refer to the phone itself after scanning.

For temporary access outside the local network, follow
[`public-qr-tunnel.md`](public-qr-tunnel.md) instead. The public launcher sets
`QR_SHARE_BASE_URL` automatically for its session.

## Using a share

Select **QR Code**, choose an item from History, and select **Create QR**. The
generated code opens a URL like:

```text
http://192.168.1.50:8000/share/RANDOM_TOKEN
```

The URL is unlisted but not authenticated: anyone who has it can view the
shared image. Shares expire after seven days. Expired pages and images return
HTTP 410, and their local files are cleaned during startup or the next share
creation.
