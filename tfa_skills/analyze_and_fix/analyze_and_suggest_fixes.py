#!/usr/bin/env python3
"""
Analyze and Suggest Fixes - Main script implementing analyze-test-failures skill using Ollama

Implements the analyze-test-failures skill for comprehensive test failure analysis:
- JUnit XML scanning and parsing
- Root cause analysis with Ollama LLM  
- Structured JSON output following skill schema
- Source code mapping and fix suggestions
- Integration with Jenkins and GitHub APIs
"""

import json
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Import the analyzer and suggestor classes
from analyze_failures import FailureAnalyzer
from fix_suggestor import FixSuggestor


def load_test_failures(input_file: str) -> list:
    """
    Load test failures from JSON file.

    Args:
        input_file: Path to input JSON file

    Returns:
        List of test failure dictionaries
    """
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)

        # Handle different JSON formats
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Check for common keys that might contain the test list
            for key in ['tests', 'failures', 'failed_tests', 'test_cases']:
                if key in data and isinstance(data[key], list):
                    return data[key]
            # If no list found, wrap the dict in a list
            return [data]
        else:
            raise ValueError(f"Unsupported JSON format in {input_file}")

    except FileNotFoundError:
        print(f"❌ Error: Input file '{input_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{input_file}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        sys.exit(1)


def save_results(output_file: str, results: dict):
    """
    Save analysis and fix results to JSON file.

    Args:
        output_file: Path to output JSON file
        results: Results dictionary to save
    """
    try:
        # Create output directory if it doesn't exist
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"✅ Results saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error saving results: {e}")
        sys.exit(1)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Analyze test failures and suggest fixes using Ollama',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic usage with skill format (default)
  python3 analyze_and_suggest_fixes.py tests_analysis/grc_failed_tests.json

  # Full skill analysis with Jenkins and GitHub context
  python3 analyze_and_suggest_fixes.py tests_analysis/grc_failed_tests.json \
    --pipeline "CI-jobs/search_tests" --build-number 456 \
    --github-repo "https://github.com/stolostron/e2e-tests" \
    --test-directory "cypress/tests" --skill-output

  # Legacy mode for backward compatibility
  python3 analyze_and_suggest_fixes.py tests_analysis/grc_failed_tests.json --legacy-mode

  # Analysis only without fix suggestions
  python3 analyze_and_suggest_fixes.py tests_analysis/grc_failed_tests.json --analyze-only
        '''
    )

    parser.add_argument(
        'input_file',
        help='Path to JSON file containing test failures'
    )

    parser.add_argument(
        '--model',
        default='llama3.1',
        help='Ollama model to use (default: llama3.1). Examples: llama3.1, llama3.2, mistral, codellama'
    )
    
    parser.add_argument(
        '--pipeline',
        help='Jenkins pipeline name (e.g., "CI-jobs/search_tests") for skill context'
    )
    
    parser.add_argument(
        '--build-number',
        type=int,
        help='Jenkins build number for skill context'
    )
    
    parser.add_argument(
        '--github-repo',
        help='GitHub repository URL for source code analysis'
    )
    
    parser.add_argument(
        '--test-directory',
        help='Directory path containing test files for skill mapping'
    )

    parser.add_argument(
        '--output',
        default='analysis_and_fixes.json',
        help='Path to output JSON file (default: analysis_and_fixes.json)'
    )

    parser.add_argument(
        '--framework',
        help='Test framework (e.g., pytest, jest, cypress). If not specified, will try to detect from test data.'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Timeout for Ollama calls in seconds (default: 60)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of tests to process (useful for testing)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed progress and timing information'
    )

    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompts (useful for CI/CD environments)'
    )

    parser.add_argument(
        '--skip-verify',
        action='store_true',
        help='Skip Ollama connection verification (faster startup in CI/CD)'
    )

    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='Only analyze failures, do not generate fix suggestions'
    )
    
    parser.add_argument(
        '--skill-output',
        action='store_true',
        help='Generate output in analyze-test-failures skill schema format'
    )
    
    parser.add_argument(
        '--legacy-mode',
        action='store_true',
        help='Use legacy analysis format instead of skill format'
    )

    args = parser.parse_args()

    # Print configuration
    print("=" * 60)
    print("🔍 Test Failure Analysis (analyze-test-failures skill)")
    print("=" * 60)
    print(f"Input file:    {args.input_file}")
    print(f"Output file:   {args.output}")
    print(f"Model:         {args.model}")
    print(f"Framework:     {args.framework or 'auto-detect'}")
    print(f"Pipeline:      {getattr(args, 'pipeline', None) or 'not specified'}")
    print(f"Build Number:  {getattr(args, 'build_number', None) or 'not specified'}")
    print(f"GitHub Repo:   {getattr(args, 'github_repo', None) or 'not specified'}")
    print(f"Skill Format:  {'No (legacy)' if getattr(args, 'legacy_mode', False) else 'Yes'}")
    print(f"Timeout:       {args.timeout}s")
    print("=" * 60)
    print()

    # Load test failures
    print("📂 Loading test failures...")
    test_failures = load_test_failures(args.input_file)

    # Apply limit if specified
    if args.limit and args.limit < len(test_failures):
        print(f"⚠️  Limiting to first {args.limit} tests (out of {len(test_failures)} total)")
        test_failures = test_failures[:args.limit]

    print(f"✅ Loaded {len(test_failures)} test failure(s)")
    print()

    # Initialize analyzer with skill mode
    use_skill_mode = not getattr(args, 'legacy_mode', False)
    print(f"🤖 Initializing analyzer with model: {args.model} (skill mode: {use_skill_mode})")
    analyzer = FailureAnalyzer(model=args.model, timeout=args.timeout, skill_mode=use_skill_mode)

    # Test Ollama connection (unless --skip-verify)
    if not args.skip_verify:
        print("🔌 Testing Ollama connection...")
        try:
            import ollama
            test_response = ollama.list()
            # Handle both 'name' and 'model' keys
            available_models = [m.get('model', m.get('name', 'unknown')) for m in test_response.get('models', [])]
            print(f"✅ Ollama is running. Available models: {', '.join(available_models[:5])}")

            # Check if requested model exists
            model_exists = any(args.model in model for model in available_models)
            if not model_exists:
                print(f"⚠️  Warning: Model '{args.model}' not found. Available models: {', '.join(available_models)}")
                if not args.yes:
                    try:
                        response = input(f"Continue anyway? (y/n): ")
                        if response.lower() != 'y':
                            print("❌ Aborted by user")
                            sys.exit(1)
                    except (EOFError, KeyboardInterrupt):
                        print("\n❌ No interactive terminal available. Use --yes to skip prompts.")
                        sys.exit(1)
                else:
                    print("⚠️  Continuing anyway (--yes flag enabled)")
        except Exception as e:
            print(f"⚠️  Warning: Could not verify Ollama connection: {e}")
            if not args.yes:
                try:
                    response = input("Continue anyway? (y/n): ")
                    if response.lower() != 'y':
                        print("❌ Aborted by user")
                        sys.exit(1)
                except (EOFError, KeyboardInterrupt):
                    print("\n❌ No interactive terminal available. Use --yes to skip prompts.")
                    sys.exit(1)
            else:
                print("⚠️  Continuing anyway (--yes flag enabled)")
        print()
    else:
        print("⏩ Skipping Ollama connection verification (--skip-verify enabled)")
        print()

    # Prepare skill context parameters
    skill_kwargs = {}
    if getattr(args, 'pipeline', None):
        skill_kwargs['pipeline_name'] = args.pipeline
    if getattr(args, 'build_number', None):
        skill_kwargs['build_number'] = args.build_number
    if getattr(args, 'github_repo', None):
        skill_kwargs['github_repo'] = args.github_repo
    if getattr(args, 'test_directory', None):
        skill_kwargs['test_directory'] = args.test_directory
    
    # Analyze failures
    print("🔬 Analyzing test failures using analyze-test-failures skill...")
    if skill_kwargs:
        print(f"📋 Using skill context: {', '.join(f'{k}={v}' for k, v in skill_kwargs.items())}")
    print()
    
    # Apply skill context to each test failure
    enhanced_test_failures = []
    for test_case in test_failures:
        enhanced_test_case = test_case.copy()
        enhanced_test_case.update(skill_kwargs)
        enhanced_test_failures.append(enhanced_test_case)
    
    analysis_results = analyzer.analyze_multiple_failures(enhanced_test_failures, args.framework)

    # Count successful analyses
    successful_analyses = sum(1 for r in analysis_results if r.get('analysis', {}).get('success'))
    print()
    print(f"📊 Analysis complete: {successful_analyses}/{len(analysis_results)} successful")
    print()

    # Generate fix suggestions (unless --analyze-only is specified)
    if not args.analyze_only:
        print(f"🛠️  Generating fix suggestions...")
        print()
        suggestor = FixSuggestor(model=args.model, timeout=args.timeout)
        final_results = suggestor.suggest_fixes_for_analyses(analysis_results)

        # Get fix summary
        fix_summary = suggestor.get_fix_summary(final_results)
        print()
        print(f"📊 Fix generation complete: {fix_summary['successful_fixes']}/{fix_summary['total_fixes']} successful")
    else:
        final_results = analysis_results
        fix_summary = None

    # Prepare output based on skill format
    if getattr(args, 'skill_output', False) or use_skill_mode:
        # Use analyze-test-failures skill schema format
        output_data = {
            "analysisMetadata": {
                "pipeline": getattr(args, 'pipeline', None) or "unknown",
                "buildNumber": getattr(args, 'build_number', None) or 0,
                "analysisTimestamp": datetime.now().isoformat(),
                "totalFailures": len(test_failures),
                "processingTime": "completed",
                "model": args.model,
                "skillVersion": "3.0.0"
            },
            "failureAnalysis": [],
            "summaryMetrics": {
                "automationBugs": 0,
                "infrastructureIssues": 0,
                "productIssues": 0,
                "environmentIssues": 0
            }
        }
        
        # Transform results to skill format
        for result in final_results:
            if result.get('analysis', {}).get('success'):
                analysis = result['analysis']
                
                # Count categories for summary metrics
                category = analysis.get('failureDetails', {}).get('category', 'automation')
                if category == 'automation':
                    output_data['summaryMetrics']['automationBugs'] += 1
                elif category == 'infrastructure':
                    output_data['summaryMetrics']['infrastructureIssues'] += 1
                elif category == 'product':
                    output_data['summaryMetrics']['productIssues'] += 1
                elif category == 'environment':
                    output_data['summaryMetrics']['environmentIssues'] += 1
                
                # Add to failure analysis
                output_data['failureAnalysis'].append(analysis)
    else:
        # Use legacy format
        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "input_file": args.input_file,
                "model": args.model,
                "framework": args.framework,
                "total_tests": len(test_failures),
                "successful_analyses": successful_analyses,
                "analyze_only": args.analyze_only
            },
            "results": final_results
        }

    if fix_summary:
        output_data["metadata"]["fix_summary"] = fix_summary

    # Save results
    print()
    print("💾 Saving results...")
    save_results(args.output, output_data)

    # Print summary
    print()
    print("=" * 60)
    print("✨ Summary")
    print("=" * 60)
    print(f"Total tests analyzed:     {len(test_failures)}")
    print(f"Successful analyses:      {successful_analyses}")
    
    if use_skill_mode and 'summaryMetrics' in output_data:
        print()
        print("Skill Analysis Summary:")
        metrics = output_data['summaryMetrics']
        print(f"  - Automation bugs:      {metrics['automationBugs']}")
        print(f"  - Infrastructure issues: {metrics['infrastructureIssues']}")
        print(f"  - Product issues:       {metrics['productIssues']}")
        print(f"  - Environment issues:   {metrics['environmentIssues']}")
    
    if fix_summary:
        print(f"Successful fix suggestions: {fix_summary['successful_fixes']}")
        print()
        print("Fix type distribution:")
        for fix_type, count in fix_summary.get('fix_type_distribution', {}).items():
            print(f"  - {fix_type}: {count}")
        print()
        print("Priority distribution:")
        for priority, count in fix_summary.get('priority_distribution', {}).items():
            print(f"  - {priority}: {count}")
    print("=" * 60)
    print()
    print("✅ Done!")


if __name__ == "__main__":
    main()
