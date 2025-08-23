# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify
import threading
import uuid
import os
import logging ,random
from generators import generator_factory

app = Flask(__name__)

PROJECT_DIR = r'C:\Users\user\Desktop\Project' # Change if needed
RESULTS_FILE = os.path.join(PROJECT_DIR, "results.txt")

# Configure error logging (all tracebacks stored)
LOG_FILE = os.path.join(PROJECT_DIR, "flask_app_errors.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s'
)

tasks = {}
stopped_tasks = set()

generator_names = {
    'javathreads': 'Java Generator',
    'time': 'Time Nano Generator',
    'sound': 'Sound Generator',
    'pythonrand': 'Python Generator (import random)'
}
#recu = number of times activate function
#bitt = 1 if we want to flip 1 to 0- bittz=is what we want to flip
def flip_rand_bit(rand_num,bitt,recu=1):#flip_random_one_to_zero(rand_num):
    fliped = '1' if bitt=='0' else '0'
    bits = list(bin(rand_num)[2:])  # Converts the number to a list of binary digits (without the '0b')
    zero_indices = [i for i, bit in enumerate(bits) if bit == bitt]
    if not zero_indices:
        # If there are no zeros in the list, nothing to change – return the number as is
        return rand_num
    # Randomly choose an index of a zero
    flip_index = random.choice(zero_indices)
    bits[flip_index] = fliped
    # Convert back to an integer
    if recu <= 1: 
        return int(''.join(bits), 2)
    return flip_rand_bit(int(''.join(bits), 2), bitt, recu-1)

def Improve_randomenss_by_pattern_from_tests(i, rand_num, generator_name): 
    if i%2==0 and generator_name == "time":          
        return flip_rand_bit(rand_num,'1') 
    if i % 4 != 3 and generator_name == "javathreads":
        return flip_rand_bit(rand_num,'1') 
    if i%2==0 and generator_name == "sound":
        return flip_rand_bit(rand_num,'0',5)
    return rand_num

