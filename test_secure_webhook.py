#!/usr/bin/env python3
"""
Test script for the secure Jira webhook server

This script tests various aspects of the secure webhook server including
SSL functionality, authentication, and endpoint responses.
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any

# Disable SSL warnings for self-signed certificates during testing
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SecureWebhookTester:
    def __init__(self, base_url: str = "https://localhost:5000", webhook_secret: str = None):
        self.base_url = base_url.rstrip('/')
        self.webhook_secret = webhook_secret
        self.results = []
    
    def log_result(self, test_name: str, success: bool, message: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_ssl_connection(self) -> bool:
        """Test basic SSL connection"""
        try:
            response = requests.get(f"{self.base_url}/health", verify=False, timeout=10)
            if response.status_code == 200:
                data = response.json()
                is_secure = data.get('secure', False)
                if is_secure:
                    self.log_result("SSL Connection", True, f"Server is running securely (version {data.get('version', 'unknown')})")
                    return True
                else:
                    self.log_result("SSL Connection", False, "Server is not in secure mode")
                    return False
            else:
                self.log_result("SSL Connection", False, f"Health check failed with status {response.status_code}")
                return False
        except requests.exceptions.SSLError as e:
            self.log_result("SSL Connection", False, f"SSL error: {str(e)}")
            return False
        except requests.exceptions.ConnectionError as e:
            self.log_result("SSL Connection", False, f"Connection error: {str(e)}")
            return False
        except Exception as e:
            self.log_result("SSL Connection", False, f"Unexpected error: {str(e)}")
            return False
    
    def test_health_endpoint(self) -> bool:
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", verify=False, timeout=10)
            if response.status_code == 200:
                data = response.json()
                required_fields = ['status', 'timestamp', 'jira_connected', 'secure']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_result("Health Endpoint", True, f"All required fields present. Jira connected: {data['jira_connected']}")
                    return True
                else:
                    self.log_result("Health Endpoint", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_result("Health Endpoint", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Health Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_webhook_without_auth(self) -> bool:
        """Test webhook endpoint without authentication (should fail if auth is enabled)"""
        try:
            test_payload = {
                "webhookEvent": "jira:issue_created",
                "issue": {"key": "TEST-1"}
            }
            
            response = requests.post(
                f"{self.base_url}/jira-webhook",
                json=test_payload,
                verify=False,
                timeout=10
            )
            
            if self.webhook_secret:
                # If secret is configured, request should fail
                if response.status_code == 401:
                    self.log_result("Webhook Auth Required", True, "Properly rejected unauthenticated request")
                    return True
                else:
                    self.log_result("Webhook Auth Required", False, f"Expected 401, got {response.status_code}")
                    return False
            else:
                # If no secret configured, request should succeed
                if response.status_code in [200, 400]:  # 400 is OK for test payload
                    self.log_result("Webhook No Auth", True, "Request processed (no auth configured)")
                    return True
                else:
                    self.log_result("Webhook No Auth", False, f"Unexpected status: {response.status_code}")
                    return False
        except Exception as e:
            self.log_result("Webhook Auth Test", False, f"Error: {str(e)}")
            return False
    
    def test_webhook_with_auth(self) -> bool:
        """Test webhook endpoint with authentication"""
        if not self.webhook_secret:
            self.log_result("Webhook With Auth", True, "Skipped (no webhook secret configured)")
            return True
        
        try:
            test_payload = {
                "webhookEvent": "jira:issue_created", 
                "issue": {"key": "TEST-1"}
            }
            
            headers = {
                "Authorization": f"Bearer {self.webhook_secret}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.base_url}/jira-webhook",
                json=test_payload,
                headers=headers,
                verify=False,
                timeout=10
            )
            
            if response.status_code in [200, 400]:  # 400 is OK for test payload
                self.log_result("Webhook With Auth", True, f"Authenticated request accepted (status: {response.status_code})")
                return True
            else:
                self.log_result("Webhook With Auth", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_result("Webhook With Auth", False, f"Error: {str(e)}")
            return False
    
    def test_test_endpoint(self) -> bool:
        """Test the manual test endpoint"""
        try:
            headers = {}
            if self.webhook_secret:
                headers["Authorization"] = f"Bearer {self.webhook_secret}"
            
            response = requests.post(
                f"{self.base_url}/test-ticket/TEST-123",
                headers=headers,
                verify=False,
                timeout=10
            )
            
            if response.status_code in [200, 500]:  # 500 is OK if Jira not configured
                data = response.json()
                if response.status_code == 200:
                    self.log_result("Test Endpoint", True, f"Test endpoint working: {data.get('message', 'No message')}")
                else:
                    self.log_result("Test Endpoint", True, f"Test endpoint accessible (Jira not configured): {data.get('error', 'No error')}")
                return True
            else:
                self.log_result("Test Endpoint", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Test Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_invalid_endpoints(self) -> bool:
        """Test that invalid endpoints return 404"""
        try:
            response = requests.get(f"{self.base_url}/invalid-endpoint", verify=False, timeout=10)
            if response.status_code == 404:
                self.log_result("Invalid Endpoints", True, "404 returned for invalid endpoint")
                return True
            else:
                self.log_result("Invalid Endpoints", False, f"Expected 404, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Invalid Endpoints", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests and return overall success"""
        print(f"🧪 Testing Secure Webhook Server: {self.base_url}")
        print(f"🔐 Webhook Secret: {'Configured' if self.webhook_secret else 'Not configured'}")
        print("=" * 60)
        
        tests = [
            self.test_ssl_connection,
            self.test_health_endpoint,
            self.test_webhook_without_auth,
            self.test_webhook_with_auth,
            self.test_test_endpoint,
            self.test_invalid_endpoints
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            time.sleep(0.5)  # Brief pause between tests
        
        print("=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Your secure webhook server is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Please review the issues above.")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a detailed test report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'server_url': self.base_url,
            'webhook_secret_configured': bool(self.webhook_secret),
            'tests': self.results,
            'summary': {
                'total_tests': len(self.results),
                'passed': sum(1 for r in self.results if r['success']),
                'failed': sum(1 for r in self.results if not r['success'])
            }
        }

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the secure Jira webhook server")
    parser.add_argument('--url', default='https://localhost:5000', help='Base URL of the webhook server')
    parser.add_argument('--secret', help='Webhook secret for authentication testing')
    parser.add_argument('--report', help='Save detailed report to JSON file')
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = SecureWebhookTester(args.url, args.secret)
    
    # Run tests
    success = tester.run_all_tests()
    
    # Generate report if requested
    if args.report:
        report = tester.generate_report()
        with open(args.report, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📄 Detailed report saved to: {args.report}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 