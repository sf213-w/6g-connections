# Excel Spreadsheet Analyzer

Script to do web searches based on the contents of an excel spreadsheet.

## Project Purpose

Automation of tasks.

## Setup Instructions

Download

### Prerequisites

- Python 3.8 or higher installed
- [Ollama](https://ollama.com) installed and running locally
- LLaMA model pulled:

```bash
ollama pull llama3.2
```

#### Step 1: Open a Terminal and Navigate to the Project Folder

```bash
cd path/to/your/project
```

#### Step 2: Create a Virtual Environment

```bash
python -m venv venv
```

#### Step 3: Activate the Environment

For Windows PowerShell

```bash
.\venv\Scripts\Activate
```

If attempting to activate the virtual environment provides an error message saying running scripts is disabled on this system then you may need to change the exectution policy.
Run the following command to change the excecution policy for the current PowerShell session.

```bash
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

#### Step 4: Install Requirements