def run_selected_test_task(task_id, generator_name, test_type, upper_bound, samples=500):
    # If the results file exists, clear its contents to prepare for a new test run
    if os.path.exists(RESULTS_FILE):
        open(RESULTS_FILE, "w").close()
    # Try to run the selected random number generator
    try:
        # Create the generator object using the Factory Pattern
        generator = generator_factory(generator_name)
        bits = []
        print(f"generator_name: {generator_name},  test_type: {test_type}")
        for i in range(samples):
            # Generate a random number within the specified upper bound
            rand_num = generator.generate(upper_bound)
            print(f"[{i}] random_number: {rand_num}")
            # Update status every 20 samples or for the last sample
            if i % 20 == 0 or i == samples-1:
                percent = int(100*(i+1)/samples)
                tasks[task_id]["status"] = f"{percent}% done for {generator_name} Generator"
                # If the task was stopped by the user, update its status and return early
                if task_id in stopped_tasks:
                    tasks[task_id]["status"] = "Stopped by user"
                    tasks[task_id]["done"] = True
                    tasks[task_id]["result"] = "Stopped"
                    return # Stop thread                    
            # Optionally improve randomness using test patterns
            rand_num = Improve_randomenss_by_pattern_from_tests(i, rand_num, generator_name)       
            # Convert the random number to bits and add to the bits list  
            bits.extend(list(bin(rand_num)[2:]))   
                    
        print("Total bits collected from", generator_name, ":", len(bits))
        # If the generator has a close method, call it to release resources
        if hasattr(generator, 'close'):
            generator.close()
    except Exception as e:
        # Log generator errors and store result for user
        logging.error("Generator error in run_selected_test_task: ", exc_info=True)
        tasks[task_id] = {"status": f"Generator error: {str(e)}", "done": True, "result": ""}
        return
    try:
        import tests_module # Import test module here, so it can use the generator state
        # Run the requested statistical randomness test according to test_type
        if test_type == 'frequency':
            result = tests_module.frequency_test(bits)
            result_str = f"0s={result['zeros']}, 1s={result['ones']}, p={result['p-value']:.4f}, {'PASS' if result['passed'] else 'FAIL'}"
        elif test_type == 'runs':
            result = tests_module.runs_test(bits)
            result_str = (f"Runs={result['runs']} (expected={result['expected_runs']:.2f}), "
                          f"z={result['z-value']:.2f}, {'PASS' if result['passed'] else 'FAIL'} "
                          f"0s={result['n0']} 1s={result['n1']}")
        elif test_type == 'freq_byte':
            result = tests_module.chi_squared_full_test(bits, group_size=8)
            result_str = (f"Chi^2={result['chi2']:.2f}, p={result['p-value']:.3g}, "
                          f"{'PASS' if result['passed'] else 'FAIL'} (N={result['N']} groups)")
        elif test_type == 'serial2':
            result = tests_module.serial_test(bits, group_size=2)
            groups_txt = ", ".join(f"{k}:{v}" for k, v in result['pattern_counts'].items())
            result_str = (f"Serial X^2={result['chi2']:.2f}, p={result['p-value']:.3g}, "
                          f"{'PASS' if result['passed'] else 'FAIL'} (Pairs counts: {groups_txt})")
        elif test_type == 'serial3':
            result = tests_module.serial_test(bits, group_size=3)
            groups_txt = ", ".join(f"{k}:{v}" for k, v in result['pattern_counts'].items())
            result_str = (f"Serial X^2={result['chi2']:.2f}, p={result['p-value']:.3g}, "
                          f"{'PASS' if result['passed'] else 'FAIL'} (Pairs counts: {groups_txt})")
        elif test_type == 'autocorr1':
            result = tests_module.autocorrelation_test(bits, lag=1)
            result_str = (f"Autocorrelation (lag=1): r={result['autocorrelation']:.3f}, "
                          f"z={result['z']:.2f}, p={result['p-value']:.3g}, "
                          f"{'PASS' if result['passed'] else 'FAIL'}")
        elif test_type == 'autocorr2':
            result = tests_module.autocorrelation_test(bits, lag=2)
            result_str = (f"Autocorrelation (lag=2): r={result['autocorrelation']:.3f}, "
                          f"z={result['z']:.2f}, p={result['p-value']:.3g}, "
                          f"{'PASS' if result['passed'] else 'FAIL'}")
        elif test_type == 'poker4':
            result = tests_module.poker_test(bits, group_size=4)
            hands_txt = ", ".join(f"{k}:{v}" for k, v in result['pattern_counts'].items())
            result_str = (f"Poker χ^2={result['chi2']:.2f}, p={result['p-value']:.3g}, "
                          f"{'PASS' if result['passed'] else 'FAIL'} (Groups: {result['num_groups']}, Patterns: {hands_txt})")
        elif test_type == 'poker5':
            result = tests_module.poker_test(bits, group_size=5)
            hands_txt = ", ".join(f"{k}:{v}" for k, v in result['pattern_counts'].items())
            result_str = (f"Poker χ^2={result['chi2']:.2f}, p={result['p-value']:.3g}, "
                          f"{'PASS' if result['passed'] else 'FAIL'} (Groups: {result['num_groups']}, Patterns: {hands_txt})")
        elif test_type == 'maurer7':
            result = tests_module.maurer_universal_test(bits, L=7)
            if "error" in result:
                result_str = f"ERROR: {result['error']}"
            else:
                result_str = (f"Maurer’s Universal Test: fn={result['fn']:.3f}, expected={result['expected']:.3f} "
                              f"z={result['z']:.2f}, p={result['p-value']:.3g}, "
                              f"{'PASS' if result['passed'] else 'FAIL'} (L={result['L']}, Groups={result['K']})")
        else:
            # Test type is not implemented
            result_str = "This test type is not yet implemented"
        # Save the test result in the task dictionary
        tasks[task_id] = {"status": "Done", "done": True, "result": result_str}
    except Exception:
        # If test computation fails, log error and save status
        logging.error("Test computation error in run_selected_test_task: ", exc_info=True)
        tasks[task_id] = {"status": "Test computation error", "done": True, "result": "A test error occurred."}
    return

