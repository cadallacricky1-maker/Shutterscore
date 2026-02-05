import requests
import sys
import json
from datetime import datetime

class ShutterscoreAPITester:
    def __init__(self, base_url="https://shutterscore.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, expected_response_keys=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                # Check expected response keys if provided
                if expected_response_keys:
                    for key in expected_response_keys:
                        if key in response_data:
                            print(f"   ✓ Found expected key: {key}")
                        else:
                            print(f"   ⚠️  Missing expected key: {key}")
                            success = False
                
                print(f"   Response: {json.dumps(response_data, indent=2)}")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {json.dumps(response_data, indent=2)}")

            self.test_results.append({
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success,
                "response": response_data
            })

            return success, response_data

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results.append({
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": "ERROR",
                "success": False,
                "error": str(e)
            })
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200,
            expected_response_keys=["message"]
        )

    def test_waitlist_valid_email(self):
        """Test waitlist with valid email"""
        test_email = f"test_{datetime.now().strftime('%H%M%S')}@example.com"
        return self.run_test(
            "Waitlist - Valid Email",
            "POST",
            "waitlist",
            200,
            data={"email": test_email},
            expected_response_keys=["success", "message", "entry"]
        )

    def test_waitlist_duplicate_email(self):
        """Test waitlist with duplicate email"""
        test_email = "duplicate@example.com"
        
        # First submission
        success1, response1 = self.run_test(
            "Waitlist - First Submission",
            "POST",
            "waitlist",
            200,
            data={"email": test_email},
            expected_response_keys=["success", "message"]
        )
        
        # Duplicate submission
        success2, response2 = self.run_test(
            "Waitlist - Duplicate Email",
            "POST",
            "waitlist",
            200,
            data={"email": test_email},
            expected_response_keys=["success", "message"]
        )
        
        # Check if duplicate message is returned
        if success2 and "already on the waitlist" in response2.get("message", "").lower():
            print("   ✓ Duplicate email properly handled")
            return True
        else:
            print("   ⚠️  Duplicate email handling may not be working correctly")
            return False

    def test_waitlist_invalid_email(self):
        """Test waitlist with invalid email"""
        invalid_emails = [
            "invalid-email",
            "test@",
            "@example.com",
            "test.example.com",
            ""
        ]
        
        all_passed = True
        for email in invalid_emails:
            success, response = self.run_test(
                f"Waitlist - Invalid Email: '{email}'",
                "POST",
                "waitlist",
                422,
                data={"email": email}
            )
            if not success:
                all_passed = False
        
        return all_passed

    def test_waitlist_count(self):
        """Test waitlist count endpoint"""
        return self.run_test(
            "Waitlist Count",
            "GET",
            "waitlist/count",
            200,
            expected_response_keys=["count"]
        )

def main():
    print("🚀 Starting Shutterscore API Tests...")
    print("=" * 50)
    
    # Setup
    tester = ShutterscoreAPITester()
    
    # Run all tests
    print("\n📡 Testing API Connectivity...")
    tester.test_root_endpoint()
    
    print("\n📧 Testing Waitlist Functionality...")
    tester.test_waitlist_valid_email()
    tester.test_waitlist_duplicate_email()
    tester.test_waitlist_invalid_email()
    tester.test_waitlist_count()
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Check the details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())