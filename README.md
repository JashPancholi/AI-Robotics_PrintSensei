# PrintSensei

<<<<<<< HEAD
Phase 1 foundation for the PrintSensei project.
=======
## An Intelligent Multimodal Robotic Labeling and Knowledge Assistant

PrintSensei is a Raspberry Pi-based stationary robotic assistant that understands voice commands, camera images, printed documents, dashboard inputs, and physical objects.

The system processes these inputs using speech recognition, computer vision, optical character recognition, object detection, lightweight local AI models, and cloud-based AI APIs. After understanding the user's request, it automatically generates a suitable label, study card, inventory sticker, product tag, or QR-enabled knowledge label and prints it using a 58 mm thermal printer.

---

## Team Members

- Pranshu
- Jash
- Tanay
- Krish
- Division F

---

## Project Topic

**PrintSensei: An Intelligent Multimodal Robotic Labeling and Knowledge Assistant**

---

## Problem Statement

Creating labels, study notes, inventory tags, QR stickers, and product labels normally requires users to manually enter information, select a template, format the content, design the label, and operate a printer.

Conventional label printers cannot:

- Understand natural-language commands
- Recognize physical objects
- Read text from documents
- Generate summaries
- Retrieve contextual knowledge
- Automatically select the most suitable label format
- Convert multimodal information into physical output

PrintSensei solves this problem by combining multimodal artificial intelligence with an intelligent physical thermal-printing system.

---

## Proposed Solution

PrintSensei accepts information through multiple input methods:

- Voice commands
- Camera images
- Printed documents
- Physical objects
- Local dashboard input

The system analyses the input, understands the user's request, generates structured content, creates a suitable label layout, presents a preview for confirmation, and prints the final result using a thermal printer.

### Example User Commands

- “Create a label for this Arduino Uno.”
- “Summarize this textbook page.”
- “Print a QR code for my website.”
- “Create an inventory sticker for this component.”
- “Make a revision card for binary search.”
- “Read the expiry date and create a product label.”

---

## System Workflow

```text
User Input
│
├── Voice Command
├── Camera Image
├── Printed Document
├── Physical Object
└── Dashboard Input
│
▼
Speech Recognition / Vision / OCR Processing
│
▼
Intent Detection and Information Extraction
│
▼
Local AI or Cloud AI Processing
│
▼
Knowledge and Label Generation
│
▼
QR Code and Layout Creation
│
▼
Label Preview and Confirmation
│
▼
Thermal Printing
```

---

## Main Functions

### 1. Voice-Based Label Generation

The user speaks a command through the USB microphone.

The system:

1. Records the voice command
2. Converts speech into text
3. Detects the user's intent
4. Extracts the required information
5. Generates structured label content
6. Creates a print-ready layout
7. Sends the final label to the thermal printer

---

### 2. Object Recognition

The Raspberry Pi Camera captures a physical object.

An object-detection model identifies the object and sends the detected information to the AI processing module.

Objects may include:

- Arduino boards
- Raspberry Pi boards
- Electronic components
- Laboratory equipment
- Books
- Product packages
- Medicines
- Storage items
- Small tools

---

### 3. OCR-Based Text Extraction

PrintSensei can read printed text from:

- Books
- Product packages
- Existing labels
- Documents
- Notes
- Formula sheets
- Inventory records
- Product information sheets

The extracted information can then be summarized, categorized, stored, converted into structured data, or printed as a label.

---

### 4. QR-Code Generation

PrintSensei can generate QR codes containing:

- Website URLs
- Product information
- Inventory record links
- Study notes
- Contact details
- Wi-Fi credentials
- Locally hosted knowledge pages
- Portfolio links
- GitHub profiles
- Documentation links
- Plain text

Website links and other information that is difficult to enter through voice can be provided through the local dashboard.

---

### 5. Intelligent Thermal Printing

The system creates a complete monochrome label image that may contain:

