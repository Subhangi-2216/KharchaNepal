import requests

def test_cors_headers():
    """Test CORS headers on the API endpoints"""
    base_url = "http://localhost:8000"
    
    # Test endpoints
    endpoints = [
        "/api/expenses",
        "/api/users/me",
        "/api/dashboard/stats"
    ]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        
        # First, send an OPTIONS request to check CORS preflight
        print(f"\n--- Testing OPTIONS request to {endpoint} ---")
        options_response = requests.options(url, headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type"
        })
        
        print(f"Status code: {options_response.status_code}")
        print("Headers:")
        for key, value in options_response.headers.items():
            print(f"  {key}: {value}")
        
        # Then try a GET request
        print(f"\n--- Testing GET request to {endpoint} ---")
        get_response = requests.get(url, headers={"Origin": "http://localhost:8080"})
        
        print(f"Status code: {get_response.status_code}")
        print("Headers:")
        for key, value in get_response.headers.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    test_cors_headers() 