# Action-Based Execution System

**Nouveau workflow:**
```
User: "Read main.py and add a comment"
    ↓
LLM: Génère un plan d'action (JSON)
    {
      "steps": [
        {
          "description": "Read main.py to understand structure",
          "actions": [
            {"tool": "read_file", "args": {"file_path": "main.py"}}
          ]
        },
        {
          "description": "Add comment at line 10",
          "actions": [
            {
              "tool": "edit_file",
              "args": {
                "file_path": "main.py",
                "old_text": "def main():",
                "new_text": "# Main entry point\ndef main():"
              }
            }
          ]
        }
      ]
    }
    ↓
System: Affiche le plan à l'utilisateur
    ↓
User: Confirme ou rejette
    ↓
System: Exécute step by step
    ↓
System: Retourne résultats au LLM
    ↓
LLM: Analyse résultats, continue ou termine
```

---

## Architecture Cible

### Composants Nécessaires

#### 1. ExecutionPlan (Value Object)
```python
@dataclass(frozen=True)
class ActionStep:
    """Single action to execute"""
    tool_name: str
    arguments: Dict[str, Any]
    description: str

@dataclass(frozen=True)
class ExecutionStep:
    """Step containing one or more actions"""
    step_number: int
    description: str
    actions: List[ActionStep]
    depends_on: Optional[int] = None  # Previous step dependency

@dataclass(frozen=True)
class ExecutionPlan:
    """Complete execution plan from LLM"""
    plan_id: str  # UUID
    user_query: str
    steps: List[ExecutionStep]
    estimated_duration: Optional[str] = None
    requires_confirmation: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_dangerous(self) -> bool:
        """Check if any action is marked dangerous"""
        for step in self.steps:
            for action in step.actions:
                tool = get_tool(action.tool_name)
                if tool and tool.metadata.dangerous:
                    return True
        return False
```

#### 2. PlanExecutionService
```python
class PlanExecutionService:
    """
    Executes action plans step by step.

    Responsibilities:
    - Execute each step in order
    - Collect results
    - Handle errors and rollback if needed
    - Track execution state
    """

    def __init__(
        self,
        tool_scheduler: ToolScheduler,
        allow_dangerous: bool = False
    ):
        self._tool_scheduler = tool_scheduler
        self._allow_dangerous = allow_dangerous
        self._execution_history: List[ExecutionResult] = []

    def execute_plan(
        self,
        plan: ExecutionPlan,
        confirm_dangerous: bool = False
    ) -> PlanExecutionResult:
        """
        Execute complete plan step by step.

        Args:
            plan: ExecutionPlan to execute
            confirm_dangerous: User confirmed dangerous actions

        Returns:
            PlanExecutionResult with all step results
        """
        # Check if plan is dangerous and needs confirmation
        if plan.is_dangerous() and not confirm_dangerous:
            raise PlanExecutionError(
                "Plan contains dangerous actions and requires confirmation"
            )

        step_results = []

        for step in plan.steps:
            # Check dependencies
            if step.depends_on is not None:
                if not self._dependency_satisfied(step.depends_on, step_results):
                    raise PlanExecutionError(
                        f"Dependency {step.depends_on} not satisfied for step {step.step_number}"
                    )

            # Execute all actions in step
            step_result = self._execute_step(step)
            step_results.append(step_result)

            # Stop if step failed
            if not step_result.success:
                return PlanExecutionResult(
                    plan_id=plan.plan_id,
                    completed_steps=step_results,
                    success=False,
                    error=f"Step {step.step_number} failed: {step_result.error}"
                )

        return PlanExecutionResult(
            plan_id=plan.plan_id,
            completed_steps=step_results,
            success=True
        )

    def _execute_step(self, step: ExecutionStep) -> StepExecutionResult:
        """Execute single step with all its actions"""
        action_results = []

        for action in step.actions:
            try:
                # Execute tool
                result = self._tool_scheduler.execute(
                    tool_name=action.tool_name,
                    **action.arguments
                )

                action_results.append(ActionResult(
                    tool_name=action.tool_name,
                    success=True,
                    result=result
                ))

            except Exception as e:
                action_results.append(ActionResult(
                    tool_name=action.tool_name,
                    success=False,
                    error=str(e)
                ))

                # Stop step on first error
                return StepExecutionResult(
                    step_number=step.step_number,
                    success=False,
                    action_results=action_results,
                    error=str(e)
                )

        return StepExecutionResult(
            step_number=step.step_number,
            success=True,
            action_results=action_results
        )
```

