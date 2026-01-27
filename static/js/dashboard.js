// Main JavaScript for Dashboard functionality

// Show toast message
function showToast(message, type = 'info') {
    const toast = document.getElementById('messageToast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Handle file upload
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    const messageEl = document.getElementById('uploadMessage');
    messageEl.innerHTML = '<div class="info-text">⏳ Uploading file...</div>';

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.success) {
            messageEl.innerHTML = `<div class="success-message">✅ ${data.message}</div>`;
            // Instant reload
            location.reload();
        } else {
            messageEl.innerHTML = `<div class="error-message">❌ ${data.message}</div>`;
        }
    } catch (error) {
        console.error('Upload error:', error);
        messageEl.innerHTML = `<div class="error-message">❌ Upload failed: ${error.message}</div>`;
    }
}

// Delete columns
async function deleteColumns() {
    const select = document.getElementById('columnsToDelete');
    const columns = Array.from(select.selectedOptions).map(opt => opt.value);

    if (columns.length === 0) {
        showToast('Please select at least one column', 'error');
        return;
    }

    try {
        const response = await fetch('/delete_columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ columns })
        });
        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');
            location.reload();
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Error deleting columns', 'error');
    }
}

// Delete rows (range)
async function deleteRowsRange() {
    const startInput = document.getElementById('startIdx');
    const endInput = document.getElementById('endIdx');
    const start = parseInt(startInput.value);
    const end = parseInt(endInput.value);
    const maxRows = parseInt(endInput.getAttribute('max') || 1000000);

    if (start < 0 || end > maxRows || start > end) {
        showToast(`Invalid range: 0 to ${maxRows}`, 'error');
        return;
    }

    try {
        const response = await fetch('/delete_rows', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: 'range', start, end })
        });
        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');
            location.reload();
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Error deleting rows', 'error');
    }
}

// Delete rows (specific)
async function deleteRowsSpecific() {
    const indicesStr = document.getElementById('specificIndices').value;
    const indices = indicesStr.split(',').map(i => parseInt(i.trim())).filter(i => !isNaN(i));

    try {
        const response = await fetch('/delete_rows', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: 'specific', indices })
        });
        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');
            location.reload();
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Error deleting rows', 'error');
    }
}

// Apply column/row renaming
async function applyRenaming() {
    const renameInputs = document.querySelectorAll('.rename-input');
    const new_names = {};

    renameInputs.forEach(input => {
        const original = input.dataset.original;
        const newName = input.value;
        if (original !== newName) {
            new_names[original] = newName;
        }
    });

    const rowOption = document.querySelector('input[name="rowRenameOption"]:checked').value;
    const rowPrefix = document.getElementById('rowPrefix')?.value || '';

    try {
        const response = await fetch('/rename_columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                new_names,
                row_option: rowOption,
                row_prefix: rowPrefix
            })
        });
        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');
            location.reload();
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Error applying renaming', 'error');
    }
}

// Skip renaming
async function skipRenaming() {
    try {
        const response = await fetch('/rename_columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                new_names: {},
                row_option: 'keep',
                row_prefix: ''
            })
        });
        const data = await response.json();

        if (data.success) {
            showToast('Skipped renaming', 'success');
            setTimeout(() => location.reload(), 1000);
        }
    } catch (error) {
        showToast('Error skipping renaming', 'error');
    }
}

