# PrintSensei Printing Pipeline — Implementation Summary

## Goal

Implement the supplied pipeline for sending a generated image from the React frontend to a SHREYANS POSIFLOW 58D thermal label printer through a FastAPI backend running on a Raspberry Pi.

## Implemented

- Created `app/services/printer.py`.
  - Converts Pillow images to monochrome TSPL `BITMAP` commands.
  - Pads image widths to a multiple of eight pixels as required by TSPL.
  - Sends raw TSPL data to `/dev/usb/lp0`.
  - Falls back to the raw CUPS queue when direct USB is unavailable or CUPS is configured.
  - Produces a complete TSPL label with `SIZE`, `GAP`, `DIRECTION`, `CLS`, `PRINT`, and `TEAR` commands.

- Added `POST /api/print` in `app/routers.py`.
  - Accepts a Base64 image or data URI.
  - Validates label width, label height, and gap dimensions.
  - Decodes the image with Pillow and passes it to the printer service.
  - Returns a success message or an HTTP 502 printer error.

- Updated `frontend/src/App.jsx`.
  - Generated study-image previews now send the image to `/api/print` when Print is pressed.
  - Shows a sending state while the job is submitted.
  - Shows printer/network errors instead of incorrectly showing a successful print.

- Updated `frontend/vite.config.js` with an `/api` proxy to the FastAPI server.

- Added printer configuration examples to `.env.example`:

  ```env
  PRINTER_DEVICE=/dev/usb/lp0
  CUPS_QUEUE=POSIFLOW58D
  PRINTER_USE_CUPS=false
  ```

- Added `tests/test_printer.py` for bitmap encoding and API request validation.

- Added `pytest>=8.0.0` to `requirements.txt`.

## Validation Performed

- Frontend production build completed successfully with `npm run build` from `frontend/`.
- Python source compilation completed successfully.
- TSPL bitmap encoding was smoke-tested, including width padding and black-pixel bit packing.

## Remaining Deployment Steps

1. Install dependencies on the Raspberry Pi:

   ```bash
   pip install -r requirements.txt
   ```

2. Configure the printer environment variables in `.env` if the defaults do not match the Pi.
3. Ensure the service account can write to `/dev/usb/lp0` (typically membership in the `lp` group).
4. Calibrate the printer's gap sensor for the installed sticker roll.
5. Run a physical test label and adjust `DIRECTION` in `app/services/printer.py` if orientation is incorrect.

## Scope Note

Real printer submission is wired for generated study images. The existing non-study preview cards still use their prior simulated print transition and are not yet rendered/submitted as physical print jobs.
