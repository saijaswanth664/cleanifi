# Quick Start Guide

## How to Run the App

### Method 1: Using Batch File (Easiest)

1. **Double-click `run_app.bat`**
   - The app will start automatically
   - Your browser will open to `http://localhost:8501`

### Method 2: Using Command Line

1. **Open PowerShell or Command Prompt** in this folder
2. **Run one of these commands:**

   ```powershell
   # Try this first
   python -m streamlit run app.py
   
   # If that doesn't work, try:
   python3 -m streamlit run app.py
   
   # Or use full path:
   "C:\Users\DELL\AppData\Local\Programs\Python\Python313\python.exe" -m streamlit run app.py
   ```

### Method 3: Using VS Code

1. Open the project folder in VS Code
2. Press `F5` or go to Run → Start Debugging
3. Select "Python: Streamlit Debug"

## Troubleshooting

### "streamlit is not recognized"

**Solution:** Use `python -m streamlit` instead of just `streamlit`

```bash
python -m streamlit run app.py
```

### "Python is not recognized"

**Solution:** 
1. Install Python from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Restart your terminal/command prompt

### "No module named streamlit"

**Solution:** Install packages first:
```bash
python -m pip install -r requirements.txt.txt
```

Or double-click `install_requirements.bat`

## What Happens When You Run?

1. A terminal window will open
2. Streamlit server starts
3. Your browser opens automatically to `http://localhost:8501`
4. You'll see the Data Cleaning Tool interface

## Stopping the App

- Press `Ctrl+C` in the terminal
- Or close the terminal window

## Need Help?

- Check `README.md` for detailed instructions
- Check `DEBUGGER_TROUBLESHOOTING.md` for debugging issues

