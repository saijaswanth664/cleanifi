# Debugger Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: Debugger Not Starting

**Symptoms:**
- Press F5 but nothing happens
- Error: "debugpy not found"
- Error: "Python interpreter not found"

**Solutions:**

1. **Install debugpy:**
   ```bash
   pip install debugpy
   ```
   Or run: `install_requirements.bat`

2. **Check Python Interpreter:**
   - Press `Ctrl+Shift+P` in VS Code
   - Type "Python: Select Interpreter"
   - Choose the correct Python version

3. **Verify Python Extension:**
   - Install "Python" extension by Microsoft in VS Code
   - Install "Pylance" extension (recommended)

### Issue 2: Breakpoints Not Hitting

**Symptoms:**
- Breakpoints are set but code doesn't stop
- Breakpoints show as gray/unverified

**Solutions:**

1. **Check if code path is executed:**
   - Make sure the line with breakpoint is actually run
   - For Streamlit, breakpoints work but app continues running

2. **Use `justMyCode: false`:**
   - Already set in launch.json
   - Allows debugging into library code

3. **For Streamlit specifically:**
   - Streamlit runs in a separate process
   - Breakpoints in the main script work
   - Use `st.write()` for quick debugging in UI

### Issue 3: Streamlit Debugger Not Working

**Symptoms:**
- VS Code debugger starts but Streamlit doesn't run
- Error about module not found

**Solutions:**

1. **Use the correct configuration:**
   - Select "Python: Streamlit Debug" from dropdown
   - Make sure `app.py` is the active file

2. **Alternative: Use ipdb:**
   ```python
   import ipdb; ipdb.set_trace()
   ```
   This works in terminal/console

3. **Test with simple script first:**
   - Run `test_debugger.py` with F5
   - If this works, debugger is fine
   - Issue is with Streamlit-specific setup

### Issue 4: VS Code Python Extension Issues

**Solutions:**

1. **Reload VS Code:**
   - Press `Ctrl+Shift+P`
   - Type "Developer: Reload Window"

2. **Check Python Extension:**
   - Go to Extensions (Ctrl+Shift+X)
   - Search "Python"
   - Make sure it's installed and enabled

3. **Check Output Panel:**
   - View → Output
   - Select "Python" from dropdown
   - Look for error messages

## Step-by-Step Debugging Setup

### Step 1: Verify Installation

Run in terminal:
```bash
python -c "import debugpy; print('debugpy installed')"
python -c "import ipdb; print('ipdb installed')"
```

### Step 2: Test Basic Debugging

1. Open `test_debugger.py`
2. Set a breakpoint on line 12 (`result = test_function()`)
3. Press F5
4. Select "Python: Current File"
5. Debugger should stop at breakpoint

### Step 3: Test Streamlit Debugging

1. Open `app.py`
2. Set a breakpoint (e.g., line 58: `st.session_state.df = pd.read_excel(uploaded_file)`)
3. Press F5
4. Select "Python: Streamlit Debug"
5. Upload a file in the browser
6. Debugger should stop at breakpoint

## Alternative Debugging Methods

### Method 1: Using ipdb (Always Works)

Add to your code:
```python
import ipdb; ipdb.set_trace()
```

Run normally:
```bash
streamlit run app.py
```

When code hits this line, terminal becomes interactive debugger.

### Method 2: Using print() and st.write()

```python
# For terminal output
print(f"Debug: df shape = {df.shape}")

# For Streamlit UI
st.write("Debug info:", df.head())
```

### Method 3: Using Debug Helper

```python
import debug_helper
debug_helper.debug_print("df", df)
debug_helper.debug_session_state()
```

## Quick Fix Checklist

- [ ] Python installed and in PATH
- [ ] VS Code Python extension installed
- [ ] debugpy installed (`pip install debugpy`)
- [ ] ipdb installed (`pip install ipdb`)
- [ ] Python interpreter selected in VS Code
- [ ] launch.json file exists in .vscode folder
- [ ] Breakpoint set on executable line
- [ ] Correct debug configuration selected

## Still Not Working?

1. **Check VS Code Output:**
   - View → Output → Select "Python"

2. **Check Terminal Output:**
   - Look for error messages when starting debugger

3. **Try Simple Test:**
   - Run `test_debugger.py` first
   - If this doesn't work, issue is with VS Code setup

4. **Use ipdb Instead:**
   - Most reliable method
   - Works in any terminal
   - Add `import ipdb; ipdb.set_trace()` to code

## Contact/Help

If still having issues:
1. Check VS Code Python extension documentation
2. Verify Python installation
3. Try ipdb method (most reliable)

