"""
Prompt Builder

Builds and manages system and user prompts for agents.
"""

from enum import Enum
from typing import Dict
from tools.tool_ids import ToolId


class PromptRole(Enum):
    """Enumeration of available prompt roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class PromptId(Enum):
    """Enumeration of available prompt templates."""

    TASKS_AGENT = "tasks_agent"
    EXEC_AGENT = "exec_agent"
    DEFAULT_AGENT = "default_agent"
    VERIFICATION = "verification"


class PromptBuilder:
    """
    Builder for constructing prompts for different roles.

    Provides methods to incrementally build prompts by adding
    lines or blocks of text.
    """

    def __init__(self):
        """Initialize empty prompts for system, user, and assistant roles."""
        self._prompts: Dict[str, str] = {
            PromptRole.SYSTEM.value: "",
            PromptRole.USER.value: "",
            PromptRole.ASSISTANT.value: ""
        }

    def add_line(self, role: PromptRole, line: str) -> None:
        """
        Add a single line to the specified role prompt.

        Args:
            role: Role identifier from PromptRole enum
            line: Text line to append
        """
        role_key = role.value
        if role_key not in self._prompts:
            self._prompts[role_key] = ""

        if self._prompts[role_key]:
            self._prompts[role_key] += "\n"
        self._prompts[role_key] += line

    def add_block(self, role: PromptRole, block: str) -> None:
        """
        Add a text block to the specified role prompt.

        Args:
            role: Role identifier from PromptRole enum
            block: Text block to append
        """
        role_key = role.value
        if role_key not in self._prompts:
            self._prompts[role_key] = ""

        if self._prompts[role_key]:
            self._prompts[role_key] += "\n\n"
        self._prompts[role_key] += block

    def get_prompt(self, role: PromptRole) -> str:
        """
        Retrieve prompt for a specific role.

        Args:
            role: Role identifier from PromptRole enum

        Returns:
            Prompt string for the specified role
        """
        return self._prompts.get(role.value, "")

    def get_prompts(self) -> Dict[str, str]:
        """
        Retrieve all built prompts.

        Returns:
            Dictionary mapping role values to prompt strings
        """
        return self._prompts.copy()
    
    def clear_prompt(self, role: PromptRole) -> None:
        """
        Clear prompt content for a specific role.

        Args:
            role: Role identifier from PromptRole enum
        """
        self._prompts[role.value] = ""

    def clear_prompts(self) -> None:
        """
        Clear prompts
        """
        self._prompts.clear()

    @staticmethod
    def get_prompt_by_id(prompt_id: PromptId) -> str:
        """
        Retrieve a predefined prompt template by ID.

        Args:
            prompt_id: Identifier from PromptId enum

        Returns:
            Prompt template string
        """
        return get_prompt_template(prompt_id)


def _build_prompt_templates() -> Dict[PromptId, str]:
    """
    Build prompt templates with composition support.

    Returns:
        Dictionary mapping PromptId to prompt strings
    """
    verification_prompt = f"""
## DECISION PROTOCOL (POST-EXECUTION)
Evaluate the tool output strictly in this order. Stop at the first match.

1. **GLOBAL COMPLETION (STRICT)**
   - **Condition**: The tool output proves the **GLOBAL USER QUERY** is 100% finished AND there are **NO remaining actions** required (e.g., creating files, moving items).
   - **Action**: Call `{ToolId.TASKS_COMPLETED.value}`.

2. **FAILURE (MISSING PREREQUISITE)**
   - **Condition**: The step was a "Search", "Find", or "Read" operation needed for a future action, BUT returned **EMPTY**, **NONE**, or **NOT FOUND**.
   - **Action**: Call `{ToolId.TASK_ERROR.value}`.

3. **STEP SUCCESS (CONTINUE WORKFLOW)**
   - **Condition**: The specific step objective is met (e.g., directory exists), but the **GLOBAL USER QUERY** has remaining steps (e.g., creating/moving a file).
   - **Action**: Call `{ToolId.TASK_SUCCESS.value}`.

4. **FAILURE (GENERIC)**
   - **Condition**: Operation failed, exit code != 0, or traceback occurred.
   - **Action**: Call `{ToolId.TASK_ERROR.value}`.
