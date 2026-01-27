
# cleanifi
CLEANIFI – AI-assisted data cleaning web application using Flask
# AI-Based Automatic Data Cleaning Tool

# Cleanifi

Flask-based data cleaning and authentication web application for cleaning Excel files without writing code.

## Features

- 📊 Upload Excel files (.xlsx)
- 🔤 Automatic column name standardization
- 🔍 Missing value analysis
- 🤖 AI-assisted cleaning suggestions
- 🧹 Multiple cleaning methods (Mean, Median, Mode, etc.)
- 📈 Data quality scoring
- 💾 Download cleaned Excel files

## Installation

### Option 1: Using Batch Files (Easiest for Windows)

1. **Install Python** (if not already installed)
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **Install Dependencies**
   - Double-click `install_requirements.bat`
   - Wait for installation to complete

3. **Run the Application**
   - Double-click `run_app.bat`
   - The app will open in your browser automatically

### Option 2: Using Command Prompt/PowerShell

1. Open Command Prompt or PowerShell in this folder

2. Install dependencies:
   ```bash
   pip install -r requirements.txt.txt
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

## Usage

1. Upload an Excel file (.xlsx)
2. Review the original dataset
3. Accept column name standardization (optional)
4. Analyze missing values
5. Choose cleaning methods for each column with missing values
6. Apply cleaning
7. Download the cleaned Excel file

## Requirements

- Python 3.7 or higher
- streamlit
- pandas
- openpyxl
- ipdb (debugger)
- debugpy (VS Code debugger)

## Troubleshooting

- **"Python not found"**: Make sure Python is installed and added to PATH
- **"streamlit not recognized"**: Run `install_requirements.bat` first
- **Port already in use**: Close other Streamlit apps or change the port: `streamlit run app.py --server.port 8502`

## Reset Session

Use the "🔄 Reset Session" button in the sidebar to clear all data and start over.

## Debugging

### Option 1: Using VS Code Debugger

1. Open the project in VS Code
2. Go to Run and Debug (F5)
3. Select "Python: Streamlit Debug"
4. Set breakpoints in your code
5. Start debugging

### Option 2: Using Debug Helper

1. Import the debug helper in your code:
   ```python
   import debug_helper
   ```

2. Add debug statements:
   ```python
   debug_helper.debug_print("df", df)
   debug_helper.debug_session_state()
   ```

3. Or add breakpoints:
   ```python
   debug_helper.debug_breakpoint()
   ```

### Option 3: Using Debug Batch File

- Double-click `run_app_debug.bat` to run in debug mode
- Add `import ipdb; ipdb.set_trace()` where you want to break

### Debugging Tips

- Use `st.write()` to display variables in Streamlit
- Check the terminal/console for print statements
- Use Streamlit's built-in error messages
- Enable Streamlit's debug mode: `streamlit run app.py --logger.level=debug`

d76aea2 (Initial commit - Cleanifi Flask App)
