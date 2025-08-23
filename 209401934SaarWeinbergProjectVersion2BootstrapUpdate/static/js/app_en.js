// JavaScript for Random Testing System
// Fixed version with Restart button, proper progress tracking, and generator name display

// Global variables
let currentTaskId = null;
let statusInterval = null;
let currentGeneratorName = null; // Store generator name for results

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeApplication();
});

function initializeApplication() {
    setupEventListeners();
    setupFormValidation();
    setupTooltips();
}

function setupEventListeners() {
    // Test form submission
    const testForm = document.getElementById('testForm');
    if (testForm) {
        testForm.addEventListener('submit', handleTestSubmission);
    }

    // Stop test button
    const stopBtn = document.getElementById('stopBtn');
    if (stopBtn) {
        stopBtn.addEventListener('click', handleTestStop);
    }

    // Restart button
    const restartBtn = document.getElementById('restartBtn');
    if (restartBtn) {
        restartBtn.addEventListener('click', function() {
            window.location.href = '/tests';
        });
    }

    // Generator form validation
    const generatorForm = document.querySelector('form[method="POST"]');
    if (generatorForm && !generatorForm.id) {
        generatorForm.addEventListener('submit', validateGeneratorForm);
    }
}

function setupFormValidation() {
    // Real-time validation for number inputs
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('input', function() {
            validateNumberInput(this);
        });
    });
}

function setupTooltips() {
    // Initialize Bootstrap tooltips if they exist
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Test submission handler
function handleTestSubmission(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    
    // Validate form data
    if (!validateTestForm(formData)) {
        return;
    }

    // Store generator name for results
    currentGeneratorName = formData.get('generator');

    // Start the test
    startTest(formData);
}

function validateTestForm(formData) {
    const generator = formData.get('generator');
    const testType = formData.get('test_type');
    const upperBound = parseInt(formData.get('upper_bound'));
    const samples = parseInt(formData.get('samples'));

    if (!generator) {
        showToast('Validation Error', 'Please select a generator type', 'error');
        return false;
    }

    if (!testType) {
        showToast('Validation Error', 'Please select a test type', 'error');
        return false;
    }

    if (!upperBound || upperBound < 1 || upperBound > 999999) {
        showToast('Validation Error', 'Upper bound must be between 1 and 999,999', 'error');
        return false;
    }

    if (!samples || samples < 10 || samples > 1000) {
        showToast('Validation Error', 'Samples must be between 10 and 1,000', 'error');
        return false;
    }

    return true;
}

function startTest(formData) {
    const progressDiv = document.getElementById('testProgress');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const restartBtn = document.getElementById('restartBtn');
    const resultDiv = document.getElementById('testResult');

    // Show progress UI
    if (progressDiv) progressDiv.style.display = 'block';
    if (startBtn) {
        startBtn.disabled = true;
        startBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Starting...';
    }
    if (stopBtn) stopBtn.style.display = 'inline-block';
    if (restartBtn) restartBtn.style.display = 'none'; // Hide restart during test
    if (resultDiv) resultDiv.innerHTML = '';

    // Reset progress bar completely
    updateProgress(0, 'Initializing test...');

    // Send request to start test
    fetch('/start_test', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        currentTaskId = data.task_id;
        currentGeneratorName = data.generator_name || currentGeneratorName;
        
        // Start polling for status
        statusInterval = setInterval(checkTestStatus, 2000);
        
        showToast('Test Started', 'Statistical test is now running...', 'success');
    })
    .catch(error => {
        console.error('Test start error:', error);
        showToast('Error', 'Failed to start test: ' + error.message, 'error');
        resetTestUI();
    });
}

function checkTestStatus() {
    if (!currentTaskId) {
        clearInterval(statusInterval);
        return;
    }

    fetch(`/status/${currentTaskId}`)
    .then(response => response.json())
    .then(data => {
        // Update status text
        const statusText = document.getElementById('statusText');
        if (statusText) {
            statusText.textContent = data.status || 'Processing...';
        }

        // Parse and update progress - ensure we reach 100%
        const progressMatch = data.status.match(/(\d+)%/);
        let percent = 0;
        if (progressMatch) {
            percent = parseInt(progressMatch[1]);
        } else if (data.done === true) {
            percent = 100; // Force 100% when done
        }
        updateProgress(percent);

        // Check if test is complete
        if (data.done === true) {
            handleTestCompletion(data);
        }
    })
    .catch(error => {
        console.error('Status check error:', error);
        showToast('Error', 'Lost connection to test. Please refresh the page.', 'error');
        resetTestUI();
    });
}

