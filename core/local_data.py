import os
import csv
import difflib
import logging
import json
import ast

# Try to import fuzzy matching library
HAS_FUZZY = False
try:
    from thefuzz import process
    HAS_FUZZY = True
except ImportError:
    try:
        from fuzzywuzzy import process
        HAS_FUZZY = True
    except ImportError:
        pass

logger = logging.getLogger(__name__)

class LocalDrugDB:
    def __init__(self):
        # key (lower_name) -> dict with details
        self.drug_map = {} 
        # key (first word lower) -> list of full keys
        self.prefix_map = {}
        self.common_names = set()
        self.loaded = False
        
    def load_data(self):
        if self.loaded:
            return

        logger.info("Loading local drug databases...")
        # 1. Load DrugBank
        self._load_drugbank()
        
        # 2. Load Indian Datasets
        self._load_indian_datasets()
        
        self.loaded = True
        logger.info(f"Local DB loaded. {len(self.drug_map)} identifiable drugs.")

    def _add_to_map(self, key, entry):
        """Helper to add to drug_map and prefix_map"""
        k = key.lower()
        self.drug_map[k] = entry
        
        # Prefix Indexing
        # "augmentin 625" -> index under "augmentin"
        first_word = k.split()[0]
        if len(first_word) >= 3:
            if first_word not in self.prefix_map:
                self.prefix_map[first_word] = []
            self.prefix_map[first_word].append(k)

    def _load_drugbank(self):
        base_path = os.path.join(os.getcwd(), "DDI_datasets and DB data", "drugbank_all_drugbank_vocabulary.csv", "drugbank vocabulary.csv")
        
        if os.path.exists(base_path):
            try:
                with open(base_path, mode='r', encoding='utf-8', errors='replace') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        common = row.get('Common name', '').strip()
                        if not common: continue
                        
                        entry = {
                            'generic_name': common,
                            'brand_name': common,
                            'source': 'DrugBank'
                        }
                        self._add_to_map(common, entry)
                        self.common_names.add(common)
                        
                        syns = row.get('Synonyms', '')
                        if syns:
                            for syn in syns.split('|'):
                                s = syn.strip()
                                if s:
                                    self._add_to_map(s, entry)
                                    
                print(f"Loaded DrugBank data from {base_path}")
            except Exception as e:
                logger.error(f"Failed to load DrugBank CSV: {e}")
                print(f"Failed to load DrugBank CSV: {e}")

    def _load_indian_datasets(self):
        folder = os.path.join(os.getcwd(), "DDI_datasets and DB data", "Indian_Medicine_Database")
        if not os.path.exists(folder):
            return

        files = os.listdir(folder)
        for filename in files:
            file_path = os.path.join(folder, filename)
            if not filename.endswith('.csv'): continue
            
            try:
                if "extensive-a-z" in filename.lower() or "az-medicine-dataset" in filename.lower():
                    self._load_rituraj_or_shudhanshu(file_path, filename)
                elif "indian-pharmaceutical-products" in filename.lower():
                    self._load_rishgeeky(file_path, filename)
                elif "india-medicines-and-drug-info" in filename.lower():
                    self._load_apkaayush(file_path, filename)
                elif "all-india-drug-bank" in filename.lower():
                    self._load_ankushpoddar(file_path, filename)
                else:
                    self._load_generic_csv(file_path, filename)
                    
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")

    def _load_rishgeeky(self, path, filename):
        with open(path, mode='r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                brand = row.get('brand_name', '').strip()
                if not brand: continue
                
                ingredients_raw = row.get('active_ingredients', '[]')
                composition = ""
                try:
                    if ingredients_raw:
                        ing_list = ast.literal_eval(ingredients_raw)
                        comp_parts = []
                        if isinstance(ing_list, list):
                            for item in ing_list:
                                if isinstance(item, dict):
                                    comp_parts.append(f"{item.get('name','')} {item.get('strength','')}".strip())
                        composition = " + ".join(comp_parts)
                except:
                    composition = row.get('primary_ingredient', '')

                entry = {
                    'brand_name': brand,
                    'generic_name': composition if composition else brand,
                    'is_brand': True,
                    'source': 'RishgeekyDB'
                }
                self._add_to_map(brand, entry)
                count += 1
            print(f"Loaded {count} drugs from {filename}")

    def _load_rituraj_or_shudhanshu(self, path, filename):
        with open(path, mode='r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                brand = row.get('name', '').strip()
                if not brand: continue
                
                comp1 = row.get('short_composition1', '').strip()
                comp2 = row.get('short_composition2', '').strip()
                composition = f"{comp1} + {comp2}".strip(' +')
                
                side_effects = row.get('Consolidated_Side_Effects', '')
                uses = row.get('use0', '') 
                
                entry = {
                    'brand_name': brand,
                    'generic_name': composition if composition else brand,
                    'side_effects': side_effects,
                    'uses': uses,
                    'is_brand': True,
                    'source': 'Rituraj/ShudhanshuDB'
                }
                self._add_to_map(brand, entry)
                count += 1
            print(f"Loaded {count} drugs from {filename}")

    def _load_apkaayush(self, path, filename):
        with open(path, mode='r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                brand = row.get('Medicine Name', '').strip()
                if not brand:
                    brand = row.get('Product Name', '').strip()
                if not brand: continue
                
                composition = row.get('Composition', '').strip()
                
                entry = {
                    'brand_name': brand,
                    'generic_name': composition if composition else brand,
                    'is_brand': True,
                    'source': 'ApkaayushDB'
                }
                self._add_to_map(brand, entry)
                count += 1
            print(f"Loaded {count} drugs from {filename}")
            
    def _load_ankushpoddar(self, path, filename):
        with open(path, mode='r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                brand = row.get('name', '').strip()
                if not brand: continue
                
                uses = ",".join([row.get(f'use{i}', '') for i in range(5) if row.get(f'use{i}')])
                side_effects = ",".join([row.get(f'sideEffect{i}', '') for i in range(10) if row.get(f'sideEffect{i}')])

                entry = self.drug_map.get(brand.lower(), {})
                if not entry:
                    entry = {
                        'brand_name': brand,
                        'generic_name': brand, 
                        'source': 'AnkushPoddarDB'
                    }
                
                if uses: entry['uses'] = uses
                if side_effects: entry['side_effects'] = side_effects
                
                self._add_to_map(brand, entry)
                count += 1
            print(f"Loaded {count} drugs from {filename}")

    def _load_generic_csv(self, path, filename):
        pass

    def resolve_drug_name(self, query):
        """
        Attempts to resolve a raw drug name (e.g. from OCR) to a canonical Generic Name.
        Returns (generic_name, confidence_level)
        """
        if not self.loaded:
            self.load_data()
            
        q = query.strip().lower()
        if not q: return query, 0
        
        # 1. Exact match
        if q in self.drug_map:
            return self.drug_map[q]['generic_name'], 100
            
        # 2. Prefix Match (Fast)
        # Check if 'q' is a prefix for known brands (e.g. q="augmentin" -> "augmentin 625")
        # Use our prefix_map which indexes by first word
        first_word = q.split()[0]
        if first_word in self.prefix_map:
            candidates = self.prefix_map[first_word]
            # Simple heuristic: find one that starts with q
            matches = [c for c in candidates if c.startswith(q)]
            if matches:
                # Sort by length? Shortest might be the 'parent' brand which is usually safer, 
                # OR longest if we want specific?
                # Actually, usually if we just say "Augmentin", any "Augmentin X" is likely same generic.
                # Let's pick the shortest one that is >= len(q)
                matches.sort(key=len)
                best = matches[0]
                return self.drug_map[best]['generic_name'], 90 

        # 3. Fuzzy match (Fallback)
        if HAS_FUZZY:
            # Only fuzzy search against candidates sharing first letter/word to be fast
            candidates = self.prefix_map.get(first_word, [])
            if not candidates:
                 # Try first char fallback
                 pass 
            
            if candidates:
                match, score = process.extractOne(q, candidates)
                if score > 85:
                    return self.drug_map[match]['generic_name'], int(score) # Return fuzzy score directly (0-100)
        
        return query, 0
        
    def get_drug_info(self, query):
        """
        Returns the full info dict for a drug if found.
        """
        if not self.loaded: self.load_data()
        q = query.strip().lower()
        
        # Try finding key via resolve login first?
        if q in self.drug_map:
            return self.drug_map[q]
            
        # Try resolve
        n, c = self.resolve_drug_name(q)
        # This returns generic name. We want the info object.
        # Check if we can find the info object for that generic name?
        # Not easily.
        # But wait, resolve returns generic name string.
        # Use resolve logic to find the *Key* first.
        
        first_word = q.split()[0]
        if first_word in self.prefix_map:
            candidates = self.prefix_map[first_word]
            matches = [c for c in candidates if c.startswith(q)]
            if matches:
                matches.sort(key=len)
                return self.drug_map[matches[0]]
                
                return self.drug_map[matches[0]]
                
        return None

    def get_drug_details_by_generic(self, generic_name):
        """
        Searches the DB for any entry matching this generic name to retrieve side effects and uses.
        Returns a dict of aggregated info.
        """
        if not self.loaded: self.load_data()
        gn = generic_name.lower().strip()
        
        info = {'uses': set(), 'side_effects': set(), 'brands': set()}
        found = False
        
        # This implementation scans the whole map. For large DBs, an index is better.
        # But our DB is memory-based dict, so iterating ~20k items is acceptable for now.
        for key, entry in self.drug_map.items():
            if entry.get('generic_name', '').lower() == gn:
                found = True
                if 'uses' in entry and entry['uses']:
                    info['uses'].add(entry['uses'])
                if 'side_effects' in entry and entry['side_effects']:
                    info['side_effects'].add(entry['side_effects'])
                if 'brand_name' in entry:
                    info['brands'].add(entry['brand_name'])
                    
        if found:
            return {
                'uses': "; ".join(list(info['uses'])[:3]), # Limit to 3 distinct descriptions
                'side_effects': "; ".join(list(info['side_effects'])[:3]),
                'brands_sample': ", ".join(list(info['brands'])[:5])
            }
        return None

# Global instance
db = LocalDrugDB()
