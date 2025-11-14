#!/bin/bash
# TFA Framework Setup Script

set -e

echo "🚀 Setting up TFA (Test Failure Analysis) Framework"
echo "=================================================="

# Check if running from correct directory
if [[ ! -f "analyze_and_suggest_fixes.py" ]]; then
    echo "❌ Please run this script from the tfa/claude/analyze_and_fix directory"
    exit 1
fi

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo "❌ Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi
echo "✅ Python version OK: $python_version"

# Check if Claude CLI is installed
echo "📋 Checking Claude CLI..."
if ! command -v claude &> /dev/null; then
    echo "⚠️  Claude CLI not found. Installing..."
    
    # Download and install Claude CLI
    curl -O https://claude.ai/cli/install.sh
    bash install.sh
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    rm -f install.sh
    echo "✅ Claude CLI installed"
else
    echo "✅ Claude CLI found: $(which claude)"
fi

# Check Claude CLI authentication
echo "📋 Checking Claude CLI authentication..."
if ! claude auth status &> /dev/null; then
    echo "⚠️  Claude CLI not authenticated. Please run:"
    echo "   claude auth"
    echo "   Then re-run this setup script."
    exit 1
fi
echo "✅ Claude CLI authentication OK"

# Install Python dependencies
echo "📋 Installing Python dependencies..."
if [[ -f "requirements.txt" ]]; then
    pip3 install -r requirements.txt
    echo "✅ Python dependencies installed"
else
    echo "⚠️  requirements.txt not found, but core dependencies are built-in"
fi

# Test the installation
echo "📋 Testing installation..."
if python3 analyze_and_suggest_fixes.py --sample; then
    echo "✅ Sample file created successfully"
else
    echo "❌ Failed to create sample file"
    exit 1
fi

if python3 analyze_and_suggest_fixes.py sample_test_failures.json --analysis-only --max-failures 1 > /dev/null 2>&1; then
    echo "✅ Framework test successful"
    rm -f sample_test_failures.json comprehensive_analysis.json
else
    echo "❌ Framework test failed"
    echo "   Check Claude CLI setup and try again"
    exit 1
fi

echo ""
echo "🎉 TFA Framework setup complete!"
echo ""
echo "📚 Next steps:"
echo "   1. Read the quick start: cat QUICKSTART.md"
echo "   2. View full documentation: cat TFA_USER_GUIDE.md"
echo "   3. Try with your test data:"
echo "      python3 junit_xml_to_json.py your-junit.xml"
echo "      python3 analyze_and_suggest_fixes.py failed_tests.json"
echo ""
echo "💡 Pro tips:"
echo "   - Use --analysis-only for faster results"
echo "   - Use --max-failures 10 to limit processing"
echo "   - Use --max-workers 5 for large datasets"
echo ""

