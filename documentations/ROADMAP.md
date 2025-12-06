# Development Roadmap

Complete step-by-step plan to build a Claude Code-like agent system.

---

## Current Status

**Completed:**
- ✅ Mock LLM backend (OpenAI-compatible API)
- ✅ Logger system with file rotation
- ✅ LLM wrapper with retry logic
- ✅ Base Agent class
- ✅ Interactive Terminal
- ✅ Configuration management
- ✅ .env loading fixed

---

## Phase 1: Tool Foundation (Simple Tools)

### Step 1: File Operations
**File:** `tools/file_ops.py`

Create basic file operations:
- `read_file(path, offset=0, limit=None)` - Read file contents
- `write_file(path, content)` - Write/create file
- `edit_file(path, old_string, new_string)` - Replace text in file
- `file_exists(path)` - Check if file exists
- `get_file_info(path)` - Get file metadata

**Why:** Foundation for code reading and modification

---

### Step 2: Search Operations
**File:** `tools/search.py`

Create search capabilities:
- `glob_files(pattern, path='.')` - Find files by pattern
- `grep_content(pattern, path='.', files_only=False)` - Search file contents
- `list_directory(path)` - List directory contents

**Why:** Find relevant files in codebase

---

### Step 3: Shell Execution
**File:** `tools/shell.py`

Create command execution:
- `run_command(cmd, timeout=30)` - Execute shell command
- `run_in_background(cmd)` - Background execution
- `kill_process(pid)` - Process management

**Why:** Run tests, build, and other operations

---

### Step 4: Git Operations
**File:** `tools/git_ops.py`

Create Git integration:
- `git_status()` - Check repository status
- `git_diff(file=None)` - View changes
- `git_add(files)` - Stage files
- `git_commit(message)` - Create commit
- `git_log(count=10)` - View history

**Why:** Version control integration

---

## Phase 2: Tool System Architecture

### Step 5: Tool Base Class
**File:** `tools/base_tool.py`

Create unified tool interface:
```python
class Tool:
    name: str
    description: str
    parameters: dict

    def execute(self, **kwargs) -> ToolResult
    def validate(self, **kwargs) -> bool
```

**Why:** Standardize tool execution

---

### Step 6: Tool Registry
**File:** `tools/registry.py`

Create tool management:
- `register_tool(tool)` - Add tool
- `get_tool(name)` - Retrieve tool
- `list_tools()` - Available tools
- `execute_tool(name, **kwargs)` - Execute with validation

**Why:** Central tool management

---

## Phase 3: Agent Enhancement

### Step 7: Tool-Enabled Agent
**Update:** `agents/agent.py`

Add tool support:
- Parse tool calls from LLM responses
- Execute tools safely
- Return results to LLM
- Handle tool errors

**Why:** Enable agent to use tools

---

### Step 8: Context Manager
**File:** `agents/context.py`

Create context assembly:
- `load_project_files()` - Read relevant files
- `build_context(query)` - Assemble context for LLM
- `manage_token_budget()` - Keep within limits
- `track_modifications()` - Monitor changes

**Why:** Provide relevant context to LLM

---

### Step 9: Conversation Memory
**Update:** `agents/agent.py`

Add multi-turn support:
- Maintain conversation history
- Track tool usage across turns
- Persist session state
- Resume conversations

**Why:** Context continuity

---

## Phase 4: Intelligence Layer

### Step 10: Planning Agent
**File:** `agents/planner.py`

Create task decomposition:
- Break complex tasks into steps
- Generate execution plan
- Validate plan feasibility
- Track plan progress

**Why:** Handle complex multi-step tasks

---

### Step 11: Safety Layer
**File:** `agents/safety.py`

Add safety checks:
- Validate tool inputs
- Check for dangerous operations
- Secret scanning
- Path traversal prevention
- Command injection prevention

**Why:** Prevent harmful operations

---

## Phase 5: Advanced Features

### Step 12: Test Runner
**File:** `tools/test_runner.py`

Create test execution:
- Detect test framework
- Run tests
- Parse test results
- Report failures to agent

**Why:** Enable test-driven development

---

### Step 13: Observability
**File:** `tools/telemetry.py`

Add monitoring:
- Track tool usage
- Log LLM interactions
- Measure token usage
- Performance metrics

**Why:** Debug and optimize

---

### Step 14: Session Manager
**File:** `agents/session.py`

Add persistence:
- Save/load sessions
- State checkpointing
- Resume interrupted work
- Session history

**Why:** Long-running workflows

---

### Step 15: Complete Workflow
**Update:** `main.py`

Integrate everything:
- Tool-enabled conversations
- Automatic planning for complex tasks
- Safety validation
- Test execution loops
- Session persistence

**Why:** Production-ready system

---

## Implementation Order

### Week 1: Tools Foundation
- Day 1-2: File operations + Search
- Day 3-4: Shell execution + Git
- Day 5: Tool base class + Registry

### Week 2: Agent Integration
- Day 1-2: Tool-enabled agent
- Day 3-4: Context manager
- Day 5: Conversation memory

### Week 3: Intelligence
- Day 1-2: Planning agent
- Day 3-4: Safety layer
- Day 5: Test runner

### Week 4: Polish
- Day 1-2: Observability
- Day 3-4: Session manager
- Day 5: Integration and testing

---

## Success Criteria

**Phase 1 Complete:**
- Can read, write, edit files
- Can search codebase
- Can execute commands
- Can perform Git operations

**Phase 2 Complete:**
- Unified tool interface
- Tools registered and discoverable
- Safe tool execution

**Phase 3 Complete:**
- Agent can use tools
- Context assembled automatically
- Multi-turn conversations work

**Phase 4 Complete:**
- Complex tasks decomposed
- Safety checks prevent errors
- Tests can be run and interpreted

**Phase 5 Complete:**
- Full observability
- Sessions persist
- Production-ready workflow

---

## Testing Strategy

**Unit Tests:**
- Each tool independently
- Tool registry
- Safety validators

**Integration Tests:**
- Agent + Tools
- Context + LLM
- Complete workflows

**End-to-End Tests:**
- Real coding tasks
- Multi-step operations
- Error recovery

---

## Next Steps

1. Start with Phase 1, Step 1 (File Operations)
2. Test each component before moving forward
3. Update this document as you progress
4. Mark completed items with ✅

**Current Task:** Create `tools/file_ops.py`
