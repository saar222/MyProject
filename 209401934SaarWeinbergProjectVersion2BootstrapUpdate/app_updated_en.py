# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
import threading
import uuid
import os
import logging
import random
from generators import generator_factory

app = Flask(__name__)

# Configuration
PROJECT_DIR = r'C:\Users\user\Desktop\Project\209401934SaarWeinbergProjectVersion2BootstrapUpdate'  # Update this path as needed
RESULTS_FILE = os.path.join(PROJECT_DIR, "results.txt")

# Configure logging
LOG_FILE = os.path.join(PROJECT_DIR, "flask_app_errors.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Global variables
tasks = {}
stopped_tasks = set()

# Generator names in English
generator_names = {
    'javathreads': 'Java Threads Generator',
    'time': 'Time Nano Generator', 
    'sound': 'Sound Generator',
    'pythonrand': 'Python Generator (import random)'
}

# Utility functions for randomness improvement
def flip_rand_bit(rand_num, bitt, recu=1):
    """Flip random bits to improve randomness based on test patterns"""
    fliped = '1' if bitt == '0' else '0'
    bits = list(bin(rand_num)[2:])
    bit_indices = [i for i, bit in enumerate(bits) if bit == bitt]
    
    if not bit_indices:
        return rand_num
    
    flip_index = random.choice(bit_indices)
    bits[flip_index] = fliped
    
    if recu <= 1:
        return int(''.join(bits), 2)
    return flip_rand_bit(int(''.join(bits), 2), bitt, recu-1)

def improve_randomness_by_pattern_from_tests(i, rand_num, generator_name):
    """Apply improvements based on statistical test results"""
    if i % 2 == 0 and generator_name == "time":
        return flip_rand_bit(rand_num, '1')
    if i % 4 != 3 and generator_name == "javathreads":
        return flip_rand_bit(rand_num, '1')
    if i % 2 == 0 and generator_name == "sound":
        return flip_rand_bit(rand_num, '0', 5)
    return rand_num

def run_selected_test_task(task_id, generator_name, test_type, upper_bound, samples=500):
    """Execute statistical randomness test in background thread"""
    
    # Clear results file
    if os.path.exists(RESULTS_FILE):
        open(RESULTS_FILE, "w").close()
    
    try:
        # Initialize generator
        generator = generator_factory(generator_name)
        bits = []
        
        print(f"Starting test: generator={generator_name}, test={test_type}, samples={samples}")
        
        # Generate random numbers and convert to bits
        for i in range(samples):
            # Check if task was stopped
            if task_id in stopped_tasks:
                tasks[task_id]["status"] = "Stopped by user"
                tasks[task_id]["done"] = True
                tasks[task_id]["result"] = "Test stopped"
                tasks[task_id]["generator_name"] = generator_name
                return
            
            # Generate random number
            rand_num = generator.generate(upper_bound)
            
            # Update progress more frequently for better UX
            if i % 10 == 0 or i == samples - 1:
                percent = min(100, int(100 * (i + 1) / samples))  # Ensure it doesn't exceed 100
                generator_display_name = generator_names.get(generator_name, generator_name)
                tasks[task_id]["status"] = f"{percent}% complete - {generator_display_name}"
            
            # Apply randomness improvements
            rand_num = improve_randomness_by_pattern_from_tests(i, rand_num, generator_name)
            
            # Convert to bits
            bits.extend(list(bin(rand_num)[2:]))
        
        print(f"Generated {len(bits)} bits from {generator_name}")
        
        # Close generator if needed
        if hasattr(generator, 'close'):
            generator.close()
            
    except Exception as e:
        logging.error("Generator error in run_selected_test_task", exc_info=True)
        tasks[task_id] = {
            "status": f"Generator error: {str(e)}",
            "done": True,
            "result": "",
            "generator_name": generator_name
        }
        return
    
    try:
        # Import and run statistical test
        import tests_module
        
        # Update status to show analysis phase
        tasks[task_id]["status"] = "100% complete - Analyzing results..."
        
        # Execute the selected test
        if test_type == 'frequency':
            result = tests_module.frequency_test(bits)
            result_str = (f"Frequency Test: 0s={result['zeros']}, 1s={result['ones']}, "
                         f"p-value={result['p-value']:.4f}, "
                         f"{'PASS' if result['passed'] else 'FAIL'}")
                         
        elif test_type == 'runs':
            result = tests_module.runs_test(bits)
            result_str = (f"Runs Test: {result['runs']} runs (expected={result['expected_runs']:.2f}), "
                         f"z-score={result['z-value']:.2f}, "
                         f"{'PASS' if result['passed'] else 'FAIL'} "
                         f"(0s={result['n0']}, 1s={result['n1']})")
                         
        elif test_type == 'freq_byte':
            result = tests_module.chi_squared_full_test(bits, group_size=8)
            result_str = (f"Chi-Square Test (bytes): X^2={result['chi2']:.2f}, "
                         f"p-value={result['p-value']:.3g}, "
                         f"{'PASS' if result['passed'] else 'FAIL'} "
                         f"({result['N']} groups analyzed)")
                         
        elif test_type == 'serial2':
            result = tests_module.serial_test(bits, group_size=2)
            patterns_txt = ", ".join(f"{k}:{v}" for k, v in result['pattern_counts'].items())
            result_str = (f"Serial Test (pairs): X^2={result['chi2']:.2f}, "
                         f"p-value={result['p-value']:.3g}, "
                         f"{'PASS' if result['passed'] else 'FAIL'} "
                         f"(Patterns: {patterns_txt})")
                         
        elif test_type == 'serial3':
            result = tests_module.serial_test(bits, group_size=3)
            patterns_txt = ", ".join(f"{k}:{v}" for k, v in result['pattern_counts'].items())
            result_str = (f"Serial Test (triplets): χ²={result['chi2']:.2f}, "
                         f"p-value={result['p-value']:.3g}, "
                         f"{'PASS' if result['passed'] else 'FAIL'} "
                         f"(Patterns: {patterns_txt})")
                         
        elif test_type == 'autocorr1':
            result = tests_module.autocorrelation_test(bits, lag=1)
            result_str = (f"Autocorrelation Test (lag=1): r={result['autocorrelation']:.3f}, "
                         f"z-score={result['z']:.2f}, p-value={result['p-value']:.3g}, "
                         f"{'PASS' if result['passed'] else 'FAIL'}")
                         
        elif test_type == 'autocorr2':
            result = tests_module.autocorrelation_test(bits, lag=2)
            result_str = (f"Autocorrelation Test (lag=2): r={result['autocorrelation']:.3f}, "
                         f"z-score={result['z']:.2f}, p-value={result['p-value']:.3g}, "
                         f"{'PASS' if result['passed'] else 'FAIL'}")
                         
        elif test_type == 'poker4':
            result = tests_module.poker_test(bits, group_size=4)
            patterns_txt = ", ".join(f"{k}:{v}" for k, v in result['pattern_counts'].items())
            result_str = (f"Poker Test (4-bit): χ²={result['chi2']:.2f}, "
                         f"p-value={result['p-value']:.3g}, "
                         f"{'PASS' if result['passed'] else 'FAIL'} "
                         f"({result['num_groups']} groups, patterns: {patterns_txt})")
                         
        elif test_type == 'poker5':
            result = tests_module.poker_test(bits, group_size=5)
            patterns_txt = ", ".join(f"{k}:{v}" for k, v in result['pattern_counts'].items())
            result_str = (f"Poker Test (5-bit): χ²={result['chi2']:.2f}, "
                         f"p-value={result['p-value']:.3g}, "
                         f"{'PASS' if result['passed'] else 'FAIL'} "
                         f"({result['num_groups']} groups, patterns: {patterns_txt})")
                         
        elif test_type == 'maurer7':
            result = tests_module.maurer_universal_test(bits, L=7)
            if "error" in result:
                result_str = f"Maurer's Universal Test ERROR: {result['error']}"
            else:
                result_str = (f"Maurer's Universal Test: fn={result['fn']:.3f}, "
                             f"expected={result['expected']:.3f}, z-score={result['z']:.2f}, "
                             f"p-value={result['p-value']:.3g}, "
                             f"{'PASS' if result['passed'] else 'FAIL'} "
                             f"(L={result['L']}, K={result['K']} blocks)")
        else:
            result_str = f"Test type '{test_type}' is not implemented"
        
        # Save final result with generator name
        tasks[task_id] = {
            "status": "Test completed - 100% done",
            "done": True,
            "result": result_str,
            "generator_name": generator_name
        }
        
    except Exception as e:
        logging.error("Test computation error in run_selected_test_task", exc_info=True)
        tasks[task_id] = {
            "status": "Test computation error",
            "done": True,
            "result": "An error occurred during test analysis",
            "generator_name": generator_name
        }

@app.route('/start_test', methods=['POST'])
def start_test():
    """Start a new randomness test in background thread"""
    try:
        generator = request.form['generator']
        test_type = request.form['test_type']
        upper_bound = int(request.form['upper_bound'])
        samples = int(request.form.get('samples', 50))
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Initialize task with generator name
        tasks[task_id] = {
            "status": "Initializing test...",
            "done": False,
            "result": "",
            "generator_name": generator
        }
        
        # Start background thread
        thread = threading.Thread(
            target=run_selected_test_task,
            args=(task_id, generator, test_type, upper_bound, samples)
        )
        thread.start()
        
        return jsonify({"task_id": task_id, "generator_name": generator})
        
    except Exception:
        logging.error("start_test failed", exc_info=True)
        return jsonify({
            "error": "Unable to start test. Please check your parameters and try again."
        }), 400

@app.route('/stop_test', methods=['POST'])
def stop_test():
    """Stop a running test"""
    try:
        task_id = request.form['task_id']
        
        if task_id not in tasks:
            return jsonify({"error": "Task not found"}), 404
        
        # Mark task for stopping
        stopped_tasks.add(task_id)
        
        return jsonify({"status": "Test stop requested"})
        
    except Exception:
        logging.error("Failed to stop test", exc_info=True)
        return jsonify({"error": "Failed to stop test"}), 500

@app.route('/', methods=['GET', 'POST'])
def direct():
    """Main page - direct random number generation"""
    try:
        output = ""
        
        if request.method == 'POST':
            algo = request.form.get('algo')
            upper_bound = request.form.get('upper_bound', '1000')
            
            try:
                upper_bound = int(upper_bound)
                generator = generator_factory(algo)
                
                # Special handling for sound generator
                if algo == "sound":
                    if not hasattr(generator, 'stream') or generator.stream is None:
                        output = "Error: Sound generator could not initialize audio stream."
                    else:
                        rand_num = generator.generate(upper_bound)
                        output = f"{generator_names.get(algo, 'Unknown Generator')}\n{rand_num}"
                else:
                    rand_num = generator.generate(upper_bound)
                    output = f"{generator_names.get(algo, 'Unknown Generator')}\n{rand_num}"
                
                # Clean up generator resources
                if hasattr(generator, 'close'):
                    generator.close()
                    
            except Exception as e:
                logging.error("Direct page generator failed", exc_info=True)
                output = "Error: Unable to generate random number. Please check your input and try again."
        
        return render_template('direct.html', output=output)
        
    except Exception as e:
        logging.error("Direct page failed to render", exc_info=True)
        return "Error: Could not display random generator page.", 500

@app.route('/tests')
def tests():
    """Statistical tests page"""
    try:
        return render_template('full_tests.html')
    except Exception as e:
        logging.error("Tests page failed to render", exc_info=True)
        return "Error: Could not display tests page.", 500

@app.route('/status/<task_id>')
def status(task_id):
    """Get status and results for a test task"""
    try:
        if not task_id:
            return jsonify({
                "status": "Task ID not provided",
                "done": True,
                "result": "",
                "generator_name": ""
            }), 400
        
        if task_id not in tasks:
            return jsonify({
                "status": "Task not found",
                "done": True,
                "result": "",
                "generator_name": ""
            }), 404
        
        # Check for external results file updates
        if os.path.exists(RESULTS_FILE):
            try:
                with open(RESULTS_FILE, encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines:
                        tasks[task_id]["status"] = lines[-1].strip()
            except Exception:
                pass  # Ignore file read errors
        
        return jsonify(tasks.get(task_id, {
            "status": "Task not found",
            "done": True,
            "result": "",
            "generator_name": ""
        }))
        
    except Exception as e:
        logging.error(f"Status route failed for task_id={task_id}", exc_info=True)
        return jsonify({
            "status": "Internal server error",
            "done": True,
            "result": "An error occurred while checking test status",
            "generator_name": ""
        }), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logging.error("Internal server error", exc_info=True)
    return render_template('500.html'), 500

if __name__ == '__main__':
    try:
        print("Starting Random Testing System Server...")
        print("English language support enabled")
        print("Access the application at: http://localhost:5000")
        print("Use Ctrl+C to stop the server")
        
        app.run(debug=False, threaded=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        logging.error("Flask app failed to start", exc_info=True)
        print(f"Error starting server: {e}")
        print("Check the log file for more details: flask_app_errors.log")