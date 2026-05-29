#!/usr/bin/env python3
"""
Test Failure Analysis with AI Integration (Ollama, OpenAI, Claude, etc.)

Implements the analyze-test-failures skill using configurable AI backends.
"""

import argparse
import json
import logging
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
import urllib.parse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AIProvider:
    """Base class for AI providers"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def analyze_failure(self, prompt: str) -> str:
        raise NotImplementedError


class OllamaProvider(AIProvider):
    """Ollama AI provider"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        try:
            import ollama
            self.ollama = ollama
        except ImportError:
            raise ImportError("ollama package not installed. Run: pip install ollama")
    
    def analyze_failure(self, prompt: str) -> str:
        model = self.config.get('model', 'llama3.2')
        try:
            response = self.ollama.chat(
                model=model,
                messages=[
                    {'role': 'system', 'content': 'You are an expert test automation engineer. Provide detailed analysis in JSON format.'},
                    {'role': 'user', 'content': prompt}
                ]
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            return ""


class OpenAIProvider(AIProvider):
    """OpenAI API provider"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        try:
            import openai
            self.client = openai.OpenAI(api_key=config.get('api_key'))
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def analyze_failure(self, prompt: str) -> str:
        model = self.config.get('model', 'gpt-4')
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {'role': 'system', 'content': 'You are an expert test automation engineer. Provide detailed analysis in JSON format.'},
                    {'role': 'user', 'content': prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return ""


class ClaudeProvider(AIProvider):
    """Claude (Anthropic) API provider"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=config.get('api_key'))
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    def analyze_failure(self, prompt: str) -> str:
        model = self.config.get('model', 'claude-3-haiku-20240307')
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=4000,
                system="You are an expert test automation engineer. Provide detailed analysis in JSON format.",
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            return ""


class GenericAPIProvider(AIProvider):
    """Generic REST API provider for any AI service"""
    
    def analyze_failure(self, prompt: str) -> str:
        url = self.config.get('api_url')
        headers = self.config.get('headers', {})
        payload = self.config.get('payload_template', {})
        
        # Replace placeholders in payload
        payload_str = json.dumps(payload).replace('{{PROMPT}}', prompt)
        payload = json.loads(payload_str)
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            # Extract response based on configuration
            response_data = response.json()
            response_path = self.config.get('response_path', 'response')
            
            # Navigate through nested response
            result = response_data
            for key in response_path.split('.'):
                result = result.get(key, '')
            
            return str(result)
        except Exception as e:
            logger.error(f"Generic API analysis failed: {e}")
            return ""


class TestFailureAnalyzer:
    """Main analyzer class"""
    
    def __init__(self, config: Dict):
        self.jenkins_config = config.get('jenkins', {})
        self.ai_config = config.get('ai', {})
        self.ai_provider = self._create_ai_provider()
    
    def _create_ai_provider(self) -> AIProvider:
        """Create AI provider based on configuration"""
        provider_type = self.ai_config.get('provider', 'ollama').lower()
        
        if provider_type == 'ollama':
            return OllamaProvider(self.ai_config)
        elif provider_type == 'openai':
            return OpenAIProvider(self.ai_config)
        elif provider_type == 'claude':
            return ClaudeProvider(self.ai_config)
        elif provider_type == 'generic':
            return GenericAPIProvider(self.ai_config)
        else:
            raise ValueError(f"Unknown AI provider: {provider_type}")
    
    def analyze_build_failures(self, pipeline_name: str, build_number: int, options: Optional[Dict] = None) -> Dict[str, Any]:
        """Main analysis method"""
        start_time = time.time()
        options = options or {}
        
        logger.info(f"Starting analysis of {pipeline_name} build {build_number}")
        
        result = {
            "analysisMetadata": {
                "pipeline": pipeline_name,
                "buildNumber": build_number,
                "analysisTimestamp": datetime.utcnow().isoformat() + "Z",
                "totalFailures": 0,
                "processingTime": "",
                "aiProvider": self.ai_config.get('provider', 'unknown')
            },
            "failureAnalysis": [],
            "summaryMetrics": {
                "automationBugs": 0,
                "infrastructureIssues": 0,
                "productIssues": 0,
                "environmentIssues": 0
            }
        }
        
        try:
            # Get build information
            build_info = self._get_build_info(pipeline_name, build_number)
            if not build_info:
                logger.error("Failed to retrieve build information")
                return result
            
            # Extract test failures
            test_failures = self._extract_test_failures(pipeline_name, build_number)
            result["analysisMetadata"]["totalFailures"] = len(test_failures)
            
            if not test_failures:
                logger.info("No test failures found in this build")
                return result
            
            # Analyze failures with AI
            max_failures = options.get('max_failures', 10)
            for i, failure in enumerate(test_failures[:max_failures]):
                logger.info(f"Analyzing failure {i+1}/{min(len(test_failures), max_failures)}: {failure['testCaseName']}")
                
                analysis = self._analyze_failure_with_ai(failure, build_info, options)
                if analysis:
                    result["failureAnalysis"].append(analysis)
                    self._update_summary_metrics(analysis, result["summaryMetrics"])
            
            processing_time = time.time() - start_time
            result["analysisMetadata"]["processingTime"] = f"{processing_time:.1f}s"
            
            logger.info(f"Analysis completed in {processing_time:.1f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            result["analysisMetadata"]["processingTime"] = f"{time.time() - start_time:.1f}s"
            return result
    
    def _get_build_info(self, pipeline_name: str, build_number: int) -> Optional[Dict]:
        """Fetch build information from Jenkins"""
        try:
            jenkins_url = self.jenkins_config.get('url', '').rstrip('/')
            jenkins_user = self.jenkins_config.get('user', '')
            jenkins_token = self.jenkins_config.get('token', '')
            
            if not all([jenkins_url, jenkins_user, jenkins_token]):
                raise ValueError("Jenkins credentials not configured")
            
            encoded_pipeline = urllib.parse.quote(pipeline_name, safe='')
            url = f"{jenkins_url}/job/{encoded_pipeline}/{build_number}/api/json"
            
            response = requests.get(url, auth=(jenkins_user, jenkins_token), timeout=30)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get build info: {str(e)}")
            return None
    
    def _extract_test_failures(self, pipeline_name: str, build_number: int) -> List[Dict]:
        """Extract test failures from Jenkins"""
        failures = []
        
        try:
            jenkins_url = self.jenkins_config.get('url', '').rstrip('/')
            jenkins_user = self.jenkins_config.get('user', '')
            jenkins_token = self.jenkins_config.get('token', '')
            
            encoded_pipeline = urllib.parse.quote(pipeline_name, safe='')
            url = f"{jenkins_url}/job/{encoded_pipeline}/{build_number}/testReport/api/json"
            
            response = requests.get(url, auth=(jenkins_user, jenkins_token), timeout=30)
            if response.status_code == 404:
                logger.warning("No test report found for this build")
                return failures
            
            response.raise_for_status()
            test_report = response.json()
            
            # Extract failures
            for suite in test_report.get('suites', []):
                for case in suite.get('cases', []):
                    if case.get('status') in ['FAILED', 'ERROR']:
                        failure = {
                            'testCaseName': case.get('name', ''),
                            'className': case.get('className', ''),
                            'failureMessage': case.get('errorDetails', ''),
                            'stackTrace': case.get('errorStackTrace', ''),
                            'duration': case.get('duration', 0),
                            'suiteName': suite.get('name', '')
                        }
                        failures.append(failure)
            
            logger.info(f"Found {len(failures)} test failures")
            return failures
            
        except Exception as e:
            logger.error(f"Failed to extract test failures: {str(e)}")
            return failures
    
    def _analyze_failure_with_ai(self, failure: Dict, build_info: Dict, options: Dict) -> Optional[Dict]:
        """Analyze failure using AI provider"""
        try:
            prompt = self._build_analysis_prompt(failure, build_info, options)
            response = self.ai_provider.analyze_failure(prompt)
            
            if not response:
                return None
            
            # Try to extract JSON from response
            analysis_json = self._extract_json_from_response(response)
            if analysis_json:
                return analysis_json
            
            # Fallback to structured parsing
            return self._create_fallback_analysis(failure, response)
            
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return None
    
    def _build_analysis_prompt(self, failure: Dict, build_info: Dict, options: Dict) -> str:
        """Build analysis prompt for AI"""
        return f"""
Analyze this test failure and provide analysis in JSON format:

TEST FAILURE:
- Test: {failure['testCaseName']}
- Class: {failure['className']}
- Suite: {failure['suiteName']}
- Duration: {failure['duration']}s
- Message: {failure['failureMessage']}
- Stack Trace: {failure['stackTrace']}

BUILD CONTEXT:
- Pipeline: {build_info.get('fullDisplayName', 'Unknown')}
- Result: {build_info.get('result', 'Unknown')}
- URL: {build_info.get('url', 'Unknown')}

Provide JSON with these exact fields:
{{
  "testCaseName": "{failure['testCaseName']}",
  "failureMessage": "Brief failure message",
  "rootCauseAnalysis": "Detailed cause analysis",
  "codeFixSuggestion": "Specific fix recommendations",
  "sourceCodeMapping": {{
    "filePath": "estimated path",
    "lineNumber": 0,
    "testMethod": "{failure['testCaseName']}",
    "testClass": "{failure['className']}"
  }},
  "failureDetails": {{
    "stackTrace": "truncated trace",
    "errorType": "ElementNotFound|Timeout|Assertion|Exception|Network",
    "severity": "HIGH|MEDIUM|LOW", 
    "category": "automation|infrastructure|product|environment"
  }},
  "fixMetadata": {{
    "confidenceScore": 0.8,
    "automationBug": true,
    "estimatedEffort": "X minutes",
    "suggestedLines": ["code suggestions"]
  }}
}}

Focus on identifying automation bugs vs product issues and provide actionable fixes.
Return ONLY the JSON, no other text.
"""
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict]:
        """Extract JSON from AI response"""
        try:
            # Find JSON boundaries
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except Exception as e:
            logger.debug(f"JSON extraction failed: {e}")
        
        return None
    
    def _create_fallback_analysis(self, failure: Dict, response: str) -> Dict:
        """Create fallback analysis structure"""
        return {
            "testCaseName": failure['testCaseName'],
            "failureMessage": failure['failureMessage'][:200] + "...",
            "rootCauseAnalysis": response[:500] + "...",
            "codeFixSuggestion": "See rootCauseAnalysis for details",
            "sourceCodeMapping": {
                "filePath": "Unknown",
                "lineNumber": 0,
                "testMethod": failure['testCaseName'],
                "testClass": failure['className']
            },
            "failureDetails": {
                "stackTrace": failure['stackTrace'][:500] + "...",
                "errorType": "Unknown",
                "severity": "MEDIUM",
                "category": "automation"
            },
            "fixMetadata": {
                "confidenceScore": 0.5,
                "automationBug": True,
                "estimatedEffort": "Unknown",
                "suggestedLines": []
            }
        }
    
    def _update_summary_metrics(self, analysis: Dict, metrics: Dict):
        """Update summary metrics"""
        category = analysis.get('failureDetails', {}).get('category', 'automation')
        metrics[f"{category}{'Bugs' if category == 'automation' else 'Issues'}"] += 1


def load_config(config_file: str = 'config.json') -> Dict:
    """Load configuration from file"""
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load config: {e}")
    
    return {}


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Analyze test failures with AI')
    parser.add_argument('pipeline_name', help='Jenkins pipeline name')
    parser.add_argument('build_number', type=int, help='Build number')
    parser.add_argument('--config', default='config.json', help='Config file')
    parser.add_argument('--output', help='Output JSON file')
    parser.add_argument('--max-failures', type=int, default=10, help='Max failures to analyze')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        logger.error(f"Configuration file {args.config} not found or invalid")
        sys.exit(1)
    
    # Initialize analyzer
    try:
        analyzer = TestFailureAnalyzer(config)
    except Exception as e:
        logger.error(f"Failed to initialize analyzer: {e}")
        sys.exit(1)
    
    # Run analysis
    options = {'max_failures': args.max_failures}
    result = analyzer.analyze_build_failures(args.pipeline_name, args.build_number, options)
    
    # Save results
    output_file = args.output or f"analysis_{args.pipeline_name.replace('/', '_')}_{args.build_number}.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    # Print summary
    print(f"\n=== ANALYSIS SUMMARY ===")
    print(f"Pipeline: {result['analysisMetadata']['pipeline']}")
    print(f"Build: {result['analysisMetadata']['buildNumber']}")
    print(f"AI Provider: {result['analysisMetadata']['aiProvider']}")
    print(f"Total Failures: {result['analysisMetadata']['totalFailures']}")
    print(f"Processing Time: {result['analysisMetadata']['processingTime']}")
    print(f"Automation Bugs: {result['summaryMetrics']['automationBugs']}")
    print(f"Infrastructure Issues: {result['summaryMetrics']['infrastructureIssues']}")
    print(f"Product Issues: {result['summaryMetrics']['productIssues']}")
    print(f"Environment Issues: {result['summaryMetrics']['environmentIssues']}")
    print(f"\nResults saved to: {output_file}")


if __name__ == '__main__':
    main()