#!/usr/bin/env python3
"""
Preview test case before uploading to TestRail
Fetches ADO requirement, parses it, and displays for review
"""

from ado_to_testrail import ADOClient, ADOToTestRailConverter
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def preview_test_case(ado_url_or_id):
    """
    Fetch and parse ADO requirement, display for preview
    
    Args:
        ado_url_or_id: ADO work item URL or ID
        
    Returns:
        Parsed TestCaseData object
    """
    
    # Initialize ADO client
    ado_org = os.getenv('ADO_ORG', 'wkaxcess')
    ado_project = os.getenv('ADO_PROJECT', 'Audit')
    ado_pat = os.getenv('ADO_PAT_TOKEN')
    
    if not ado_pat:
        print("❌ Error: ADO_PAT_TOKEN not found in environment variables")
        print("   Set it in .env file or as environment variable")
        return None
    
    try:
        ado_client = ADOClient(ado_org, ado_project, ado_pat)
        
        # Fetch work item
        print(f"📥 Fetching ADO work item...")
        if isinstance(ado_url_or_id, str) and ado_url_or_id.startswith('http'):
            work_item = ado_client.get_work_item_from_url(ado_url_or_id)
        else:
            work_item = ado_client.get_work_item(int(ado_url_or_id))
        
        print(f"   ✓ Retrieved work item")
        
        # Create a dummy converter just for parsing
        class DummyTestRailClient:
            pass
        
        converter = ADOToTestRailConverter(ado_client, DummyTestRailClient())
        
        # Parse requirement
        print(f"📝 Parsing requirement...")
        test_case = converter.parse_ado_requirement(work_item)
        print(f"   ✓ Parsed successfully\n")
        
        return test_case
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def display_test_case(test_case):
    """
    Display test case in a readable format
    
    Args:
        test_case: TestCaseData object
    """
    
    print("=" * 80)
    print("TEST CASE PREVIEW")
    print("=" * 80)
    
    # Title
    print(f"\n📌 TITLE")
    print(f"   {test_case.title}")
    
    # Priority
    priority_names = {1: "Low", 3: "Medium", 5: "High"}
    print(f"\n⚙️  PRIORITY")
    print(f"   {priority_names.get(test_case.priority_id, 'Unknown')} (ID: {test_case.priority_id})")
    
    # Description
    print(f"\n📄 DESCRIPTION")
    if test_case.description:
        for line in test_case.description.split('\n')[:10]:  # Show first 10 lines
            print(f"   {line}")
        if len(test_case.description.split('\n')) > 10:
            print(f"   ... (truncated)")
    else:
        print(f"   (No description)")
    
    # Preconditions
    print(f"\n📋 PRECONDITIONS")
    if test_case.preconditions:
        for line in test_case.preconditions.split('\n'):
            print(f"   • {line}")
    else:
        print(f"   (No preconditions)")
    
    # Test Steps
    print(f"\n🧪 TEST STEPS ({len(test_case.steps)} steps)")
    for i, step in enumerate(test_case.steps, 1):
        print(f"\n   Step {i}:")
        print(f"   ACTION:")
        # Wrap long lines
        action_lines = step['content'].split('\n')
        for line in action_lines:
            print(f"      {line}")
        
        print(f"   EXPECTED RESULT:")
        expected_lines = step['expected'].split('\n')
        for line in expected_lines:
            print(f"      {line}")
    
    print(f"\n" + "=" * 80)


def export_to_json(test_case, filename="test_case_preview.json"):
    """
    Export test case to JSON for review
    
    Args:
        test_case: TestCaseData object
        filename: Output filename
    """
    
    data = {
        "title": test_case.title,
        "description": test_case.description,
        "preconditions": test_case.preconditions,
        "priority_id": test_case.priority_id,
        "type_id": test_case.type_id,
        "steps": test_case.steps
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n💾 Exported to {filename}")


def main():
    """Main function"""
    
    print("ADO to TestRail - Test Case Preview")
    print("=" * 80)
    
    # Get ADO work item URL/ID from user or use default
    ado_input = input("\nEnter ADO work item URL or ID (or press Enter for default): ").strip()
    
    if not ado_input:
        # Use the example from the requirements
        ado_input = "1556295"  # From your spec
        print(f"Using default: {ado_input}")
    
    # Fetch and parse
    test_case = preview_test_case(ado_input)
    
    if not test_case:
        print("\n❌ Failed to fetch and parse test case")
        return
    
    # Display preview
    display_test_case(test_case)
    
    # Ask for export to JSON
    export_choice = input("\n📁 Export to JSON? (y/n): ").strip().lower()
    if export_choice == 'y':
        export_to_json(test_case)
    
    # Ask for validation
    print("\n" + "=" * 80)
    validate_choice = input("✅ Does this test case look correct? (y/n): ").strip().lower()
    
    if validate_choice == 'y':
        print("\n✓ Test case validated!")
        print("You can now upload it to TestRail using upload_test_case.py")
    else:
        print("\n✗ Please review the test case and make adjustments if needed")
        print("You can edit the ADO requirement and try again")


if __name__ == "__main__":
    main()
