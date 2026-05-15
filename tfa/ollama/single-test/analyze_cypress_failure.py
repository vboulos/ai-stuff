#!/usr/bin/env python3
"""
Analyze the specific Cypress failure message
"""

from analyze_failure import analyze_failure

# Your Cypress failure message
failure_message = """Timed out retrying after 120000ms: expected '<dd.pf-v5-c-description-list__description>' to contain text 'Policy is placed on hub or managed clusters with label acm-virt-config=acm-dr-virt-config-file-name. Creates a velero Schedule for all virtualmachines.kubevirt.io resources with a cluster.open-cluster-management.io/backup-vm label.', but the text was 'Policy is placed on hub or managed clusters with label acm-virt-config=acm-dr-virt-config-file-name.Creates a velero Schedule for all virtualmachines.kubevirt.io resources with a cluster.open-cluster-management.io/backup-vm label.'

AssertionError: Timed out retrying after 120000ms: expected '<dd.pf-v5-c-description-list__description>' to contain text 'Policy is placed on hub or managed clusters with label acm-virt-config=acm-dr-virt-config-file-name. Creates a velero Schedule for all virtualmachines.kubevirt.io resources with a cluster.open-cluster-management.io/backup-vm label.', but the text was 'Policy is placed on hub or managed clusters with label acm-virt-config=acm-dr-virt-config-file-name.Creates a velero Schedule for all virtualmachines.kubevirt.io resources with a cluster.open-cluster-management.io/backup-vm label.'
    at eval (webpack://acmqe-grc-test/./tests/cypress/support/views.js:4742:80)
    at Array.forEach (<anonymous>)
    at Context.eval (webpack://acmqe-grc-test/./tests/cypress/support/views.js:4730:26)"""

def main():
    print("🔍 Analyzing Cypress Failure Message...")
    print("=" * 60)
    
    result = analyze_failure(
        test_name="cypress_text_assertion_test",
        failure_message=failure_message,
        # framework="cypress"
    )
    
    if result["success"]:
        print("✅ Analysis Results:")
        print(f"\n📋 Root Cause:\n{result['root_cause']}")
        print(f"\n🔧 Suggested Fix:\n{result['suggested_fix']}")
        
        if result['code_example']:
            print(f"\n💻 Code Example:\n{result['code_example']}")
        
        print(f"\n📊 Confidence Score: {result['confidence_score']:.2f}")
    else:
        print(f"❌ Analysis failed: {result['error']}")

if __name__ == "__main__":
    main()