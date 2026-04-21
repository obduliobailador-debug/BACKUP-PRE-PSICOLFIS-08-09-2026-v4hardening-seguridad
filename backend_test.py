import requests
import sys
import json
from datetime import datetime

class PSICOLFISAPITester:
    def __init__(self, base_url="https://landing-link-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

            print(f"   Response Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout")
            return False, {}
        except requests.exceptions.ConnectionError:
            print(f"❌ Failed - Connection error")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_checkout_session_iris(self):
        """Test creating checkout session for IRIS agent"""
        data = {
            "agent_id": "iris",
            "origin_url": "https://landing-link-fix.preview.emergentagent.com"
        }
        return self.run_test("Checkout Session - IRIS", "POST", "checkout/session", 200, data)

    def test_checkout_session_alex(self):
        """Test creating checkout session for ALEX agent"""
        data = {
            "agent_id": "alex", 
            "origin_url": "https://landing-link-fix.preview.emergentagent.com"
        }
        return self.run_test("Checkout Session - ALEX", "POST", "checkout/session", 200, data)

    def test_checkout_session_umbral(self):
        """Test creating checkout session for UMBRAL agent"""
        data = {
            "agent_id": "umbral",
            "origin_url": "https://landing-link-fix.preview.emergentagent.com"
        }
        return self.run_test("Checkout Session - UMBRAL", "POST", "checkout/session", 200, data)

    def test_invalid_agent(self):
        """Test creating checkout session with invalid agent"""
        data = {
            "agent_id": "invalid_agent",
            "origin_url": "https://landing-link-fix.preview.emergentagent.com"
        }
        return self.run_test("Invalid Agent ID", "POST", "checkout/session", 400, data)

    def test_status_endpoint_create(self):
        """Test creating a status check"""
        data = {
            "client_name": f"test_client_{datetime.now().strftime('%H%M%S')}"
        }
        return self.run_test("Create Status Check", "POST", "status", 200, data)

    def test_status_endpoint_get(self):
        """Test getting status checks"""
        return self.run_test("Get Status Checks", "GET", "status", 200)

def main():
    print("🚀 Starting PSICOLFIS API Tests...")
    print("=" * 50)
    
    tester = PSICOLFISAPITester()
    
    # Test basic connectivity
    print("\n📡 Testing Basic Connectivity...")
    tester.test_root_endpoint()
    
    # Test status endpoints
    print("\n📊 Testing Status Endpoints...")
    tester.test_status_endpoint_create()
    tester.test_status_endpoint_get()
    
    # Test checkout endpoints for all agents
    print("\n💳 Testing Checkout Endpoints...")
    tester.test_checkout_session_iris()
    tester.test_checkout_session_alex()
    tester.test_checkout_session_umbral()
    
    # Test error handling
    print("\n🚫 Testing Error Handling...")
    tester.test_invalid_agent()
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Backend is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the backend implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())