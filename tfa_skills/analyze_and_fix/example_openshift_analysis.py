#!/usr/bin/env python3
"""
Example: Using the OpenShift/ACM specialized prompt for test failure analysis

This script demonstrates how to analyze OpenShift/Kubernetes/ACM test failures
using the specialized expert prompt.
"""

import os
import json
from analyze_failures import FailureAnalyzer


def analyze_with_openshift_prompt():
    """Analyze test failures using the OpenShift/ACM specialized prompt."""

    # Get the path to the specialized prompt
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, "prompts", "analysis_prompt_openshift_acm.txt")

    # Initialize analyzer with OpenShift/ACM prompt
    print("🔧 Initializing FailureAnalyzer with OpenShift/ACM specialized prompt...")
    analyzer = FailureAnalyzer(
        model="llama3.1",  # or "llama3.2", "mistral", etc.
        prompt_file=prompt_path
    )

    # Sample OpenShift/ACM test failures
    test_failures = [
        {
            "name": "test_managed_cluster_import",
            "failure_message": """
            Error: ManagedCluster 'cluster1' stuck in 'Pending' condition for 600 seconds
            Last observed status:
              conditions:
              - type: ManagedClusterConditionAvailable
                status: Unknown
                reason: ManagedClusterNotReachable
                message: "cluster is not reachable: Get https://api.cluster1.example.com:6443/version: dial tcp: i/o timeout"
            """,
            "framework": "ginkgo"
        },
        {
            "name": "test_policy_compliance_enforcement",
            "failure_message": """
            AssertionError: Expected Policy status to be 'Compliant' but got 'NonCompliant'
            Policy: policy-limitrange
            Namespace: managed-cluster-1
            PlacementRule matched 3 clusters but only 2 show compliant status
            Cluster 'dev-cluster-3' shows violation: limitrange not found in namespace 'production'
            """,
            "framework": "ginkgo"
        },
        {
            "name": "test_operator_deployment_rollout",
            "failure_message": """
            Timeout: ClusterServiceVersion 'advanced-cluster-management.v2.9.0' did not reach 'Succeeded' phase within 300s
            Current Phase: Installing
            Operator pod 'multicluster-operators-hub-subscription-7d9f8b5c4d-xyz' in CrashLoopBackOff
            Last log: panic: runtime error: invalid memory address or nil pointer dereference
            """,
            "framework": "pytest"
        },
        {
            "name": "test_submariner_connection",
            "failure_message": """
            NetworkError: Submariner cable connection failed between hub and managed cluster
            Gateway nodes:
              - hub-worker-0 (10.0.1.15) -> Status: error
              - managed-worker-0 (10.0.2.20) -> Status: connecting
            IPsec tunnel establishment timeout after 180s
            Possible network policy or firewall blocking ports 4500/4800
            """,
            "framework": "ginkgo"
        }
    ]

    print(f"\n📊 Analyzing {len(test_failures)} OpenShift/ACM test failures...\n")
    print("=" * 80)

    results = []

    for i, test_case in enumerate(test_failures, 1):
        print(f"\n🔬 [{i}/{len(test_failures)}] Analyzing: {test_case['name']}")
        print("-" * 80)

        result = analyzer.analyze_failure(
            test_name=test_case['name'],
            failure_message=test_case['failure_message'],
            framework=test_case['framework']
        )

        if result["success"]:
            print(f"✅ Analysis completed (confidence: {result['confidence_score']:.2f})")
            print(f"\n📋 ROOT CAUSE:")
            print(f"   {result['root_cause'][:200]}...")

            print(f"\n🔧 SUGGESTED FIX:")
            print(f"   {result['suggested_fix'][:200]}...")

            print(f"\n⚠️  SEVERITY: {result['severity'].upper()}")
            print(f"📂 CATEGORY: {result['error_category']}")

            if result.get('additional_context'):
                print(f"\n💡 ADDITIONAL CONTEXT:")
                print(f"   {result['additional_context'][:200]}...")

            if result.get('code_example'):
                print(f"\n💻 CODE EXAMPLE:")
                print(f"   {result['code_example'][:150]}...")
        else:
            print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")

        results.append({
            "test": test_case['name'],
            "analysis": result
        })

        print("\n" + "=" * 80)

    # Save results
    output_file = "openshift_acm_analysis_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Full results saved to: {output_file}")

    # Summary
    successful = sum(1 for r in results if r['analysis']['success'])
    print(f"\n📈 SUMMARY:")
    print(f"   Total analyzed: {len(results)}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {len(results) - successful}")

    # Category distribution
    categories = {}
    severities = {}
    for r in results:
        if r['analysis']['success']:
            cat = r['analysis']['error_category']
            sev = r['analysis']['severity']
            categories[cat] = categories.get(cat, 0) + 1
            severities[sev] = severities.get(sev, 0) + 1

    print(f"\n📊 ERROR CATEGORIES:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   {cat}: {count}")

    print(f"\n⚠️  SEVERITY DISTRIBUTION:")
    for sev, count in sorted(severities.items(), key=lambda x: x[1], reverse=True):
        print(f"   {sev}: {count}")


if __name__ == "__main__":
    try:
        analyze_with_openshift_prompt()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 Make sure to install ollama: pip install ollama")
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        print("\n💡 Make sure you're running this from the analyze_and_fix directory")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
