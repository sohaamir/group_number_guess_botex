# test_connection.py
import requests

def test_otree_connection():
    print("Testing oTree connection...")
    try:
        # Try basic connection
        r = requests.get('http://localhost:8000')
        print(f"Connection to main page: {'Success' if r.status_code == 200 else 'Failed'} (Status: {r.status_code})")
        
        # Try API endpoint with REST key
        rest_key = 'otree_rest_F7Xu2pKm9bLz3vQd8TsAj5gW4eHnR6yE'
        r_api = requests.get(
            'http://localhost:8000/api/otree_version', 
            headers={'otree-rest-key': rest_key}
        )
        print(f"Connection to API: {'Success' if r_api.status_code == 200 else 'Failed'} (Status: {r_api.status_code})")
        if r_api.status_code == 200:
            print(f"API Response: {r_api.json()}")
        else:
            print(f"API Error: {r_api.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_otree_connection()
    