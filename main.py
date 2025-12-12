import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from core.logger import logger
from cli.terminal import Terminal
from core.llm_wrapper import LLMWrapperConfig
from core.orchestrator import Orchestrator
from agents.config import AgentConfig
from agents.default_agent import DefaultAgent


class Application:
    """Main application with an interactive terminal and an orchestrated agent system."""

    def __init__(self):
        """Initialize application."""
        self.orchestrator = None
        self.terminal = None

    def _build_agents(self, llm, tool_scheduler, tool_registry, memory_manager):
        """
        Build the list of agents that the orchestrator will use.

        Args:
            llm: LLM wrapper instance
            tool_scheduler: Tool scheduler instance
            tool_registry: Tool registry instance
            memory_manager: Memory manager instance

        Returns:
            List of configured agents

        Tool Configuration Examples:
            tools=None      -> No tools available (agent cannot use any tools)
            tools=[]        -> All tools available (default behavior)
            tools=["read_file", "write_file"]  -> Only specified tools available
        """
        agents = []

        # Create default agent configuration
        default_config = AgentConfig(
            name="DefaultAgent",
            description="A general-purpose AI assistant that can help with various tasks",
            tools=["read_file"],
            max_agent_turns=10,
            max_history_turns=10,
            system_prompt="""You are a helpful AI assistant with access to various tools.
You can execute commands, read and write files, and perform various tasks to help users.
Be concise, precise, and helpful in your responses.
When using tools, explain what you're doing and why."""
        )

        # Create the default agent
        default_agent = DefaultAgent(
            llm=llm,
            tool_scheduler=tool_scheduler,
            tool_registry=tool_registry,
            memory_manager=memory_manager,
            config=default_config
        )

        agents.append(default_agent)

        logger.info("APP", f"Built {len(agents)} agent(s)", {
            "agents": [agent._config.name for agent in agents]
        })

        return agents

    def setup(self):
        """Setup all components required for the orchestrator and agent to run."""
        logger.info("APP", "Setting up application")

        # 1. Define LLM Configuration (reads from .env automatically)
        llm_config = LLMWrapperConfig()
        logger.info("APP", "LLM Config loaded", {
            "base_url": llm_config.base_url,
            "model": llm_config.model,
            "temperature": llm_config.temperature,
            "timeout": llm_config.timeout
        })

        # 2. Initialize the Orchestrator (without agents initially)
        self.orchestrator = Orchestrator(
            llm_config=llm_config,
            agents=None
        )
        logger.info("APP", "Orchestrator components initialized.")

        # 3. Get components from orchestrator
        llm, tool_scheduler, tool_registry, memory_manager = self.orchestrator.get_components()

        # 4. Build agents using orchestrator components
        agents = self._build_agents(llm, tool_scheduler, tool_registry, memory_manager)

        # 5. Set agents in orchestrator
        self.orchestrator.set_agents(agents)
        logger.info("APP", "Agents registered with orchestrator.")

        # 6. Setup the terminal for user interaction with commands auto-loaded
        self.terminal = Terminal(orchestrator=self.orchestrator)

    def handle_input(self, user_input: str):
        """
        Handle user input by passing it to the orchestrator.

        Args:
            user_input: The user's message from the terminal.
        """
        try:
            print("\nAssistant is thinking...\n", end="", flush=True)
            output = self.orchestrator.process_user_input(user_input)

            print("\r" + " " * 30 + "\r", end="")

            if output.success:
                print(f"Assistant: {output.response}\n")
            else:
                print(f"\nError: {output.error}\n")
                logger.error("APP", "Orchestrator processing failed", {"error": output.error})

        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}\n")
            logger.error("APP", "Input handling error", {"error": str(e)})

    def run(self):
        """Run the main application loop."""
        logger.separator("Application Starting")

        try:
            self.setup()

            self.terminal.run(input_handler=self.handle_input)

            logger.separator("Application Complete")
            return 0

        except KeyboardInterrupt:
            print("\nExiting...")
            logger.info("APP", "Application interrupted by user")
            return 130

        except Exception as e:
            logger.critical("APP", "Fatal application error", {"error": str(e)})
            print(f"\nA fatal error occurred: {e}\n")
            return 1


def main():
    """Main entry point"""
    app = Application()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
