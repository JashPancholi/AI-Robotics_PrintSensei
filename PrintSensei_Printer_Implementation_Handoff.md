# PrintSensei — Real Printer Integration Handoff

## Purpose

This document is the implementation handoff for integrating the **real SHREYANS POSIFLOW 58D thermal label printer** into PrintSensei.

This is based on **physical testing performed on the actual printer and Raspberry Pi 5**, not a theoretical printer integration.

The required final flow is:

```text
Existing PrintSensei Image Generation
        ↓
Generated Image File
        ↓
Print Button
        ↓
POST /api/print
        ↓
Printer Service
        ↓
ESC/POS Raster
        ↓
USB /dev/usb/lp0
        ↓
SHREYANS POSIFLOW 58D
        ↓
Physical Printed Label
```

Do **not** redesign the existing image-generation pipeline.

Do **not** create a second image only for printing.

Use the exact generated image that PrintSensei already creates and stores.

---

# 1. Physical Printer

Printer:

**SHREYANS POSIFLOW 58D 2-Inch (58mm) Portable Thermal Label & Receipt Printer**

Connection:

**USB**

Host:

**Raspberry Pi 5**

Linux device:

```text
/dev/usb/lp0
```

---

# 2. USB Detection — Physically Verified

When connected to the Raspberry Pi, the printer appeared as:

```text
Bus 001 Device 002: ID 0456:0808 Analog Devices, Inc. USB Portable Printer
```

`dmesg` showed:

```text
Product: USB Portable Printer
Manufacturer: STMicroelectronics
SerialNumber: Printer
```

Linux loaded the `usblp` driver and created:

```text
/dev/usb/lp0
```

The application should therefore support direct printing through:

```text
/dev/usb/lp0
```

---

# 3. Linux Permissions — Physically Verified

The Pi user was added to the `lp` group:

```bash
sudo usermod -aG lp $USER
```

The shell was refreshed with:

```bash
newgrp lp
```

This test succeeded:

```bash
test -r /dev/usb/lp0 && test -w /dev/usb/lp0 && echo "PRINTER ACCESS OK"
```

Expected:

```text
PRINTER ACCESS OK
```

The application should not require `sudo` for normal printing.

---

# 4. CUPS — Tested and Available

CUPS was installed:

```bash
sudo apt update
sudo apt install -y cups
sudo systemctl enable --now cups
```

The printer appeared through:

```bash
lpinfo -v
```

as:

```text
direct usb://STMicroelectronics/USB%20Portable%20Printer%20%20%20%20?serial=Printer
```

A raw CUPS queue was created:

```bash
sudo lpadmin -p POSIFLOW58D \
  -v 'usb://STMicroelectronics/USB%20Portable%20Printer%20%20%20%20?serial=Printer' \
  -m raw

sudo lpadmin -d POSIFLOW58D
sudo cupsenable POSIFLOW58D
sudo cupsaccept POSIFLOW58D
```

The queue is:

```text
POSIFLOW58D
```

CUPS may be retained as an optional fallback, but **direct USB is the preferred application path**.

---

# 5. Basic Printer Test — Physically Verified

Raw text was sent through CUPS:

```bash
printf 'PRINTSENSEI TEST\n\n\n' | lp -d POSIFLOW58D
```

The printer physically printed the text.

This verified that the physical path:

```text
Raspberry Pi → USB → POSIFLOW 58D
```

works.

---

# 6. CRITICAL: Printer Protocol Investigation

The printer protocol was tested experimentally.

Do not assume TSPL just because the printer is a label printer.

## ESC/POS — WORKS

ESC/POS raster image printing was tested on the physical printer.

The working raster command is:

```python
b"\x1d\x76\x30\x00"
```

This is the ESC/POS:

```text
GS v 0
```

raster image command.

A Pillow-generated monochrome image was converted to this format and physically printed.

A 384-pixel-wide image was successfully printed.

Larger text/image tests were also physically printed.

Therefore:

```text
ESC/POS RASTER = VERIFIED WORKING
```

---

# 7. TSPL — DO NOT USE

TSPL was also tested.

A payload containing commands such as:

```text
SIZE 50 mm,30 mm
GAP 2 mm,0 mm
CLS
BITMAP ...
PRINT 1
TEAR
```

was sent to the physical printer.

The printer did **not** interpret the TSPL commands.

Instead, it physically printed the TSPL commands as literal text.

The paper showed text equivalent to:

```text
SIZE 50 mm,30 mm
GAP 2 mm,0 mm
DIRECTION 1
CLS
BITMAP ...
PRINT 1
TEAR
```

Therefore:

# DO NOT USE TSPL

Do not implement the final POSIFLOW 58D print path with:

```text
SIZE
GAP
BITMAP
PRINT
TEAR
```

as TSPL commands.

The experimentally verified protocol is:

# ESC/POS RASTER

This is the most important hardware finding in this document.

---

# 8. Working Image Printing Method

The existing PrintSensei generated image should be converted to a 1-bit
monochrome Pillow image.

Target print width:

```text
384 pixels
```

The printer is approximately 203 DPI.

