# Execution Workflow Tests

This directory contains integration tests for the agent execution workflow.

## Structure

- `test_execution_workflow.py`: Main test file containing workflow tests
- `test_files/`: Reference files used by tests
- `expected_outputs/`: Expected output files for comparison
- `generated/`: Directory where tests generate output files (gitignored)

## Test Cases

### File Operations Tests
- `test_read_file_workflow`: Tests reading a file with read_file tool
- `test_write_file_workflow`: Tests writing a file with write_file tool
- `test_edit_file_workflow`: Tests editing file content with edit_file tool
- `test_file_info_workflow`: Tests getting file metadata with file_info tool
- `test_ls_workflow`: Tests listing directory contents with list_files tool

### Search Operations Tests
- `test_grep_workflow`: Tests pattern search with grep tool
- `test_find_file_workflow`: Tests finding files by pattern with find_file tool
- `test_get_file_structure_workflow`: Tests getting directory structure with get_file_structure tool
- `test_code_search_workflow`: Tests searching code patterns with code_search tool

### Bash Operations Tests
- `test_pwd_workflow`: Tests getting current directory with bash tool
- `test_git_status_workflow`: Tests git status with git_status tool
- `test_git_log_workflow`: Tests git commit history with git_log tool

### Multi-Step Tests
- `test_read_modify_write_workflow`: Tests reading a file and writing modified content (2 steps with dependency)
- `test_sequential_operations_workflow`: Tests creating two files then listing them (3 steps with dependencies)
- `test_multi_action_step_workflow`: Tests executing multiple actions in parallel within a single step

## Running Tests

Tests must be run from the project root directory to ensure proper module imports:

```bash
cd /home/maboye/workplace/maboye.ai
source venv/bin/activate
pytest tests/execution_workflow/test_execution_workflow.py -v
```

Or run all execution workflow tests:

```bash
pytest tests/execution_workflow/ -v
```

Note: The backend mock must be running on localhost:8000 before running tests.
