#!/usr/bin/env python3
"""
ADO to TestRail Test Case Converter
Converts Azure DevOps requirements to TestRail test cases with a single comprehensive test case
"""

import requests
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs


@dataclass
class TestCaseData:
    """Data structure for a test case"""
    title: str
    description: str
    preconditions: str
    steps: List[Dict[str, str]]  # List of {"content": "...", "expected": "..."}
    priority_id: int = 3  # Default to medium
    type_id: int = 1  # Default to acceptance test


class ADOClient:
    """Client for Azure DevOps API"""
    
    def __init__(self, organization: str, project: str, pat_token: str):
        """
        Initialize ADO client
        
        Args:
            organization: ADO organization name
            project: ADO project name
            pat_token: Personal Access Token
        """
        self.organization = organization
        self.project = project
        self.base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
        self.session = requests.Session()
        self.session.auth = ("", pat_token)
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_work_item(self, work_item_id: int) -> Dict:
        """
        Get work item details from ADO
        
        Args:
            work_item_id: Work Item ID
            
        Returns:
            Work item data dictionary
        """
        url = f"{self.base_url}/wit/workitems/{work_item_id}"
        params = {"\$expand": "all", "api-version": "7.0"}
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_work_item_from_url(self, url: str) -> Dict:
        """
        Extract work item ID from ADO URL and fetch it
        
        Args:
            url: ADO work item URL
            
        Returns:
            Work item data dictionary
        """
        # Extract work item ID from URL
        match = re.search(r'workitem[s]?[=/](\d+)', url)
        if not match:
            raise ValueError(f"Could not extract work item ID from URL: {url}")
        
        work_item_id = int(match.group(1))
        return self.get_work_item(work_item_id)


class TestRailClient:
    """Client for TestRail API"""
    
    def __init__(self, base_url: str, api_token: str):
        """
        Initialize TestRail client
        
        Args:
            base_url: TestRail base URL (e.g., https://your-instance.testrail.io)
            api_token: TestRail API token
        """
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/v2"
        self.session = requests.Session()
        self.session.auth = (api_token, "")
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_projects(self) -> List[Dict]:
        """Get all projects"""
        response = self.session.get(f"{self.api_url}/get_projects")
        response.raise_for_status()
        return response.json().get('projects', [])
    
    def get_project(self, project_id: int) -> Dict:
        """Get project details"""
        response = self.session.get(f"{self.api_url}/get_project/{project_id}")
        response.raise_for_status()
        return response.json()
    
    def get_suites(self, project_id: int) -> List[Dict]:
        """Get test suites for a project"""
        response = self.session.get(f"{self.api_url}/get_suites/{project_id}")
        response.raise_for_status()
        return response.json()
    
    def get_suite(self, suite_id: int) -> Dict:
        """Get test suite details"""
        response = self.session.get(f"{self.api_url}/get_suite/{suite_id}")
        response.raise_for_status()
        return response.json()
    
    def add_case(self, section_id: int, case_data: TestCaseData) -> Dict:
        """
        Add a new test case to TestRail
        
        Args:
            section_id: Section ID where to add the case
            case_data: TestCaseData object with case details
            
        Returns:
            Created test case data
        """
        # Format steps for TestRail
        custom_steps = []
        for i, step in enumerate(case_data.steps, 1):
            custom_steps.append({
                "content": step['content'],
                "expected": step['expected']
            })
        
        payload = {
            "title": case_data.title,
            "description": case_data.description,
            "preconditions": case_data.preconditions,
            "custom_steps": custom_steps,
            "priority_id": case_data.priority_id,
            "type_id": case_data.type_id
        }
        
        response = self.session.post(
            f"{self.api_url}/add_case/{section_id}",
            data=json.dumps(payload)
        )
        response.raise_for_status()
        return response.json()


