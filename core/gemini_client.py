import os
import google.generativeai as genai
from dotenv import load_dotenv
import PIL.Image
from core.puter_client import perform_ocr_puter

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("Warning: GEMINI_API_KEY not found in environment.")

def perform_ocr_gemini(image_path):
    """
    Sends an image to Gemini 1.5 Flash for accurate OCR.
    """
    if not api_key:
        return "Error: System configuration error (API Key)."
    
    if not os.path.exists(image_path):
        return f"Error: Image not found at {image_path}"

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = PIL.Image.open(image_path)
        
        prompt = "Extract all text from this prescription image verbatim. Output only the extracted text."
        
        response = model.generate_content([prompt, img])
        
        return response.text
    except Exception as e:
        return f"Error using AI OCR: {str(e)}"

def analyze_text(text, patient_details=None):
    """
    Performs DDI analysis on the given text (whether OCR or Manual).
    """
    if not api_key:
        return "Analysis Failed: System configuration error (API Key)."

    # Construct Prompt with Patient Details
    patient_info_str = ""
    if patient_details:
        patient_info_str = f"""
Patient Details:
- Name: {patient_details.get('name', 'N/A')}
- Age: {patient_details.get('age', 'N/A')}
- Gender: {patient_details.get('gender', 'N/A')}
- Weight: {patient_details.get('weight', 'N/A')}
- Body Type: {patient_details.get('body_type', 'N/A')}
"""

    # Safe name extraction
    p_name = patient_details.get('name', 'Patient') if patient_details else 'Patient'

    # Updated Prompt for formatted output
    analysis_prompt = f"""
You are a medical assistant. I will provide you with text from a prescription.
Please analyze this text and check for:
1. Drug Names and Dosages inferred from the text.
2. Potential Drug-Drug Interactions (DDI) between the identified drugs.
3. Any specific warnings based on the Patient Details provided below.

{patient_info_str}

Prescription Text:
"{text}"

Please provide the output in a clean, readable format with clear sections for "Identified Medications", "Analysis & Warnings", and "Recommendations".

IMPORTANT: You MUST also include a section titled "Knowledge Graph Representation".
In this section, represent the relationships using text arrows ( -> ) like the following examples:
- Patient ({p_name}) -> presents with -> Condition (Name)
- Condition -> caused by -> Event
- Doctor -> prescribes -> Drug Name
- Drug Name -> treats -> Condition

Keep this section concise and strictly text-based arrows.

Disclaimer: Emphasize that this is an AI analysis and requires professional verification.
"""

    # Model Priority: 2.5-Pro -> 2.5-flash-lite -> 1.5-flash
    # Model Priority: 2.5-Flash -> 2.5-Flash-Lite -> 3-Flash
    models_to_try = ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-3-flash']
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(analysis_prompt)
            print(f"Success with model: {model_name}")
            return response.text
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            continue
            
    return "Analysis failed reset the parameters"

def enhance_ocr_text(raw_text):
    """
    Uses Gemini to correct and format OCR text.
    """
    if not api_key: return raw_text
    
    prompt = f"""
    The following text is OCR output from a medical prescription. It may contain typos or noise.
    Please correct spelling errors, especially for drug names, and format it as a clean list.
    Return ONLY the corrected text.
    
    OCR Text:
    "{raw_text}"
    """
    
    # Model Priority for Enhancement
    # Model Priority: 2.5-Flash -> 2.5-Flash-Lite -> 3-Flash
    models_to_try = ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-3-flash']
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Enhancement model {model_name} failed: {e}")
            continue
            
    return raw_text # Fallback to raw

