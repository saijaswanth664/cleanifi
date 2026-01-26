import hashlib
import json
import os
import secrets
import time
import config
import firebase_admin
from firebase_admin import credentials, firestore, auth

# Initialize Firebase Admin SDK
firebase_app = None
try:
    # Check for service account JSON in environment variable
    service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
    if service_account_info:
        # If it's a string, it might be JSON content
        try:
            cert_dict = json.loads(service_account_info)
            cred = credentials.Certificate(cert_dict)
        except json.JSONDecodeError:
            # If it's not JSON, it might be a path to a file
            cred = credentials.Certificate(service_account_info)
        
        firebase_app = firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase initialized successfully!")
    else:
        db = None
except Exception as e:
    print(f"Warning: Firebase failed to initialize. Falling back to local JSON. Error: {e}")
    db = None

USER_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")
INTEGRITY_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "integrity.json")
PASSWORD_VAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'password_vault.json')

# In-memory rate limiting: {username: {"attempts": int, "lockout_until": float}}
login_attempts = {}

def sanitize_input(text):
    """Basic XSS prevention - removes HTML tags."""
    if not isinstance(text, str):
        return text
    import re
    return re.sub(r'<[^>]*?>', '', text)

SECURITY_QUESTIONS = [
    "What was the name of your first pet?",
    "In what city were you born?",
    "What was your childhood nickname?",
    "What is the name of your favorite book?",
    "What was the name of your first school?",
    "What is your mother's maiden name?"
]

