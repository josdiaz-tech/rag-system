#!/usr/bin/env python3
"""
Quick test script to verify RAG system is working
Run this after starting the backend server
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health():
    """Test health endpoint"""
    print_section("1. Testing Health Endpoint")
    
    response = requests.get(f"{BASE_URL}/health")
    data = response.json()
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(data, indent=2)}")
    
    return response.status_code == 200

def test_register(email, password):
    """Test user registration"""
    print_section("2. Testing User Registration")
    
    payload = {
        "email": email,
        "password": password,
        "full_name": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=payload)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ User registered successfully!")
        print(f"User ID: {data['id']}")
        print(f"Email: {data['email']}")
        return True
    elif response.status_code == 400 and "already registered" in response.text:
        print("⚠️  User already exists, continuing...")
        return True
    else:
        print(f"❌ Registration failed: {response.text}")
        return False

def test_login(email, password):
    """Test user login and get token"""
    print_section("3. Testing User Login")
    
    payload = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=payload)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        print(f"✅ Login successful!")
        print(f"Token (first 50 chars): {token[:50]}...")
        return token
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def test_upload_document(token, pdf_path):
    """Test document upload"""
    print_section("4. Testing Document Upload")
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF file not found: {pdf_path}")
        print("Please provide a test PDF file")
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(pdf_path, "rb") as f:
        files = {"file": (Path(pdf_path).name, f, "application/pdf")}
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/documents/upload",
            headers=headers,
            files=files
        )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Document uploaded successfully!")
        print(f"Document ID: {data['id']}")
        print(f"Status: {data['status']}")
        return data['id']
    else:
        print(f"❌ Upload failed: {response.text}")
        return None

def test_document_status(token, doc_id, max_wait=120):
    """Test document processing status"""
    print_section("5. Checking Document Processing Status")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    start_time = time.time()
    while True:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/documents/{doc_id}/status",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data["status"]
            
            print(f"Status: {status}", end="")
            
            if status == "ready":
                print(f"\n✅ Document ready for queries!")
                return True
            elif status == "failed":
                print(f"\n❌ Document processing failed!")
                print(f"Error: {data.get('error_message')}")
                return False
            elif status == "processing":
                elapsed = time.time() - start_time
                if elapsed > max_wait:
                    print(f"\n⏱️  Timeout after {max_wait}s")
                    return False
                print(f" (waiting... {int(elapsed)}s)", end="\r")
                time.sleep(5)
        else:
            print(f"\n❌ Failed to check status: {response.text}")
            return False

def test_query(token, question):
    """Test querying the document"""
    print_section("6. Testing Document Query")
    
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"question": question}
    
    print(f"Question: {question}")
    print("\nGenerating answer...\n")
    
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/query/",
        headers=headers,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Query successful!")
        print(f"\nAnswer:")
        print("-" * 60)
        print(data["answer"])
        print("-" * 60)
        print(f"\nChunks retrieved: {data['chunks_retrieved']}")
        print(f"Response time: {data['response_time']:.2f}s")
        
        if data.get("sources"):
            print(f"\nSources:")
            for i, source in enumerate(data["sources"][:3], 1):
                print(f"  {i}. {source.get('source_file')} (chunk {source.get('chunk_index')})")
        
        return True
    else:
        print(f"❌ Query failed: {response.text}")
        return False

def main():
    """Run all tests"""
    print("\n")
    print("="*60)
    print("  RAG SYSTEM - QUICK TEST SCRIPT")
    print("="*60)
    print("\nThis script will test the following:")
    print("  1. Health check")
    print("  2. User registration")
    print("  3. User login")
    print("  4. Document upload")
    print("  5. Document processing")
    print("  6. Document query")
    
    # Configuration
    TEST_EMAIL = "test@example.com"
    TEST_PASSWORD = "SecurePass123!"
    TEST_PDF = "test.pdf"  # Change this to your test PDF path
    TEST_QUESTION = "What is this document about?"
    
    # Run tests
    try:
        # 1. Health check
        if not test_health():
            print("\n❌ Health check failed! Is the server running?")
            print("Start the server with: python main.py")
            return
        
        # 2. Register user
        if not test_register(TEST_EMAIL, TEST_PASSWORD):
            print("\n❌ Registration failed!")
            return
        
        # 3. Login and get token
        token = test_login(TEST_EMAIL, TEST_PASSWORD)
        if not token:
            print("\n❌ Login failed!")
            return
        
        # 4. Upload document
        print(f"\n📄 Looking for test PDF at: {TEST_PDF}")
        print("If you don't have a test PDF, place one in the backend directory")
        
        doc_id = test_upload_document(token, TEST_PDF)
        if not doc_id:
            print("\n⚠️  Skipping document tests (no PDF provided)")
            print("\nBasic authentication tests passed! ✅")
            return
        
        # 5. Wait for processing
        if not test_document_status(token, doc_id):
            print("\n❌ Document processing failed!")
            return
        
        # 6. Query the document
        if not test_query(token, TEST_QUESTION):
            print("\n❌ Query failed!")
            return
        
        # Success!
        print_section("✅ ALL TESTS PASSED!")
        print("\nYour RAG system is working correctly! 🎉")
        print("\nNext steps:")
        print("  - Try uploading more PDFs")
        print("  - Ask different questions")
        print("  - Build a frontend UI")
        print("  - Check out the API docs: http://localhost:8000/docs")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to server!")
        print("Make sure the backend is running:")
        print("  cd backend")
        print("  source venv/bin/activate")
        print("  python main.py")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