- Heading
- Description
- QR code
- Barcode
- Date
- Category
- Quantity
- Shelf number
- Inventory ID
- Small icon
- Small diagram
- Revision summary
- Product information

The final image is converted into a printer-compatible bitmap and printed using a 58 mm thermal printer.

---

## Operating Modes

### Study Mode

Study Mode creates:

- Revision cards
- Topic summaries
- Formula cards
- Definitions
- Flashcards
- Short explanations
- QR-linked detailed notes

Example output:

```text
BINARY SEARCH

• Requires sorted data
• Divides the search range

Time Complexity: O(log n)

[QR Code]
```

---

### Inventory Mode

Inventory Mode creates labels for laboratory components, storage items, and equipment.

An inventory label may contain:

- Component name
- Quantity
- Shelf number
- Category
- Inventory ID
- QR code
- Purchase date
- Warranty details
- Notes

---

### Product Mode

Product Mode creates labels containing:

- Product name
- Price
- Weight
- Manufacturing date
- Expiry date
- Ingredients
- Barcode
- QR code
- Product category

---

### OCR Mode

OCR Mode captures a page, package, note, or document, extracts its text, and converts the content into a concise printable label or summary.

---

### QR Mode

QR Mode creates QR stickers from:

- URLs
- Contact details
- Wi-Fi credentials
- Text
- Inventory records
- Study notes
- Local knowledge pages

---

### Object Information Mode

Object Information Mode recognizes a physical object and prints a compact information label containing:

- Object name
- Short description
- Specifications
- Category
- Related QR code
- Safety information
- Usage information

---

## Hardware Requirements

| Sr. No. | Hardware Component | Quantity | Purpose | Estimated Cost |
|---:|---|---:|---|---:|
| 1 | Raspberry Pi 4B, 4 GB RAM | 1 | Main processing unit and robot controller | Already available |
| 2 | Official Raspberry Pi Camera Module V2, 8 MP | 1 | Object detection, OCR, document scanning, and image capture | ₹1,700 |
| 3 | HOIN H-58BT, 58 mm USB and Bluetooth thermal printer | 1 | Printing labels, QR codes, text, diagrams, and stickers | ₹2,100 |
| 4 | 2.42-inch 128×64 OLED display, SPI/I²C | 1 | Robot face, menu, status messages, and confirmations | ₹1,200 |
| 5 | USB plug-and-play microphone | 1 | Voice-command input | ₹250 |
| 6 | TV remote-style 5-way navigation switch | 1 | Up, down, left, right, and OK menu navigation | ₹150 |
| 7 | Separate momentary push-to-talk button | 1 | Start and stop voice recording | ₹100 |
| 8 | WS2812B RGB LED ring or LED indicator module | 1 | Display listening, processing, printing, and error states | ₹160 |
| 9 | Mini speaker or active buzzer | 1 | Voice response and notification sounds | ₹300 |
| 10 | 32 GB Class 10 microSD card | 1 | Raspberry Pi OS, AI models, database, and software | ₹500 |
| 11 | Official 5.1 V, 3 A USB-C Raspberry Pi power supply | 1 | Stable power supply for Raspberry Pi | ₹700 |
| 12 | Raspberry Pi heatsink and cooling fan | 1 set | Temperature control during AI-model inference | ₹350 |
| 13 | 58 mm direct-thermal adhesive paper rolls | 1 pack | Printable sticker media | ₹350 |
| 14 | Jumper wires, connectors, perfboard, and resistors | 1 set | Hardware wiring and circuit assembly | ₹350 |
| 15 | Prototype enclosure or robot body | 1 | Housing the Raspberry Pi, OLED, buttons, and printer | ₹1,000 |

### Estimated Total Cost

**Approximately ₹9,210**, excluding the Raspberry Pi 4B.

---

## Purpose of Major Components

### Raspberry Pi 4B

The Raspberry Pi acts as the main brain of PrintSensei.

It will:

