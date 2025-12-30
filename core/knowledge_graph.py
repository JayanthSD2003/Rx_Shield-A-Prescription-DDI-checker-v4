import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

class KnowledgeGraphManager:
    def __init__(self):
        self.output_path = "knowledge_graph.png"
        
    def generate_graph(self, drug_names=None, full_text=None):
        """
        Generates the 'Integrated Patient & DDI Analysis' Graph.
        Visuals: Patient (Center) -> Diagnosis (Top) -> Drugs (Surrounding)
        Edges: Green (Protective), Red (Risk), Blue (Standard Flow)
        """
        # 1. Get Data from Gemini
        from core.gemini_client import extract_extended_graph_data_gemini
        
        # Prefer full text context if available
        if full_text:
            context_text = full_text
        else:
            context_text = f"Prescribed Drugs: {', '.join(drug_names) if drug_names else 'None'}"
        
        data = extract_extended_graph_data_gemini(context_text)
        
        if not data:
            # Fallback Dummy Data if API Fails
            data = {
                "patient_name": "Patient",
                "date": "Dec 2025",
                "diagnosis": ["Screening"],
                "drugs": drug_names if drug_names else ["Drug A", "Drug B"],
                "relationships": []
            }

        # 2. Build Graph
        G = nx.DiGraph() # Directed Graph
        
        # Nodes
        patient_node = data.get('patient_name', 'Patient')
        G.add_node(patient_node, type='patient', label=patient_node)
        
        # Conditions
        for cond in data.get('diagnosis', []):
            G.add_node(cond, type='condition', label=cond)
            G.add_edge(patient_node, cond, type='has_condition')
            
        # Drugs
        for drug in data.get('drugs', []):
            G.add_node(drug, type='drug', label=drug)
            G.add_edge(patient_node, drug, type='prescribed')
            
        # DDI Relationships
        for rel in data.get('relationships', []):
            src = rel.get('source')
            tgt = rel.get('target')
            rtype = rel.get('type') # Protective, Risk
            desc = rel.get('description', '')
            
            # Ensure nodes exist (Gemini might return slightly diff names)
            if src not in G.nodes: G.add_node(src, type='drug', label=src)
            if tgt not in G.nodes: G.add_node(tgt, type='drug', label=tgt)
            
            G.add_edge(src, tgt, type='ddi', ddi_type=rtype, label=desc)

        # 3. Layout & Drawing
        plt.figure(figsize=(12, 10))
        # plt.title("Integrated Patient & DDI Analysis", fontsize=16, fontweight='bold', pad=20) # Title often crops, relying on UI label
        
        # Custom Positioning
        pos = {}
        # Patient Center
        pos[patient_node] = (0, 0)
        
        # Conditions (Top semicircle)
        import numpy as np
        conditions = [n for n, attr in G.nodes(data=True) if attr.get('type') == 'condition']
        if conditions:
            # Spread 180 degrees tops
            angle_step = np.pi / (len(conditions) + 1)
            for i, cond in enumerate(conditions):
                theta = (i + 1) * angle_step
                pos[cond] = (np.cos(theta) * 0.8, np.sin(theta) * 0.8 + 0.2)
                
        # Drugs (Bottom semicircle)
        drugs = [n for n, attr in G.nodes(data=True) if attr.get('type') == 'drug']
        if drugs:
            # Spread 180 degrees bottom
            angle_step = np.pi / (len(drugs) + 1)
            for i, drug in enumerate(drugs):
                theta = np.pi + (i + 1) * angle_step
                pos[drug] = (np.cos(theta) * 0.8, np.sin(theta) * 0.8 - 0.2)

        # Helper: Text Wrap
        import textwrap
        def wrap(text): return "\n".join(textwrap.wrap(text, width=12))

        # Draw Patient (Center, Distinct)
        # Using a larger node with border
        nx.draw_networkx_nodes(G, pos, nodelist=[patient_node], 
                               node_color='#48dbfb', 
                               node_size=6000, 
                               alpha=1.0, 
                               edgecolors='white', 
                               linewidths=3)
        nx.draw_networkx_labels(G, pos, {patient_node: wrap(patient_node)}, font_size=12, font_weight='bold')
        
        # Draw Conditions
        if conditions:
            nx.draw_networkx_nodes(G, pos, nodelist=conditions, 
                                   node_color='#54a0ff', 
                                   node_size=4000, 
                                   node_shape='o', # Circle for consistency or 's'
                                   alpha=0.9,
                                   edgecolors='white',
                                   linewidths=2)
            nx.draw_networkx_labels(G, pos, {n: wrap(n) for n in conditions}, font_size=9, font_color='white', font_weight='bold')
            
        # Draw Drugs
        if drugs:
            nx.draw_networkx_nodes(G, pos, nodelist=drugs, 
                                   node_color='#ff9f43', 
                                   node_size=4500, 
                                   alpha=1.0,
                                   edgecolors='white',
                                   linewidths=2)
            nx.draw_networkx_labels(G, pos, {n: wrap(n) for n in drugs}, font_size=10, font_weight='bold')

        # Draw Edges (Standard) - Curved
        std_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') != 'ddi']
        nx.draw_networkx_edges(G, pos, edgelist=std_edges, edge_color='#bdc3c7', arrows=True, width=1.5, connectionstyle='arc3,rad=0.1')
        
        
        # Draw Edges (DDI - Protective)
        prot_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') == 'ddi' and d.get('ddi_type') == 'Protective']
        if prot_edges:
            nx.draw_networkx_edges(G, pos, edgelist=prot_edges, edge_color='#2ecc71', width=4, arrowstyle='-|>', arrowsize=20, connectionstyle='arc3,rad=0.2')
            edge_labels = { (u,v): d['label'] for u,v,d in G.edges(data=True) if (u,v) in prot_edges }
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='green', font_size=8)
            
        # Draw Edges (DDI - Risk)
        risk_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') == 'ddi' and d.get('ddi_type') == 'Risk']
        if risk_edges:
            nx.draw_networkx_edges(G, pos, edgelist=risk_edges, edge_color='#ff6b6b', width=2, style='dashed', arrowstyle='-|>', arrowsize=15, connectionstyle='arc3,rad=-0.2')
            edge_labels = { (u,v): d['label'] for u,v,d in G.edges(data=True) if (u,v) in risk_edges }
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=8)

        # Legend
        handles = [
            mpatches.Patch(color='#2ecc71', label='Protective Interaction'),
            mpatches.Patch(color='#ff6b6b', label='Risk/Adverse Effect'),
            mpatches.Patch(color='#ff9f43', label='Medication'),
            mpatches.Patch(color='#54a0ff', label='Condition')
        ]
        plt.legend(handles=handles, loc='lower right', frameon=True)

        plt.axis('off')
        try:
            plt.savefig(self.output_path, format="PNG", bbox_inches='tight', dpi=120)
            plt.close()
            return os.path.abspath(self.output_path)
        except Exception as e:
            print(f"Graph Save Error: {e}")
            return None
