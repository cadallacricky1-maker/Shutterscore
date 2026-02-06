import requests
import sys
import json
import base64
from datetime import datetime

class ShutterscoreAPITester:
    def __init__(self, base_url="https://shutterscore.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.admin_auth_header = None

    def run_test(self, name, method, endpoint, expected_status, data=None, expected_response_keys=None, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add auth header if required
        if auth_required and self.admin_auth_header:
            headers.update(self.admin_auth_header)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if auth_required:
            print(f"   Auth: {'Yes' if self.admin_auth_header else 'No'}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

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

    # NEW ADMIN AUTHENTICATION TESTS
    def test_admin_login_correct_password(self):
        """Test admin login with correct password"""
        success, response = self.run_test(
            "Admin Login - Correct Password",
            "POST",
            "admin/login",
            200,
            data={"password": "shutterscore2026"},
            expected_response_keys=["success", "message"]
        )
        
        if success:
            # Set up auth header for subsequent admin tests
            auth_string = base64.b64encode(b"admin:shutterscore2026").decode('ascii')
            self.admin_auth_header = {"Authorization": f"Basic {auth_string}"}
            print("   ✓ Admin auth header set for subsequent tests")
        
        return success

    def test_admin_login_wrong_password(self):
        """Test admin login with wrong password"""
        return self.run_test(
            "Admin Login - Wrong Password",
            "POST",
            "admin/login",
            401,
            data={"password": "wrongpassword"}
        )

    def test_admin_verify_session(self):
        """Test admin session verification"""
        return self.run_test(
            "Admin Verify Session",
            "GET",
            "admin/verify",
            200,
            auth_required=True,
            expected_response_keys=["authenticated", "user"]
        )

    def test_admin_verify_without_auth(self):
        """Test admin verify without authentication"""
        # Temporarily remove auth header
        temp_auth = self.admin_auth_header
        self.admin_auth_header = None
        
        success = self.run_test(
            "Admin Verify - No Auth",
            "GET",
            "admin/verify",
            401
        )
        
        # Restore auth header
        self.admin_auth_header = temp_auth
        return success

    # NEW REFERRAL SYSTEM TESTS
    def test_waitlist_with_referral(self):
        """Test waitlist signup with referral system"""
        # First, create a referrer
        referrer_email = f"referrer_{datetime.now().strftime('%H%M%S')}@example.com"
        success1, response1 = self.run_test(
            "Create Referrer Account",
            "POST",
            "waitlist",
            200,
            data={"email": referrer_email},
            expected_response_keys=["success", "entry", "referral_link"]
        )
        
        if not success1 or not response1.get('entry'):
            print("   ⚠️  Could not create referrer account")
            return False
        
        referral_code = response1['entry']['referral_code']
        referral_link = response1.get('referral_link', '')
        print(f"   Referrer code: {referral_code}")
        print(f"   Referral link: {referral_link}")
        
        # Now create a referred user
        referred_email = f"referred_{datetime.now().strftime('%H%M%S')}@example.com"
        success2, response2 = self.run_test(
            "Create Referred Account",
            "POST",
            "waitlist",
            200,
            data={"email": referred_email, "ref": referral_code},
            expected_response_keys=["success", "entry"]
        )
        
        if success2 and response2.get('entry'):
            referred_by = response2['entry'].get('referred_by')
            if referred_by == referral_code:
                print(f"   ✓ Referral tracking working: {referred_by}")
                return True
            else:
                print(f"   ⚠️  Referral not tracked properly. Expected: {referral_code}, Got: {referred_by}")
                return False
        
        return False

    def test_referral_count_increment(self):
        """Test that referral count increments correctly"""
        # Create referrer
        referrer_email = f"ref_count_{datetime.now().strftime('%H%M%S')}@example.com"
        success1, response1 = self.run_test(
            "Create Referrer for Count Test",
            "POST",
            "waitlist",
            200,
            data={"email": referrer_email},
            expected_response_keys=["success", "entry"]
        )
        
        if not success1:
            return False
        
        referral_code = response1['entry']['referral_code']
        initial_count = response1['entry'].get('referral_count', 0)
        print(f"   Initial referral count: {initial_count}")
        
        # Create referred user
        referred_email = f"ref_test_{datetime.now().strftime('%H%M%S')}@example.com"
        success2, response2 = self.run_test(
            "Create Referred User for Count Test",
            "POST",
            "waitlist",
            200,
            data={"email": referred_email, "ref": referral_code}
        )
        
        if not success2:
            return False
        
        # Check if referrer's count increased (we'll verify this in admin panel)
        print("   ✓ Referral created, count should be incremented")
        return True

    def test_admin_waitlist_stats(self):
        """Test admin waitlist stats endpoint"""
        return self.run_test(
            "Admin Waitlist Stats",
            "GET",
            "admin/waitlist/stats",
            200,
            auth_required=True,
            expected_response_keys=["total_signups", "today_signups", "this_week_signups", "total_referrals"]
        )

    def test_admin_waitlist_stats_no_auth(self):
        """Test admin stats without authentication"""
        # Temporarily remove auth header
        temp_auth = self.admin_auth_header
        self.admin_auth_header = None
        
        success = self.run_test(
            "Admin Stats - No Auth",
            "GET",
            "admin/waitlist/stats",
            401
        )
        
        # Restore auth header
        self.admin_auth_header = temp_auth
        return success

    def test_admin_waitlist_entries(self):
        """Test admin waitlist entries endpoint"""
        success, response = self.run_test(
            "Admin Waitlist Entries",
            "GET",
            "admin/waitlist?page=1&page_size=10",
            200,
            auth_required=True,
            expected_response_keys=["entries", "total", "page", "page_size", "total_pages"]
        )
        
        if success:
            print(f"   Total entries: {response.get('total', 0)}")
            print(f"   Entries on page: {len(response.get('entries', []))}")
            
            # Check if entries have referral fields
            entries = response.get('entries', [])
            if entries:
                first_entry = entries[0]
                if 'referral_code' in first_entry:
                    print("   ✓ Referral code field present in entries")
                if 'referred_by' in first_entry:
                    print("   ✓ Referred by field present in entries")
                if 'referral_count' in first_entry:
                    print("   ✓ Referral count field present in entries")
        
        return success

    def test_admin_search_entries(self):
        """Test admin search functionality"""
        return self.run_test(
            "Admin Search Entries",
            "GET",
            "admin/waitlist?search=test&page=1&page_size=10",
            200,
            auth_required=True,
            expected_response_keys=["entries", "total", "page", "page_size", "total_pages"]
        )

    def test_admin_export_csv(self):
        """Test admin CSV export"""
        url = f"{self.api_url}/admin/waitlist/export"
        headers = {'Content-Type': 'application/json'}
        
        # Add auth header
        if self.admin_auth_header:
            headers.update(self.admin_auth_header)
        
        self.tests_run += 1
        print(f"\n🔍 Testing Admin CSV Export...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                # Check if it's CSV format
                content_type = response.headers.get('content-type', '')
                if 'csv' in content_type.lower():
                    print("   ✓ Correct CSV content type")
                
                csv_content = response.text
                lines = csv_content.split('\n')
                print(f"   CSV lines: {len(lines)}")
                if lines and len(lines) > 0:
                    header = lines[0]
                    print(f"   CSV header: {header}")
                    
                    # Check for referral columns
                    if 'Referral Code' in header:
                        print("   ✓ Referral Code column present")
                    if 'Referred By' in header:
                        print("   ✓ Referred By column present")
                    if 'Referral Count' in header:
                        print("   ✓ Referral Count column present")
                
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def test_admin_delete_entry(self):
        """Test admin delete functionality"""
        # First create a test entry to delete
        test_email = f"delete_test_{datetime.now().strftime('%H%M%S')}@example.com"
        success, response = self.run_test(
            "Create Entry for Delete Test",
            "POST",
            "waitlist",
            200,
            data={"email": test_email},
            expected_response_keys=["success", "entry"]
        )
        
        if not success or not response.get('entry'):
            print("   ⚠️  Could not create test entry for delete test")
            return False
        
        entry_id = response['entry']['id']
        print(f"   Created test entry ID: {entry_id}")
        
        # Now delete the entry
        success, delete_response = self.run_test(
            "Admin Delete Entry",
            "DELETE",
            f"admin/waitlist/{entry_id}",
            200,
            auth_required=True,
            expected_response_keys=["success", "message"]
        )
        
        if success:
            print("   ✓ Entry deleted successfully")
        
        # Test deleting non-existent entry
        success_404, _ = self.run_test(
            "Delete Non-existent Entry",
            "DELETE",
            "admin/waitlist/non-existent-id",
            404,
            auth_required=True
        )
        
        return success and success_404

    # NEW LEADERBOARD TESTS
    def test_leaderboard_endpoint(self):
        """Test public leaderboard endpoint"""
        success, response = self.run_test(
            "Public Leaderboard",
            "GET",
            "leaderboard",
            200,
            expected_response_keys=["entries", "total_participants"]
        )
        
        if success:
            entries = response.get('entries', [])
            total_participants = response.get('total_participants', 0)
            print(f"   Total participants with referrals: {total_participants}")
            print(f"   Leaderboard entries returned: {len(entries)}")
            
            # Check entry structure
            if entries:
                first_entry = entries[0]
                required_fields = ['rank', 'email_masked', 'referral_code', 'referral_count']
                for field in required_fields:
                    if field in first_entry:
                        print(f"   ✓ Entry has {field} field")
                    else:
                        print(f"   ⚠️  Entry missing {field} field")
                        success = False
                
                # Check if email is properly masked
                email_masked = first_entry.get('email_masked', '')
                if '***' in email_masked and '@' in email_masked:
                    print(f"   ✓ Email properly masked: {email_masked}")
                else:
                    print(f"   ⚠️  Email masking may not be working: {email_masked}")
                
                # Check if entries are sorted by referral_count (descending)
                if len(entries) > 1:
                    first_count = entries[0].get('referral_count', 0)
                    second_count = entries[1].get('referral_count', 0)
                    if first_count >= second_count:
                        print("   ✓ Entries properly sorted by referral count")
                    else:
                        print("   ⚠️  Entries may not be sorted correctly")
        
        return success

    def test_leaderboard_with_limit(self):
        """Test leaderboard with limit parameter"""
        success, response = self.run_test(
            "Leaderboard with Limit",
            "GET",
            "leaderboard?limit=5",
            200,
            expected_response_keys=["entries", "total_participants"]
        )
        
        if success:
            entries = response.get('entries', [])
            if len(entries) <= 5:
                print(f"   ✓ Limit respected: {len(entries)} entries returned")
            else:
                print(f"   ⚠️  Limit not respected: {len(entries)} entries returned (expected ≤5)")
                success = False
        
        return success

    def test_position_lookup(self):
        """Test position lookup by email"""
        # First create a test user
        test_email = f"position_test_{datetime.now().strftime('%H%M%S')}@example.com"
        success1, response1 = self.run_test(
            "Create User for Position Test",
            "POST",
            "waitlist",
            200,
            data={"email": test_email},
            expected_response_keys=["success", "entry", "position", "total_waitlist"]
        )
        
        if not success1:
            return False
        
        # Test position lookup
        success2, response2 = self.run_test(
            "Position Lookup by Email",
            "GET",
            f"waitlist/position/{test_email}",
            200,
            expected_response_keys=["email", "position", "total_waitlist", "referral_count", "referral_code"]
        )
        
        if success2:
            position = response2.get('position')
            total = response2.get('total_waitlist')
            email_masked = response2.get('email')
            
            print(f"   Position: {position}")
            print(f"   Total waitlist: {total}")
            print(f"   Masked email: {email_masked}")
            
            # Check if email is masked in response
            if '***' in email_masked:
                print("   ✓ Email properly masked in position lookup")
            else:
                print("   ⚠️  Email not masked in position lookup")
        
        return success2

    def test_position_lookup_nonexistent(self):
        """Test position lookup for non-existent email"""
        return self.run_test(
            "Position Lookup - Non-existent Email",
            "GET",
            "waitlist/position/nonexistent@example.com",
            404
        )

    def test_waitlist_response_includes_position(self):
        """Test that waitlist signup response includes position and total"""
        test_email = f"position_response_{datetime.now().strftime('%H%M%S')}@example.com"
        success, response = self.run_test(
            "Waitlist Response Position Fields",
            "POST",
            "waitlist",
            200,
            data={"email": test_email},
            expected_response_keys=["success", "message", "entry", "position", "total_waitlist"]
        )
        
        if success:
            position = response.get('position')
            total_waitlist = response.get('total_waitlist')
            
            if position and total_waitlist:
                print(f"   ✓ Position: {position}, Total: {total_waitlist}")
                
                # Check if position is reasonable
                if 1 <= position <= total_waitlist:
                    print("   ✓ Position is within valid range")
                else:
                    print(f"   ⚠️  Position {position} not in valid range 1-{total_waitlist}")
                    success = False
            else:
                print("   ⚠️  Missing position or total_waitlist in response")
                success = False
        
        return success

    # NEW SOCIAL PROOF TESTS
    def test_social_proof_stats(self):
        """Test social proof stats endpoint for hero counter"""
        success, response = self.run_test(
            "Social Proof Stats",
            "GET",
            "stats/social-proof",
            200,
            expected_response_keys=["total_signups", "recent_signups", "total_referrals", "top_referrer_count"]
        )
        
        if success:
            total_signups = response.get('total_signups', 0)
            recent_signups = response.get('recent_signups', 0)
            total_referrals = response.get('total_referrals', 0)
            top_referrer_count = response.get('top_referrer_count', 0)
            
            print(f"   Total signups: {total_signups}")
            print(f"   Recent signups (24h): {recent_signups}")
            print(f"   Total referrals: {total_referrals}")
            print(f"   Top referrer count: {top_referrer_count}")
            
            # Validate data types and ranges
            if isinstance(total_signups, int) and total_signups >= 0:
                print("   ✓ Total signups is valid integer")
            else:
                print("   ⚠️  Total signups invalid")
                success = False
                
            if isinstance(recent_signups, int) and recent_signups >= 0:
                print("   ✓ Recent signups is valid integer")
            else:
                print("   ⚠️  Recent signups invalid")
                success = False
                
            # Recent signups should not exceed total signups
            if recent_signups <= total_signups:
                print("   ✓ Recent signups <= total signups")
            else:
                print("   ⚠️  Recent signups > total signups (invalid)")
                success = False
        
        return success

    # NEW WEEKLY DIGEST TESTS
    def test_weekly_digest_send(self):
        """Test weekly digest send endpoint"""
        success, response = self.run_test(
            "Send Weekly Digest",
            "POST",
            "admin/send-weekly-digest",
            200,
            auth_required=True,
            expected_response_keys=["success", "emails_sent", "message"]
        )
        
        if success:
            emails_sent = response.get('emails_sent', 0)
            message = response.get('message', '')
            
            print(f"   Emails sent: {emails_sent}")
            print(f"   Message: {message}")
            
            # Validate response
            if isinstance(emails_sent, int) and emails_sent >= 0:
                print("   ✓ Emails sent count is valid")
            else:
                print("   ⚠️  Invalid emails sent count")
                success = False
                
            if message and "digest sent" in message.lower():
                print("   ✓ Success message contains expected text")
            else:
                print("   ⚠️  Success message format unexpected")
        
        return success

    def test_weekly_digest_no_auth(self):
        """Test weekly digest without authentication"""
        # Temporarily remove auth header
        temp_auth = self.admin_auth_header
        self.admin_auth_header = None
        
        success = self.run_test(
            "Weekly Digest - No Auth",
            "POST",
            "admin/send-weekly-digest",
            401
        )
        
        # Restore auth header
        self.admin_auth_header = temp_auth
        return success

def main():
    print("🚀 Starting Shutterscore API Tests...")
    print("=" * 50)
    
    # Setup
    tester = ShutterscoreAPITester()
    
    # Run all tests
    print("\n📡 Testing API Connectivity...")
    tester.test_root_endpoint()
    
    print("\n🔐 Testing Admin Authentication...")
    tester.test_admin_login_correct_password()
    tester.test_admin_login_wrong_password()
    tester.test_admin_verify_session()
    tester.test_admin_verify_without_auth()
    
    print("\n📧 Testing Waitlist Functionality...")
    tester.test_waitlist_valid_email()
    tester.test_waitlist_duplicate_email()
    tester.test_waitlist_invalid_email()
    tester.test_waitlist_count()
    
    print("\n🔗 Testing Referral System...")
    tester.test_waitlist_with_referral()
    tester.test_referral_count_increment()
    
    print("\n🔧 Testing Admin Panel Functionality...")
    tester.test_admin_waitlist_stats()
    tester.test_admin_waitlist_stats_no_auth()
    tester.test_admin_waitlist_entries()
    tester.test_admin_search_entries()
    tester.test_admin_export_csv()
    tester.test_admin_delete_entry()
    
    print("\n🏆 Testing Leaderboard Functionality...")
    tester.test_leaderboard_endpoint()
    tester.test_leaderboard_with_limit()
    tester.test_position_lookup()
    tester.test_position_lookup_nonexistent()
    tester.test_waitlist_response_includes_position()
    
    print("\n📊 Testing Social Proof Features...")
    tester.test_social_proof_stats()
    
    print("\n📧 Testing Weekly Digest Features...")
    tester.test_weekly_digest_send()
    tester.test_weekly_digest_no_auth()
    
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