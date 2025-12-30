import requests

def test_search(location_name):
    print(f"Testing search for: {location_name}")
    geo_url = "https://nominatim.openstreetmap.org/search"
    headers = {'User-Agent': 'RxShieldApp/1.0'}
    
    # Query sent exactly as is
    query = location_name
    
    # Remove countrycodes to test raw
    params = {
        'q': query, 
        'format': 'json', 
        'limit': 5
    }
    
    try:
        resp = requests.get(geo_url, params=params, headers=headers)
        data = resp.json()
        
        print(f"Query sent: {query}")
        print("Results:")
        for item in data:
            print(f"- {item['display_name']} (Lat: {item['lat']}, Lon: {item['lon']})")
            
        if not data:
            print("No results found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("--- Test 1: Bangalore (Connectivity Check) ---")
    test_search("Bangalore") 
    print("\n--- Test 2: Madanayakanahalli (Raw) ---")
    test_search("Madanayakanahalli")