// Apply cleaning
async function applyCleaning() {
    const cleaningSelects = document.querySelectorAll('.cleaning-select');
    const cleaning_choices = {};
    const type_choices = {};
    const precision_choices = {};

    cleaningSelects.forEach(select => {
        const column = select.dataset.column;
        const method = select.value;
        const dtype = select.dataset.dtype;

        cleaning_choices[column] = method;

        // Get manual input value if method is Manual Input
        if (method === 'Manual Input') {
            const manualInput = select.closest('.missing-item').querySelector('.manual-value');
            if (manualInput) {
                cleaning_choices[`val_${column}`] = manualInput.value;
            }
        }

        // Get numeric options if dtype is Numeric
        if (dtype === 'Numeric') {
            const typeRadio = document.querySelector(`input[name="type_${column}"]:checked`);
            if (typeRadio) {
                type_choices[column] = typeRadio.value;
            }

            const precisionInput = select.closest('.missing-item').querySelector('.precision-input');
            if (precisionInput) {
                precision_choices[column] = parseInt(precisionInput.value);
            }
        }
    });

    showToast('Applying cleaning methods...', 'info');

    try {
        const response = await fetch('/apply_cleaning', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cleaning_choices,
                type_choices,
                precision_choices
            })
        });
        const data = await response.json();

        if (data.success) {
            // Show detailed cleaning report
            if (data.stats) {
                const stats = data.stats;
                let reportHtml = `
                    <div class="cleaning-report-modal" id="cleaningReport">
                        <div class="report-content">
                            <h2>📊 Data Cleaning Report</h2>
                            
                            <div class="report-comparison">
                                <div class="report-column">
                                    <h3>Before Cleaning</h3>
                                    <div class="stat-item">
                                        <span class="stat-label">Total Rows:</span>
                                        <span class="stat-value">${stats.before.rows}</span>
                                    </div>
                                    <div class="stat-item">
                                        <span class="stat-label">Total Columns:</span>
                                        <span class="stat-value">${stats.before.cols}</span>
                                    </div>
                                    <div class="stat-item">
                                        <span class="stat-label">Missing Values:</span>
                                        <span class="stat-value error">${stats.before.missing}</span>
                                    </div>
                                    <div class="stat-item">
                                        <span class="stat-label">Data Quality:</span>
                                        <span class="stat-value">${stats.before.quality}%</span>
                                    </div>
                                </div>
                                
                                <div class="arrow">→</div>
                                
                                <div class="report-column">
                                    <h3>After Cleaning</h3>
                                    <div class="stat-item">
                                        <span class="stat-label">Total Rows:</span>
                                        <span class="stat-value">${stats.after.rows}</span>
                                    </div>
                                    <div class="stat-item">
                                        <span class="stat-label">Total Columns:</span>
                                        <span class="stat-value">${stats.after.cols}</span>
                                    </div>
                                    <div class="stat-item">
                                        <span class="stat-label">Missing Values:</span>
                                        <span class="stat-value success">${stats.after.missing}</span>
                                    </div>
                                    <div class="stat-item">
                                        <span class="stat-label">Data Quality:</span>
                                        <span class="stat-value success">${stats.after.quality}%</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="improvement-summary">
                                <h3>✨ Improvements</h3>
                                <p>✅ ${stats.improvement.missing_reduced} missing values filled</p>
                                <p>✅ ${data.cells_modified} cells modified</p>
                                ${data.rows_deleted > 0 ? `<p>🗑️ ${data.rows_deleted} rows deleted</p>` : ''}
                                <p class="quality-gain">📈 Data quality improved by ${stats.improvement.quality_improved}%</p>
                            </div>
                            
                            <button class="btn btn-primary" onclick="closeCleaningReport()">Continue</button>
                        </div>
                    </div>
                `;

                document.body.insertAdjacentHTML('beforeend', reportHtml);
                setTimeout(() => {
                    document.getElementById('cleaningReport').classList.add('show');
                }, 100);
            } else {
                showToast(data.message, 'success');
                setTimeout(() => location.reload(), 1500);
            }
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Error applying cleaning', 'error');
    }
}

function closeCleaningReport() {
    const report = document.getElementById('cleaningReport');
    if (report) {
        report.classList.remove('show');
        setTimeout(() => {
            report.remove();
            location.reload();
        }, 300);
    }
}

// Global variable to track if password is applied
let passwordApplied = false;
let appliedPassword = '';

// Toggle password protection fields
function togglePasswordProtection() {
    const passwordFields = document.getElementById('passwordFields');
    const checkbox = document.getElementById('passwordProtect');

    if (checkbox.checked) {
        passwordFields.style.display = 'block';
    } else {
        passwordFields.style.display = 'none';
        passwordApplied = false;
        appliedPassword = '';
    }
}

