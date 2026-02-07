"""
Backend API Tests for Payment and Charity Features
Tests: Charities, Payment Packages, Checkout Sessions, Photo Submission
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_CONTEST_ID = "7f4dde52-93f6-4bbd-8382-a1c587e34b41"


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestCharitiesAPI:
    """Tests for /api/charities endpoint"""
    
    def test_get_charities_returns_200(self, api_client):
        """GET /api/charities should return 200"""
        response = api_client.get(f"{BASE_URL}/api/charities")
        assert response.status_code == 200
    
    def test_get_charities_returns_list(self, api_client):
        """GET /api/charities should return charities list"""
        response = api_client.get(f"{BASE_URL}/api/charities")
        data = response.json()
        
        assert "charities" in data
        assert isinstance(data["charities"], list)
        assert len(data["charities"]) == 5  # 5 charities defined
    
    def test_charities_have_required_fields(self, api_client):
        """Each charity should have id, name, description"""
        response = api_client.get(f"{BASE_URL}/api/charities")
        data = response.json()
        
        for charity in data["charities"]:
            assert "id" in charity
            assert "name" in charity
            assert "description" in charity
            assert "total_raised" in charity
            assert "donation_count" in charity
    
    def test_charities_totals_returned(self, api_client):
        """Response should include total_raised and total_donations"""
        response = api_client.get(f"{BASE_URL}/api/charities")
        data = response.json()
        
        assert "total_raised" in data
        assert "total_donations" in data
        assert isinstance(data["total_raised"], (int, float))
        assert isinstance(data["total_donations"], int)


class TestPaymentPackagesAPI:
    """Tests for /api/payments/packages endpoint"""
    
    def test_get_packages_returns_200(self, api_client):
        """GET /api/payments/packages should return 200"""
        response = api_client.get(f"{BASE_URL}/api/payments/packages")
        assert response.status_code == 200
    
    def test_packages_structure(self, api_client):
        """Packages should have free, standard, premium"""
        response = api_client.get(f"{BASE_URL}/api/payments/packages")
        data = response.json()
        
        assert "packages" in data
        packages = data["packages"]
        
        assert "free" in packages
        assert "standard" in packages
        assert "premium" in packages
    
    def test_package_amounts(self, api_client):
        """Package amounts should be correct"""
        response = api_client.get(f"{BASE_URL}/api/payments/packages")
        packages = response.json()["packages"]
        
        assert packages["free"]["amount"] == 0
        assert packages["standard"]["amount"] == 5
        assert packages["premium"]["amount"] == 10


class TestCreateCheckoutAPI:
    """Tests for POST /api/payments/create-checkout endpoint"""
    
    def test_free_entry_returns_success(self, api_client):
        """Free entry should return success without Stripe redirect"""
        payload = {
            "contest_id": TEST_CONTEST_ID,
            "payer_name": "Test Free User",
            "payer_email": f"testfree_{uuid.uuid4().hex[:8]}@example.com",
            "package_id": "free",
            "charity_id": "wildlife",
            "charity_percentage": 10,
            "origin_url": BASE_URL
        }
        
        response = api_client.post(f"{BASE_URL}/api/payments/create-checkout", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["is_free"] is True
        assert "transaction_id" in data
    
    def test_paid_entry_returns_checkout_url(self, api_client):
        """Paid entry should return Stripe checkout URL"""
        payload = {
            "contest_id": TEST_CONTEST_ID,
            "payer_name": "Test Paid User",
            "payer_email": f"testpaid_{uuid.uuid4().hex[:8]}@example.com",
            "package_id": "standard",
            "charity_id": "ocean",
            "charity_percentage": 20,
            "origin_url": BASE_URL
        }
        
        response = api_client.post(f"{BASE_URL}/api/payments/create-checkout", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "checkout_url" in data
        assert "stripe.com" in data["checkout_url"]
        assert data["amount"] == 5.0
        assert data["charity_amount"] == 1.0  # 20% of $5
    
    def test_premium_entry_charity_calculation(self, api_client):
        """Premium entry charity amount should be calculated correctly"""
        payload = {
            "contest_id": TEST_CONTEST_ID,
            "payer_name": "Test Premium User",
            "payer_email": f"testpremium_{uuid.uuid4().hex[:8]}@example.com",
            "package_id": "premium",
            "charity_id": "habitat",
            "charity_percentage": 30,
            "origin_url": BASE_URL
        }
        
        response = api_client.post(f"{BASE_URL}/api/payments/create-checkout", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["amount"] == 10.0
        assert data["charity_amount"] == 3.0  # 30% of $10
    
    def test_invalid_contest_returns_404(self, api_client):
        """Invalid contest ID should return 404"""
        payload = {
            "contest_id": "invalid-contest-id",
            "payer_name": "Test User",
            "payer_email": "test@example.com",
            "package_id": "free",
            "origin_url": BASE_URL
        }
        
        response = api_client.post(f"{BASE_URL}/api/payments/create-checkout", json=payload)
        assert response.status_code == 404
    
    def test_invalid_package_returns_400(self, api_client):
        """Invalid package ID should return 400"""
        payload = {
            "contest_id": TEST_CONTEST_ID,
            "payer_name": "Test User",
            "payer_email": "test@example.com",
            "package_id": "invalid_package",
            "origin_url": BASE_URL
        }
        
        response = api_client.post(f"{BASE_URL}/api/payments/create-checkout", json=payload)
        assert response.status_code == 400


class TestContestsAPI:
    """Tests for contest-related endpoints"""
    
    def test_list_contests_returns_200(self, api_client):
        """GET /api/contests should return 200"""
        response = api_client.get(f"{BASE_URL}/api/contests")
        assert response.status_code == 200
    
    def test_list_contests_returns_array(self, api_client):
        """GET /api/contests should return contests array"""
        response = api_client.get(f"{BASE_URL}/api/contests")
        data = response.json()
        
        assert "contests" in data
        assert isinstance(data["contests"], list)
    
    def test_get_contest_detail(self, api_client):
        """GET /api/contests/{id} should return contest details"""
        response = api_client.get(f"{BASE_URL}/api/contests/{TEST_CONTEST_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == TEST_CONTEST_ID
        assert "title" in data
        assert "theme" in data
        assert "status" in data
        assert "photo_count" in data
    
    def test_get_contest_leaderboard(self, api_client):
        """GET /api/contests/{id}/leaderboard should return leaderboard"""
        response = api_client.get(f"{BASE_URL}/api/contests/{TEST_CONTEST_ID}/leaderboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)


class TestPhotosAPI:
    """Tests for photo submission endpoint"""
    
    def test_submit_photo_returns_200(self, api_client):
        """POST /api/photos should create photo entry"""
        payload = {
            "contest_id": TEST_CONTEST_ID,
            "photographer_name": f"TEST_Photographer_{uuid.uuid4().hex[:6]}",
            "photographer_email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "photo_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4",
            "title": f"TEST_Photo_{uuid.uuid4().hex[:6]}",
            "description": "Test photo submission"
        }
        
        response = api_client.post(f"{BASE_URL}/api/photos", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["contest_id"] == TEST_CONTEST_ID
        assert data["status"] == "pending"
    
    def test_list_photos_by_contest(self, api_client):
        """GET /api/photos?contest_id={id} should return photos"""
        response = api_client.get(f"{BASE_URL}/api/photos?contest_id={TEST_CONTEST_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert "photos" in data
        assert isinstance(data["photos"], list)
    
    def test_photo_has_required_fields(self, api_client):
        """Photos should have required fields"""
        response = api_client.get(f"{BASE_URL}/api/photos?contest_id={TEST_CONTEST_ID}")
        data = response.json()
        
        if data["photos"]:
            photo = data["photos"][0]
            assert "id" in photo
            assert "title" in photo
            assert "photographer_name" in photo
            assert "photo_url" in photo
            assert "status" in photo


class TestPaymentStatusAPI:
    """Tests for payment status endpoint"""
    
    def test_invalid_session_returns_404(self, api_client):
        """GET /api/payments/status/{invalid_id} should return 404"""
        response = api_client.get(f"{BASE_URL}/api/payments/status/invalid-session-id")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