384 pixels corresponds to approximately 48 mm of printable width.

If the image width is not divisible by 8, pad the right side with white pixels
until it is divisible by 8.

For each row:

- 8 pixels become 1 byte.
- Black pixels become set bits.
- White pixels become cleared bits.

The raster payload begins with:

```python
b"\x1d\x76\x30\x00"
```

followed by four bytes containing:

```text
width_bytes_low
width_bytes_high
height_low
height_high
```

and then the packed bitmap bytes.

Conceptually:

```python
raster_header = (
    b"\x1d\x76\x30\x00"
    + bytes([
        width_bytes & 0xFF,
        (width_bytes >> 8) & 0xFF,
        height & 0xFF,
        (height >> 8) & 0xFF,
    ])
)

payload = raster_header + bitmap_data
```

Then send `payload` to `/dev/usb/lp0`.

---

# 9. Direct USB Transport

The physically verified direct transport is:

```python
with open("/dev/usb/lp0", "wb") as printer:
    printer.write(payload)
    printer.flush()
```

where:

```text
payload = ESC/POS GS v 0 raster bytes
```

This should be the preferred implementation.

Do not send PNG/JPEG bytes directly to the printer.

Do not use TSPL.

Do not require `sudo`.

---

# 10. Existing PrintSensei Image Pipeline

PrintSensei already generates images.

The existing architecture is conceptually:

```text
User Request
     ↓
Label / Study / Diagram Generation
     ↓
LabelRenderer
     ↓
Pillow Image
     ↓
Generated Image
```

Generated images are already stored by the project, including the existing:

```text
diagram_images/
```

The printer integration must be downstream of this pipeline.

Do not replace or duplicate the image-generation system.

---

# 11. Required Final Application Flow

The final application must work like this:

```text
User generates Study / Label / Diagram
        ↓
PrintSensei generates the image
        ↓
Image is saved using the existing image storage flow
        ↓
Generated image is displayed in the UI
        ↓
User clicks PRINT
        ↓
Frontend sends that generated image to POST /api/print
        ↓
Backend decodes the image
        ↓
Pillow image
        ↓
Printer service converts image to 1-bit monochrome
        ↓
ESC/POS GS v 0 raster encoding
        ↓
/dev/usb/lp0
        ↓
POSIFLOW 58D
        ↓
Physical label prints
```

The image printed must be the **same generated image** that PrintSensei saved
and displayed.

---

# 12. Print Button

The existing Print button must become a real hardware printing action.

It must not:

- merely display "Printing..."
- open the browser print dialog
- download the image
- fake a successful print
- generate another image
- use TSPL

It must call the backend print endpoint.

Recommended endpoint:

```text
POST /api/print
```

---

# 13. Backend `/api/print`

Implement or update:

```text
POST /api/print
```

The endpoint should accept the generated image as a Base64/data URI.

Flow:

```text
Frontend
   ↓
POST /api/print
   ↓
Validate request
   ↓
Decode Base64/data URI
   ↓
Pillow Image
   ↓
Printer service
   ↓
ESC/POS raster
   ↓
/dev/usb/lp0
```

The endpoint should:

1. Validate the request.
2. Decode the image.
3. Open it with Pillow.
4. Call the printer service.
5. Return success if the physical write succeeds.
6. Return a useful HTTP error if the printer operation fails.

Do not regenerate the label inside the endpoint.

---

# 14. Printer Service

Use/create:

```text
app/services/printer.py
```

A simple API is preferred:

```python
def print_label(
    image: Image.Image,
    config: PrinterConfig | None = None,
) -> tuple[bool, str]:
    ...
```

The printer service should:

1. Receive the final Pillow image.
2. Convert it to 1-bit monochrome.
3. Pad width to a multiple of 8 if needed.
4. Encode ESC/POS `GS v 0`.
5. Send the bytes to `/dev/usb/lp0`.
6. Return a success/failure tuple.

The printer service should not know how the image was generated.

---

# 15. Environment Configuration

Support:

```env
PRINTER_DEVICE=/dev/usb/lp0
CUPS_QUEUE=POSIFLOW58D
PRINTER_USE_CUPS=false
```

Direct USB should be the default.

If CUPS fallback is retained, it must receive the already-encoded ESC/POS
payload as raw data.

For example:

```bash
lp -d POSIFLOW58D -o raw
```

CUPS must not rasterize or otherwise transform the image.

---

# 16. Image Dimensions

The verified working image width is:

```text
384 px
```

Do not arbitrarily change the existing renderer's output dimensions.

If the renderer already produces a suitable image, use it directly.

The label height may be dynamic.

Do not force every label to exactly 50 × 50 mm.

The printer service should handle the actual generated image height.

---

# 17. Generated Image Must Remain the Source of Truth

This is critical.

The application already generates and stores images.

Do not create:

```text
Generated Image A
```

for the UI and:

```text
Generated Image B
```

for the printer.

Instead:

```text
                 ┌──→ Display
Generated Image ─┼──→ Save
                 └──→ Print
```

The exact generated image should be used for all three.

---

# 18. Physical Printer Test

Before relying on the application, Codex should implement a small hardware
smoke test.