def load_json_file(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_json_file(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except IOError:
        return False

def get_file_hash(path):
    """Calculates the SHA-256 hash of a file combined with an integrity salt."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data + config.INTEGRITY_SALT.encode()).hexdigest()

def update_integrity(path):
    """Updates the stored integrity hash for a file."""
    integrity = load_json_file(INTEGRITY_DB_PATH)
    file_hash = get_file_hash(path)
    if file_hash:
        integrity[os.path.basename(path)] = file_hash
        save_json_file(INTEGRITY_DB_PATH, integrity)

def check_file_integrity(path):
    """Checks if the file hash matches the stored integrity hash."""
    integrity = load_json_file(INTEGRITY_DB_PATH)
    current_hash = get_file_hash(path)
    stored_hash = integrity.get(os.path.basename(path))
    # If no integrity hash yet, initialize it
    if stored_hash is None and current_hash is not None:
        update_integrity(path)
        return True
    return current_hash == stored_hash

def hash_password(password, salt=None):
    """Encodes a password into a secure PBKDF2 hash using a salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        config.PASSWORD_SALT_ROUNDS
    ).hex()
    
    return pwd_hash, salt

def add_user(username, password, question_index=None, answer=None):
    """Registers a new user with security questions."""
    username = username.strip().lower()
    
    if db:
        try:
            # Check if user exists in Firestore
            user_ref = db.collection('users').document(username)
            if user_ref.get().exists:
                return False, "User already exists!"
            
            pwd_hash, salt = hash_password(password.strip())
            user_data = {
                "display_name": username,
                "password": pwd_hash,
                "salt": salt,
                "created_at": firestore.SERVER_TIMESTAMP
            }
            
            if question_index is not None and answer is not None:
                answer_hash, answer_salt = hash_password(answer.strip().lower())
                user_data.update({
                    "question_index": question_index,
                    "answer_hash": answer_hash,
                    "answer_salt": answer_salt
                })
            
            user_ref.set(user_data)
            return True, "Account created successfully!"
        except Exception as e:
            return False, f"Firestore Error: {str(e)}"

    # Local fallback
    users = load_json_file(USER_DB_PATH)
    if username in users:
        return False, "User already exists!"
    
    pwd_hash, salt = hash_password(password.strip())
    
    user_data = {
        "display_name": username,
        "password": pwd_hash,
        "salt": salt
    }
    
    if question_index is not None and answer is not None:
        answer_hash, answer_salt = hash_password(answer.strip().lower())
        user_data["question_index"] = question_index
        user_data["answer_hash"] = answer_hash
        user_data["answer_salt"] = answer_salt
    
    users[username] = user_data
    
    if save_json_file(USER_DB_PATH, users):
        update_integrity(USER_DB_PATH)
        return True, "Account created successfully!"
    else:
        return False, "Error saving user data."

def verify_user(username, password):
    """Verifies credentials against Firestore or local hashes."""
    username = username.strip().lower()
    password = password.strip()
    now = time.time()

    # Rate Limiting Check (Keep in-memory for now)
    if username in login_attempts:
        stats = login_attempts[username]
        if stats["lockout_until"] > now:
            remaining = int(stats["lockout_until"] - now)
            return False, f"Account temporarily locked. Try again in {remaining}s."

    stored_data = None
    if db:
        try:
            user_doc = db.collection('users').document(username).get()
            if user_doc.exists:
                stored_data = user_doc.to_dict()
        except Exception:
            pass

    if not stored_data:
        # Fallback to local
        if not check_file_integrity(USER_DB_PATH):
            print(f"CRITICAL: Integrity check failed for {USER_DB_PATH}")
        users = load_json_file(USER_DB_PATH)
        stored_data = users.get(username)

    if not stored_data:
        return False, "User not found!"
    
    stored_hash = stored_data.get("password")
    salt = stored_data.get("salt")
    
    # Old hash compatibility check (if salt is missing, it's an old SHA-256 hash)
    if not salt:
        current_hash = hashlib.sha256(password.encode()).hexdigest()
    else:
        current_hash, _ = hash_password(password, salt)

    if stored_hash == current_hash:
        # Success - reset attempts
        if username in login_attempts:
            del login_attempts[username]
        return True, "Login successful!"
    else:
        # Failure - update rate limiting
        if username not in login_attempts:
            login_attempts[username] = {"attempts": 1, "lockout_until": 0}
        else:
            login_attempts[username]["attempts"] += 1
            if login_attempts[username]["attempts"] >= config.MAX_LOGIN_ATTEMPTS:
                login_attempts[username]["lockout_until"] = now + config.LOCKOUT_TIME_SECONDS
                return False, f"Too many attempts. Locked for {config.LOCKOUT_TIME_SECONDS // 60}m."
        
        remaining = config.MAX_LOGIN_ATTEMPTS - login_attempts[username]["attempts"]
        return False, f"Incorrect password! {remaining} attempts remaining."

def get_user_question(username):
    """Retrieves the security question for a user."""
    users = load_json_file(USER_DB_PATH)
    username = username.strip().lower()
    if username not in users:
        return None
    q_idx = users[username].get("question_index")
    if q_idx is not None and 0 <= q_idx < len(SECURITY_QUESTIONS):
        return SECURITY_QUESTIONS[q_idx]
    return None

def verify_security_answer(username, answer):
    """Verifies the security answer for password reset."""
    users = load_json_file(USER_DB_PATH)
    username = username.strip().lower()
    if username not in users:
        return False
    
    stored = users[username]
    answer_hash = stored.get("answer_hash")
    answer_salt = stored.get("answer_salt")
    
    if not answer_hash or not answer_salt:
        return False
    
    current_hash, _ = hash_password(answer.strip().lower(), answer_salt)
    return current_hash == answer_hash

def reset_password(username, new_password):
    """Updates the user password."""
    users = load_json_file(USER_DB_PATH)
    username = username.strip().lower()
    if username not in users:
        return False
    
    pwd_hash, salt = hash_password(new_password.strip())
    users[username]["password"] = pwd_hash
    users[username]["salt"] = salt
    
    if save_json_file(USER_DB_PATH, users):
        update_integrity(USER_DB_PATH)
        return True
    return False

# Password Vault Functions using Firestore
def load_password_vault():
    if db:
        try:
            vault_docs = db.collection('vault').get()
            vault = {}
            for doc in vault_docs:
                vault[doc.id] = doc.to_dict().get('entries', [])
            return vault
        except Exception:
            pass
    return load_json_file(PASSWORD_VAULT_PATH)

def save_file_password(username, filename, file_password):
    from datetime import datetime
    entry = {
        'filename': filename, 
        'password': file_password, 
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if db:
        try:
            user_vault_ref = db.collection('vault').document(username)
            user_vault_ref.set({
                'entries': firestore.ArrayUnion([entry])
            }, merge=True)
            return True
        except Exception:
            pass

    # Local fallback
    vault = load_password_vault()
    if username not in vault:
        vault[username] = []
    vault[username].append(entry)
    
    # Save the whole vault locally
    try:
        with open(PASSWORD_VAULT_PATH, "w") as f:
            json.dump(vault, f, indent=4)
        update_integrity(PASSWORD_VAULT_PATH)
        return True
    except IOError:
        return False

def get_user_passwords(username):
    if db:
        try:
            doc = db.collection('vault').document(username).get()
            if doc.exists:
                return doc.to_dict().get('entries', [])
        except Exception:
            pass
    vault = load_password_vault()
    return vault.get(username, [])

def delete_password_entry(username, filename):
    if db:
        try:
            user_vault_ref = db.collection('vault').document(username)
            entries = get_user_passwords(username)
            new_entries = [p for p in entries if p['filename'] != filename]
            user_vault_ref.set({'entries': new_entries})
            return True
        except Exception:
            pass
            
    vault = load_password_vault()
    if username in vault:
        vault[username] = [p for p in vault[username] if p['filename'] != filename]
        try:
            with open(PASSWORD_VAULT_PATH, "w") as f:
                json.dump(vault, f, indent=4)
            update_integrity(PASSWORD_VAULT_PATH)
            return True
        except IOError:
            return False
    return False

def verify_google_token(id_token):
    """Verifies a Firebase ID Token and returns user info."""
    if not firebase_app:
        return None, "Firebase not initialized"
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token, None
    except Exception as e:
        return None, str(e)
