# Sisifus Analytics - Job Application Email Parser

[![CI](https://github.com/fabricioguidine/sisifus-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/fabricioguidine/sisifus-analytics/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/fabricioguidine/sisifus-analytics/branch/main/graph/badge.svg)](https://codecov.io/gh/fabricioguidine/sisifus-analytics)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
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
   - Select **"mbox"** format
6. Click **"Next step"**
7. Choose:
   - **Delivery method**: "Add to Drive" or "Send download link via email"
   - **Frequency**: "Export once"
   - **File type & size**: Keep defaults
8. Click **"Create export"**
9. Wait for Google to prepare your export (may take hours for large accounts)
10. Download the ZIP file when ready
11. Extract the ZIP file
12. Navigate to the extracted folder structure:
    - `takeout-YYYYMMDDTHHMMSSZ-XXX-001/Takeout/E-mail/`
    - You'll find `.mbox` files here (e.g., `Todos os e-mails, incluindo Spam e Lixeira-002.mbox`)
    - You can ignore the `Configurações do usuário` folder (it contains settings, not emails)

### Import the exported emails:

```bash
# Option A: Place .mbox file(s) in input folder, then auto-import
# Copy your .mbox file(s) to the input/ folder, then:
python -m src.import_emails

# Option B: Import directly from a specific file
python -m src.import_emails "input/Todos os e-mails, incluindo Spam e Lixeira-002.mbox"

# Option C: Import from Google Takeout folder structure (auto-detects .mbox files)
# If you extracted the entire Takeout folder in input/, it will find .mbox files automatically
python -m src.import_emails
```

**Important Notes:**
- The tool automatically searches for `.mbox` files in the `input/` folder (including subdirectories)
- Configuration files (JSON files in `Configurações do usuário` folder) are automatically ignored
- You can have multiple `.mbox` files - all will be imported
- Only `.mbox` files are supported (Google Takeout format)

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
  - Typical size: ~50-200 MB for 100K emails

**Output Folder** (`output/`):
The application generates three output files in the `output/` directory:

1. **`analytics.json`**: Complete analytics data including:
   - Status breakdown
   - Company details
   - Date ranges
   - Individual email records
   - Typical size: ~30-150 MB

2. **`applications.csv`**: Spreadsheet-friendly format with columns:
   - Company
   - Status
   - Date
   - Subject
   - Confidence score
   - Typical size: ~5-20 MB

3. **`sankey_diagram.html`**: Interactive visualization that you can open in any web browser
   - Typical size: ~100-500 KB

## ⚡ Performance & Benchmarks

### File Size Estimates

Based on typical email data, here are approximate file sizes:

| Emails | .mbox File Size | emails.json Size | Processing Time* |
|--------|----------------|------------------|------------------|
| 1,000 | ~2-5 MB | ~1-3 MB | < 1 minute |
| 10,000 | ~20-50 MB | ~10-30 MB | ~1-2 minutes |
| 50,000 | ~100-250 MB | ~50-150 MB | ~3-5 minutes |
| 100,000 | ~200-500 MB | ~100-300 MB | ~5-10 minutes |
| 146,000+ | ~300-750 MB | ~150-450 MB | ~7-15 minutes |

\* *Processing time includes classification and analytics generation. Import time is separate (see below).*

### Processing Speed

The application uses **optimized batch processing** for fast classification:

```
Performance Graph (Emails/Second):
─────────────────────────────────────────────────────────────────────────
500 │                                                        ████████████
    │                                                ████████████████████
400 │                                        ████████████████████████████
    │                                ████████████████████████████████████
300 │                        ████████████████████████████████████████████
    │                ████████████████████████████████████████████████████
200 │        ████████████████████████████████████████████████████████████
    │████████████████████████████████████████████████████████████████████
100 │████████████████████████████████████████████████████████████████████
    │████████████████████████████████████████████████████████████████████
  0 └─────────────────────────────────────────────────────────────────────
      Before        After        Batch Size: 1000     Optimized
    
    Before Optimization:  ~3 emails/sec   (❌ ~13 hours for 146K emails)
    After Optimization:   ~100-500 emails/sec   (✅ ~7-15 minutes)
```

### Import Performance

**Import from .mbox files:**
- **Speed**: ~200-1,500 emails/second
- **Example**: 146,422 emails imported in ~9.3 minutes (~262 emails/second)
- Shows progress bar with real-time statistics

### Classification Performance

**Classification speed:**
- **Batch processing**: 1,000 emails per batch
- **Speed**: ~100-500 emails/second (after optimization)
- **Optimizations**:
  - ✅ Batch processing (1000 emails at once)
  - ✅ Limited body text search (first 5000 chars)
  - ✅ Early exit for high-confidence matches
  - ✅ Compiled regex patterns

### Real-World Example

**Dataset**: 146,422 emails

| Step | Time | Speed |
|------|------|-------|
| Import from .mbox | ~9.3 min | ~262 emails/sec |
| Classification | ~7-15 min | ~100-500 emails/sec |
| Analytics Generation | ~1-2 min | - |
| **Total** | **~17-26 min** | - |

### Memory Usage

- **Import**: ~200-500 MB RAM for 100K emails
- **Classification**: ~300-800 MB RAM during processing
- **Analytics**: ~100-300 MB RAM

**Note**: Large datasets (200K+ emails) may require 2-4 GB RAM.

## 💾 Storage Requirements

### Disk Space Needed

| Emails | Minimum Space | Recommended Space |
|--------|--------------|-------------------|
| 1,000 | ~10 MB | ~50 MB |
| 10,000 | ~100 MB | ~500 MB |
| 50,000 | ~500 MB | ~2 GB |
| 100,000 | ~1 GB | ~4 GB |
| 146,000+ | ~1.5 GB | ~6 GB |

**Space breakdown:**
- Google Takeout ZIP: ~2-3x final size (compressed)
- Extracted .mbox file: Base size
- `emails.json`: ~1-3x .mbox size (includes metadata)
- Output files: ~10-20% of `emails.json` size

### Tips for Large Datasets

- ✅ Use SSD storage for faster processing
- ✅ Ensure 4+ GB free RAM for 100K+ emails
- ✅ Close other applications during processing
- ✅ Process during off-hours for large imports

## 🧠 Classification Logic

The application uses **keyword-based pattern matching** (no LLM required) to classify emails into job application statuses. The classification process has two main stages:

### Stage 1: Job-Related Filtering

Before classification, emails are filtered to identify job-related content:

- **Job-related emails**: Contain keywords like "job", "application", "interview", "recruiter", "hiring", "position", "candidate", "opportunity", "career", etc.
- **Non-job emails**: Newsletters, promotions, personal emails, spam, etc. are marked as `not_job_related` and excluded from job application statistics
- **Job-related domains**: Emails from known job platforms (LinkedIn, Indeed, Glassdoor, etc.) are automatically considered job-related

### Stage 2: Status Classification

Job-related emails are classified into the following statuses using regex pattern matching:

| Status | Description | Examples |
|--------|-------------|----------|
| **applied** | Initial application submitted | "Thank you for your application", "Application received", "Job opportunity" |
| **confirmation** | Application confirmation received | "We have received your application", "Application successfully received" |
| **interview_1, interview_2, ...** | Interview stages (numbered) | "First interview", "Phone screen", "Technical interview", "Final round" |
| **offer** | Job offer received | "We are pleased to offer", "Job offer", "Congratulations, we'd like to offer" |
| **accepted** | Offer accepted | "I accept", "I'm excited to accept", "Accepting the offer" |
| **rejected** | Application rejected by company | "We regret to inform", "Not selected", "Decided to pursue other candidates" |
| **withdrew** | Application withdrawn by user | "Withdraw application", "No longer interested", "Declined interview" |
| **no_reply** | No clear status (low confidence) | Job-related emails that don't match any specific status pattern |
| **not_job_related** | Non-job emails (excluded from stats) | Newsletters, promotions, personal emails |

### Classification Process

1. **Email Preprocessing**: Extract subject and body text (HTML converted to plain text)
2. **Job Filtering**: Check if email contains job-related keywords or is from a job platform
3. **Pattern Matching**: Search for status-specific keywords in subject and body (first 5000 chars)
4. **Confidence Scoring**: Calculate confidence based on number of matching patterns
5. **Priority Rules**: Higher-priority statuses (e.g., "rejected", "offer") override lower-priority ones
6. **Company Extraction**: Extract company name from email domain or sender name

### Accuracy

The application calculates accuracy as the percentage of emails classified with confidence > 0.5. Typical accuracy ranges from **70-90%** depending on:

- Email wording and clarity
- Language (English vs. Portuguese patterns supported)
- Email quality and formatting
- Presence of standard job application terminology

**Note**: The keyword-based approach is fast and privacy-preserving, but may misclassify:
- Unusual email wording or non-standard formats
- Emails in languages not explicitly supported
- Ambiguous statuses that require context

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

The application tracks the following job application statuses:

### Application Flow Statuses

1. **Applied** (`applied`): Initial applications sent by you or job opportunities received
2. **Confirmation** (`confirmation`): Receipt confirmations from companies
3. **Interview Stages** (`interview_1`, `interview_2`, `interview_3`, etc.): Interview rounds (numbered sequentially)
4. **Offer** (`offer`): Job offers received from companies
5. **Accepted** (`accepted`): Offers you accepted

### Outcome Statuses

6. **Rejected** (`rejected`): Applications rejected by the company (consolidated in Sankey diagram)
7. **Withdrew** (`withdrew`): Applications you withdrew or declined (consolidated in Sankey diagram)
8. **Ghosted** (`no_reply` + `no_progress_after_interview_X`): No response received, consolidated into single "Ghosted" node in Sankey diagram

### Excluded Statuses

9. **Not Job Related** (`not_job_related`): Non-job emails excluded from application statistics

### Sankey Diagram Consolidation

In the Sankey diagram visualization, similar statuses are consolidated for clarity:

- **Rejected**: All rejection types (direct and after interviews) → Single "Rejected" node
- **Withdrew**: All withdrawal types (direct and after interviews) → Single "Withdrew" node  
- **Ghosted**: "No Reply" and "No Progress After Interview X" → Single "Ghosted" node

## ⚠️ Limitations

### Classification Limitations

1. **Keyword-Based Approach**
   - Classification relies on pattern matching, so unusual email wording may be misclassified
   - Emails with non-standard formats or creative language may not match patterns
   - Context-dependent emails (e.g., sarcasm, informal language) may be misclassified
   - **Accuracy**: Typically 70-90% depending on email quality and wording

2. **Language Support**
   - Primary support for **English** and **Portuguese** keywords
   - Other languages may have lower accuracy
   - Mixed-language emails may not be classified correctly

3. **Status Ambiguity**
   - Some emails may match multiple status patterns (priority rules apply)
   - Low-confidence emails are classified as `no_reply`
   - Edge cases (e.g., "we decided not to proceed" from user vs. company) may be misclassified

4. **Company Name Extraction**
   - Relies on email domains (e.g., `noreply@company.com` → "company")
   - May not always extract the correct company name
   - Generic domains (gmail.com, outlook.com) may result in "Unknown" company
   - Third-party recruiters may show recruiter company instead of actual employer

5. **Interview Stage Detection**
   - Stages are detected from email content (e.g., "first interview", "final round")
   - If stage numbers aren't explicit, may not be numbered correctly
   - Missing intermediate stages are inferred in the Sankey diagram

### Data Limitations

6. **Email Import**
   - Only supports `.mbox` format (Google Takeout)
   - Corrupted or malformed emails may be skipped
   - Very large files (>500MB) may take significant time to import

7. **Sankey Diagram Assumptions**
   - Assumes linear progression: applications → interviews → offers
   - Non-linear flows (e.g., direct offers without interviews) are handled but may look unusual
   - Missing intermediate interview stages are estimated from higher stages

8. **Performance**
   - Very large datasets (500K+ emails) may require:
     - 4-8 GB RAM
     - 30+ minutes processing time
     - Significant disk space (2-4 GB)
   - Date filtering is recommended for large datasets

### Known Edge Cases

- **False Positives**: Non-job emails may be classified as job-related if they contain job keywords
- **False Negatives**: Job emails with unusual wording may be marked as `not_job_related`
- **Rejection vs. Withdrawal**: May misclassify user declines as company rejections (or vice versa) if language is ambiguous
- **Multiple Companies**: Emails from third-party recruiters may show recruiter company instead of actual employer

## 🔧 Troubleshooting

### Import Issues

- Ensure your `.mbox` file is not corrupted
- Check that the file path is correct
- Verify the file format is `.mbox` (Google Takeout format)
- The tool automatically ignores configuration folders (`Configurações do usuário`)
- Make sure the `.mbox` file is in the `input/` folder or a subdirectory

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