#### 3. PlanningAgent (Nouveau type d'agent)
```python
class PlanningAgent:
    """
    Agent specialized in creating execution plans.

    Does NOT execute tools directly. Instead, generates
    structured JSON plans for the PlanExecutionService.
    """

    def __init__(
        self,
        llm: LLMWrapper,
        available_tools: List[Tool]
    ):
        self._llm = llm
        self._available_tools = available_tools
        self._planning_prompt = self._build_planning_prompt()

    def create_plan(self, user_query: str) -> ExecutionPlan:
        """
        Create execution plan from user query.

        Args:
            user_query: User's request

        Returns:
            ExecutionPlan with structured steps
        """
        # Build prompt for LLM
        messages = [
            {
                "role": "system",
                "content": self._planning_prompt
            },
            {
                "role": "user",
                "content": f"Create a plan to: {user_query}"
            }
        ]

        # Get plan from LLM (JSON response)
        response = self._llm.chat(messages, response_format="json")
        plan_json = json.loads(response.choices[0].message.content)

        # Parse JSON into ExecutionPlan
        return self._parse_plan(plan_json, user_query)

    def _build_planning_prompt(self) -> str:
        """Build system prompt for planning"""
        tools_description = self._format_available_tools()

        return f"""You are a planning agent that creates execution plans.

Your task is to break down user requests into step-by-step action plans.

Available tools:
{tools_description}

Output format (JSON):
{{
  "steps": [
    {{
      "step_number": 1,
      "description": "Read the file to understand structure",
      "actions": [
        {{
          "tool_name": "read_file",
          "arguments": {{"file_path": "main.py"}},
          "description": "Read main.py contents"
        }}
      ]
    }},
    {{
      "step_number": 2,
      "description": "Make the requested modification",
      "actions": [
        {{
          "tool_name": "edit_file",
          "arguments": {{
            "file_path": "main.py",
            "old_text": "...",
            "new_text": "..."
          }},
          "description": "Add comment to main function"
        }}
      ],
      "depends_on": 1
    }}
  ],
  "estimated_duration": "5 seconds",
  "requires_confirmation": true
}}

Rules:
1. Break complex tasks into small steps
2. Each step should have clear description
3. List all required actions for each step
4. Set depends_on for steps that need previous results
5. Mark requires_confirmation=true for destructive operations
6. Be precise with tool arguments
7. Explain what each action does"""
```

---

## Workflow Complet

### 1. Réception de la requête

```python
# core/orchestrator.py

def process_user_input(self, user_input: str) -> AgentOutput:
    """
    Process user input with planning approach.

    Workflow:
    1. Route to appropriate agent
    2. Agent creates execution plan (JSON)
    3. Display plan to user
    4. Get user confirmation if needed
    5. Execute plan step by step
    6. Return results
    """
    # 1. Route to agent
    agent = self._route_to_agent(user_input)

    # 2. Create execution plan (LLM generates JSON)
    plan = agent.create_execution_plan(user_input)

    # 3. Display plan to user
    self._display_plan(plan)

    # 4. Get confirmation if needed
    if plan.requires_confirmation:
        confirmed = self._get_user_confirmation(plan)
        if not confirmed:
            return AgentOutput(
                response="Plan cancelled by user",
                success=False
            )

    # 5. Execute plan
    result = self._plan_execution_service.execute_plan(
        plan,
        confirm_dangerous=True
    )

    # 6. Format and return results
    return self._format_execution_result(result)
```

### 2. Affichage du plan

```python
def _display_plan(self, plan: ExecutionPlan):
    """Display plan to user for review"""
    print("\n" + "="*60)
    print("EXECUTION PLAN")
    print("="*60)
    print(f"Query: {plan.user_query}")
    print(f"Steps: {len(plan.steps)}")
    if plan.estimated_duration:
        print(f"Estimated duration: {plan.estimated_duration}")
    print()

    for step in plan.steps:
        print(f"Step {step.step_number}: {step.description}")
        for action in step.actions:
            tool_desc = f"  → {action.tool_name}"
            if action.description:
                tool_desc += f": {action.description}"
            print(tool_desc)

            # Show key arguments
            for key, value in action.arguments.items():
                print(f"      {key}: {str(value)[:50]}...")
        print()

    if plan.is_dangerous():
        print("⚠️  WARNING: This plan contains potentially dangerous operations")
    print("="*60)
```

### 3. Confirmation utilisateur

```python
def _get_user_confirmation(self, plan: ExecutionPlan) -> bool:
    """Get user confirmation for plan execution"""
    while True:
        response = input("Execute this plan? [y/n/details]: ").lower()

        if response == 'y':
            return True
        elif response == 'n':
            return False
        elif response == 'details':
            self._show_plan_details(plan)
        else:
            print("Please answer 'y', 'n', or 'details'")
```

---

## Exemple Concret

### Requête utilisateur
```
User: "Read main.py and add docstring to the main() function"
```

### Plan généré par le LLM
```json
{
  "steps": [
    {
      "step_number": 1,
      "description": "Read main.py to locate main() function",
      "actions": [
        {
          "tool_name": "read_file",
          "arguments": {"file_path": "main.py"},
          "description": "Read entire file to understand structure"
        }
      ]
    },
    {
      "step_number": 2,
      "description": "Add docstring to main() function",
      "actions": [
        {
          "tool_name": "edit_file",
          "arguments": {
            "file_path": "main.py",
            "old_text": "def main():\n    \"\"\"Main entry point\"\"\"",
            "new_text": "def main():\n    \"\"\"\n    Main application entry point.\n    \n    Initializes the application and runs the main loop.\n    \n    Returns:\n        int: Exit code (0 for success)\n    \"\"\""
          },
          "description": "Replace simple docstring with detailed one"
        }
      ],
      "depends_on": 1
    }
  ],
  "estimated_duration": "3 seconds",
  "requires_confirmation": true
}
```