def extract_generics_gemini(text):
    """
    Ask Gemini to identify all drugs and return their Generic Names as a python list.
    """
    if not api_key: return []
    
    prompt = f"""
    Analyze the following medical text and identify all pharmaceutical drugs prescribed.
    For each drug, find its GENERIC NAME (Active Ingredient).
    Return the result effectively as a python list of strings.
    Example output format: ["Metformin", "Paracetamol", "Amoxycillin"]
    Do not include dosages. Return ONLY the list.

    Text:
    "{text}"
    """
    
    # Model Priority for Generics
    # Model Priority: 2.5-Flash -> 2.5-Flash-Lite -> 3-Flash
    models_to_try = ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-3-flash']
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            # Clean response to get list
            cleaned = response.text.strip()
            if cleaned.startswith("```json"): cleaned = cleaned[7:-3]
            elif cleaned.startswith("```python"): cleaned = cleaned[9:-3]
            elif cleaned.startswith("```"): cleaned = cleaned[3:-3]
            
            import ast
            try:
                return ast.literal_eval(cleaned)
            except:
                # Fallback parsing
                return [line.strip('- ').strip() for line in cleaned.split('\n') if line.strip()]
        except Exception as e:
            print(f"Generic extraction model {model_name} failed: {e}")
            continue
            
    return []

def get_interactions_gemini(drug_list):
    """
    Asks Gemini to identify DDIs between the provided drugs and return a structured list.
    Returns: List of dicts [{'drug1': 'A', 'drug2': 'B', 'severity': 'High', 'description': '...'}]
    """
    if not api_key or not drug_list or len(drug_list) < 2: return []
    
    prompt = f"""
    Analyze the following list of drugs for Drug-Drug Interactions (DDIs).
    Drugs: {", ".join(drug_list)}
    
    Return a JSON list of objects where each object represents an interaction pair.
    Format:
    [
      {{
        "drug1": "Name1",
        "drug2": "Name2",
        "severity": "Severe" | "Major" | "Moderate" | "Minor",
        "description": "Short description of the interaction risk."
      }}
    ]
    
    If no interactions exist, return [].
    Make sure to capture ALL potential interactions.
    Return ONLY the JSON.
    """
    
    models_to_try = ['gemini-1.5-flash', 'gemini-pro'] # Stable models preferred
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            cleaned = response.text.strip()
            if cleaned.startswith("```json"): cleaned = cleaned[7:-3]
            elif cleaned.startswith("```"): cleaned = cleaned[3:-3]
            
            import json
            data = json.loads(cleaned)
            return data
            
        except Exception as e:
            print(f"Gemini DDI Graph extraction failed ({model_name}): {e}")
            continue
            
    return []

def extract_extended_graph_data_gemini(text, patient_details=None):
    """
    Extracts structured data for the Advanced Knowledge Graph:
    - Patient Info, Date
    - Diagnosis/Conditions
    - Drugs
    - Specific DDI Relationships (Protective vs Risk)
    """
    if not api_key: return None
    
    # Safe handling if patient_details is None
    if patient_details:
        p_name = patient_details.get('name', 'Patient')
    else:
        p_name = 'Patient'
    
    prompt = f"""
    Analyze the following prescription text and extract structured data for a Knowledge Graph.
    
    Text: "{text}"
    Patient Name Context: {p_name}
    
    Return a JSON object with this exact structure:
    {{
      "patient_name": "Name extracted or '{p_name}'",
      "date": "Date extracted or 'Unknown'",
      "diagnosis": ["Condition 1", "Condition 2"],
      "drugs": ["Drug 1", "Drug 2"],
      "relationships": [
        {{
            "source": "DrugName1",
            "target": "DrugName2",
            "type": "Protective" | "Risk", 
            "description": "Short label e.g., 'Gastric Protection' or 'Irritation Risk'"
        }}
        // Add relationships between Drugs and Conditions if explicit, e.g.
        // {{ "source": "Drug1", "target": "Condition1", "type": "Treats", "description": "Treats" }}
      ]
    }}
    
    Focus on finding "Rational Polypharmacy" interactions (e.g. PPI protecting against NSAID side effects).
    Return ONLY JSON.
    """
    
    # Model Priority: 2.5-Flash -> 2.5-Flash-Lite -> 3-Flash
    models_to_try = ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-3-flash']
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            cleaned = response.text.strip()
            if cleaned.startswith("```json"): cleaned = cleaned[7:-3]
            elif cleaned.startswith("```"): cleaned = cleaned[3:-3]
            
            import json
            return json.loads(cleaned)
        except Exception as e:
            print(f"Graph Data Extraction Error ({model_name}): {e}")
            continue
            
    return None

