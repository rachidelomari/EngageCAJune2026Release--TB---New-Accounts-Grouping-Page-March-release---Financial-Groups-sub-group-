#!/usr/bin/env python3
"""
Example usage of the ADO to TestRail converter
"""

from ado_to_testrail import ADOClient, TestRailClient, ADOToTestRailConverter
import os
from dotenv import load_dotenv

# Load environment variables from .env file (optional)
load_dotenv()


def example_1_basic_conversion():
    """Basic example: Convert single ADO work item to TestRail"""
    
    # Get credentials from environment or hardcode them
    ado_org = os.getenv('ADO_ORG', 'your-organization')
    ado_project = os.getenv('ADO_PROJECT', 'your-project')
    ado_pat = os.getenv('ADO_PAT_TOKEN', 'your-pat-token')
    
    testrail_url = os.getenv('TESTRAIL_BASE_URL', 'https://your-instance.testrail.io')
    testrail_token = os.getenv('TESTRAIL_API_TOKEN', 'your-api-token')
    
    # Initialize clients
    ado_client = ADOClient(ado_org, ado_project, ado_pat)
    testrail_client = TestRailClient(testrail_url, testrail_token)
    
    # Create converter
    converter = ADOToTestRailConverter(ado_client, testrail_client)
    
    # Convert and upload
    result = converter.convert_and_upload(
        ado_url="https://wkaxcess.visualstudio.com/Audit/_workitems/edit/1556295",
        testrail_section_id=12345  # Replace with your section ID
    )
    
    print(f"\n✓ Test case created successfully!")
    print(f"  ID: {result['id']}")
    print(f"  Title: {result['title']}")
    print(f"  Steps: {len(result.get('custom_steps', []))}")


def example_2_batch_conversion():
    """Example: Convert multiple ADO work items"""
    
    ado_org = os.getenv('ADO_ORG', 'your-organization')
    ado_project = os.getenv('ADO_PROJECT', 'your-project')
    ado_pat = os.getenv('ADO_PAT_TOKEN', 'your-pat-token')
    
    testrail_url = os.getenv('TESTRAIL_BASE_URL', 'https://your-instance.testrail.io')
    testrail_token = os.getenv('TESTRAIL_API_TOKEN', 'your-api-token')
    
    ado_client = ADOClient(ado_org, ado_project, ado_pat)
    testrail_client = TestRailClient(testrail_url, testrail_token)
    converter = ADOToTestRailConverter(ado_client, testrail_client)
    
    # List of ADO work items to convert
    work_items = [
        1556295,
        1556296,
        1556297,
    ]
    
    testrail_section_id = 12345  # Replace with your section ID
    created_cases = []
    
    for work_item_id in work_items:
        try:
            result = converter.convert_and_upload(
                ado_url=str(work_item_id),
                testrail_section_id=testrail_section_id
            )
            created_cases.append(result['id'])
        except Exception as e:
            print(f"✗ Failed to convert work item {work_item_id}: {str(e)}")
    
    print(f"\n✓ Successfully created {len(created_cases)} test cases")
    print(f"  IDs: {', '.join(map(str, created_cases))}")


if __name__ == "__main__":
    print("ADO to TestRail Converter Examples")
    print("=" * 50)
    
    # Uncomment the example you want to run:
    
    # example_1_basic_conversion()
    # example_2_batch_conversion()
    
    print("\nEdit this file and uncomment the example you want to run.")