- Run Raspberry Pi OS
- Control connected devices
- Run lightweight offline AI models
- Manage cloud API requests
- Store print history
- Host the local dashboard
- Generate QR codes
- Prepare label layouts
- Maintain inventory records
- Control the thermal printer

---

### Camera Module

The camera will be used to:

- Capture physical objects
- Detect electronic components
- Scan printed documents
- Read product information
- Extract text using OCR
- Capture images for cloud vision APIs
- Scan existing QR codes
- Provide a live camera preview

---

### OLED Display

The OLED will show system states such as:

```text
READY
LISTENING
PROCESSING
OBJECT DETECTED
LABEL READY
PRINT?
PRINTING
DONE
ERROR
```

It may also display simple animated robot faces.

---

### Navigation Controls

The 5-way navigation switch provides:

```text
        UP

LEFT    OK    RIGHT

       DOWN
```

A separate push-to-talk button is held while the user speaks.

The controls can be used to:

- Select a mode
- Confirm a label
- Cancel an operation
- Navigate menus
- Start voice input
- Reprint a previous label

---

### Thermal Printer

The thermal printer acts as the main physical output mechanism of the robot.

It can print:

- Study cards
- Inventory tags
- Product labels
- QR stickers
- Barcodes
- Revision notes
- Object-information labels
- Small monochrome diagrams

---

### LED Ring

Suggested LED states:

| LED Colour | Robot State |
|---|---|
| White or Green | Ready |
| Blue | Listening |
| Yellow | Processing |
| Purple | Generating label |
| Green animation | Printing |
| Red | Error |

---

### Speaker or Buzzer

The speaker or buzzer provides:

- Button feedback
- Recording notifications
- Processing notifications
- Print-complete notifications
- Error alerts
- Optional voice responses

---

## Local Dashboard

The Raspberry Pi hosts a local web dashboard that can be accessed from a phone or laptop connected to the same network.

Example address:

```text
http://printsensei.local
```

or:

```text
http://<raspberry-pi-ip-address>
```

The dashboard may include:

- Robot status
- Raspberry Pi temperature
- Printer connection status
- Camera status
- Microphone status
- Internet status
- Camera preview
- Voice-command transcript
- Detected intent
- Intent confidence
- Object-detection result
- OCR-extracted text
- Label preview
- Print confirmation
- Saved website links
- Inventory records
- Knowledge library
- Print history
- Reprint option
- Settings

The dashboard also allows users to paste website links and other text that may be difficult to provide through voice input.

---

## Dashboard Sections

### Home

The Home page displays:

- Robot status
- Printer status
- Camera status
- Microphone status
- Raspberry Pi temperature
- Storage usage
- Internet connectivity
- Number of labels printed

---

### Sticker Preview

The Sticker Preview page shows the generated label before printing.

Available actions may include:

- Print
- Edit
- Regenerate
- Save
- Cancel

---

### Print History

Every printed label can be saved in the local database.

Print History may include:

- Label title
- Label category
- Date and time
- Input method
- Reprint option
- Edit option
- Delete option

---

### Saved Links

Users can save commonly used links such as:

- Portfolio
- GitHub
- LinkedIn
- Business website
- WhatsApp
- Product page
- Documentation page

After saving a link, the user can say:

```text
Print my GitHub QR.
```

The robot retrieves the saved link and generates the QR code automatically.

---

### Inventory Database

The Inventory section may store:

- Component name
- Quantity
- Shelf number
- Category
- Inventory ID
- Product image
- Purchase date
- Warranty
- Notes
- QR record

---

### Knowledge Library

The Knowledge Library stores generated notes and summaries.

Examples include:

- Binary Search
- Merge Sort
- TCP Handshake
- OSI Model
- Arduino Uno
- Raspberry Pi
- Resistors
- Capacitors

Users can reopen a topic and:

- Generate a sticker
- Print a flashcard
- Open full notes
- Generate a QR code
- Delete the entry

---

### Voice Console

The Voice Console can display:

```text
Recognized Speech
        ↓
Detected Intent
        ↓
Intent Confidence
        ↓
Selected Mode
        ↓
Generated Output
```

This helps demonstrate the AI pipeline during project evaluation.

---

### AI Processing Console

The AI Processing Console may show:

```text
Speech Recognition
        ↓
Intent Classification
        ↓
Object Detection or OCR
        ↓
Knowledge Generation
        ↓
QR-Code Generation
        ↓
Label Composition
        ↓
Ready to Print
```

---

## Artificial Intelligence Components

### Local Processing

The Raspberry Pi can perform:

- Intent classification
- Object detection
- OCR
- QR-code generation
- Barcode generation
- Label composition
- Printer control
- Database management
- Local knowledge retrieval
- Basic offline command processing

Possible lightweight models and tools include:

- YOLO nano models
- MobileNet SSD
- Tesseract OCR
- PaddleOCR
- Whisper Tiny
- Whisper.cpp
- TF-IDF with Logistic Regression
- Sentence-transformer embeddings
- FAISS
- SQLite
- OpenCV
- Python Imaging Library

---

### Cloud Processing

Cloud AI APIs may be used for:

- Advanced summarization
- Vision-language understanding
- Complex reasoning
- Translation
- Structured knowledge generation
- Creative illustration generation
- Difficult object analysis
- Long document summarization

The core printing, QR generation, database, and basic label-generation functions should continue to work locally when cloud services are unavailable.

---

## Software Architecture

```text
Input Layer
├── USB Microphone
├── Raspberry Pi Camera
├── Push-to-Talk Button
├── Navigation Switch
└── Local Dashboard

Processing Layer
├── Speech Recognition
├── Object Detection
├── OCR
├── Intent Classification
├── Local Knowledge Retrieval
└── Cloud AI Integration

Generation Layer
├── Content Generator
├── QR-Code Generator
├── Barcode Generator
├── Label Layout Engine
└── Bitmap Converter

Output Layer
├── OLED Display
├── LED Ring
├── Speaker or Buzzer
├── Dashboard Preview
└── Thermal Printer
```

---

## Robotics Classification

PrintSensei is a stationary desktop robot rather than a mobile rover.

It contains the three fundamental layers of a robotic system.

### Sensing

- Camera
- Microphone
- Push-to-talk button
- Navigation switch
- Dashboard input

### Intelligence

- Speech recognition
- Computer vision
- OCR
- Object detection
- Intent classification
- Local AI models
- Cloud AI APIs
- Knowledge retrieval
- Automatic layout generation

### Actuation

- Thermal printer
- OLED display
- RGB LED ring
- Speaker
- Buzzer

The thermal printer is the robot's primary physical actuator.

---

## Innovation

PrintSensei combines the following technologies in one low-cost robotic system:

- Voice interaction
- Camera-based perception
- Object recognition
- OCR
- Natural-language understanding
- Local edge AI
- Cloud AI
- Knowledge retrieval
- QR-code generation
- Barcode generation
- Automatic label design
- Physical thermal printing
- Local dashboard control

Unlike a conventional label printer, PrintSensei understands the user's request and determines what information should be printed.

Unlike a standard AI assistant, PrintSensei transforms digital intelligence into a physical and immediately usable output.

---

## Target Users

- Engineering students
- Teachers
- Colleges
- Robotics laboratories
- Research laboratories
- Libraries
- Makerspaces
- Small businesses
- Shop owners
- Inventory managers
- Educational institutions

---

## Applications

- Laboratory inventory management
- Educational revision aids
- Product packaging
- QR-based knowledge labels
- Classroom note generation
- Storage organization
- Library management
- Electronic-component identification
- Small-business product labeling
- Document summarization
- Smart physical tagging
- Product-information extraction
- Expiry-date label generation
- Component identification
- Local knowledge management

---

## Related Literature

### 1. Large Language Models for Robotics: Opportunities, Challenges, and Perspectives

