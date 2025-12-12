# ROADMAP: Build Claude Code-like CLI from Current Architecture

## Current State (✅ DONE)

### Architecture Components
- ✅ **Domain Layer**: RegisteredAgent, AgentIdentity, AgentCapabilities, ConversationContext
- ✅ **Repository Layer**: InMemoryAgentRepository, InMemoryMemoryRepository
- ✅ **Service Layer**: AgentMemoryCoordinator, AgentPromptConstructor, AgentExecutionService, AgentFactory
- ✅ **Orchestrator**: Coordinates all components
- ✅ **Agent**: Base agent with LLM + tool calling
- ✅ **Terminal**: CLI interface with commands (/help, /memory, etc.)
- ✅ **LLM Integration**: OpenAI-compatible chat API with tool calling
- ✅ **Tools Infrastructure**: ToolScheduler, ToolRegistry, ToolBase

### What Works
```bash
python main.py
# User can chat with a single agent
# Agent has access to tools
# Memory is tracked per conversation
# /memory command shows history
```

---

## Target: Claude Code-like Multi-Agent CLI

### Core Features to Implement
1. **File manipulation tools** (read, write, edit files)
2. **Code search tools** (grep, find, navigate codebase)
3. **Bash execution tools** (run commands, manage processes)
4. **Multi-agent specialization** (code agent, git agent, test agent)
5. **Intelligent routing** (route user request to best agent)
6. **Extended context** (multi-file context, cross-agent collaboration)

---

## Implementation Plan

### Phase 1: Essential Tools (Priority 1)

#### Step 1.1: File Manipulation Tools
**Location**: `tools/implementations/file_tools.py`

**Tools to implement**:
```python
class ReadFileTool(ToolBase):
    """Read file contents with line numbers"""
    def execute(self, file_path: str, start_line: int = 0, num_lines: int = 100):
        # Read file with line numbers (cat -n style)
        pass

class WriteFileTool(ToolBase):
    """Write or create new file"""
    def execute(self, file_path: str, content: str):
        # Write entire file content
        pass

class EditFileTool(ToolBase):
    """Edit file with find/replace"""
    def execute(self, file_path: str, old_text: str, new_text: str):
        # Find exact match and replace
        pass

class ListFilesTool(ToolBase):
    """List files in directory"""
    def execute(self, directory: str = ".", pattern: str = "*"):
        # List files matching pattern
        pass
```

**Register tools**:
```python
# In tools/implementations/__init__.py
def register_all_tools():
    from .file_tools import ReadFileTool, WriteFileTool, EditFileTool, ListFilesTool

    registry = get_registry()
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(EditFileTool())
    registry.register(ListFilesTool())
```

**Test**:
```bash
python main.py
User: "Read the file main.py"
Agent: [uses ReadFileTool] "Here's the content..."
```

---

#### Step 1.2: Code Search Tools
**Location**: `tools/implementations/search_tools.py`

**Tools to implement**:
```python
class GrepTool(ToolBase):
    """Search for text pattern in files"""
    def execute(self, pattern: str, directory: str = ".", file_pattern: str = "*.py"):
        # Search with regex, return file:line:content
        pass

class FindFileTool(ToolBase):
    """Find files by name pattern"""
    def execute(self, name_pattern: str, directory: str = "."):
        # Find files matching name
        pass

class GetFileStructureTool(ToolBase):
    """Get directory tree structure"""
    def execute(self, directory: str = ".", max_depth: int = 3):
        # Return tree-like structure
        pass
```

**Test**:
```bash
User: "Find all files that contain 'Agent'"
Agent: [uses GrepTool] "Found in: core/orchestrator.py:21, agents/agent.py:15..."
```

---

#### Step 1.3: Bash Execution Tools
**Location**: `tools/implementations/bash_tools.py`