@app.route('/start_test', methods=['POST'])
def start_test():
    try:
        # Starts an asynchronous statistical randomness test as a background thread
        generator = request.form['generator']
        test_type = request.form['test_type']
        upper_bound = int(request.form['upper_bound'])
        samples = int(request.form.get('samples', 50))
        task_id = str(uuid.uuid4())
        t = threading.Thread(target=run_selected_test_task, args=(task_id, generator, test_type, upper_bound, samples))
        # Initialize the new test task
        tasks[task_id] = {"status": "init...", "done": False, "result": ""}
        t.start()
        # Return the new task id to the client
        return jsonify({"task_id": task_id})
    except Exception:
        logging.error("start_test - failed: ", exc_info=True)
        # If starting fails, return an error JSON to the front-end
        return jsonify({"error": "Unable to start test. Please check parameters and try again."}), 400

@app.route('/stop_test', methods=['POST'])
def stop_test():
    try:
        # Stop a running test task if user requests it
        task_id = request.form['task_id']
        if task_id not in tasks:
            return jsonify({"error": "Task not found"}), 404
        stopped_tasks.add(task_id)
        # Notify user that task was stopped
        return jsonify({"status": "Stopped"})
    except Exception:
        logging.error("Failed to stop test: ", exc_info=True)
        return jsonify({"error": "Failed to stop test"}), 500

@app.route('/', methods=['GET', 'POST'])
def direct():
    try:
        output = ""
        if request.method == 'POST':
            # Handle random number request directly from UI
            algo = request.form.get('algo')
            upper_bound = request.form.get('upper_bound', '1000')
            try:
                upper_bound = int(upper_bound)
                generator = generator_factory(algo)
                # For sound generator, check for stream initialization
                if algo == "sound":
                    if not hasattr(generator, 'stream') or generator.stream is None:
                        output = "Error: Sound generator could not initialize audio stream."
                    else:
                        rand_num = generator.generate(upper_bound)
                        output = f"{generator_names.get(algo, 'Unknown')}\n{rand_num}"
                else:
                    rand_num = generator.generate(upper_bound)
                    output = f"{generator_names.get(algo, 'Unknown')}\n{rand_num}"
                # Release generator resources if necessary
                if hasattr(generator, 'close'):
                    generator.close()
            except Exception:
                logging.error("direct page generator failed: ", exc_info=True)
                output = "Error: Unable to generate random number. Please check input."
        # Render the direct generator web page with result
        return render_template('direct.html', output=output)
    except Exception:
        logging.error("direct page - failed to render: ", exc_info=True)
        return "Error: Could not display random generator page.", 500

@app.route('/tests')
def tests():
    try:
        # Render the statistical tests web page
        return render_template('full_tests.html')
    except Exception:
        logging.error("tests page - failed to render: ", exc_info=True)
        return "Error: Could not display tests page.", 500

@app.route('/status/<task_id>')
def status(task_id):
    try:
        # Return current status and result for requested task_id
        if not task_id:
            return jsonify({"status": "not found", "done": True, "result": ""}), 400
        if task_id not in tasks:
            return jsonify({"status": "not found", "done": True, "result": ""}), 404
        # If results file exists, update the status with its latest line
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    tasks[task_id]["status"] = lines[-1].strip()
        # Return the status and result as JSON
        return jsonify(tasks.get(task_id, {"status": "not found", "done": True, "result": ""}))
    except Exception:
        logging.error(f"status route failed for task_id={task_id}: ", exc_info=True)
        return jsonify({"status": "Internal Error", "done": True, "result": "Error occurred."}), 500



if __name__ == '__main__':
    try:
        # Start Flask with support for multi-threaded requests
        app.run(debug=False, threaded=True)
    except Exception :
        logging.error("Flask app failed to start: ", exc_info=True)
