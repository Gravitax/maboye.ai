import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from core.logger import logger
from cli.terminal import Terminal
from core.llm_wrapper import LLMWrapperConfig
from core.orchestrator import Orchestrator
from core.domain import RegisteredAgent


class Application:
    """Main application with orchestrated multi-agent system."""

    def __init__(self):
        """Initialize application."""
        self.orchestrator = None
        self.terminal = None

    def _register_agents(self):
        """
        Register agents in the agent repository.

        Creates RegisteredAgent domain objects and saves them to the repository.
        """
        agent_repository = self.orchestrator.get_agent_repository()

        # Create and register default agent
        agent = RegisteredAgent.create_new(
            name="DefaultAgent",
            description="A general-purpose AI assistant that can help with various tasks",
            authorized_tools=["read_file"],
            system_prompt="""You are a helpful AI assistant with access to various tools.
You can execute commands, read and write files, and perform various tasks to help users.
Be concise, precise, and helpful in your responses.
When using tools, explain what you're doing and why."""
        )

        agent_repository.save(agent)

        logger.info("APP", "Agent registered", {
            "agent_id": agent.get_agent_id(),
            "agent_name": agent.get_agent_name()
        })

        return agent_repository

    def setup(self):
        """Setup all components for the orchestrator and agents."""
        logger.info("APP", "Setting up application")

        # 1. Load LLM configuration
        llm_config = LLMWrapperConfig()
        logger.info("APP", "LLM config loaded", {
            "base_url": llm_config.base_url,
            "model": llm_config.model
        })

        # 2. Initialize orchestrator
        self.orchestrator = Orchestrator(llm_config=llm_config)
        logger.info("APP", "Orchestrator initialized")

        # 3. Register agents
        agent_repository = self._register_agents()
        logger.info("APP", "Agents ready", {
            "total": agent_repository.count(),
            "active": len(agent_repository.find_active())
        })

        # 4. Setup terminal
        self.terminal = Terminal(orchestrator=self.orchestrator)
        logger.info("APP", "Terminal ready")

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
