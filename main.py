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
        Register specialized agents in the agent repository.

        Creates RegisteredAgent domain objects from profiles and saves them.
        Registers 3 specialized agents: CodeAgent, GitAgent, BashAgent
        """
        from agents.profiles import ALL_PROFILES

        agent_repository = self.orchestrator.get_agent_repository()

        # Register all specialized agents from profiles
        for profile in ALL_PROFILES:
            # Extract LLM configuration if present
            llm_config = profile.get("llm_config", {})

            agent = RegisteredAgent.create_new(
                name=profile["name"],
                description=profile["description"],
                authorized_tools=profile["authorized_tools"],
                system_prompt=profile["system_prompt"],
                max_reasoning_turns=profile.get("max_reasoning_turns", 10),
                max_memory_turns=profile.get("max_memory_turns", 10),
                specialization_tags=profile.get("specialization_tags", []),
                llm_temperature=llm_config.get("temperature", 0.7),
                llm_max_tokens=llm_config.get("max_tokens", 1000),
                llm_timeout=llm_config.get("timeout", 30),
                llm_response_format=llm_config.get("response_format", "default")
            )

            agent_repository.save(agent)
        return agent_repository

    def setup(self):
        """Setup all components for the orchestrator and agents."""

        # 1. Load LLM configuration
        llm_config = LLMWrapperConfig()

        # 2. Initialize orchestrator
        self.orchestrator = Orchestrator(llm_config=llm_config)

        # 3. Register agents
        agent_repository = self._register_agents()

        # 4. Setup terminal
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

        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}\n")

    def run(self):
        """Run the main application loop."""
        try:
            self.setup()

            self.terminal.run(input_handler=self.handle_input)

            return 0

        except KeyboardInterrupt:
            print("\nExiting...")
            return 130

        except Exception as e:
            print(f"\nA fatal error occurred: {e}\n")
            return 1


def main():
    """Main entry point"""
    app = Application()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
