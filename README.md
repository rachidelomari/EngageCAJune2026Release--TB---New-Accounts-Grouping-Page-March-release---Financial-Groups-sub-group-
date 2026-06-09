# ADO to TestRail Converter

Automates the conversion of Azure DevOps (ADO) requirements to TestRail test cases.

## Features

- ✅ Fetches requirements directly from ADO work items
- ✅ Intelligently parses preconditions and test steps
- ✅ Creates comprehensive test cases in TestRail
- ✅ Maps ADO priority levels to TestRail priority IDs
- ✅ Supports ADO URLs and work item IDs

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Update the following in `ado_to_testrail.py`:

### Azure DevOps
- `ADO_ORG`: Your ADO organization name
- `ADO_PROJECT`: Your ADO project name
- `ADO_PAT_TOKEN`: Personal Access Token (see [Create a PAT](https://docs.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate))

### TestRail
- `TESTRAIL_BASE_URL`: Your TestRail instance URL (e.g., https://your-instance.testrail.io)
- `TESTRAIL_API_TOKEN`: Your TestRail API token (see [TestRail API Authentication](https://www.gurock.com/testrail/docs/api/getting-started/authentication))
- `TESTRAIL_SECTION_ID`: The section ID in TestRail where test cases will be added

## Usage

### Basic Usage

```python
from ado_to_testrail import ADOClient, TestRailClient, ADOToTestRailConverter

# Initialize clients
ado_client = ADOClient("your-org", "your-project", "your-pat-token")
testrail_client = TestRailClient("https://your-instance.testrail.io", "your-api-token")

# Create converter
converter = ADOToTestRailConverter(ado_client, testrail_client)

# Convert and upload
result = converter.convert_and_upload(
    ado_url="https://wkaxcess.visualstudio.com/Audit/_workitems/edit/1556295",
    testrail_section_id=12345
)

print(f"Created test case ID: {result['id']}")
```

### Command Line

```bash
python ado_to_testrail.py
```

## Test Case Structure

The converter creates test cases with:

- **Title**: From ADO work item title
- **Description**: Full ADO requirement description
- **Preconditions**: Extracted from the beginning of the description
- **Test Steps**: Numbered steps with expected results
- **Priority**: Mapped from ADO priority
- **Type**: Acceptance test (default)

## Priority Mapping

| ADO Priority | TestRail Priority ID | Level |
|---|---|---|
| 1 - Non Critical | 1 | Low |
| 2 - Medium | 3 | Medium |
| 3 - Critical | 5 | High |

## Requirements Format

ADO requirements should follow this structure:

```
Preconditions:
- User is logged in
- Engagement is unlocked

1
Step 1 action description
Expected result

2
Step 2 action description
Expected result
```

## Error Handling

The converter includes error handling for:
- Invalid ADO URLs
- Missing work item IDs
- API authentication failures
- Network errors

## Troubleshooting

### "Could not extract work item ID from URL"
Ensure the ADO URL includes the work item ID (e.g., `?workitem=1556295`)

### "401 Unauthorized"
Verify your API tokens are correct and have appropriate permissions

### "404 Not Found"
Confirm the TestRail section ID exists and you have access to it

## License

MIT
