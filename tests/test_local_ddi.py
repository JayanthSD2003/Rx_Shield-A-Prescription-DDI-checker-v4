from core.drug_client import check_interactions_for_list
import logging

# Setup basic logging to see output
logging.basicConfig(level=logging.INFO)

print("Testing Check Interactions with Local Data...")

# Test 1: DrugBank Synonym (Tylenol -> Acetaminophen)
print("\n--- Test 1: Synonym Resolution (Tylenol) ---")
# 'Tylenol' should map to 'Acetaminophen' if DrugBank loaded correctly
report = check_interactions_for_list(["Tylenol", "Warfarin"])
print(report)

# Test 2: Typo Correction (if fuzzy works, or exact match)
print("\n--- Test 2: Typo Correction ---")
# 'Paracitamol' might be corrected to 'Paracetamol' if fuzzy logic is enabled
report2 = check_interactions_for_list(["Paracetamol", "Aspirin"])
print(report2)
