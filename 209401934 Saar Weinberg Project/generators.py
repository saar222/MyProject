# -- coding: utf-8 --
"""
Created on Mon Aug 18 23:50:52 2025
@author: user

This module implements several random number generators, some based on
hardware, OS/system time, Java threads, and Python's built-in generator.
It also includes a factory for their creation and resource/error management.
"""

import numpy as np
import time, os, math, random, logging, pyaudio, subprocess
import secrets

# Project directory configuration
PROJECT_DIR = r'C:\Users\user\Desktop\Project' # Update this path if you move the project
# Configure logging to file for error tracking and debugging generator errors
logging.basicConfig(
    filename=os.path.join(PROJECT_DIR, "generator_errors.log"),
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s'
)

def safe_run(cmd, desc=""):
    """
    Run an external command as a subprocess, and handle any errors or abnormal exits.
    Returns the stdout (if successful) or an error message string.
    Used for calling the Java generator.
    """
    try:
        proc = subprocess.run(cmd, cwd=PROJECT_DIR, capture_output=True, text=True, encoding="utf-8")
        debug_txt = f"\n--- Output ---\n{proc.stdout}\n--- Error ---\n{proc.stderr}\n--- Return code --- {proc.returncode}\n"
        if proc.returncode != 0:
            # Log and report failure
            logging.error(f"{desc} failed: {proc.stderr or proc.stdout or 'No output'} {debug_txt}")
            return f"Error in {desc}: {proc.stderr or proc.stdout or 'No output'}\n{debug_txt}"
        output_txt = proc.stdout.strip() or proc.stderr.strip() or "(No output)"
        return output_txt + "\n"
    except Exception as e:
        logging.error(f"Exception in {desc}: {str(e)}")
        return f"Exception in {desc}: {str(e)}"


class RandomGenerator:
    """
    Base interface for all random generators in the project.
    Any sub-class must implement generate(self, upper_bound)
    """
    def generate(self, upper_bound: int) -> int:
        raise NotImplementedError("Implement generate in subclass")
  
        
class JavaRandomGenerator(RandomGenerator):
    """
    Runs a Java-based random generator by launching a Java process and parsing its output.
    """
    def generate(self, upper_bound: int) -> int:
        result = safe_run(["java", "MyRandomProject", str(upper_bound)], desc="Java")
        try:
            return abs(int(result.strip())) # Ensure positive integer only!
        except Exception as e:
            logging.error(f"Java generator output isn't valid: {result.strip()} | Error: {e}")
            return 0 # Default value on error
        
        
class PythonRandomGenerator(RandomGenerator):
    """
    Uses Python's built-in random module to generate a random int in [0, upper_bound].
    """
    def generate(self, upper_bound: int) -> int:
        try:
            return random.randint(0, upper_bound)
        except Exception as e:
            logging.error(f"Python random generation failed: {e}")
            return 0

def busy_wait_ns(ns):
    """
    Performs a busy-wait loop for ns nanoseconds.
    Used internally by some generators for timing entropy.
    """
    target = time.perf_counter_ns() + ns
    while time.perf_counter_ns() < target:
        pass

       
class NanoTimeRandomGenerator(RandomGenerator):
    """
    Generates a random number by using nanosecond-resolution system time and a random sleep.
    Fast but weak for cryptographic security.
    """
    def generate(self, upper_bound: int) -> int: #max upper_bound=999999999
        try:
            sleep_randomly=secrets.SystemRandom().uniform(0.000001, 0.000002) # sleep random microseconds
            time.sleep(sleep_randomly)
            now = int(str(time.time_ns()//100)[-6:]) # take 6 least sig. digits for entropy
            return now % (upper_bound+1)
        except Exception as e:
            logging.error(f"Nano time generator failed: {e}")
            return 0
        
        
class SoundRandomGenerator(RandomGenerator):
    """
    Uses microphone audio data (ambient noise) as an entropy source.
    Samples are read, processed, and converted into a random number.
    """
    def __init__(self):
        self.stream = None
        self.p = None
        self.init()
    def init(self):
        try:
            self.CHUNK = 1024
            self.FORMAT = pyaudio.paInt16
            self.CHANNELS = 1
            self.RATE = 44100
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True, frames_per_buffer=self.CHUNK)
        except Exception as e:
            self.stream = None
            self.p = None
            logging.error(f"Failed to initialize SoundRandomGenerator: {e}")

    def generate(self, upper_bound: int) -> int:
        """
        Reads several chunks of sound, extracts RMS and max values, and uses them to form a random int.
        """
        try:
            random_values = []
            for _ in range(4): # Read multiple times for better entropy
                data = np.frombuffer(self.stream.read(self.CHUNK), dtype=np.int16)
                rms = np.sqrt(np.mean(data ** 2))
                max_abs = np.max(np.abs(data))
                if max_abs == 0:
                    continue
                random_values.append(100 * (rms / max_abs)) # Normalized randomness
            if not random_values:
                raise RuntimeError("No valid audio data")
            mean_values = np.mean(random_values)
            if math.isnan(mean_values):
                return 0
            random_num = int(mean_values * 10000000000000000)
            return random_num % (upper_bound + 1)
        except Exception as e:
            logging.error(f"Sound generator failed: {e}")
            return 0

    def close(self):
        """
        Closes the PyAudio stream and handles resource release.
        """
        try:
            if self.stream is not None:
                self.stream.stop_stream()
                self.stream.close()
            if self.p is not None:
                self.p.terminate()
        except Exception as e:
            logging.error(f"Failed to close SoundRandomGenerator resources: {e}")
    def __del__(self):
        # Automatically called when the object is destroyed
        try:
            self.close()
        except Exception:
            pass

# --- Factory Pattern: dynamic creation based on generator name string ---
def generator_factory(name: str) -> RandomGenerator:
    """
    Factory function to create a random generator object, given its string name.
    Supports 'javathreads', 'pythonrand', 'time', and 'sound'.
    Throws ValueError for unrecognized names.
    """
    mapping = {
        "javathreads": JavaRandomGenerator,
        "pythonrand": PythonRandomGenerator,
        "time": NanoTimeRandomGenerator,
        "sound": SoundRandomGenerator,
    }
    if name not in mapping:
        logging.error(f"Unknown generator name: {name}")
        raise ValueError(f"Unknown generator name: {name}")
    return mapping[name]() # create a new instance