### Affichage terminal
```
============================================================
EXECUTION PLAN
============================================================
Query: Read main.py and add docstring to the main() function
Steps: 2
Estimated duration: 3 seconds

Step 1: Read main.py to locate main() function
  → read_file: Read entire file to understand structure
      file_path: main.py

Step 2: Add docstring to main() function
  → edit_file: Replace simple docstring with detailed one
      file_path: main.py
      old_text: def main():...
      new_text: def main():...

⚠️  WARNING: This plan contains potentially dangerous operations
============================================================
Execute this plan? [y/n/details]: y

Executing step 1/2... ✓
Executing step 2/2... ✓

Plan completed successfully!
```

---

## Implémentation Progressive

### Phase 1: Structure de base
1. Créer `core/domain/execution_plan.py` avec value objects
2. Créer `core/services/plan_execution_service.py`
3. Tester exécution de plans hardcodés

### Phase 2: Génération par LLM
1. Créer `agents/planning_agent.py`
2. Configurer LLM pour output JSON
3. Parser JSON → ExecutionPlan

### Phase 3: Intégration orchestrator
1. Modifier `orchestrator.process_user_input()`
2. Ajouter affichage plan
3. Ajouter confirmation utilisateur

### Phase 4: Améliorations
1. Rollback sur erreur
2. Pause/resume execution
3. Sauvegarde historique plans
4. Retry failed steps

---

## Fichiers à Créer

```
core/domain/
├── execution_plan.py          # ExecutionPlan, ExecutionStep, ActionStep

core/services/
├── plan_execution_service.py  # PlanExecutionService
├── plan_parser.py              # Parse JSON → ExecutionPlan

agents/
├── planning_agent.py           # PlanningAgent
└── execution_agent.py          # Executes and monitors plans

core/
└── orchestrator.py             # Modified to use planning workflow
```

---

## Configuration LLM pour JSON Output

```python
# Dans PlanningAgent

def create_plan(self, user_query: str) -> ExecutionPlan:
    messages = [...]

    # Force JSON output avec structured output
    response = self._llm.chat(
        messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "execution_plan",
                "schema": {
                    "type": "object",
                    "properties": {
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "step_number": {"type": "integer"},
                                    "description": {"type": "string"},
                                    "actions": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "tool_name": {"type": "string"},
                                                "arguments": {"type": "object"},
                                                "description": {"type": "string"}
                                            },
                                            "required": ["tool_name", "arguments"]
                                        }
                                    },
                                    "depends_on": {"type": ["integer", "null"]}
                                },
                                "required": ["step_number", "description", "actions"]
                            }
                        },
                        "estimated_duration": {"type": ["string", "null"]},
                        "requires_confirmation": {"type": "boolean"}
                    },
                    "required": ["steps"]
                }
            }
        }
    )
```

---

## Tests

```python
# tests/services/test_plan_execution_service.py

def test_execute_simple_plan():
    """Test execution of simple 2-step plan"""
    plan = ExecutionPlan(
        plan_id="test-001",
        user_query="Read and edit file",
        steps=[
            ExecutionStep(
                step_number=1,
                description="Read file",
                actions=[
                    ActionStep(
                        tool_name="read_file",
                        arguments={"file_path": "test.txt"},
                        description="Read test file"
                    )
                ]
            ),
            ExecutionStep(
                step_number=2,
                description="Edit file",
                actions=[
                    ActionStep(
                        tool_name="edit_file",
                        arguments={
                            "file_path": "test.txt",
                            "old_text": "hello",
                            "new_text": "world"
                        },
                        description="Replace hello with world"
                    )
                ],
                depends_on=1
            )
        ]
    )

    service = PlanExecutionService(tool_scheduler)
    result = service.execute_plan(plan, confirm_dangerous=True)

    assert result.success
    assert len(result.completed_steps) == 2
```

---

## Migration depuis système actuel

### Étape 1: Parallèle
- Garder système actuel (tool calling direct)
- Ajouter nouveau système (action-based) en parallèle
- Flag pour choisir le mode

### Étape 2: Test
- Tester nouveau système sur queries simples
- Valider génération plans par LLM
- Vérifier exécution correcte

### Étape 3: Migration progressive
- Migrer agent par agent
- CodeAgent d'abord (moins critique)
- GitAgent et BashAgent ensuite (plus critiques)

### Étape 4: Décommission ancien système
- Supprimer tool calling direct
- Tout passe par planning

---

## Conclusion

Ce système offre:
- **Sécurité**: Validation avant exécution
- **Transparence**: User voit le plan
- **Contrôle**: Confirmation explicite
- **Traçabilité**: Logs de chaque action
- **Flexibilité**: Plans réutilisables

**Prochaine étape**: Implémenter Phase 1 (structures de base)
