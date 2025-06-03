import requests
import json

# API base URL
BASE_URL = "https://906e-34-125-115-226.ngrok-free.app"

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print("\nTesting health check endpoint:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing health check: {e}")
        return False

def extract_answer(response_text):
    """Extract the answer part after [/INST]"""
    if "[/INST]" in response_text:
        return response_text.split("[/INST]")[-1].strip()
    return response_text

def test_chat_endpoint():
    """Test the chat endpoint with a sample question"""
    try:
        # Test question about tuition reduction
        test_query = {
            "text": "Sinh viên có anh chị em ruột đang theo học được giảm bao nhiêu học phí?"
        }
        
        print("\nTesting chat endpoint:")
        print(f"Query: {test_query['text']}")
        
        response = requests.post(
            f"{BASE_URL}/chat",
            json=test_query,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        # Extract and print only the answer
        response_data = response.json()
        answer = extract_answer(response_data["response"])
        print(f"Answer: {answer}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing chat endpoint: {e}")
        return False

def main():
    print("Starting API tests...")
    print("=" * 50)
    
    # Run tests
    health_check_passed = test_health_check()
    chat_test_passed = test_chat_endpoint()
    
    # Print summary
    print("\nTest Summary:")
    print("=" * 50)
    print(f"Health Check Test: {'✅ PASSED' if health_check_passed else '❌ FAILED'}")
    print(f"Chat Endpoint Test: {'✅ PASSED' if chat_test_passed else '❌ FAILED'}")
    
    if health_check_passed and chat_test_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")

if __name__ == "__main__":
    main() 