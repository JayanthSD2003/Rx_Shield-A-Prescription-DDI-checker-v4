
import requests
import json

def get_rxcui(drug_name):
    try:
        url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={drug_name}"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if 'idGroup' in data and 'rxnormId' in data['idGroup']:
            return data['idGroup']['rxnormId'][0]
    except Exception as e:
        print(f"Error for {drug_name}: {e}")
    return None

drugs = ["Aspirin", "Paracetamol", "Warfarin"]
cuis = []
mapping = {}

print("Resolving CUIs...")
for d in drugs:
    c = get_rxcui(d)
    print(f"{d} -> {c}")
    if c:
        cuis.append(c)
        mapping[c] = d

if len(cuis) > 1:
    cui_str = "+".join(cuis)
    url = f"https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={cui_str}"
    print(f"Fetching: {url}")
    
    resp = requests.get(url)
    data = resp.json()
    
    print("\nAPI Response Structure:")
    if 'fullInteractionTypeGroup' in data:
        for group in data['fullInteractionTypeGroup']:
            for interaction in group['fullInteractionType']:
                for pair in interaction['interactionPair']:
                    c1 = pair['interactionConcept'][0]['minConceptItem']['rxcui']
                    c2 = pair['interactionConcept'][1]['minConceptItem']['rxcui']
                    severity = pair.get('severity', 'N/A')
                    
                    name1 = mapping.get(c1, f"UNKNOWN({c1})")
                    name2 = mapping.get(c2, f"UNKNOWN({c2})")
                    
                    print(f"Interaction: {name1} <--> {name2} (Sev: {severity})")
                    if name1.startswith("UNKNOWN") or name2.startswith("UNKNOWN"):
                        print(f"  FAILED MATCH! returned CUI {c1}/{c2} not in sent list {list(mapping.keys())}")
    else:
        print("No interactions found.")