**Tools to implement**:
```python
class BashTool(ToolBase):
    """Execute bash commands safely"""
    def execute(self, command: str, timeout: int = 30):
        # Execute with subprocess, capture output
        # Security: whitelist safe commands
        pass

class GitTool(ToolBase):
    """Git operations"""
    def execute(self, operation: str, args: list):
        # git status, git diff, git log, etc.
        pass
```

**Security considerations**:
- Whitelist safe commands (ls, cat, git, etc.)
- Blacklist dangerous commands (rm -rf, dd, etc.)
- Run with timeout
- Sanitize arguments

**Test**:
```bash
User: "Show git status"
Agent: [uses GitTool] "On branch main, modified files: ..."
```

---

### Phase 2: Multi-Agent Specialization (Priority 2)

#### Step 2.1: Define Agent Profiles
**Location**: `agents/profiles/`

**Create specialized agent configs**:
```python
# agents/profiles/code_agent.py
CODE_AGENT_CONFIG = {
    "name": "CodeAgent",
    "description": "Expert in reading, writing, and refactoring code",
    "authorized_tools": [
        "read_file",
        "write_file",
        "edit_file",
        "grep",
        "find_file",
        "get_file_structure"
    ],
    "system_prompt": """You are a code expert.
You can read, write, edit, and navigate codebases.
When asked to modify code, always read the file first.
Make precise, targeted changes."""
}

# agents/profiles/git_agent.py
GIT_AGENT_CONFIG = {
    "name": "GitAgent",
    "description": "Expert in git version control",
    "authorized_tools": [
        "git",
        "read_file",
        "bash"
    ],
    "system_prompt": """You are a git expert.
You can check status, create commits, manage branches.
Always check git status before making changes."""
}

# agents/profiles/bash_agent.py
BASH_AGENT_CONFIG = {
    "name": "BashAgent",
    "description": "Expert in running shell commands",
    "authorized_tools": [
        "bash",
        "list_files"
    ],
    "system_prompt": """You are a bash expert.
You can execute commands and manage processes.
Explain what commands do before running them."""
}
```

#### Step 2.2: Register Multiple Agents
**Location**: `main.py`

**Modify agent registration**:
```python
def _register_agents(self):
    from agents.profiles import CODE_AGENT_CONFIG, GIT_AGENT_CONFIG, BASH_AGENT_CONFIG

    agent_repository = self.orchestrator.get_agent_repository()

    # Register specialized agents
    for config in [CODE_AGENT_CONFIG, GIT_AGENT_CONFIG, BASH_AGENT_CONFIG]:
        agent = RegisteredAgent.create_new(
            name=config["name"],
            description=config["description"],
            authorized_tools=config["authorized_tools"],
            system_prompt=config["system_prompt"]
        )
        agent_repository.save(agent)
        logger.info("APP", f"Registered {config['name']}")

    return agent_repository
```

**Test**:
```bash
python main.py
# Should register 3 agents: CodeAgent, GitAgent, BashAgent
```

---

### Phase 3: Intelligent Agent Routing (Priority 3)

#### Step 3.1: Implement Routing Service
**Location**: `core/services/agent_routing_service.py`

**Routing logic**:
```python
class AgentRoutingService:
    """Route user requests to the best agent"""

    def __init__(self, agent_repository: AgentRepository):
        self._agent_repository = agent_repository
        self._keyword_map = {
            "git": ["git", "commit", "branch", "merge", "push", "pull"],
            "code": ["read", "write", "edit", "refactor", "function", "class"],
            "bash": ["run", "execute", "command", "install", "process"]
        }

    def route_to_best_agent(self, user_input: str) -> str:
        """
        Determine best agent for request.

        Returns:
            agent_id of best matching agent
        """
        user_lower = user_input.lower()

        # Score each agent
        scores = {}
        for agent in self._agent_repository.find_active():
            score = 0
            agent_name = agent.get_agent_name().lower()

            # Check keyword matches
            if "git" in agent_name and any(kw in user_lower for kw in self._keyword_map["git"]):
                score += 10
            if "code" in agent_name and any(kw in user_lower for kw in self._keyword_map["code"]):
                score += 10
            if "bash" in agent_name and any(kw in user_lower for kw in self._keyword_map["bash"]):
                score += 10

            scores[agent.get_agent_id()] = score

        # Return agent with highest score, or first active agent
        if scores:
            best_agent_id = max(scores, key=scores.get)
            if scores[best_agent_id] > 0:
                return best_agent_id

        # Default: first active agent
        active = self._agent_repository.find_active()
        return active[0].get_agent_id() if active else None
```