// Validate password against requirements
function validatePassword() {
    const password = document.getElementById('downloadPassword').value;
    const confirmPassword = document.getElementById('confirmDownloadPassword').value;
    const messageEl = document.getElementById('passwordMessage');
    const applyBtn = document.getElementById('applyPasswordBtn');

    // Check each requirement
    const requirements = {
        length: password.length >= 7,
        uppercase: /[A-Z]/.test(password),
        number: /[0-9]/.test(password),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };

    // Update requirement checkmarks
    document.getElementById('req-length').innerHTML =
        (requirements.length ? '✓' : '✗') + ' Minimum 7 characters';
    document.getElementById('req-length').style.color = requirements.length ? '#10b981' : '#ef4444';

    document.getElementById('req-uppercase').innerHTML =
        (requirements.uppercase ? '✓' : '✗') + ' At least one uppercase letter (A-Z)';
    document.getElementById('req-uppercase').style.color = requirements.uppercase ? '#10b981' : '#ef4444';

    document.getElementById('req-number').innerHTML =
        (requirements.number ? '✓' : '✗') + ' At least one number (0-9)';
    document.getElementById('req-number').style.color = requirements.number ? '#10b981' : '#ef4444';

    document.getElementById('req-special').innerHTML =
        (requirements.special ? '✓' : '✗') + ' At least one special character (!@#$%^&*)';
    document.getElementById('req-special').style.color = requirements.special ? '#10b981' : '#ef4444';

    // Check if all requirements met
    const allRequirementsMet = Object.values(requirements).every(v => v);

    // Check if passwords match
    const passwordsMatch = password === confirmPassword && password !== '';

    // Enable/disable apply button
    if (allRequirementsMet && passwordsMatch) {
        applyBtn.disabled = false;
        messageEl.innerHTML = '<div class="success-message">✓ Password meets all requirements and matches!</div>';
    } else {
        applyBtn.disabled = true;
        if (password !== '' && confirmPassword !== '') {
            if (!allRequirementsMet) {
                messageEl.innerHTML = '<div class="error-message">❌ Password does not meet requirements</div>';
            } else if (!passwordsMatch) {
                messageEl.innerHTML = '<div class="error-message">❌ Passwords do not match</div>';
            }
        } else {
            messageEl.innerHTML = '';
        }
    }
}

// Apply password
function applyPassword() {
    const password = document.getElementById('downloadPassword').value;
    const confirmPassword = document.getElementById('confirmDownloadPassword').value;
    const messageEl = document.getElementById('passwordMessage');

    if (password === confirmPassword) {
        passwordApplied = true;
        appliedPassword = password;
        messageEl.innerHTML = '<div class="success-message">✓ Password applied successfully! You can now download.</div>';

        // Disable password fields after applying
        document.getElementById('downloadPassword').disabled = true;
        document.getElementById('confirmDownloadPassword').disabled = true;
        document.getElementById('applyPasswordBtn').disabled = true;
        document.getElementById('applyPasswordBtn').innerHTML = '✓ Password Applied';
    }
}

// Toggle password visibility
function togglePasswordVisibility(fieldId) {
    const field = document.getElementById(fieldId);
    const button = field.nextElementSibling;

    if (field.type === 'password') {
        field.type = 'text';
        button.innerHTML = '🙈';
    } else {
        field.type = 'password';
        button.innerHTML = '👁️';
    }
}

// Download file
async function downloadFile() {
    const passwordProtect = document.getElementById('passwordProtect').checked;

    if (passwordProtect) {
        if (!passwordApplied) {
            showToast('Please apply the password first by clicking "Apply Password"', 'error');
            return;
        }

        // Download with password protection using the applied password
        window.location.href = `/download?password_protect=true&password=${encodeURIComponent(appliedPassword)}`;
    } else {
        // Download without password
        window.location.href = '/download';
    }
}

// Undo action
async function undoAction() {
    try {
        const response = await fetch('/undo', {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');
            location.reload();
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Error undoing action', 'error');
    }
}

// Apply column reordering
async function applyColumnReorder() {
    const columnItems = document.querySelectorAll('#columnReorder .column-item');
    const column_order = Array.from(columnItems).map(item => item.dataset.column);

    try {
        const response = await fetch('/reorder_columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ column_order })
        });
        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');
            location.reload();
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Error reordering columns', 'error');
    }
}

// Add serial number column
async function addSerialNumber() {
    const prefix = document.getElementById('serialPrefix')?.value || 'row_';
    const position = document.querySelector('input[name="serialPosition"]:checked')?.value || 'start';

    try {
        const response = await fetch('/add_serial_number', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prefix, position })
        });
        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');
            location.reload();
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Error adding serial number', 'error');
    }
}

