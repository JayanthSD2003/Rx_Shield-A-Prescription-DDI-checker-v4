
from core.knowledge_graph import KnowledgeGraphManager
import networkx as nx

def debug_kg():
    print("--- Starting KG Debug ---")
    kg = KnowledgeGraphManager()
    
    # Input drugs
    inputs = ["Warfarin", "Aspirin"]
    print(f"Inputs: {inputs}")
    
    # Manually reproduce the logic to inspect G
    drug_names = inputs
    G = nx.Graph()
    
    # 1. Add Drug Nodes
    for drug in drug_names:
        G.add_node(drug, type='drug')
    print(f"Nodes after step 1: {G.nodes()}")
    
    # 2. Simulate Gemini Interaction
    gemini_interactions = [
        {
            "drug1": "Warfarin",
            "drug2": "Aspirin", 
            "severity": "Severe",
            "description": "Risk of bleeding"
        }
    ]
    
    print(f"Simulated Gemini Reponse: {gemini_interactions}")
    
    # 3. Add Interaction Nodes (Reflected Logic)
    for item in gemini_interactions:
        d1 = item.get('drug1')
        d2 = item.get('drug2')
        sev = item.get('severity')
        desc = item.get('description')
        
        target_n1 = None
        target_n2 = None
        
        # Match logic
        lower_map = {n.lower(): n for n in drug_names}
        if d1.lower() in lower_map: target_n1 = lower_map[d1.lower()]
        if d2.lower() in lower_map: target_n2 = lower_map[d2.lower()]
        
        print(f"Matching '{d1}' -> '{target_n1}'")
        print(f"Matching '{d2}' -> '{target_n2}'")
        
        if target_n1 and target_n2:
            int_id = f"AI_Int_{target_n1}_{target_n2}"
            lbl = f"{target_n1}-{target_n2}\nInteraction\n({sev})\n{desc}"
            G.add_node(int_id, type='interaction', label=lbl)
            G.add_edge(target_n1, int_id)
            G.add_edge(target_n2, int_id)
            print(f"Added interaction node {int_id} and edges.")
            
    print(f"Final Nodes: {G.nodes()}")
    print(f"Final Edges: {G.edges()}")
    
    if len(G.edges()) == 0:
        print("FAIL: No edges created.")
    else:
        print("SUCCESS: Edges created.")

if __name__ == "__main__":
    debug_kg()