Example test image:

```python
from PIL import Image, ImageDraw

image = Image.new("1", (384, 220), 1)
draw = ImageDraw.Draw(image)

draw.text((20, 20), "PRINTSENSEI", fill=0)
draw.text((20, 70), "PRINTER TEST", fill=0)
draw.rectangle((20, 110, 360, 190), outline=0)
```

Send it through the same `print_label()` implementation.

Expected physical result:

```text
PRINTSENSEI
PRINTER TEST
```

plus the rectangle.

This test must use:

```text
ESC/POS GS v 0
```

and:

```text
/dev/usb/lp0
```

If the paper contains TSPL commands such as `SIZE`, `GAP`, `BITMAP`, etc.,
the implementation is wrong.

---

# 19. Application End-to-End Test

After the hardware smoke test:

### Step 1

Generate a real study/label/diagram through the existing PrintSensei flow.

### Step 2

Confirm the generated image is saved in the existing generated-image /
diagram-image storage.

### Step 3

Confirm the image appears in the UI.

### Step 4

Click:

```text
PRINT
```

### Step 5

Confirm the frontend calls:

```text
POST /api/print
```

### Step 6

Confirm the backend sends the image through:

```text
ESC/POS GS v 0
```

to:

```text
/dev/usb/lp0
```

### Step 7

Confirm the POSIFLOW 58D physically prints the same generated image.

---

# 20. Error Handling

If the printer is disconnected or unavailable, the application should not
crash.

Examples of useful errors:

```text
Printer not connected
```

or:

```text
Unable to access /dev/usb/lp0
```

or the underlying OS error.

The frontend should display a clear print failure message.

---

# 21. Tests to Add/Update

Add/update printer tests to test ESC/POS, not TSPL.

At minimum:

## Test 1 — ESC/POS header

Given a Pillow image, verify that the generated payload begins with:

```python
b"\x1d\x76\x30\x00"
```

## Test 2 — width padding

Given an image whose width is not divisible by 8, verify that the encoder
pads it correctly.

## Test 3 — image dimensions

Verify that width/height bytes in the ESC/POS header match the encoded image.

## Test 4 — print endpoint

Verify that:

```text
POST /api/print
```

accepts a valid image and invokes the printer service.

## Test 5 — invalid image

Invalid Base64/image data should return an appropriate error.

Do not write tests that expect TSPL.

---

# 22. Existing Code Should Be Inspected Before Editing

Before making changes:

1. Inspect the current repository.
2. Locate the existing image-generation pipeline.
3. Locate where generated images are saved.
4. Locate the existing Print button.
5. Locate any existing `/api/print` implementation.
6. Locate any existing printer service.
7. Preserve working code where possible.
8. Modify only what is required for real printing.

Do not blindly overwrite the existing application.

---

# 23. Important Existing Printer Code Warning

If the repository currently contains a printer implementation based on TSPL,
do not assume it is correct.

The actual physical test proved:

```text
TSPL → WRONG for this printer setup
ESC/POS raster → WORKING
```

Replace the TSPL print path with ESC/POS raster.

The final printer path must not send TSPL commands.

---

# 24. Acceptance Criteria

The implementation is complete only when all of these are true:

- [ ] POSIFLOW 58D is detected through USB.
- [ ] `/dev/usb/lp0` is supported.
- [ ] Direct USB printing works.
- [ ] ESC/POS `GS v 0` raster is used.
- [ ] TSPL is not used.
- [ ] 384px-wide generated images can be printed.
- [ ] Dynamic image height is supported.
- [ ] Existing image generation remains unchanged.
- [ ] Existing generated images remain stored normally.
- [ ] Print button uses the generated image.
- [ ] Print button calls `/api/print`.
- [ ] Backend decodes the image.
- [ ] Backend sends the image to the printer service.
- [ ] Printer service sends ESC/POS to `/dev/usb/lp0`.
- [ ] Physical POSIFLOW 58D prints the image.
- [ ] Printer errors are returned to the UI.
- [ ] Tests cover ESC/POS encoding.
- [ ] No browser print dialog is required.
- [ ] No manual image conversion is required.

---

# 25. FINAL INSTRUCTION TO CODEX / ANTIGRAVITY

Treat this document as the hardware integration record.

Do not invent a new printer protocol.

Do not use TSPL.

Do not create a separate image-generation pipeline.

The hardware behavior has already been experimentally verified.

The known-good path is:

```text
PrintSensei generated image
        ↓
same saved/displayed image
        ↓
Print button
        ↓
POST /api/print
        ↓
Pillow 1-bit conversion
        ↓
ESC/POS GS v 0 raster
        ↓
/dev/usb/lp0
        ↓
SHREYANS POSIFLOW 58D
        ↓
REAL PHYSICAL PRINT
```

Implement this path using the existing project architecture.

After implementation, report:

1. Which files were changed.
2. What printer code was added/modified.
3. How the generated image reaches the printer.
4. Test results.
5. Any hardware-specific setup still required.

The final result must make the existing PrintSensei **Print** button perform a
real physical print on the POSIFLOW 58D.