function handleTestCompletion(data) {
    // Stop status polling
    clearInterval(statusInterval);
    statusInterval = null;
    currentTaskId = null;

    // Ensure progress shows 100% when completed
    updateProgress(100, 'Test completed successfully!');

    // Display results with generator name
    const resultDiv = document.getElementById('testResult');
    if (resultDiv && data.result) {
        // Generator display names
        const generatorNames = {
            'javathreads': 'Java Threads Generator',
            'time': 'Time Nano Generator', 
            'sound': 'Sound Generator',
            'pythonrand': 'Python Generator (import random)'
        };
        
        const generatorDisplayName = generatorNames[currentGeneratorName] || 
                                   generatorNames[data.generator_name] || 
                                   currentGeneratorName || 
                                   'Unknown Generator';

        resultDiv.innerHTML = `
            <div class="result-card">
                <h4 class="mb-3">
                    <i class="bi bi-check-circle-fill"></i> Test Results
                </h4>
                <div class="alert alert-info mb-3">
                    <strong><i class="bi bi-gear-fill"></i> Generator:</strong> ${escapeHtml(generatorDisplayName)}
                </div>
                <div class="bg-dark text-light p-3 rounded">
                    <pre style="margin: 0; white-space: pre-wrap; font-family: 'Courier New', monospace;">${escapeHtml(data.result)}</pre>
                </div>
            </div>
        `;
    }

    // Reset UI with restart option
    resetTestUI(true);
    
    // Show completion notification
    const resultStatus = data.result && data.result.includes('PASS') ? 'success' : 'info';
    showToast('Test Complete', 'Statistical analysis finished!', resultStatus);
}

function handleTestStop() {
    if (!currentTaskId) return;

    const formData = new FormData();
    formData.append('task_id', currentTaskId);

    fetch('/stop_test', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        showToast('Test Stopping', 'Test stop request sent...', 'info');
    })
    .catch(error => {
        console.error('Stop test error:', error);
        showToast('Error', 'Failed to stop test', 'error');
    });
}

function resetTestUI(showRestartButton = false) {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const restartBtn = document.getElementById('restartBtn');
    const progressDiv = document.getElementById('testProgress');

    if (startBtn) {
        if (showRestartButton) {
            startBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Run Another Test';
            startBtn.classList.remove('btn-success');
            startBtn.classList.add('btn-primary');
        } else {
            startBtn.innerHTML = '<i class="bi bi-play-fill"></i> Start Test';
            startBtn.classList.remove('btn-primary');
            startBtn.classList.add('btn-success');
        }
        startBtn.disabled = false;
    }

    if (stopBtn) {
        stopBtn.style.display = 'none';
    }

    if (restartBtn) {
        restartBtn.style.display = showRestartButton ? 'inline-block' : 'none';
    }

    // Don't hide progress div if showing results
    if (progressDiv && !showRestartButton) {
        progressDiv.style.display = 'none';
    }

    // Clear intervals
    if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
    }

    currentTaskId = null;
}

function updateProgress(percent, statusMessage = null) {
    const progressBar = document.getElementById('progressBar');
    const statusText = document.getElementById('statusText');

    // Ensure percent is within bounds
    percent = Math.min(100, Math.max(0, percent));

    if (progressBar) {
        progressBar.style.width = `${percent}%`;
        progressBar.setAttribute('aria-valuenow', percent);
        progressBar.textContent = `${percent}%`;
        
        // Update color and animation based on progress
        if (percent >= 100) {
            progressBar.classList.remove('progress-bar-animated', 'bg-info');
            progressBar.classList.add('bg-success');
        } else if (percent >= 50) {
            progressBar.classList.remove('bg-success');
            progressBar.classList.add('bg-info');
        } else {
            progressBar.classList.remove('bg-success', 'bg-info');
            progressBar.classList.add('progress-bar-animated');
        }
    }

    if (statusText && statusMessage) {
        statusText.textContent = statusMessage;
    }
}

// Generator form validation
function validateGeneratorForm(event) {
    const algo = document.getElementById('algo');
    const upperBound = document.getElementById('upper_bound');

    if (algo && !algo.value) {
        event.preventDefault();
        showToast('Validation Error', 'Please select a generator type', 'error');
        algo.focus();
        return false;
    }

    if (upperBound && (!upperBound.value || upperBound.value < 1)) {
        event.preventDefault();
        showToast('Validation Error', 'Please enter a valid upper bound (minimum 1)', 'error');
        upperBound.focus();
        return false;
    }

    return true;
}

function validateNumberInput(input) {
    const value = parseInt(input.value);
    const min = parseInt(input.getAttribute('min')) || 1;
    const max = parseInt(input.getAttribute('max')) || Infinity;

    // Remove any existing validation classes
    input.classList.remove('is-valid', 'is-invalid');

    if (isNaN(value) || value < min || value > max) {
        input.classList.add('is-invalid');
        return false;
    } else {
        input.classList.add('is-valid');
        return true;
    }
}

// Toast notification system
function showToast(title, message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) return;

    // Create toast element
    const toastId = 'toast-' + Date.now();
    const iconClass = {
        'success': 'bi-check-circle-fill text-success',
        'error': 'bi-exclamation-triangle-fill text-danger',
        'warning': 'bi-exclamation-triangle-fill text-warning',
        'info': 'bi-info-circle-fill text-primary'
    }[type] || 'bi-info-circle-fill text-primary';

    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="${iconClass} me-2"></i>
                <strong class="me-auto">${escapeHtml(title)}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${escapeHtml(message)}
            </div>
        </div>
    `;

    // Add to container
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    // Initialize and show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: type === 'error' ? 8000 : 5000
    });

    toast.show();

    // Remove from DOM after hiding
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Auto-focus functionality
function setupAutoFocus() {
    // Focus on first form element
    const firstInput = document.querySelector('select, input[type="text"], input[type="number"]');
    if (firstInput) {
        firstInput.focus();
    }
}

// Call setup functions
document.addEventListener('DOMContentLoaded', setupAutoFocus);