def clean_markdown_to_text(text):
    import re
    # Remove bold/italic markers (* or _)
    text = text.replace('**', '').replace('__', '')
    # Remove headers (## Header) -> Header
    text = re.sub(r'#+\s*', '', text)
    # Ensure bullet points are simple dashes
    text = text.replace('* ', '- ')
    # Remove generic code blocks if any
    text = text.replace('```', '')
    return text.strip()

def analyze_prescription(image_path, patient_details=None):
    """
    Orchestrates the analysis:
    1. Puter OCR -> Raw Text
    2. Gemini -> Enhanced Text (Correction)
    3. Gemini -> Analysis (DDI)
    4. Gemini -> Extract Generics -> Local Data Lookup
    """
    try:
        # Step 1: Puter OCR
        print(f"Starting OCR with Puter for {image_path}...")
        extracted_text = perform_ocr_puter(image_path)
        source = "AI Analysis Enhanced"
        
        if "Error" in extracted_text or not extracted_text:
             return f"OCR Failed: {extracted_text}"

        # Step 2: Enhancement
        if api_key:
            enhanced_text = enhance_ocr_text(extracted_text)
        else:
            enhanced_text = extracted_text

        # Step 3: DDI Analysis
        raw_analysis = analyze_text(enhanced_text, patient_details)
        # Convert to pure text
        analysis_result = clean_markdown_to_text(raw_analysis)

        # Step 4: Local Dataset Lookup (Integrated per request)
        local_report = ""
        processed_generics = set()
        try:
            from core.local_data import db
            
            # Use Gemini to get Generics explicitly
            extracted_generics = extract_generics_gemini(enhanced_text)
            
            # Fetch details
            if extracted_generics:
                local_report = "\nFrom the Drug dataset / database\n"
                
                found_any = False

                for raw_gen in extracted_generics:
                    # Resolve API Generic Name -> Local DB Generic Key
                    # This handles fuzzy matching (e.g. "Paracetamol 500" -> "Paracetamol")
                    canonical_name, conf = db.resolve_drug_name(str(raw_gen))
                    
                    if conf > 60: # Threshold for match
                        if canonical_name in processed_generics: continue
                        processed_generics.add(canonical_name)
                        
                        details = db.get_drug_details_by_generic(canonical_name)
                        if details:
                            found_any = True
                            local_report += f"\n[Generic: {canonical_name}]\n"
                            if details['uses']: local_report += f"  - Uses: {details['uses']}\n"
                            if details['side_effects']: local_report += f"  - Side Effects: {details['side_effects']}\n"
                            if details['brands_sample']: local_report += f"  - Common Brands: {details['brands_sample']}\n"
                
                if not found_any:
                    local_report = "" # Hide section if nothing found in local DB

        except Exception as local_e:
            local_report = f"\n(Local Data Lookup Error: {local_e})"

        # 5. Strict Blacklist Filtering (User Request)
        BLACKLIST = {
            'phone', 'patient', 'date', 'physician', 'hospital', 'reg', 'dr', 'tab', 'cap',
            'tablet', 'capsule', 'injection', 'inj', 'syrup', 'syp', 'clarify', 'age', 'sex',
            'mr', 'mrs', 'name', 'address', 'signature', 'sign', 'department', 'unit', 'mobile'
        }
        
        final_drug_list = []
        for d in processed_generics:
            if d.lower() not in BLACKLIST and len(d) > 2:
                final_drug_list.append(d)
                
        # Format the final output matching output_preview.txt structure
        formatted_output = f"""--- Step 1: Raw OCR Results (Puter) ---
{extracted_text}
===============================================================================================

--- Step 2: Enhanced Text (Gemini Correction) ---
{enhanced_text}
===============================================================================================

--- Step 3: Extracted Analysis ---
{analysis_result}

================================================================================================

--- Step 4: Local Database Verification ---
{local_report if local_report else "No local data found matching the identified drugs."}
================================================================================================"""
        
        # Return Tuple: (Output Text, List of Drugs Found)
        return formatted_output, final_drug_list

    except Exception as e:
        return f"Error during analysis: {str(e)}", []
