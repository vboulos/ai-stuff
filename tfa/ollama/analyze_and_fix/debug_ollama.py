#!/usr/bin/env python3
"""
Debug script to check Ollama status and identify issues
"""

import sys
import time
import json

try:
    import ollama
except ImportError:
    print("❌ Error: ollama package not installed")
    sys.exit(1)


def check_ollama_running():
    """Check if Ollama is running."""
    print("=" * 60)
    print("🔌 Checking Ollama Status")
    print("=" * 60)

    try:
        response = ollama.list()
        print("✅ Ollama is running")
        return True
    except Exception as e:
        print(f"❌ Ollama not responding: {e}")
        return False


def list_models():
    """List all available models."""
    print("\n" + "=" * 60)
    print("📦 Available Models")
    print("=" * 60)

    try:
        response = ollama.list()
        models = response.get('models', [])

        if not models:
            print("⚠️  No models found!")
            return []

        print(f"Found {len(models)} model(s):\n")

        model_names = []
        for model in models:
            name = model.get('model', model.get('name', 'unknown'))
            size = model.get('size', 0)
            size_gb = size / (1024**3)
            modified = model.get('modified_at', model.get('modified', 'unknown'))

            model_names.append(name)
            print(f"  📌 {name}")
            print(f"     Size: {size_gb:.2f} GB ({size:,} bytes)")
            print(f"     Modified: {modified}")
            print()

        return model_names

    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return []


def test_model(model_name, max_wait=30):
    """Test if a model actually works with a timeout."""
    print("=" * 60)
    print(f"🧪 Testing Model: {model_name}")
    print("=" * 60)

    print(f"Sending simple test query (max wait: {max_wait}s)...")
    start_time = time.time()

    try:
        response = ollama.chat(
            model=model_name,
            messages=[
                {
                    'role': 'user',
                    'content': 'Respond with only the word "OK"'
                }
            ],
            options={
                'temperature': 0.1,
                'num_predict': 5,  # Limit tokens to speed up
            }
        )

        elapsed = time.time() - start_time

        if response and 'message' in response:
            content = response['message']['content']
            print(f"✅ Model responded in {elapsed:.2f}s")
            print(f"   Response: {content}")

            if elapsed > 20:
                print(f"\n⚠️  WARNING: Response took {elapsed:.1f}s")
                print("   This is very slow. Your full analysis will take hours!")
                print("\n   Possible causes:")
                print("   - Model not fully downloaded")
                print("   - Insufficient CPU/RAM")
                print("   - Running in constrained container")

            return True, elapsed
        else:
            print("❌ Invalid response from model")
            return False, 0

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Error after {elapsed:.1f}s: {e}")

        error_msg = str(e).lower()
        if 'not found' in error_msg or '404' in error_msg:
            print("\n💡 Model not found - trying to download it now...")
            try:
                print(f"   Running: ollama pull {model_name}")
                ollama.pull(model_name)
                print("✅ Model downloaded successfully")
                print("   Please run this script again to test")
            except Exception as pull_error:
                print(f"❌ Failed to pull model: {pull_error}")

        return False, 0


def estimate_processing_time(num_tests, response_time):
    """Estimate total time for processing tests."""
    print("\n" + "=" * 60)
    print("⏱️  Processing Time Estimate")
    print("=" * 60)

    # Each test needs 2 calls: analysis + fix
    total_calls = num_tests * 2
    total_seconds = total_calls * response_time

    minutes = total_seconds / 60
    hours = total_seconds / 3600

    print(f"Tests to process: {num_tests}")
    print(f"Calls per test: 2 (analysis + fix)")
    print(f"Total API calls: {total_calls}")
    print(f"Avg time per call: {response_time:.1f}s")
    print(f"\n📊 Estimated total time:")
    print(f"   {total_seconds:.0f} seconds = {minutes:.1f} minutes", end="")
    if hours >= 1:
        print(f" = {hours:.1f} hours")
    else:
        print()

    if minutes > 60:
        print("\n❌ THIS WILL TAKE TOO LONG!")
        print("\n💡 Recommendations:")
        print("   1. Use --limit 5 to test with fewer tests")
        print("   2. Use --analyze-only (skips fix generation, 2x faster)")
        print("   3. Use a smaller/faster model")
        print("   4. Increase container resources (CPU/RAM)")
    elif minutes > 15:
        print("\n⚠️  This will take significant time")
        print("   Consider using --limit or --analyze-only")
    else:
        print("\n✅ Processing time looks reasonable")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Debug Ollama setup')
    parser.add_argument('--model', default='llama3.2', help='Model to test')
    parser.add_argument('--num-tests', type=int, default=10, help='Number of tests to estimate for')

    args = parser.parse_args()

    # Check if Ollama is running
    if not check_ollama_running():
        print("\n💡 Make sure Ollama is running:")
        print("   ollama serve")
        sys.exit(1)

    # List available models
    available_models = list_models()

    if not available_models:
        print(f"\n💡 No models installed. Install one with:")
        print(f"   ollama pull {args.model}")
        sys.exit(1)

    # Test the specified model
    success, response_time = test_model(args.model)

    if success:
        # Estimate processing time
        estimate_processing_time(args.num_tests, response_time)

        print("\n" + "=" * 60)
        print("✅ Diagnostics Complete")
        print("=" * 60)
        print(f"\nYou can now run:")
        print(f"  python3 analyze_and_suggest_fixes.py <input> --model {args.model}")
    else:
        print("\n" + "=" * 60)
        print("❌ Model Test Failed")
        print("=" * 60)
        print("\nPlease fix the issues above before running the analysis script")
        sys.exit(1)


if __name__ == "__main__":
    main()