// Reset app
async function resetApp() {
    if (!confirm('Are you sure you want to reset the app? All data will be lost.')) {
        return;
    }

    try {
        const response = await fetch('/reset', {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');
            location.reload();
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Error resetting app', 'error');
    }
}

// Event listeners for dynamic elements
document.addEventListener('DOMContentLoaded', function () {
    // Row deletion mode toggle
    const deleteModRadios = document.querySelectorAll('input[name="deleteMode"]');
    deleteModRadios.forEach(radio => {
        radio.addEventListener('change', function () {
            const rangeInputs = document.getElementById('rangeInputs');
            const specificInputs = document.getElementById('specificInputs');

            if (this.value === 'range') {
                rangeInputs.style.display = 'flex';
                specificInputs.style.display = 'none';
            } else {
                rangeInputs.style.display = 'none';
                specificInputs.style.display = 'flex';
            }
        });
    });

    // Row renaming option toggle
    const rowRenameRadios = document.querySelectorAll('input[name="rowRenameOption"]');
    rowRenameRadios.forEach(radio => {
        radio.addEventListener('change', function () {
            const prefixInput = document.getElementById('prefixInput');
            if (this.value === 'prefix') {
                prefixInput.style.display = 'block';
            } else {
                prefixInput.style.display = 'none';
            }
        });
    });

    // Cleaning method change handlers
    const cleaningSelects = document.querySelectorAll('.cleaning-select');
    cleaningSelects.forEach(select => {
        select.addEventListener('change', function () {
            const missingItem = this.closest('.missing-item');
            const manualInput = missingItem.querySelector('.manual-input');
            const numericOptions = missingItem.querySelector('.numeric-options');

            // Show/hide manual input
            if (this.value === 'Manual Input') {
                manualInput.style.display = 'block';
            } else {
                manualInput.style.display = 'none';
            }

            // Show/hide numeric options
            if (numericOptions) {
                if (this.value in ['Mean', 'Median']) {
                    numericOptions.style.display = 'flex';
                } else {
                    numericOptions.style.display = 'none';
                }
            }
        });
    });

    // Numeric type toggle (Integer/Float)
    document.querySelectorAll('input[type="radio"][name^="type_"]').forEach(radio => {
        radio.addEventListener('change', function () {
            const precisionSlider = this.closest('.numeric-options').querySelector('.precision-slider');
            if (precisionSlider) {
                if (this.value === 'Float') {
                    precisionSlider.style.display = 'flex';
                } else {
                    precisionSlider.style.display = 'none';
                }
            }
        });
    });

    // Precision slider update
    document.querySelectorAll('.precision-input').forEach(slider => {
        slider.addEventListener('input', function () {
            const valueDisplay = this.closest('.precision-slider').querySelector('.precision-value');
            if (valueDisplay) {
                valueDisplay.textContent = this.value;
            }
        });
    });

    // Password protect checkbox
    const passwordProtectCheckbox = document.getElementById('passwordProtect');
    if (passwordProtectCheckbox) {
        passwordProtectCheckbox.addEventListener('change', function () {
            const passwordFields = document.getElementById('passwordFields');
            if (this.checked) {
                passwordFields.style.display = 'block';
            } else {
                passwordFields.style.display = 'none';
            }
        });
    }

    // Drag and drop for column reordering
    const columnReorderContainer = document.getElementById('columnReorder');
    if (columnReorderContainer) {
        let draggedItem = null;

        const columnItems = columnReorderContainer.querySelectorAll('.column-item');
        columnItems.forEach(item => {
            item.addEventListener('dragstart', function (e) {
                draggedItem = this;
                setTimeout(() => this.classList.add('dragging'), 0);
            });

            item.addEventListener('dragend', function (e) {
                setTimeout(() => this.classList.remove('dragging'), 0);
                draggedItem = null;
            });

            item.addEventListener('dragover', function (e) {
                e.preventDefault();
                const afterElement = getDragAfterElement(columnReorderContainer, e.clientY);
                if (afterElement == null) {
                    columnReorderContainer.appendChild(draggedItem);
                } else {
                    columnReorderContainer.insertBefore(draggedItem, afterElement);
                }
            });
        });

        function getDragAfterElement(container, y) {
            const draggableElements = [...container.querySelectorAll('.column-item:not(.dragging)')];

            return draggableElements.reduce((closest, child) => {
                const box = child.getBoundingClientRect();
                const offset = y - box.top - box.height / 2;

                if (offset < 0 && offset > closest.offset) {
                    return { offset: offset, element: child };
                } else {
                    return closest;
                }
            }, { offset: Number.NEGATIVE_INFINITY }).element;
        }
    }
});

// Password Vault Functions
function showVaultUnlock() {
    document.getElementById('vaultUnlockModal').classList.add('show');
}

function closeVaultUnlock() {
    document.getElementById('vaultUnlockModal').classList.remove('show');
    document.getElementById('vaultVerifyPassword').value = '';
    document.getElementById('vaultVerifyMessage').innerHTML = '';
}

async function verifyVault() {
    const password = document.getElementById('vaultVerifyPassword').value;
    const messageEl = document.getElementById('vaultVerifyMessage');

    if (!password) {
        messageEl.innerHTML = '<div class="error-message">Password is required</div>';
        return;
    }

    try {
        const response = await fetch('/verify_vault', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });
        const data = await response.json();

        if (data.success) {
            document.getElementById('vaultOverlay').style.display = 'none';
            document.getElementById('passwordVaultContent').style.display = 'block';
            closeVaultUnlock();
            loadSavedPasswords();
            showToast('Vault unlocked', 'success');
        } else {
            messageEl.innerHTML = `<div class="error-message">❌ ${data.message}</div>`;
        }
    } catch (error) {
        messageEl.innerHTML = '<div class="error-message">❌ Verification failed</div>';
    }
}

async function loadSavedPasswords() {
    try {
        const response = await fetch('/get_saved_passwords');
        const data = await response.json();
        const container = document.getElementById('passwordVaultContent');

        if (data.success && data.passwords.length > 0) {
            let html = '';
            data.passwords.forEach((p, idx) => {
                const id = 'pwd' + idx;
                html += `
                    <div class="vault-password-item">
                        <div style="flex: 1;">
                            <strong style="font-size: 0.85rem; color: var(--text-primary);">📄 ${p.filename}</strong>
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin: 0.3rem 0;">
                                <span class="vault-password" id="${id}" style="color: var(--text-secondary); font-family: monospace;">${'•'.repeat(12)}</span>
                                <button class="vault-eye-btn" onclick="toggleVaultPassword('${id}', '${p.password}')">👁️</button>
                            </div>
                            <small style="color: var(--text-secondary); font-size: 0.7rem; opacity: 0.7;">🕒 ${p.date}</small>
                        </div>
                        <button class="vault-delete-btn" onclick="deleteVaultPassword('${p.filename}')" title="Delete">🗑️</button>
                    </div>
                `;
            });
            container.innerHTML = html;
        } else {
            container.innerHTML = '<p class="info-text" style="font-size: 0.85rem; padding: 1rem; opacity: 0.6;">No saved passwords</p>';
        }
    } catch (error) {
        console.error('Error loading passwords:', error);
        document.getElementById('passwordVaultContent').innerHTML = '<p class="info-text" style="font-size: 0.85rem;">Error loading</p>';
    }
}

// Load status placeholder
document.addEventListener('DOMContentLoaded', function () {
    // Initial UI state setup for vault is handled by HTML display properties
});

function toggleVaultPassword(id, password) {
    const el = document.getElementById(id);
    const btn = el.nextElementSibling;
    if (el.textContent === password) {
        el.textContent = '•'.repeat(12);
        btn.textContent = '👁️';
    } else {
        el.textContent = password;
        btn.textContent = '🙈';
    }
}

async function deleteVaultPassword(filename) {
    if (!confirm('Delete this password?')) return;

    try {
        const response = await fetch('/delete_saved_password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
        const data = await response.json();
        if (data.success) {
            showToast('Password deleted', 'success');
            loadSavedPasswords();
        }
    } catch (error) {
        console.error('Error deleting password:', error);
    }
}

