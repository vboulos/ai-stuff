#!/usr/bin/env python3
"""
Example usage of the Test Failure Analysis tool

This script demonstrates how to use the analyzer with different AI providers
and configuration options.
"""

import json
import os
from analyze_test_failures import TestFailureAnalyzer

def example_ollama():
    """Example using Ollama (local AI)"""
    print("=== Ollama Example ===")
    
    config = {
        "jenkins": {
            "url": "https://your-jenkins.com",
            "user": "jenkins-user",
            "token": "your-token"
        },
        "ai": {
            "provider": "ollama",
            "model": "llama3.2"
        }
    }
    
    analyzer = TestFailureAnalyzer(config)
    result = analyzer.analyze_build_failures(
        pipeline_name="CI-jobs/search_tests",
        build_number=123,
        options={"max_failures": 5}
    )
    
    print(f"Found {result['analysisMetadata']['totalFailures']} failures")
    return result

def example_openai():
    """Example using OpenAI GPT"""
    print("=== OpenAI Example ===")
    
    config = {
        "jenkins": {
            "url": "https://your-jenkins.com", 
            "user": "jenkins-user",
            "token": "your-token"
        },
        "ai": {
            "provider": "openai",
            "model": "gpt-4",
            "api_key": os.environ.get("OPENAI_API_KEY")
        }
    }
    
    analyzer = TestFailureAnalyzer(config)
    result = analyzer.analyze_build_failures(
        pipeline_name="CI-jobs/api_tests",
        build_number=456,
        options={"max_failures": 3}
    )
    
    print(f"Found {result['analysisMetadata']['totalFailures']} failures")
    return result

def example_claude():
    """Example using Claude"""
    print("=== Claude Example ===")
    
    config = {
        "jenkins": {
            "url": "https://your-jenkins.com",
            "user": "jenkins-user", 
            "token": "your-token"
        },
        "ai": {
            "provider": "claude",
            "model": "claude-3-haiku-20240307",
            "api_key": os.environ.get("ANTHROPIC_API_KEY")
        }
    }
    
    analyzer = TestFailureAnalyzer(config)
    result = analyzer.analyze_build_failures(
        pipeline_name="qe-automation/ui_tests",
        build_number=789,
        options={"max_failures": 10}
    )
    
    print(f"Found {result['analysisMetadata']['totalFailures']} failures")
    return result

def example_custom_api():
    """Example using a custom AI API"""
    print("=== Custom API Example ===")
    
    config = {
        "jenkins": {
            "url": "https://your-jenkins.com",
            "user": "jenkins-user",
            "token": "your-token"
        },
        "ai": {
            "provider": "generic",
            "api_url": "https://api.your-ai-service.com/v1/chat",
            "headers": {
                "Authorization": f"Bearer {os.environ.get('CUSTOM_AI_TOKEN')}",
                "Content-Type": "application/json"
            },
            "payload_template": {
                "model": "custom-model",
                "messages": [{"role": "user", "content": "{{PROMPT}}"}]
            },
            "response_path": "choices.0.message.content"
        }
    }
    
    analyzer = TestFailureAnalyzer(config)
    result = analyzer.analyze_build_failures(
        pipeline_name="integration-tests",
        build_number=999,
        options={"max_failures": 5}
    )
    
    print(f"Found {result['analysisMetadata']['totalFailures']} failures")
    return result

def save_example_config():
    """Save example configuration files"""
    
    # Ollama config
    ollama_config = {
        "jenkins": {
            "url": "https://jenkins.example.com",
            "user": "your-username",
            "token": "your-api-token"
        },
        "ai": {
            "provider": "ollama",
            "model": "llama3.2"
        }
    }
    
    with open('config-ollama.json', 'w') as f:
        json.dump(ollama_config, f, indent=2)
    
    print("Saved example config: config-ollama.json")

def main():
    """Run examples based on available configuration"""
    
    print("Test Failure Analysis Examples")
    print("=" * 40)
    
    # Save example config
    save_example_config()
    
    # Check which AI providers are available
    try:
        import ollama
        print("✓ Ollama available")
        # Uncomment to run: example_ollama()
    except ImportError:
        print("✗ Ollama not available (pip install ollama)")
    
    try:
        import openai
        if os.environ.get("OPENAI_API_KEY"):
            print("✓ OpenAI available")
            # Uncomment to run: example_openai()
        else:
            print("✗ OpenAI API key not set")
    except ImportError:
        print("✗ OpenAI not available (pip install openai)")
    
    try:
        import anthropic
        if os.environ.get("ANTHROPIC_API_KEY"):
            print("✓ Claude available")
            # Uncomment to run: example_claude()
        else:
            print("✗ Anthropic API key not set")
    except ImportError:
        print("✗ Anthropic not available (pip install anthropic)")
    
    print("\nTo run examples:")
    print("1. Configure your Jenkins credentials in the config files")
    print("2. Set up your AI provider (Ollama, OpenAI, Claude)")
    print("3. Uncomment the example function calls above")
    print("4. Run: python3 example_usage.py")

if __name__ == "__main__":
    main()