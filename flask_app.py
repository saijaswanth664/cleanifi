from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import pandas as pd
import re
from io import BytesIO
import time
import auth_utils
import config
import msoffcrypto
import os
import io
import secrets
import pickle
import tempfile
from werkzeug.utils import secure_filename
from auth_utils import sanitize_input
from flask_talisman import Talisman
from flask_session import Session
import subprocess

app = Flask(__name__)
# Force HTTPS and set security headers in production
# Skip force_https for local development unless we have local certs
Talisman(app, content_security_policy=None, force_https=False) 

# Session Configuration
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(app.root_path, 'flask_session')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = False
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

# Initialize Session
Session(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Custom Jinja2 filter for column name cleaning
@app.template_filter('clean_column_name')
def clean_column_name_filter(col):
    return clean_column_name(col)

# Custom Jinja2 filter for number formatting
@app.template_filter('number_format')
def number_format_filter(value):
    try:
        return f"{int(value):,}"
    except:
        return value


# ---------------- HELPER FUNCTIONS (PRESERVED FROM STREAMLIT) ----------------
def save_to_history(action_name):
    """Saves a snapshot of the current dataframe to history."""
    if 'df' in session and session['df'] is not None:
        if 'history' not in session:
            session['history'] = []
        
        snapshot = {
            "df": session['df'],
            "columns": list(pd.DataFrame(session['df']).columns),
            "action": action_name,
            "timestamp": time.time()
        }
        session['history'].append(snapshot)
        # Keep only last 10 versions to save memory
        if len(session['history']) > 10:
            session['history'].pop(0)
        session.modified = True

def undo_action():
    """Restores the last snapshot from history."""
    if 'history' in session and session['history']:
        last_state = session['history'].pop()
        session['df'] = last_state["df"]
        session['original_columns'] = last_state["columns"]
        session.modified = True
        return True, f"⏪ Reverted: {last_state['action']}"
    return False, "No history to undo"

def clean_column_name(col):
    col = str(col).lower()
    col = re.sub(r"[^\w\s]", "", col)  # remove special characters
    col = col.strip()
    col = col.replace(" ", "_")
    return col

def is_strong_password(password):
    """Enforces strong password rules."""
    if len(password) < 7:
        return False, "Password must be at least 7 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character (@#$%!&*)."
    return True, "Strong password!"

def encrypt_excel(df, password):
    """Encrypts a pandas DataFrame into a native password-protected Excel file using PowerShell/COM."""
    temp_dir = tempfile.gettempdir()
    unsecured_path = os.path.join(temp_dir, f"unsecured_{int(time.time())}.xlsx")
    secured_path = os.path.join(temp_dir, f"secured_{int(time.time())}.xlsx")
    
    try:
        # 1. Save to temporary unsecured file
        df.to_excel(unsecured_path, index=False, engine='openpyxl')
        
        # 2. Use PowerShell to encrypt via Excel COM
        # We escape single quotes in the password for the PowerShell string
        safe_password = password.replace("'", "''")
        
        ps_script = f"""
        $excel = New-Object -ComObject Excel.Application
        $excel.Visible = $false
        $excel.DisplayAlerts = $false
        try {{
            $wb = $excel.Workbooks.Open('{unsecured_path}')
            $wb.Password = '{safe_password}'
            $wb.SaveAs('{secured_path}')
            $wb.Close()
        }} finally {{
            $excel.Quit()
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
        }}
        """
        
        result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(secured_path):
            with open(secured_path, "rb") as f:
                output = io.BytesIO(f.read())
            return output, True
        else:
            print(f"ERROR: PowerShell encryption failed. Return code: {result.returncode}")
            # Fallback to unencrypted
            with open(unsecured_path, "rb") as f:
                output = io.BytesIO(f.read())
            return output, False
            
    except Exception as e:
        print(f"DEBUG: Encryption fallback engaged. Reason: {e}")
        # Final fallback
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Cleaned Data')
        output.seek(0)
        return output, False
    finally:
        # Cleanup
        for path in [unsecured_path, secured_path]:
            if os.path.exists(path):
                try: os.remove(path)
                except: pass

def df_to_session_dict(df):
    """Convert DataFrame to a JSON-serializable dict for session storage."""
    # Replace NaT and NaN with None for JSON serialization
    df = df.copy()
    # Convert datetime columns to string to avoid NaT issues
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype(str).replace('NaT', None)
    # Use where() instead of fillna() for pandas 2.x compatibility
    return df.where(pd.notna(df), None).to_dict('records')

def init_session():
    """Initialize session variables if they don't exist"""
    defaults = {
        'logged_in': False,
        'df': None,
        'original_df': None,
        'uploaded_original_df': None,
        'original_columns': None,
        'columns_cleaned': False,
        'renaming_done': False,
        'cleaning_done': False,
        'uploaded_file_id': None,
        'history': [],
        'change_log': [],
        'original_stats': {},
        'secure_download': False,
        'download_password': '',
        'dark_mode': False
    }
    for key, value in defaults.items():
        if key not in session:
            session[key] = value

# ---------------- ROUTES ----------------

@app.route('/')
def index():
    init_session()
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return render_template('login.html', dark_mode=session.get('dark_mode', False))

@app.route('/login', methods=['POST'])
def login():
    username = sanitize_input(request.form.get('username', '').strip())
    password = request.form.get('password', '').strip()
    
    if username and password:
        success, message = auth_utils.verify_user(username, password)
        if success:
            session['logged_in'] = True
            session['username'] = username
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        else:
            return jsonify({'success': False, 'message': message})
    return jsonify({'success': False, 'message': 'Please enter username and password'})

@app.route('/login_with_google', methods=['POST'])
def login_with_google():
    data = request.get_json()
    id_token = data.get('id_token')
    
    if not id_token:
        return jsonify({'success': False, 'message': 'No ID Token provided'})
    
    user_info, error = auth_utils.verify_google_token(id_token)
    if error:
        return jsonify({'success': False, 'message': f'Verification failed: {error}'})
    
    username = user_info.get('email', user_info.get('name'))
    session['logged_in'] = True
    session['username'] = username
    session['user_info'] = user_info
    
    return jsonify({'success': True, 'redirect': url_for('dashboard')})

@app.route('/signup', methods=['POST'])
def signup():
    username = sanitize_input(request.form.get('username', '').strip())
    password = request.form.get('password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    question_index = request.form.get('question_index')
    answer = request.form.get('answer', '').strip()
    
    if username and password and question_index is not None and answer:
        if password == confirm_password:
            # Check password strength
            is_valid, msg = is_strong_password(password)
            if not is_valid:
                return jsonify({'success': False, 'message': msg})
                
            success, message = auth_utils.add_user(username, password, int(question_index), answer)
            return jsonify({'success': success, 'message': message})
        else:
            return jsonify({'success': False, 'message': 'Passwords do not match'})
    return jsonify({'success': False, 'message': 'Please fill in all fields (including security question)'})

@app.route('/get_recovery_question', methods=['POST'])
def get_recovery_question():
    username = request.form.get('username', '').strip()
    if not username:
        return jsonify({'success': False, 'message': 'Username required'})
    
    question = auth_utils.get_user_question(username)
    if question:
        return jsonify({'success': True, 'question': question})
    return jsonify({'success': False, 'message': 'User not found or no security question set'})

@app.route('/reset_password', methods=['POST'])
def reset_password():
    username = request.form.get('username', '').strip()
    answer = request.form.get('answer', '').strip()
    new_password = request.form.get('new_password', '').strip()
    
    if not username or not answer or not new_password:
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    if auth_utils.verify_security_answer(username, answer):
        is_valid, msg = is_strong_password(new_password)
        if not is_valid:
            return jsonify({'success': False, 'message': msg})
            
        if auth_utils.reset_password(username, new_password):
            return jsonify({'success': True, 'message': 'Password reset successful!'})
        else:
            return jsonify({'success': False, 'message': 'Error resetting password'})
    else:
        return jsonify({'success': False, 'message': 'Incorrect answer to security question'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    init_session()
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    
    # Prepare data for template
    df_data = None
    df_stats = None
    missing_summary = []
    
    if session.get('df') is not None:
        df = pd.DataFrame(session['df'])
        df_data = {
            'columns': list(df.columns),
            'rows': len(df),
            'preview': df.head(10).to_dict('records')
        }
        
        # Calculate stats
        total_cells = df.size
        missing_total = df.isnull().sum().sum()
        df_stats = {
            'rows': len(df),
            'columns': len(df.columns),
            'total_cells': total_cells,
            'missing_total': missing_total
        }
        
        # Missing value analysis
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            if pd.api.types.is_numeric_dtype(df[col]):
                dtype = "Numeric"
            elif pd.api.types.is_datetime64_any_dtype(df[col]) or "date" in col.lower() or "time" in col.lower():
                dtype = "DateTime"
            else:
                dtype = "Text"
            
            if missing_count > 0:
                missing_summary.append({
                    "column": col,
                    "dtype": dtype,
                    "missing_count": missing_count,
                    "missing_pct": f"{(missing_count / len(df) * 100):.2f}%"
                })
    
    return render_template('dashboard.html',
                         dark_mode=session.get('dark_mode', False),
                         df_data=df_data,
                         df_stats=df_stats,
                         missing_summary=missing_summary,
                         original_stats=session.get('original_stats', {}),
                         renaming_done=session.get('renaming_done', False),
                         cleaning_done=session.get('cleaning_done', False),
                         history_count=len(session.get('history', [])),
                         sheet_names=session.get('sheet_names', []),
                         current_sheet=session.get('current_sheet', None))

@app.route('/upload', methods=['POST'])
def upload_file():
    print("=" * 80)
    print("UPLOAD ROUTE CALLED!")
    print(f"Request files: {request.files}")
    print(f"Request form: {request.form}")
    print("=" * 80)
    
    if 'file' not in request.files:
        print("ERROR: No 'file' in request.files")
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    file = request.files['file']
    print(f"File received: {file.filename}")
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    allowed_extensions = ('.xlsx', '.csv')
    if file and file.filename.lower().endswith(allowed_extensions):
        try:
            # Save file to temp location for multi-sheet support
            temp_dir = tempfile.gettempdir()
            temp_filename = secure_filename(f"cleanifi_{int(time.time())}_{file.filename}")
            temp_path = os.path.join(temp_dir, temp_filename)
            file.save(temp_path)
            
            # Store temp path in session
            session['temp_file_path'] = temp_path
            session['file_type'] = 'csv' if file.filename.lower().endswith('.csv') else 'xlsx'
            
            # Read the file based on extension
            filename_lower = file.filename.lower()
            sheet_names = []
            
            if filename_lower.endswith('.csv'):
                df = pd.read_csv(temp_path)
                current_sheet = None
            else:
                # Get sheet names for Excel
                xl = pd.ExcelFile(temp_path)
                sheet_names = xl.sheet_names
                current_sheet = sheet_names[0]
                df = pd.read_excel(temp_path, sheet_name=current_sheet)
                
                session['sheet_names'] = sheet_names
                session['current_sheet'] = current_sheet
            
            # Convert DataFrame to dict for session storage
            session['df'] = df_to_session_dict(df)
            session['uploaded_original_df'] = df_to_session_dict(df)
            session['original_columns'] = list(df.columns)
            session['columns_cleaned'] = False
            session['cleaning_done'] = False
            session['renaming_done'] = False
            session['uploaded_file_id'] = f"{file.filename}_{len(df)}"
            session['history'] = []
            session['change_log'] = []
            
            # Store original stats
            session['original_stats'] = {
                "rows": int(len(df)),
                "cols": int(len(df.columns)),
                "missing": int(df.isnull().sum().sum()),
                "quality": round(100 - (df.isnull().sum().sum() / df.size * 100), 2)
            }
            session.modified = True
            
            return jsonify({
                'success': True,
                'message': f'File uploaded successfully: {file.filename}',
                'stats': session['original_stats'],
                'sheets': sheet_names,
                'current_sheet': current_sheet
            })
        except Exception as e:
            import traceback
            print("=" * 80)
            print("ERROR DURING FILE UPLOAD:")
            print(f"Exception: {e}")
            print(f"Exception type: {type(e).__name__}")
            print("Traceback:")
            traceback.print_exc()
            print("=" * 80)
            return jsonify({'success': False, 'message': f'Error reading file: {str(e)}'})
    
    return jsonify({'success': False, 'message': 'Please upload an .xlsx or .csv file'})

@app.route('/change_sheet', methods=['POST'])
def change_sheet():
    data = request.get_json()
    sheet_name = data.get('sheet_name')
    
    if not sheet_name:
        return jsonify({'success': False, 'message': 'No sheet name provided'})
        
    temp_path = session.get('temp_file_path')
    if not temp_path or not os.path.exists(temp_path):
        return jsonify({'success': False, 'message': 'File session expired. Please upload again.'})
        
    try:
        df = pd.read_excel(temp_path, sheet_name=sheet_name)
        
        session['df'] = df_to_session_dict(df)
        session['uploaded_original_df'] = df_to_session_dict(df)
        session['original_columns'] = list(df.columns)
        session['columns_cleaned'] = False
        session['cleaning_done'] = False
        session['renaming_done'] = False
        session['history'] = []
        session['change_log'] = []
        session['current_sheet'] = sheet_name
        
        session['original_stats'] = {
            "rows": int(len(df)),
            "cols": int(len(df.columns)),
            "missing": int(df.isnull().sum().sum()),
            "quality": round(100 - (df.isnull().sum().sum() / df.size * 100), 2)
        }
        session.modified = True
        
        return jsonify({
            'success': True, 
            'message': f'Switched to sheet: {sheet_name}',
            'stats': session['original_stats']
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error loading sheet: {str(e)}'})

@app.route('/delete_columns', methods=['POST'])
def delete_columns():
    try:
        data = request.get_json()
        columns_to_delete = data.get('columns', [])

        if not columns_to_delete:
            return jsonify({'success': False, 'message': 'No columns selected'})

        df = pd.DataFrame(session['df'])

        # Verify all columns exist
        missing = [c for c in columns_to_delete if c not in df.columns]
        if missing:
            return jsonify({'success': False, 'message': f'Column(s) not found: {", ".join(missing)}'})

        save_to_history(f"Deleted columns: {', '.join(columns_to_delete)}")
        df = df.drop(columns=columns_to_delete)
        session['df'] = df_to_session_dict(df)
        session['original_columns'] = list(df.columns)
        session['change_log'].append(f"Removed columns: {', '.join(columns_to_delete)}")
        session.modified = True

        return jsonify({'success': True, 'message': f'Removed {len(columns_to_delete)} column(s)'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deleting columns: {str(e)}'})

@app.route('/delete_rows', methods=['POST'])
def delete_rows():
    try:
        data = request.get_json()
        mode = data.get('mode')

        df = pd.DataFrame(session['df'])
        rows_before = len(df)

        if mode == 'range':
            start_idx = int(data.get('start', 0))
            end_idx = int(data.get('end', 0))

            if start_idx < 0 or end_idx >= len(df) or start_idx > end_idx:
                return jsonify({'success': False, 'message': f'Invalid range: {start_idx} to {end_idx}. Valid range is 0 to {len(df)-1}.'})

            target_indices = df.index[start_idx:end_idx + 1]
            df = df.drop(index=target_indices)

        elif mode == 'specific':
            indices = data.get('indices', [])
            if not indices:
                return jsonify({'success': False, 'message': 'No row indices provided'})
            valid_indices = [i for i in indices if i in df.index]
            if not valid_indices:
                return jsonify({'success': False, 'message': 'None of the provided indices exist in the dataset'})
            df = df.drop(index=valid_indices)
        else:
            return jsonify({'success': False, 'message': 'Invalid delete mode'})

        df = df.reset_index(drop=True)
        rows_after = len(df)
        removed = rows_before - rows_after
        session['df'] = df_to_session_dict(df)
        session['change_log'].append(f"Deleted {removed} row(s) ({mode} mode)")
        session.modified = True

        return jsonify({'success': True, 'message': f'Removed {removed} row(s)'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deleting rows: {str(e)}'})

@app.route('/reorder_columns', methods=['POST'])
def reorder_columns():
    try:
        data = request.get_json()
        new_order = data.get('column_order', [])

        if not new_order:
            return jsonify({'success': False, 'message': 'No column order provided'})

        df = pd.DataFrame(session['df'])

        if set(new_order) != set(df.columns):
            return jsonify({'success': False, 'message': 'Column mismatch — please reload and try again'})

        save_to_history("Reordered columns")
        df = df[new_order]
        session['df'] = df_to_session_dict(df)
        session['original_columns'] = list(df.columns)
        session['change_log'].append("Reordered columns")
        session.modified = True

        return jsonify({'success': True, 'message': 'Columns reordered successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error reordering columns: {str(e)}'})

@app.route('/add_serial_number', methods=['POST'])
def add_serial_number():
    try:
        data = request.get_json()
        prefix = data.get('prefix', 'row_') or 'row_'
        position = data.get('position', 'start')

        df = pd.DataFrame(session['df'])

        # Use a unique column name to avoid conflicts
        col_name = 'serial_number'
        counter = 1
        while col_name in df.columns:
            col_name = f'serial_number_{counter}'
            counter += 1

        save_to_history("Added serial number column")
        serial_numbers = [f"{prefix}{i + 1}" for i in range(len(df))]

        if position == 'start':
            df.insert(0, col_name, serial_numbers)
        else:
            df[col_name] = serial_numbers

        session['df'] = df_to_session_dict(df)
        session['original_columns'] = list(df.columns)
        session['change_log'].append(f"Added serial number column '{col_name}'")
        session.modified = True

        return jsonify({'success': True, 'message': f'Serial number column "{col_name}" added'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error adding serial number: {str(e)}'})

@app.route('/rename_columns', methods=['POST'])
def rename_columns():
    try:
        data = request.get_json()
        new_names = data.get('new_names', {})
        row_option = data.get('row_option', 'keep')
        row_prefix = data.get('row_prefix', '')

        df = pd.DataFrame(session['df'])

        # Check for duplicate target names (two columns renamed to the same name)
        if new_names:
            target_names = list(new_names.values())
            if len(target_names) != len(set(target_names)):
                return jsonify({'success': False, 'message': 'Two or more columns cannot be renamed to the same name'})

            # Check new names don't clash with existing columns not being renamed
            existing_cols = set(df.columns) - set(new_names.keys())
            clashes = [v for v in new_names.values() if v in existing_cols]
            if clashes:
                return jsonify({'success': False, 'message': f'Name(s) already exist: {", ".join(clashes)}'})

            df.rename(columns=new_names, inplace=True)

        if row_option == 'prefix' and row_prefix:
            df.index = [f"{row_prefix}{i}" for i in range(len(df))]
        elif row_option == 'reset':
            df.index = range(1, len(df) + 1)

        session['df'] = df_to_session_dict(df)
        session['original_columns'] = list(df.columns)
        session['renaming_done'] = True
        session['change_log'].append(f"Renamed {len(new_names)} column(s)")
        session.modified = True

        return jsonify({'success': True, 'message': 'Renaming applied successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error renaming columns: {str(e)}'})

@app.route('/apply_cleaning', methods=['POST'])
def apply_cleaning():
    data = request.get_json()
    cleaning_choices = data.get('cleaning_choices', {})
    type_choices = data.get('type_choices', {})
    precision_choices = data.get('precision_choices', {})
    
    save_to_history("Before applying cleaning rules")
    df = pd.DataFrame(session['df'])
    
    rows_deleted = 0
    cells_modified = 0
    applied_methods = []
    
    for col, method in cleaning_choices.items():
        if col not in df.columns:
            continue
        
        if method in ["Keep As Is", "Keep NaN"]:
            continue
        
        print(f"DEBUG: Applying '{method}' to column '{col}'")
        
        if method == "Forward Fill":
            missing_before = df[col].isnull().sum()
            df[col] = df[col].ffill()
            cells_modified += missing_before
            applied_methods.append(f"{col}: Forward Filled {missing_before} cells")
        
        elif method == "Backward Fill":
            missing_before = df[col].isnull().sum()
            df[col] = df[col].bfill()
            cells_modified += missing_before
            applied_methods.append(f"{col}: Backward Filled {missing_before} cells")
        
        elif method == "Mean":
            # Safely calculate mean from numeric values only
            numeric_vals = pd.to_numeric(df[col], errors='coerce')
            if numeric_vals.notna().any():
                value = numeric_vals.mean()
                if pd.notna(value):
                    fill_type = type_choices.get(col, "Integer")
                    if fill_type == "Integer":
                        value = int(round(value))
                    else:
                        prec = precision_choices.get(col, 2)
                        value = round(float(value), prec)
                    
                    # Fill only original nulls
                    mask = df[col].isnull()
                    missing_before = mask.sum()
                    df[col] = df[col].fillna(value)
                    
                    if missing_before > 0:
                        cells_modified += missing_before
                        applied_methods.append(f"{col}: Mean Imputed {missing_before} cells (val={value})")
        
        elif method == "Median":
            # Safely calculate median from numeric values only
            numeric_vals = pd.to_numeric(df[col], errors='coerce')
            if numeric_vals.notna().any():
                value = numeric_vals.median()
                if pd.notna(value):
                    fill_type = type_choices.get(col, "Integer")
                    if fill_type == "Integer":
                        value = int(round(value))
                    else:
                        prec = precision_choices.get(col, 2)
                        value = round(float(value), prec)
                    
                    # Fill only original nulls
                    mask = df[col].isnull()
                    missing_before = mask.sum()
                    df[col] = df[col].fillna(value)
                    
                    if missing_before > 0:
                        cells_modified += missing_before
                        applied_methods.append(f"{col}: Median Imputed {missing_before} cells (val={value})")
        
        elif method in ["Mode", "Most Frequent"]:
            non_null_values = df[col].dropna()
            if len(non_null_values) > 0:
                mode_values = df[col].mode()
                if len(mode_values) > 0:
                    value = mode_values[0]
                    missing_before = df[col].isnull().sum()
                    df[col] = df[col].fillna(value)
                    cells_modified += missing_before
                    applied_methods.append(f"{col}: Mode Imputed {missing_before} cells (val={value})")
        
        elif method == "Fill with 'Unknown'":
            missing_before = df[col].isnull().sum()
            df[col] = df[col].fillna("Unknown")
            cells_modified += missing_before
            applied_methods.append(f"{col}: Filled {missing_before} cells with 'Unknown'")
        
        elif method == "Delete Rows":
            before = len(df)
            df = df.dropna(subset=[col])
            rows_deleted += before - len(df)
            applied_methods.append(f"{col}: Deleted {before - len(df)} rows with NaNs")
        
        elif method == "Manual Input":
            custom_val = cleaning_choices.get(f"val_{col}", "")
            missing_before = df[col].isnull().sum()
            df[col] = df[col].fillna(custom_val)
            if missing_before > 0:
                cells_modified += missing_before
                applied_methods.append(f"{col}: Imputed '{custom_val}' (Manual Input)")
    
    # Convert column names to snake_case
    try:
        new_cols = []
        seen = {}
        for c in df.columns:
            base = clean_column_name(c)
            if base in seen:
                seen[base] += 1
                new_name = f"{base}_{seen[base]}"
            else:
                seen[base] = 1
                new_name = base
            new_cols.append(new_name)
        df.columns = new_cols
    except Exception:
        pass
    
    session['df'] = df_to_session_dict(df)
    session['columns_cleaned'] = True
    session['cleaning_done'] = True
    session['change_log'].extend(applied_methods)
    session.modified = True
    
    # Calculate after-cleaning stats
    after_stats = {
        "rows": int(len(df)),
        "cols": int(len(df.columns)),
        "missing": int(df.isnull().sum().sum()),
        "quality": round(100 - (df.isnull().sum().sum() / df.size * 100), 2)
    }
    
    # Get original stats for comparison
    original_stats = session.get('original_stats', {})
    
    return jsonify({
        'success': True,
        'message': 'Cleaning applied successfully',
        'cells_modified': int(cells_modified),
        'rows_deleted': int(rows_deleted),
        'stats': {
            'before': original_stats,
            'after': after_stats,
            'improvement': {
                'missing_reduced': int(original_stats.get('missing', 0) - after_stats['missing']),
                'quality_improved': round(after_stats['quality'] - original_stats.get('quality', 0), 2)
            }
        }
    })

@app.route('/download')
def download():
    if session.get('df') is None:
        return "No data to download", 400
    
    df = pd.DataFrame(session['df'])
    export_format = request.args.get('format', 'xlsx')
    use_password = request.args.get('password_protect') == 'true'
    password = request.args.get('password', '')
    
    if export_format == 'csv':
        # CSV export (no password protection)
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        csv_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
        return send_file(
            csv_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name='cleaned_data.csv'
        )
    
    # XLSX export
    if use_password and password:
        # Validate password
        is_valid, msg = is_strong_password(password)
        if not is_valid:
            return jsonify({'success': False, 'message': msg})
        
        # Save password to vault
        username = session.get('username')
        if username:
            auth_utils.save_file_password(username, "cleaned_data_protected.xlsx", password)
        
        output, success = encrypt_excel(df, password)
        if success:
            filename = "cleaned_data_protected.xlsx"
        else:
            # Fallback to unencrypted if encryption failed
            filename = "cleaned_data_unprotected.xlsx"
            print("WARNING: Returning unencrypted file because encryption failed.")
    else:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Cleaned Data')
        output.seek(0)
        filename = "cleaned_data.xlsx"
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@app.route('/sort_data', methods=['POST'])
def sort_data():
    try:
        data = request.get_json()
        column = data.get('column')
        order = data.get('order', 'asc')

        if not column:
            return jsonify({'success': False, 'message': 'No column selected'})

        df = pd.DataFrame(session['df'])
        if column not in df.columns:
            return jsonify({'success': False, 'message': f'Column "{column}" not found'})

        save_to_history(f"Sorted by {column} ({order})")
        ascending = order == 'asc'
        df = df.sort_values(by=column, ascending=ascending, na_position='last').reset_index(drop=True)

        session['df'] = df_to_session_dict(df)
        session['change_log'].append(f"Sorted by '{column}' ({'ascending' if ascending else 'descending'})")
        session.modified = True

        return jsonify({'success': True, 'message': f'Data sorted by "{column}" ({"ascending" if ascending else "descending"})'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error sorting data: {str(e)}'})

@app.route('/merge_columns', methods=['POST'])
def merge_columns():
    try:
        data = request.get_json()
        columns = data.get('columns', [])
        separator = data.get('separator', '_')
        new_name = data.get('new_name', '').strip()

        if len(columns) < 2:
            return jsonify({'success': False, 'message': 'Select at least 2 columns to merge'})

        if not new_name:
            new_name = separator.join(columns)

        df = pd.DataFrame(session['df'])

        # Check all selected columns exist
        for col in columns:
            if col not in df.columns:
                return jsonify({'success': False, 'message': f'Column "{col}" not found'})

        # Warn if new name already exists (and is not one of the merged columns)
        if new_name in df.columns and new_name not in columns:
            return jsonify({'success': False, 'message': f'A column named "{new_name}" already exists. Choose a different name.'})

        save_to_history(f"Merged columns: {', '.join(columns)}")

        # Merge: safely convert each cell to string, replacing NaN with empty string
        df[new_name] = df[columns].apply(
            lambda row: separator.join(str(v) if pd.notna(v) else '' for v in row),
            axis=1
        )

        session['df'] = df_to_session_dict(df)
        session['original_columns'] = list(df.columns)
        session['change_log'].append(f"Merged columns [{', '.join(columns)}] → '{new_name}'")
        session.modified = True

        return jsonify({'success': True, 'message': f'Columns merged into "{new_name}"'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Merge failed: {str(e)}'})

@app.route('/split_column', methods=['POST'])
def split_column():
    try:
        data = request.get_json()
        column = data.get('column')
        delimiter = data.get('delimiter', ',')

        if not column:
            return jsonify({'success': False, 'message': 'No column selected'})

        if not delimiter:
            return jsonify({'success': False, 'message': 'Delimiter cannot be empty'})

        df = pd.DataFrame(session['df'])
        if column not in df.columns:
            return jsonify({'success': False, 'message': f'Column "{column}" not found'})

        save_to_history(f"Split column: {column}")

        # Fill NaN with empty string before splitting to avoid "nan" appearing in results
        split_df = df[column].fillna('').astype(str).str.split(delimiter, expand=True)
        split_df.columns = [f"{column}_part{i + 1}" for i in range(split_df.shape[1])]

        # Insert new columns right after the original column
        col_idx = df.columns.get_loc(column)
        for i, new_col in enumerate(split_df.columns):
            df.insert(col_idx + 1 + i, new_col, split_df[new_col].str.strip())

        session['df'] = df_to_session_dict(df)
        session['original_columns'] = list(df.columns)
        session['change_log'].append(f"Split column '{column}' by '{delimiter}' → {split_df.shape[1]} parts")
        session.modified = True

        return jsonify({'success': True, 'message': f'Column "{column}" split into {split_df.shape[1]} part(s)'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error splitting column: {str(e)}'})

@app.route('/toggle_dark_mode', methods=['POST'])
def toggle_dark_mode():
    session['dark_mode'] = not session.get('dark_mode', False)
    session.modified = True
    return jsonify({'success': True, 'dark_mode': session['dark_mode']})

@app.route('/undo', methods=['POST'])
def undo():
    success, message = undo_action()
    return jsonify({'success': success, 'message': message})

@app.route('/reset', methods=['POST'])
def reset():
    keys_to_clear = [
        'df', 'original_df', 'original_columns',
        'columns_cleaned', 'renaming_done', 'cleaning_done', 'uploaded_file_id',
        'history', 'change_log', 'original_stats'
    ]
    for k in keys_to_clear:
        if k in session:
            del session[k]
    
    init_session()
    return jsonify({'success': True, 'message': 'App reset successfully'})

@app.route('/get_saved_passwords')
def get_saved_passwords():
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'passwords': []})
    passwords = auth_utils.get_user_passwords(username)
    return jsonify({'success': True, 'passwords': passwords})

@app.route('/delete_saved_password', methods=['POST'])
def delete_saved_password():
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'message': 'Not logged in'})
    data = request.get_json()
    filename = data.get('filename')
    if auth_utils.delete_password_entry(username, filename):
        return jsonify({'success': True, 'message': 'Password deleted'})
    else:
        return jsonify({'success': False, 'message': 'Error deleting password'})

@app.route('/check_vault_status')
def check_vault_status():
    init_session()
    if not session.get('logged_in'):
        return jsonify({'success': False})
    
    username = session.get('username')
    # User has access if they have a local password OR a vault master password
    has_access = auth_utils.has_local_password(username) or auth_utils.verify_vault_password(username, "") # verify_vault_password with "" checks if doc exists
    
    return jsonify({
        'success': True,
        'needs_setup': not auth_utils.has_local_password(username) and not auth_utils.has_vault_password(username)
    })

@app.route('/set_vault_password', methods=['POST'])
def set_vault_password_route():
    init_session()
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    data = request.get_json()
    password = data.get('password', '').strip()
    username = session.get('username')
    
    if not password:
        return jsonify({'success': False, 'message': 'Password is required'})
        
    if auth_utils.set_vault_password(username, password):
        return jsonify({'success': True, 'message': 'Vault password set successfully'})
    return jsonify({'success': False, 'message': 'Error setting vault password'})

@app.route('/verify_vault', methods=['POST'])
def verify_vault():
    init_session()
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    data = request.get_json()
    password = data.get('password', '').strip()
    username = session.get('username')
    
    if username and password:
        if auth_utils.verify_vault_password(username, password):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Incorrect verification password'})
    return jsonify({'success': False, 'message': 'Password required'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