#### Step 3.2: Integrate Routing into Orchestrator
**Location**: `core/orchestrator.py`

**Add routing**:
```python
class Orchestrator:
    def __init__(self, llm_config: Optional[LLMWrapperConfig] = None):
        # ... existing setup ...

        # Add routing service
        self._routing_service = AgentRoutingService(
            agent_repository=self._agent_repository
        )

    def process_user_input(self, user_input: str) -> AgentOutput:
        # Route to best agent
        agent_id = self._routing_service.route_to_best_agent(user_input)

        if not agent_id:
            return AgentOutput(
                response="No agents available",
                success=False,
                error="No agents"
            )

        # Execute with routed agent
        result = self._execution_service.execute_agent(
            agent_id=agent_id,
            user_input=user_input
        )

        return result.output
```

**Test**:
```bash
User: "Show me git status"
# Should route to GitAgent

User: "Read the file main.py"
# Should route to CodeAgent

User: "Run ls -la"
# Should route to BashAgent
```

---

### Phase 4: Extended Context & Collaboration (Priority 4)

#### Step 4.1: Multi-file Context
**Location**: `core/services/agent_prompt_constructor.py`

**Add context methods**:
```python
class AgentPromptConstructor:
    def build_with_file_context(
        self,
        conversation_context: ConversationContext,
        file_paths: List[str]
    ) -> List[Message]:
        """Build messages with additional file context"""

        messages = self.build_conversation_messages(conversation_context)

        # Add file context before user message
        file_context = self._build_file_context(file_paths)
        messages.insert(-1, {
            "role": "system",
            "content": f"Relevant files:\n{file_context}"
        })

        return messages

    def _build_file_context(self, file_paths: List[str]) -> str:
        """Format file contents for context"""
        context_parts = []
        for path in file_paths:
            try:
                with open(path, 'r') as f:
                    content = f.read()
                context_parts.append(f"File: {path}\n```\n{content}\n```")
            except:
                pass
        return "\n\n".join(context_parts)
```

#### Step 4.2: Cross-Agent Collaboration
**Location**: Agent execution flow

**Allow agents to delegate**:
```python
class DelegateTool(ToolBase):
    """Delegate task to another agent"""

    def __init__(self, orchestrator):
        super().__init__()
        self._orchestrator = orchestrator

    def execute(self, target_agent: str, task: str):
        """
        Delegate task to another specialized agent.

        Args:
            target_agent: Name of agent to delegate to
            task: Task description

        Returns:
            Result from delegated agent
        """
        # Find target agent
        agent = self._orchestrator.get_agent_repository().find_by_name(target_agent)

        if not agent:
            return f"Agent {target_agent} not found"

        # Execute on target agent
        result = self._orchestrator._execution_service.execute_agent(
            agent_id=agent.get_agent_id(),
            user_input=task
        )

        return result.output.response
```

**Example workflow**:
```
User: "Read main.py and create a git commit"

CodeAgent: [reads main.py with ReadFileTool]
CodeAgent: [delegates to GitAgent] "Create commit for changes in main.py"
GitAgent: [uses GitTool] "Created commit: ..."
CodeAgent: "I've read the file and GitAgent created the commit"
```

---

## Testing Strategy

### Unit Tests
```bash
# Test individual tools
python -m pytest tests/tools/test_file_tools.py
python -m pytest tests/tools/test_search_tools.py
python -m pytest tests/tools/test_bash_tools.py

# Test routing
python -m pytest tests/services/test_routing_service.py
```

