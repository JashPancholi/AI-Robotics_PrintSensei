# Steps to Run PrintSensei

These instructions run the current PrintSensei frontend, backend, local QR
storage, and temporary public QR sharing through Cloudflare Quick Tunnel.

## 1. Install prerequisites

Install:

- Python 3.13 or newer
- Node.js and npm
- Cloudflare `cloudflared`

On Windows, install `cloudflared` with:

```powershell
winget install --id Cloudflare.cloudflared
```

Restart the terminal and verify it is available:

```powershell
cloudflared --version
```

## 2. Open the project directory

```powershell
cd C:\Users\krish\OneDrive\Desktop\proj\AI-Robotics_PrintSensei
```

Run all remaining backend commands from this directory.

## 3. Create the Python environment

Create the environment if `venv` does not already exist:

```powershell
python -m venv venv
```

Activate it and install the backend dependencies:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 4. Configure the backend

Create `.env` from the example if it does not exist:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set your OpenAI API key:

```dotenv
OPENAI_API_KEY=your-key-here
```

Keep these settings for the current project:

```dotenv
HOST=0.0.0.0
PORT=8000
QR_SHARE_TTL_DAYS=7
```

`run_public_demo.py` supplies the temporary public QR hostname automatically.
Do not copy a `trycloudflare.com` URL into `.env`.

## 5. Install frontend dependencies

Run this once, or whenever `frontend/package.json` changes:

```powershell
cd frontend
npm install
cd ..
```

## 6. Stop older backend processes

Only one process can use port 8000. Stop any previous backend terminal with
Ctrl+C before starting the public demo.

To check whether the ports are occupied:

```powershell
netstat -ano | Select-String ':8000\s+.*LISTENING|:8001\s+.*LISTENING'
```

If the command prints nothing, both required ports are free.

## 7. Start the backend and public QR tunnel

In the first terminal, run:

```powershell
.\venv\Scripts\python.exe run_public_demo.py
```

Wait for this message:

```text
PrintSensei public QR demo is ready.
Public share URL: https://RANDOM-NAME.trycloudflare.com
```

Keep this terminal running. It manages:

- The private PrintSensei backend on port 8000.
- The share-only server on port 8001.
- The Cloudflare Quick Tunnel.

## 8. Start the frontend

Open a second terminal in the project directory:

```powershell
cd frontend
npm run dev
```

Open the URL displayed by Vite, normally:

```text
http://localhost:5173
```

## 9. Generate and share an image

1. Select **Study**.
2. Select **Text** and enter the requested output.
3. Wait for the generated image and return to the options page.
4. Select **QR Code**.
5. Choose an item from History.
6. Select **Create QR**.
7. Scan the QR code from a phone on any internet connection.
8. Use **Print QR** to simulate printing while `HARDWARE_MODE=pc`.

## 10. Stop the project

Press Ctrl+C in the frontend terminal, then press Ctrl+C in the public-demo
terminal. The temporary Cloudflare address stops working immediately.

Cloudflare Quick Tunnel creates a different hostname each time it starts.
Previously generated public QR codes will not work in the next session; create
new QR codes after restarting the launcher.

## LAN-only alternative

To run without Cloudflare, set `QR_SHARE_BASE_URL` in `.env` to the computer's
private LAN address:

```dotenv
QR_SHARE_BASE_URL=http://192.168.1.50:8000
```

Replace the example IP, then run:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

In another terminal, start the frontend with `npm run dev`. LAN-only QR links
require the phone to be on the same network.

## Run verification checks

Backend tests:

```powershell
.\venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

Frontend production build:

```powershell
cd frontend
npm run build
```

## Common problems

- **`cloudflared` is not recognized:** Restart VS Code after installation, or
  temporarily run `$env:Path += ';C:\Program Files (x86)\cloudflared'`.
- **Port 8000 is already in use:** Stop the previous backend before running the
  launcher again.
- **QR page opens but an old QR no longer works:** Quick Tunnel URLs change
  after every launcher restart; generate a new QR.
- **Create QR reports a configuration error:** Start the project through
  `run_public_demo.py`, or configure `QR_SHARE_BASE_URL` for LAN-only mode.
- **The public page stops loading:** Confirm the launcher, backend, and device
  all remain powered on and connected to the internet.
