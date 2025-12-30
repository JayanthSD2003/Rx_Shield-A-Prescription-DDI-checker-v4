import time
import logging
import random
import string
from core.local_data import db
from core.drug_client import extract_potential_drugs, check_interactions_for_list

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_synthetic_noise(text, noise_level=0.1):
    """
    Introduces typos/noise into a string.
    noise_level: Probability of a character being flipped.
    """
    chars = string.ascii_letters + string.digits
    noisy_text = ""
    for char in text:
        if random.random() < noise_level:
            # Replace with random char
            noisy_text += random.choice(chars)
        else:
            noisy_text += char
    return noisy_text

def run_benchmark():
    output = []
    def log(msg=""):
        output.append(str(msg))
        print(msg)

    log("=== Starting Enhanced DDI Pipeline Benchmark ===\n")
    
    # 1. Load DB
    t0 = time.time()
    db.load_data()
    t1 = time.time()
    log(f"Database Load Time: {t1 - t0:.4f} seconds")
    
    total_drugs = len(db.drug_map)
    log(f"Total Drugs in DB: {total_drugs}")
    
    if total_drugs == 0:
        log("Error: Database empty! Cannot run benchmark.")
        return "\n".join(output)

    # 2. Synthetic OCR Accuracy (Correction Test)
    log("\n--- Synthetic OCR Correction Test ---")
    log("Sampling 20 random drugs from DB, applying noise, and attempting resolution...")
    
    sample_size = 20
    # ensure we have enough drugs
    keys = list(db.drug_map.keys())
    sample_keys = random.sample(keys, min(sample_size, total_drugs))
    
    passes = 0
    
    for original_name in sample_keys:
        # Create noisy version
        extracted_name = generate_synthetic_noise(original_name, noise_level=0.15) 
        
        # Resolve
        resolved_name, confidence = db.resolve_drug_name(extracted_name)
        
        # Check correctness
        # The correct result is the generic name associated with the original key
        expected_generic = db.drug_map[original_name]['generic_name']
        
        # Relaxed check: 
        # 1. Exact match of generic name
        # 2. Confidence is High or Medium (implies successful resolution)
        # Note: If resolved_name matches expected_generic, we consider it a pass.
        
        match_success = False
        if resolved_name and expected_generic:
             match_success = (resolved_name.lower() == expected_generic.lower())
        
        status = "PASS" if match_success else "FAIL"
        if match_success: passes += 1
            
        log(f"[{status}] Orig: '{original_name}' -> Noisy: '{extracted_name}' -> Res: '{resolved_name}' (Conf: {confidence})")
        
    accuracy = (passes / len(sample_keys)) * 100
    log(f"\nCorrection Accuracy Score: {accuracy:.2f}%")

    # 3. DDI Analysis Latency
    log("\n--- DDI Analysis Latency Test ---")
    log("Picking random pairs and checking interaction API latency...")
    
    latency_samples = 3
    total_time = 0
    
    for i in range(latency_samples):
        # Pick 2 random drugs
        pair = random.sample(keys, 2)
        log(f"Checking pair: {pair}")
        
        t_start = time.time()
        try:
            # We use the raw pair strings. check_interactions_for_list resolves them first.
            check_interactions_for_list(pair)
            duration = time.time() - t_start
            log(f"  Time: {duration:.4f}s")
            total_time += duration
        except Exception as e:
            log(f"  Failed: {e}")
            
    avg_latency = total_time / latency_samples
    log(f"\nAverage DDI Latency: {avg_latency:.4f}s")
    
    log("\n=== Benchmark Complete ===")
    
    return "\n".join(output)

if __name__ == "__main__":
    run_benchmark()