### Integration Tests
```bash
# Test multi-agent workflow
python -m pytest tests/integration/test_multi_agent_workflow.py
```

### Manual Testing
```bash
# Start CLI and test scenarios
python main.py

# Scenario 1: File reading
User: "Read the orchestrator code"
Expected: CodeAgent reads core/orchestrator.py

# Scenario 2: Git operations
User: "Show me recent commits"
Expected: GitAgent shows git log

# Scenario 3: Bash commands
User: "List all Python files"
Expected: BashAgent runs find . -name "*.py"
```

---

## CLI Commands to Add

### Agent Management
```python
# cli/commands/agent_command.py

class AgentCommand(BaseCommand):
    """Manage agents"""

    def execute(self, args: List[str]):
        if not args:
            self._list_agents()
        elif args[0] == "switch":
            self._switch_agent(args[1])
        elif args[0] == "info":
            self._show_agent_info(args[1])
```

**Usage**:
```bash
/agents              # List all agents with stats
/agent switch Code   # Switch to CodeAgent
/agent info Git      # Show GitAgent details
```

---

## Deployment Checklist

### Before Launch
- [ ] All essential tools implemented (file, search, bash)
- [ ] 3 specialized agents registered (Code, Git, Bash)
- [ ] Routing service routes correctly
- [ ] Tool execution is secure (sanitized inputs)
- [ ] Memory isolation works per agent
- [ ] CLI commands functional (/agents, /memory, /help)
- [ ] Error handling robust
- [ ] Logging comprehensive

### Performance
- [ ] Tool execution < 2 seconds
- [ ] Agent response < 5 seconds
- [ ] Memory usage < 500MB for 3 agents
- [ ] No memory leaks in long sessions

### Documentation
- [ ] Tool documentation in TOOLS_CONFIGURATION.md
- [ ] Agent profiles documented
- [ ] User guide for CLI commands
- [ ] Architecture diagram updated

---

## Next Steps

1. **Week 1**: Implement Phase 1 (Essential Tools)
2. **Week 2**: Implement Phase 2 (Multi-Agent Specialization)
3. **Week 3**: Implement Phase 3 (Intelligent Routing)
4. **Week 4**: Implement Phase 4 (Extended Context)
5. **Week 5**: Testing, refinement, documentation

---

## Architecture Diagram

```
User Input
    ↓
Terminal CLI
    ↓
Orchestrator
    ↓
AgentRoutingService → Selects best agent
    ↓
AgentExecutionService → Executes agent
    ↓
Agent (CodeAgent/GitAgent/BashAgent)
    ↓
LLM + Tools
    ↓
Response
```

---

## Success Metrics

### User Experience
- User can manipulate files without leaving CLI
- User can navigate codebase with natural language
- User can execute commands safely
- Agents route intelligently to correct specialist

### Technical
- 90%+ routing accuracy
- < 5 second response time
- Zero critical errors in 100 operations
- Memory stable over 1 hour session

---

## Current vs Target

| Feature | Current State | Target State |
|---------|--------------|--------------|
| Agents | 1 generic agent | 3+ specialized agents |
| Tools | Basic (1-2) | Comprehensive (10+) |
| Routing | None (single agent) | Intelligent routing |
| File ops | None | Read/Write/Edit |
| Code search | None | Grep/Find/Navigate |
| Bash | None | Safe command execution |
| Context | Single file | Multi-file context |
| Collaboration | None | Cross-agent delegation |

---

## Resources

### Reference Implementations
- **Claude Code**: https://github.com/anthropics/claude-code
- **Gemini CLI**: Google's CLI implementation
- **Cursor**: AI code editor patterns

### Key Technologies
- **LLM**: OpenAI-compatible API (function calling)
- **Tools**: Python subprocess, file I/O, regex
- **Routing**: Rule-based → ML-based (future)
- **Context**: In-memory → Vector DB (future)
