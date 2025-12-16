# Test Coverage for Agent Tools

This document lists all available tools and their test coverage status.

## File Operations Tools (5/5 tested)

| Tool Name | Test Function | Status | Description |
|-----------|--------------|--------|-------------|
| `read_file` | `test_read_file_workflow` | ✅ Tested | Read file contents |
| `write_file` | `test_write_file_workflow` | ✅ Tested | Write content to file |
| `edit_file` | `test_edit_file_workflow` | ✅ Tested | Replace text in existing file |
| `list_files` | `test_ls_workflow` | ✅ Tested | List directory contents with metadata |
| `file_info` | `test_file_info_workflow` | ✅ Tested | Get file metadata (size, permissions, timestamps) |

## Search Operations Tools (4/4 tested)

| Tool Name | Test Function | Status | Description |
|-----------|--------------|--------|-------------|
| `grep` | `test_grep_workflow` | ✅ Tested | Search for pattern in files |
| `find_file` | `test_find_file_workflow` | ✅ Tested | Find files by name pattern |
| `get_file_structure` | `test_get_file_structure_workflow` | ✅ Tested | Get directory tree structure |
| `code_search` | `test_code_search_workflow` | ✅ Tested | Search code with syntax awareness |

## Bash Operations Tools (3/6 tested)

| Tool Name | Test Function | Status | Description |
|-----------|--------------|--------|-------------|
| `bash` | `test_pwd_workflow` | ✅ Tested | Execute bash commands |
| `git_status` | `test_git_status_workflow` | ✅ Tested | Get git repository status |
| `git_log` | `test_git_log_workflow` | ✅ Tested | Get git commit history |
| `git_diff` | - | ⏳ Not tested | Get git changes diff |
| `git_add` | - | ⏳ Not tested | Stage files for commit |
| `git_commit` | - | ⏳ Not tested | Create git commit |

## Multi-Step Workflows (3/3 tested)

| Test Name | Steps | Description |
|-----------|-------|-------------|
| `test_read_modify_write_workflow` | 2 | Read file → Write modified content |
| `test_sequential_operations_workflow` | 3 | Create file1 → Create file2 → List files |
| `test_multi_action_step_workflow` | 1 (3 actions) | Create 3 files in parallel |

## Coverage Summary

- **Total Tools**: 15
- **Tested Tools**: 12 (80%)
- **Not Tested**: 3 (20%)
  - git_diff
  - git_add
  - git_commit

## Test File Resources

### test_files/
- `toto.py`: Simple Python file for read tests
- `sample_data.txt`: Multi-line text for read/modify tests
- `edit_target.txt`: File with content to be edited
- `grep_target.txt`: File with patterns for grep tests
- `search_target.py`: Python file with functions and classes for code search
- `nested_dir/nested_file.txt`: Nested file for find tests

### generated/
All test output files are created here and gitignored:
- `hello_world.py`: Created by write_file test
- `file1.txt`, `file2.txt`: Created by sequential_operations test
- `parallel1.txt`, `parallel2.txt`, `parallel3.txt`: Created by multi_action test
- `modified_data.txt`: Created by read_modify_write test

## Adding New Tool Tests

To add a test for a new tool:

1. Create test input files in `test_files/` if needed
2. Add test plan to `backendMock/routes/tests.py`:
   ```python
   elif request.test_name == "tool_name":
       steps = [ExecutionStep(...)]
   ```
3. Add test function to `test_execution_workflow.py`:
   ```python
   def test_tool_name_workflow(orchestrator: Orchestrator):
       # Test implementation
   ```
4. Update this coverage document
5. Run tests: `pytest tests/execution_workflow/test_execution_workflow.py -v`
