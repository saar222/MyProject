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
import secrets,threading

# Project directory configuration
PROJECT_DIR = r'C:\Users\user\Desktop\Project\209401934SaarWeinbergProjectVersion2BootstrapUpdate' # Update this path if you move the project
# Configure logging to file for error tracking and debugging generator errors
logging.basicConfig(
    filename=os.path.join(PROJECT_DIR, "generator_errors.log"),
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s'
)

_global_pyaudio_instance = None
_global_stream_instance = None
_lock = threading.Lock() 

def get_global_stream(CHUNK,FORMAT,CHANNELS,RATE,p):
    global _global_stream_instance
    with _lock:
      if _global_stream_instance is None:    
        _global_stream_instance= p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    return _global_stream_instance
    
def cleanup_global_stream():
    global _global_stream_instance
    with _lock:
      if _global_stream_instance is not None:
        _global_stream_instance.close()
        _global_stream_instance = None

def get_global_pyaudio():
    global _global_pyaudio_instance
    with _lock:
      if _global_pyaudio_instance is None:
        _global_pyaudio_instance = pyaudio.PyAudio()  # יצירה פעם אחת בלבד!
    return _global_pyaudio_instance

def cleanup_global_pyaudio():
    global _global_pyaudio_instance
    with _lock:
      if _global_pyaudio_instance is not None:
        _global_pyaudio_instance.terminate()
        _global_pyaudio_instance = None


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
        self.init()
        self.p = get_global_pyaudio()
        self.stream = get_global_stream(self.CHUNK,self.FORMAT,self.CHANNELS,self.RATE,self.p)
        
    def init(self):
        try:
            self.CHUNK = 1024
            self.FORMAT = pyaudio.paInt16
            self.CHANNELS = 1
            self.RATE = 44100
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
        #delete p and stream inside app file

class MixRandomGenerators(RandomGenerator):
    def __init__(self):
        self.n = NanoTimeRandomGenerator()
        self.j = JavaRandomGenerator()
        
    def generate(self, upper_bound: int) -> int:
        rand = secrets.randbits(2) #  choice:0,1
        if rand==1:
           return self.j.generate(upper_bound)
        else:  
           return self.n.generate(upper_bound)
         
        
    def close(self):
    # Safely close any sub-generator that exposes a 'close' method, then null out references
    # Rationale: prevents double-closing and helps GC by breaking reference chains 
      for attr in ("n", "j"):
        try:
            obj = getattr(self, attr, None)  # Fetch current sub-generator if exists 
            if obj and hasattr(obj, "close"):  # Only close if a proper close method is available 
                obj.close()  # SoundRandomGenerator closes only its stream; global PyAudio is terminated at process exit
        except Exception:
            # Be defensive: never let cleanup failures bubble up and hide original errors 
            pass

    def __del__(self):
        # Best-effort finalizer: ensure resources are closed if caller forgot to call close()
        # Note: destructor timing/order is not guaranteed; prefer explicit close() in app code 
        try:
            self.close()  # Idempotent due to attribute nulling and exception-guarded close() 
        except Exception:
            # Suppress any exception to avoid noisy GC-time errors 
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
        "mix":MixRandomGenerators
    }
    if name not in mapping:
        logging.error(f"Unknown generator name: {name}")
        raise ValueError(f"Unknown generator name: {name}")
    return mapping[name]() # create a new instance
