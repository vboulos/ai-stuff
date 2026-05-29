#!/usr/bin/env python3
"""
Quick test script to verify Ollama is working and check response times
"""

import time
import sys

try:
    import ollama
except ImportError:
    print("❌ Error: ollama package not installed")
    print("Install with: pip install ollama")
    sys.exit(1)


def test_ollama_connection():
    """Test if Ollama is running and list available models."""
    print("=" * 60)
    print("🔌 Testing Ollama Connection")
    print("=" * 60)

    try:
        response = ollama.list()
        models = response.get('models', [])

        if not models:
            print("⚠️  Ollama is running but no models are installed")
            print("\nTo install a model, run:")
            print("  ollama pull llama3.2")
            print("  ollama pull llama3.1")
            return False

        print(f"✅ Ollama is running with {len(models)} model(s):")
        for model in models:
            size_gb = model.get('size', 0) / (1024**3)
            model_name = model.get('name', model.get('model', 'unknown'))
            print(f"   - {model_name} ({size_gb:.1f} GB)")

        return True

    except Exception as e:
        print(f"❌ Error: Could not connect to Ollama")
        print(f"   Error message: {e}")
        print("\nMake sure Ollama is running:")
        print("  - On Mac: The Ollama app should be running")
        print("  - On Linux: Run 'ollama serve' in another terminal")
        return False


def test_model_response(model_name="llama3.2"):
    """Test a simple query to the model and measure response time."""
    print("\n" + "=" * 60)
    print(f"🤖 Testing Model: {model_name}")
    print("=" * 60)

    try:
        print(f"Sending test query to {model_name}...")
        start_time = time.time()

        response = ollama.chat(
            model=model_name,
            messages=[
                {
                    'role': 'user',
                    'content': 'Say "Hello, I am working!" and nothing else.'
                }
            ],
            options={
                'temperature': 0.1,
            }
        )

        elapsed = time.time() - start_time

        if response and 'message' in response:
            content = response['message']['content']
            print(f"✅ Model responded in {elapsed:.2f} seconds")
            print(f"   Response: {content[:100]}")

            if elapsed > 30:
                print(f"⚠️  WARNING: Response took {elapsed:.1f}s - this is slow!")
                print("   Your analysis may take a very long time.")
            elif elapsed > 10:
                print(f"⚠️  Note: Response took {elapsed:.1f}s - consider using a smaller/faster model")

            return True
        else:
            print("❌ Invalid response from model")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nPossible issues:")
        print(f"  - Model '{model_name}' not installed (run: ollama pull {model_name})")
        print("  - Ollama service not responding")
        print("  - Insufficient system resources")
        return False


def estimate_total_time(num_tests, avg_response_time):
    """Estimate total processing time."""
    print("\n" + "=" * 60)
    print("⏱️  Time Estimation")
    print("=" * 60)

    # Each test requires 2 calls: analysis + fix suggestion
    total_calls = num_tests * 2
    estimated_seconds = total_calls * avg_response_time

    minutes = estimated_seconds / 60
    hours = estimated_seconds / 3600

    print(f"Number of tests: {num_tests}")
    print(f"Calls per test: 2 (analysis + fix)")
    print(f"Total API calls: {total_calls}")
    print(f"Avg response time: {avg_response_time:.1f}s")
    print(f"\nEstimated total time:")
    print(f"  - {estimated_seconds:.0f} seconds")
    print(f"  - {minutes:.1f} minutes")
    if hours > 1:
        print(f"  - {hours:.1f} hours")

    if minutes > 30:
        print("\n⚠️  This will take a long time!")
        print("Suggestions:")
        print("  - Use --limit to process fewer tests")
        print("  - Use a faster/smaller model")
        print("  - Run with --analyze-only first")


def main():
    """Main test function."""
    import argparse

    parser = argparse.ArgumentParser(description='Test Ollama setup and performance')
    parser.add_argument('--model', default='llama3.2', help='Model to test (default: llama3.2)')
    parser.add_argument('--num-tests', type=int, default=10, help='Number of tests to estimate time for (default: 10)')

    args = parser.parse_args()

    # Test connection
    if not test_ollama_connection():
        sys.exit(1)

    # Test model response
    start = time.time()
    if not test_model_response(args.model):
        sys.exit(1)

    response_time = time.time() - start

    # Estimate time for full run
    estimate_total_time(args.num_tests, response_time)

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\nYou can now run:")
    print(f"  python3 analyze_and_suggest_fixes.py <input_file> --model {args.model}")


if __name__ == "__main__":
    main()
