import requests
import json
import urllib.parse
import re

def get_rxcui(drug_name):
    """
    Searches NLM RxNav for a drug name and returns its RxCUI (ID).
    Returns None if not found.
    """
    try:
        # strict matching is safer to avoid garbage OCR results being matched
        base_url = "https://rxnav.nlm.nih.gov/REST/rxcui.json"
        params = {'name': drug_name, 'search': 1} # search=1 allows approximate match, remove if too noisy
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'idGroup' in data and 'rxnormId' in data['idGroup']:
                # Return the first match
                return data['idGroup']['rxnormId'][0]
    except Exception:
        pass
    return None

def check_interactions_for_list(drug_names):
    """
    Takes a list of drug names strings.
    Resolves them to RxCUIs.
    Checks for interactions between them.
    Returns a formatted string report.
    """
    cuis = []
    found_drugs = []
    
    # 1. Resolve Names to IDs
    for name in drug_names:
        # Simple cleanup
        clean_name = name.strip()
        if len(clean_name) < 3: continue 
        
        cui = get_rxcui(clean_name)
        if cui:
            cuis.append(cui)
            found_drugs.append(clean_name)
    
    if len(cuis) < 2:
        return f"Found {len(found_drugs)} identifiable drugs ({', '.join(found_drugs)}). Need at least two to check for interactions."

    # 2. Check Interactions
    # https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis=207106+152923+656659
    try:
        rx_params = "+".join(cuis)
        url = f"https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={rx_params}"
        response = requests.get(url)
        
        report = []
        report.append("--- Identified Drugs (Official) ---")
        report.append(", ".join(found_drugs))
        report.append("\n--- Interaction Report (NLM RxNav) ---")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'fullInteractionTypeGroup' in data:
                # Interactions found
                for group in data['fullInteractionTypeGroup']:
                     for interaction_type in group.get('fullInteractionType', []):
                         for interaction in interaction_type.get('interactionPair', []):
                             drug1 = interaction.get('interactionConcept', [])[0].get('minConceptItem', {}).get('name', 'Drug 1')
                             drug2 = interaction.get('interactionConcept', [])[1].get('minConceptItem', {}).get('name', 'Drug 2')
                             severity = interaction.get('severity', 'N/A')
                             description = interaction.get('description', 'No description available.')
                             
                             report.append(f"• [SEVERITY: {severity}] {drug1} + {drug2}")
                             report.append(f"  Warning: {description}\n")
            else:
                report.append("No official interactions found between these drugs.")
        else:
            report.append(f"Error checking interactions: API Status {response.status_code}")
            
        return "\n".join(report)

    except Exception as e:
        return f"Error connecting to RxNav: {str(e)}"

def extract_potential_drugs(ocr_text):
    """
    Heuristic to extract list-like items from OCR text.
    Assumes prescriptions often have one drug per line.
    """
    lines = ocr_text.split('\n')
    potential_drugs = []
    
    # Common words to ignore if they appear alone or as the start
    NOISE_WORDS = {
        "TABLET", "CAPSULE", "TAB", "CAP", "INJ", "INJECTION", 
        "SYRUP", "SOL", "SOLUTION", "DROP", "DROPS", 
        "RX", "DATE", "DR", "PATIENT", "NAME", "AGE", "SEX", 
        "ADDRESS", "SIGNATURE", "PHARMACY", "HOSPITAL", 
        "TAKE", "daily", "OD", "BD", "TDS", "SOS", "BEFORE", "AFTER", "FOOD"
    }

    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue

        # Regex to remove dosage like '500mg', '5 mg', '1-0-0' at the END of string
        # We start taking words from the left until we hit a number or symbol
        
        words = line.split()
        if not words: continue
        
        candidate = []
        for w in words:
            # Clean off punctuation
            w_clean = re.sub(r'[^\w\s]', '', w)
            
            if not w_clean: continue
            
            # If word is numeric or looks like dosage (500mg), stop
            if re.match(r'^\d', w_clean):
                break
                
            # If word is in noise list, skip or stop? 
            # Usually strict skip might be dangerous, but let's try to just accept good alphabetic words
            if w_clean.upper() in NOISE_WORDS:
                continue
                
            if re.match(r'^[a-zA-Z]+$', w_clean) and len(w_clean) > 2:
                candidate.append(w_clean)
            else:
                break
        
        if candidate:
            drug_name = " ".join(candidate)
            # Dedup
            if drug_name not in potential_drugs:
                potential_drugs.append(drug_name)
            
    return potential_drugs