class ADOToTestRailConverter:
    """Converts ADO requirements to TestRail test cases"""
    
    def __init__(self, ado_client: ADOClient, testrail_client: TestRailClient):
        """
        Initialize converter
        
        Args:
            ado_client: ADO client instance
            testrail_client: TestRail client instance
        """
        self.ado = ado_client
        self.testrail = testrail_client
    
    def parse_ado_requirement(self, work_item: Dict) -> TestCaseData:
        """
        Parse ADO work item into test case data
        
        Args:
            work_item: ADO work item data
            
        Returns:
            TestCaseData object
        """
        fields = work_item.get('fields', {})
        
        # Extract basic fields
        title = fields.get('System.Title', 'Untitled Test Case')
        description = fields.get('System.Description', '')
        
        # Parse description to extract preconditions and steps
        preconditions, steps = self._parse_description(description)
        
        # Determine priority
        priority_map = {
            '1 - Non Critical': 1,  # Low
            '2 - Medium': 3,  # Medium
            '3 - Critical': 5,  # High
        }
        priority_text = fields.get('Microsoft.VSTS.Common.Priority', '2 - Medium')
        priority_id = priority_map.get(priority_text, 3)
        
        return TestCaseData(
            title=title,
            description=description,
            preconditions=preconditions,
            steps=steps,
            priority_id=priority_id
        )
    
    def _parse_description(self, description: str) -> Tuple[str, List[Dict]]:
        """
        Parse description to extract preconditions and test steps
        
        Expects format with numbered steps followed by expected results
        
        Args:
            description: Description text from ADO
            
        Returns:
            Tuple of (preconditions_text, steps_list)
        """
        if not description:
            return "", []
        
        lines = description.split('\n')
        preconditions = []
        steps = []
        current_step = None
        in_preconditions = True
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Check if this is a numbered step (e.g., "1", "2", etc.)
            if re.match(r'^\d+\s*\$', line):
                # Save previous step if exists
                if current_step:
                    steps.append(current_step)
                current_step = {"content": "", "expected": ""}
                in_preconditions = False
                continue
            
            # If we haven't found steps yet, accumulate preconditions
            if in_preconditions and not current_step:
                # Skip numbered steps section indicators
                if not re.match(r'^\d+\s*:', line):
                    preconditions.append(line)
            elif current_step:
                # We're in a step - determine if it's content or expected result
                # Simple heuristic: lines after "." are expected results
                if current_step["content"] and not current_step["expected"]:
                    # If content exists and expected is empty, add to expected
                    # Check if this looks like an expected result (contains verbs like "is", "appears", "saved")
                    if any(keyword in line.lower() for keyword in ['is ', 'appears', 'saved', 'displayed', 'shown', 'enabled', 'disabled', 'visible']):
                        current_step["expected"] = line
                    else:
                        current_step["content"] += " " + line
                else:
                    current_step["content"] += " " + line if current_step["content"] else line
        
        # Add final step
        if current_step and current_step["content"]:
            steps.append(current_step)
        
        # Clean up steps
        steps = [
            {
                "content": step["content"].strip(),
                "expected": step["expected"].strip() or "Action completed successfully"
            }
            for step in steps
        ]
        
        preconditions_text = '\n'.join(preconditions).strip()
        
        return preconditions_text, steps
    
    def convert_and_upload(
        self,
        ado_url: str,
        testrail_section_id: int
    ) -> Dict:
        """
        Convert ADO requirement and upload to TestRail
        
        Args:
            ado_url: URL or work item ID of ADO requirement
            testrail_section_id: TestRail section ID for the test case
            
        Returns:
            Created test case data from TestRail
        """
        # Fetch ADO work item
        print(f"Fetching ADO work item...")
        if isinstance(ado_url, str) and ado_url.startswith('http'):
            work_item = self.ado.get_work_item_from_url(ado_url)
        else:
            work_item = self.ado.get_work_item(int(ado_url))
        
        print(f"  ✓ Retrieved: {work_item['fields']['System.Title']}")
        
        # Parse to test case format
        print(f"Parsing requirement...")
        test_case = self.parse_ado_requirement(work_item)
        print(f"  ✓ Parsed {len(test_case.steps)} test steps")
        
        # Upload to TestRail
        print(f"Uploading to TestRail (section {testrail_section_id})...")
        created_case = self.testrail.add_case(testrail_section_id, test_case)
        print(f"  ✓ Created test case ID: {created_case['id']}")
        
        return created_case


def main():
    """Main function - example usage"""
    
    # Configuration - UPDATE THESE WITH YOUR VALUES
    ADO_ORG = "your-organization"
    ADO_PROJECT = "your-project"
    ADO_PAT_TOKEN = "your-ado-pat-token"
    
    TESTRAIL_BASE_URL = "https://your-instance.testrail.io"
    TESTRAIL_API_TOKEN = "your-testrail-api-token"
    
    # ADO work item to convert
    ADO_WORK_ITEM_URL = "https://wkaxcess.visualstudio.com/Audit/_workitems/edit/1556295"
    
    # TestRail section where to upload
    TESTRAIL_SECTION_ID = 12345  # Update with your section ID
    
    # Initialize clients
    ado_client = ADOClient(ADO_ORG, ADO_PROJECT, ADO_PAT_TOKEN)
    testrail_client = TestRailClient(TESTRAIL_BASE_URL, TESTRAIL_API_TOKEN)
    
    # Create converter
    converter = ADOToTestRailConverter(ado_client, testrail_client)
    
    # Convert and upload
    try:
        result = converter.convert_and_upload(ADO_WORK_ITEM_URL, TESTRAIL_SECTION_ID)
        print(f"\n✓ Successfully created test case!")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