"""

    return {
        PromptId.VERIFICATION: verification_prompt,

        PromptId.EXEC_AGENT: f"""
ROLE: Autonomous Execution Agent.
PRIORITY: The USER QUERY overrides the specific task description.

## CORE OPERATING RULES

1. **GLOBAL CONTEXT AWARENESS**
   - You are a workflow manager.
   - Always compare the **Tool Output** against the **GLOBAL USER QUERY**.
   - **CRITICAL DISTINCTION**:
     - If the *current step* is done but the *GLOBAL QUERY* is incomplete -> You MUST proceed to the next step (do NOT terminate).
     - Only TERMINATE with `tasks_completed` if the **ENTIRE GLOBAL USER QUERY** is fully satisfied (nothing left to do).

2. **MUTATION SAFETY PROTOCOL**
   - **READ FIRST**: Inspect resources before modifying.
   - **USE ANCHORS**: Use rigid identifiers (Line Numbers, IDs).
   - **UNIQUENESS**: Ensure selectors match exactly one target.

3. **OUTPUT FORMAT**
   - **STRICT JSON ONLY**: No markdown blocks. No comments.

## JSON SCHEMA
{{
  "tool_name": "exact_tool_name",
  "arguments": {{
    "arg_key": "arg_value"
  }}
}}
{verification_prompt}
""",

        PromptId.TASKS_AGENT: """
You are a Senior Software Architect.
Your role is to analyze the user request and the CONVERSATION HISTORY to decide if a workflow is needed.

OUTPUT RULES:
1. Respond ONLY in strict JSON format.
2. NO conversational text before or after the JSON.
3. JSON SCHEMA:
{
  "analyse": "Brief reasoning about the request.",
  "tasks": [
    {
      "step": "Actionable instruction.",
      "expected_outcome": "Verifiable condition."
    }
  ]
}

## DECISION LOGIC (CRITICAL)

### 1. DIRECT RESPONSE (NO TASKS)
Return an EMPTY list `[]` for "tasks" in these cases:
- **MEMORY RECALL**: The user asks for information present in the Chat History (e.g., "What was the sequence?", "Summarize what we just did"). Do NOT create a task to "retrieve" this; the Execution Agent can answer directly.
- **SIMPLE CONVERSATION**: Greetings, compliments, or general questions unrelated to the codebase.
- **CLARIFICATION**: If the user's request is too vague to plan (e.g., "Fix the bug" without saying which one), return empty tasks to force a dialogue.

### 2. WORKFLOW GENERATION (CREATE TASKS)
Create a list of tasks ONLY if the request requires interacting with the System, Codebase, or Files.

## TASK DESIGN GUIDELINES

1. **CONTEXTUAL CHAINING (STATE DEPENDENCY)**
   - The agents share execution memory. You must link tasks dynamically.
   - **BAD**: "Step 2: Read /home/user/project/main.py" (Hardcoded assumption).
   - **GOOD**: "Step 2: Read the content of the file identified in Step 1."
   - **GOOD**: "Step 3: Apply the fix analyzed in Step 2 to the file located in Step 1."

2. **AVOID REDUNDANCY (MEMORY PERSISTENCE)**
   - Once a file is read or a search is performed, the content is in the Agent's context.
   - **NEVER** create a task to "Read file X" if Step 1 was "Find and Read file X".
   - Instead, use: "Analyze the previously loaded content of file X..."

3. **LOGICAL GROUPING**
   - Merge prerequisites with actions.
   - **Example**: "Move the file found in Step 1 to 'tmp/', creating the directory if it doesn't exist."

4. **OUTCOME VERIFICATION**
   - The `expected_outcome` must be the definition of done.
""",

        PromptId.DEFAULT_AGENT: """
You are a helpful AI assistant.
Respond naturally to user queries and conversations.
"""
    }


PROMPT_TEMPLATES = _build_prompt_templates()


def get_prompt_template(prompt_id: PromptId) -> str:
    """
    Retrieve a prompt template by ID from the templates map.

    Args:
        prompt_id: Identifier from PromptId enum

    Returns:
        Prompt template string, empty string if not found
    """
    return PROMPT_TEMPLATES.get(prompt_id, "")
