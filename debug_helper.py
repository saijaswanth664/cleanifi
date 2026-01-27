"""
Debug Helper Functions
Add these to your code for debugging purposes
"""

import ipdb
import streamlit as st

def debug_breakpoint():
    """Add a breakpoint in your Streamlit app"""
    # Usage: debug_helper.debug_breakpoint()
    ipdb.set_trace()

def debug_print(var_name, var_value):
    """Print debug information in Streamlit"""
    # Usage: debug_helper.debug_print("df", df)
    st.write(f"🔍 DEBUG: {var_name}")
    st.write(var_value)
    st.write(f"Type: {type(var_value)}")
    if hasattr(var_value, 'shape'):
        st.write(f"Shape: {var_value.shape}")

def debug_session_state():
    """Display all session state variables"""
    st.write("🔍 DEBUG: Session State")
    for key, value in st.session_state.items():
        st.write(f"- {key}: {type(value).__name__}")

# Example usage in app.py:
# import debug_helper
# debug_helper.debug_print("df", df)
# debug_helper.debug_session_state()

