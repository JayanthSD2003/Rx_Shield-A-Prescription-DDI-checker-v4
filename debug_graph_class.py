
from core.knowledge_graph import KnowledgeGraphManager
import os

print("Testing KnowledgeGraphManager...")
kg = KnowledgeGraphManager()

# Test Case 1: Universal (Empty Input)
print("\n--- Test 1: Universal Generation (Empty Input) ---")
path = kg.generate_graph([])
print(f"Generated at: {path}")

# Test Case 2: Specific Drugs (Simulating Analysis)
print("\n--- Test 2: Specific Analysis (Aspirin, Warfarin) ---")
path2 = kg.generate_graph(["Aspirin", "Warfarin"])
print(f"Generated at: {path2}")