- **Year:** 2025
- **DOI:** `10.1016/j.jai.2024.12.003`

This paper examines how Large Language Models and multimodal Large Language Models can be integrated into robotic systems.

It discusses:

- Natural-language command understanding
- LLM-based reasoning
- Robotic task planning
- Integration of language and visual perception
- Multimodal AI for robotics
- Human-robot interaction
- Connecting AI-generated decisions with physical robot actions

PrintSensei applies these concepts by using a language model as a reasoning and coordination layer.

The system follows this process:

```text
Understand the Instruction
        ↓
Capture or Analyse the Object
        ↓
Extract Relevant Information
        ↓
Generate Structured Label Content
        ↓
Create QR Code and Layout
        ↓
Send Result to Thermal Printer
```

The main difference is that PrintSensei uses intelligent printed labels as its final physical action.

---

### 2. NaviBlind: A Multimodal AI Assistant for Visually Impaired Users to Identify Product Information from Images and Speech

- **Year:** 2025
- **DOI:** `10.22144/ctujoisd.2025.057`

NaviBlind combines product images, speech recognition, and a multimodal vision model to generate structured product information.

Related concepts include:

- Image and speech as combined inputs
- Product identification
- Vision-language model integration
- Natural voice interaction
- Structured information extraction
- Real-time multimodal processing
- Hallucination and uncertainty handling
- User-friendly web interface

NaviBlind follows this process:

```text
Product Image and Voice Question
        ↓
Multimodal AI Processing
        ↓
Structured Product Information
        ↓
Speech Output
```

PrintSensei follows a similar process:

```text
Object or Image and Voice Instruction
        ↓
Vision, OCR, and AI Processing
        ↓
Structured Knowledge Generation
        ↓
Label Design and QR-Code Generation
        ↓
Physical Thermal Printing
```

The main difference is the output method. NaviBlind provides product information through speech, whereas PrintSensei transforms the extracted information into a physical adhesive label.

---

## Combined Research Relationship

Both related papers demonstrate the importance of combining language understanding, visual perception, and AI reasoning in intelligent interactive systems.

PrintSensei combines these concepts into one workflow:

```text
Voice Interaction
+
Camera and OCR
+
Object Recognition
+
Local and Cloud AI
        ↓
Context Understanding and Reasoning
        ↓
Knowledge and Label Generation
        ↓
QR Code and Layout Creation
        ↓
Physical Thermal Printing
```

PrintSensei extends existing multimodal AI assistant concepts by introducing automatic physical knowledge and label generation as the robot's final action.

---

## Project Status

- [x] Project concept defined
- [x] Problem statement prepared
- [x] Proposed architecture prepared
- [x] Hardware requirements prepared
- [x] Initial literature review completed
- [ ] Hardware procurement
- [ ] Raspberry Pi setup
- [ ] Camera integration
- [ ] Speech-recognition integration
- [ ] OCR integration
- [ ] Object-detection integration
- [ ] Dashboard development
- [ ] Inventory database development
- [ ] Label-layout engine development
- [ ] QR-code generation integration
- [ ] Thermal-printer integration
- [ ] OLED display integration
- [ ] LED status integration
- [ ] Enclosure design
- [ ] System testing
- [ ] Final demonstration

---

## Final Project Definition

> PrintSensei is a Raspberry Pi-based intelligent multimodal robotic labeling and knowledge assistant that uses speech recognition, computer vision, OCR, object detection, local AI models, and cloud-based AI APIs to understand user requests and automatically generate and print context-aware labels, study cards, inventory tags, product stickers, and QR-enabled knowledge labels using a 58 mm thermal printer.

---

## License

This repository is intended for academic and educational use.

A suitable open-source license will be added as the project progresses.


## Additional requirements

1. create a virtual environment in root

2. create a .env file in root

## .env format
OPENAI_API_KEY=your key here
>>>>>>> e7dbc32b15474074688995618f207ca5325c39fc
