
from core.knowledge_graph import KnowledgeGraphManager

def test_kg_logic():
    kg = KnowledgeGraphManager()
    
    
    # Test Inputs simulating OCR (Gemini should find interactions here)
    inputs = ["Warfarin", "Aspirin", "Ibuprofen"]
     
    print(f"Testing inputs: {inputs}")
    
    # We need to hook into the normalization logic directly or just run generate_graph and inspect output
    # Since logic is inside generate_graph, we'll run it and intercept the print output or check the returned graph if we could (but the method saves specific file).
    # Actually, better to copy the logic into this script for isolation OR modify generate_graph to return the G object.
    # The generate_graph prints "KG: Accepted valid drug..." and "KG: Filtered out..."
    
    # Let's run it and see the console output.
    path = kg.generate_graph(inputs)
    print(f"Graph generated at: {path}")

if __name__ == "__main__":
    test_kg_logic()
