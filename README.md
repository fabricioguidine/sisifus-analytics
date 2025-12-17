# Sisifus Analytics - Job Application Email Parser

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)](https://github.com/fabricioguidine/sisifus-analytics)

A Python application that parses your email inbox to track job application statuses, generate analytics, and visualize your job search progress using a Sankey diagram.

## 🚀 Features

- 📧 **Email Import**: Import emails from exported `.mbox` files (Google Takeout format)
- 🤖 **Keyword-Based Classification**: Uses pattern matching (no LLM required) to classify emails into application statuses
- 📊 **Analytics**: Tracks applications, confirmations, interview stages, offers, and rejections
- 📈 **Visualization**: Generates interactive Sankey diagram showing application flow
- 🏢 **Company Tracking**: Extracts and tracks company names from emails
- 📅 **Date Tracking**: Records dates for all application-related emails
- ✅ **Accuracy Metrics**: Calculates classification accuracy percentage
- 🧪 **Tested**: Comprehensive pytest test suite for classification logic

### Running Locally is Very Safe

This application is designed to run **100% locally** on your machine. Here's how it handles security:

1. **No Cloud Processing**: All email parsing and classification happens on your local machine
2. **No Data Transmission**: Your emails are never sent to external servers or APIs
3. **Local Storage Only**: All input and output files are saved locally
4. **No LLM Calls**: Classification uses keyword matching, so no external API calls are made
5. **No Credentials Required**: You export your emails manually from Google Takeout - no credentials needed!

## 📦 Installation

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 📬 How to Get Your Emails

Export your emails from Google Takeout and import them into the application:

### Export from Google Takeout (Gmail):

1. Go to [Google Takeout](https://takeout.google.com/)
2. Sign in with your Google account
3. Click **"Deselect all"** to start fresh
4. Scroll down and check **"Mail"**
5. Click **"Multiple formats"** next to Mail
   - Select **"mbox"** format (recommended)
6. Click **"Next step"**
7. Choose:
   - **Delivery method**: "Add to Drive" or "Send download link via email"
   - **Frequency**: "Export once"
   - **File type & size**: Keep defaults
8. Click **"Create export"**
9. Wait for Google to prepare your export (may take hours for large accounts)
10. Download the ZIP file when ready
11. Extract the ZIP file
12. Look for the `Mail` folder inside - it contains `.mbox` files

### Import the exported emails:

```bash
# Option A: Place .mbox file in input folder, then auto-import
# Copy your .mbox file to the input/ folder, then:
python -m src.import_emails

# Option B: Import directly from a specific file
python -m src.import_emails path/to/your/Mail.mbox
```

**Supported formats:**
- ✅ `.mbox` files (Google Takeout format)

## 💻 Usage

### Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Export and import your emails**:
   ```bash
   # 1. Export emails from Google Takeout (see instructions above)
   # 2. Import the exported file:
   python -m src.import_emails /path/to/your/Mail.mbox
   
   # OR place .mbox file in input/ folder and auto-import:
   python -m src.import_emails
   ```

3. **Process the emails**:
   ```bash
   python -m src.main --use-input
   ```
   
   The script will:
   1. Load emails from `input/emails.json`
   2. Classify each email (shows progress bar)
   3. Generate analytics and visualizations
   4. Display summary statistics including accuracy percentage
   5. Save results to `output/` directory

### Email Import Options

**Import from exported files**:
```bash
# Auto-detect and import from input folder
python -m src.import_emails

# Import specific .mbox file
python -m src.import_emails /path/to/Mail.mbox
```

**Process imported emails**:
```bash
# Process emails from input folder
python -m src.main --use-input
```

### Input and Output Files

**Input Folder** (`input/`):
- **`emails.json`**: Raw email data imported from exported files
  - Contains all email metadata (subject, body, from, date)
  - Created when you import emails from Google Takeout or other sources
  - Can be reused multiple times without re-importing

**Output Folder** (`output/`):
The application generates three output files in the `output/` directory:

1. **`analytics.json`**: Complete analytics data including:
   - Status breakdown
   - Company details
   - Date ranges
   - Individual email records

2. **`applications.csv`**: Spreadsheet-friendly format with columns:
   - Company
   - Status
   - Date
   - Subject
   - Confidence score

3. **`sankey_diagram.html`**: Interactive visualization that you can open in any web browser

## 🧠 Classification Logic

The application uses keyword-based pattern matching to classify emails into the following statuses:

- **applied**: Initial application submitted
- **confirmation**: Application confirmation received
- **interview_1, interview_2, interview_3, ...**: Interview stages
- **offer**: Job offer received
- **accepted**: Offer accepted
- **rejected**: Application rejected
- **withdrew**: Application withdrawn
- **no_reply**: No clear status (low confidence)

### Accuracy

The application calculates accuracy as the percentage of emails classified with confidence > 0.5. Typical accuracy ranges from **70-90%** depending on email quality and wording.

## 📁 Project Structure

```
sisifus-analytics/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   ├── email_importer.py  # Import from exported files (Google Takeout, mbox, eml)
│   ├── email_storage.py   # Save/load emails from input folder
│   ├── import_emails.py   # Script to import emails from exported files
│   ├── classifier.py      # Keyword-based classification
│   ├── analytics.py       # Analytics and visualization
│   └── main.py            # Main entry point
├── tests/
│   ├── __init__.py
│   └── test_classifier.py # Pytest tests
├── input/                 # Email data storage (emails.json)
├── output/                # Generated analytics files
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

Or with verbose output:

```bash
pytest tests/ -v
```

Tests cover:
- Email classification for each status type
- Priority rules (e.g., rejection overrides other statuses)
- Company name extraction
- Confidence score calculations
- Batch processing

## 🏗️ Architecture

The application follows a clean, modular architecture:

- **Separation of Concerns**: Each module has a single responsibility
- **Testability**: Business logic (classifier) is easily testable
- **Extensibility**: Easy to add new status types or email providers
- **Configuration**: Settings externalized to config files
- **Error Handling**: Graceful handling of import and parsing errors

## 📋 Status Categories Tracked

The application tracks:

1. **Applications**: Initial applications sent
2. **Confirmations**: Receipt confirmations
3. **Interview Stages**: 1st, 2nd, 3rd, 4th, 5th interviews
4. **Offers**: Job offers received
5. **Accepted**: Offers accepted
6. **Rejected**: Applications rejected
7. **Withdrew**: Applications withdrawn
8. **No Reply**: No response/unknown status

## ⚠️ Limitations

- Classification is based on keyword matching, so unusual email wording might not be classified correctly
- Company name extraction relies on email domains, which may not always be accurate
- The Sankey diagram flow assumes a linear progression (applications → interviews → offers)

## 🔧 Troubleshooting

### Import Issues

- Ensure your `.mbox` file is not corrupted
- Check that the file path is correct
- Try importing a smaller subset of emails to test
- Verify the file format is `.mbox` (Google Takeout format)

### Low Accuracy

- Review the `applications.csv` file to see confidence scores
- Emails with low confidence (< 0.5) might need manual review
- Consider adding more keywords to `classifier.py` if you notice patterns

### No Emails Found

- Ensure you've successfully imported emails using `python -m src.import_emails`
- Check that `input/emails.json` exists and contains email data
- Verify your exported file contains job-related emails

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📄 License

This project is open source and available for personal use.

## ⚖️ Disclaimer

This tool is for personal use only. Always ensure you have permission to access and process email data. The authors are not responsible for any misuse of this software.

