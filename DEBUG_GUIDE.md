# Debugging Guide

## Quick Start

### 1. Install Debugger Packages
Run `install_requirements.bat` - it will install `ipdb` and `debugpy` automatically.

### 2. Choose Your Debugging Method

## Method 1: VS Code Debugger (Recommended)

1. **Open VS Code** in this project folder
2. **Press F5** or go to Run → Start Debugging
3. **Select "Python: Streamlit Debug"** from the dropdown
4. **Set breakpoints** by clicking left of line numbers (red dots appear)
5. **Run your app** - it will pause at breakpoints

### VS Code Debug Features:
- **Step Over (F10)**: Execute current line
- **Step Into (F11)**: Go into function calls
- **Step Out (Shift+F11)**: Exit current function
- **Continue (F5)**: Resume execution
- **Variables Panel**: See all variable values
- **Watch Panel**: Monitor specific variables

## Method 2: Using ipdb (Interactive Debugger)

Add this line where you want to break:
```python
import ipdb; ipdb.set_trace()
```

When the code reaches this line, you'll get an interactive debugger in the terminal.

### ipdb Commands:
- `n` (next): Execute next line
- `s` (step): Step into function
- `c` (continue): Continue execution
- `p variable_name`: Print variable value
- `pp variable_name`: Pretty print variable
- `l` (list): Show current code
- `q` (quit): Exit debugger

## Method 3: Using Debug Helper Functions

Import and use helper functions:

```python
import debug_helper

# Print variable info in Streamlit
debug_helper.debug_print("my_dataframe", df)

# Show all session state
debug_helper.debug_session_state()

# Add breakpoint
debug_helper.debug_breakpoint()
```

## Method 4: Streamlit Built-in Debugging

### Enable Debug Mode:
```bash
streamlit run app.py --logger.level=debug
```

### Use st.write() for Quick Debugging:
```python
st.write("Debug info:", variable_name)
st.write("Type:", type(variable_name))
```

## Common Debugging Scenarios

### Debug File Upload Issues
```python
if uploaded_file is not None:
    import debug_helper
    debug_helper.debug_print("uploaded_file", uploaded_file)
    debug_helper.debug_print("file_name", uploaded_file.name)
```

### Debug DataFrame Operations
```python
import debug_helper
debug_helper.debug_print("df_before", df)
# ... your code ...
debug_helper.debug_print("df_after", df)
```

### Debug Session State
```python
import debug_helper
debug_helper.debug_session_state()
```

### Debug Cleaning Logic
```python
for col, method in cleaning_choices.items():
    import ipdb; ipdb.set_trace()  # Break here
    # Your cleaning code
```

## Tips

1. **Use print() for quick checks** - Output appears in terminal
2. **Use st.write() for Streamlit UI** - Shows in browser
3. **Use ipdb for complex debugging** - Full interactive debugger
4. **Use VS Code debugger for best experience** - Integrated IDE debugging
5. **Check terminal output** - Streamlit shows errors and logs there

## Troubleshooting

- **Breakpoint not hitting**: Make sure code path is executed
- **Debugger not starting**: Check if packages are installed (`pip install ipdb debugpy`)
- **VS Code debugger issues**: Check `.vscode/launch.json` configuration
- **ipdb not working**: Make sure you're running from terminal, not Streamlit UI

## Example: Debugging Missing Values

```python
# Add this to your missing value analysis section
import debug_helper

for col in current_df.columns:
    missing_count = current_df[col].isnull().sum()
    
    # Debug this column
    if missing_count > 0:
        debug_helper.debug_print(f"Column: {col}", current_df[col])
        import ipdb; ipdb.set_trace()  # Break here to inspect
```

Happy Debugging! 🐛🔍

