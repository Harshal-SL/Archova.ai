"""Custom exception hierarchy for the AI Software Architecture Engine (SAE)."""


class DesignEngineError(Exception):
    """Base exception for all design engine errors."""

    pass


class ConfigurationError(DesignEngineError):
    """Raised when required environment configuration or model settings are missing or invalid."""

    pass


class OwnershipValidationError(DesignEngineError):
    """Raised when an agent attempts to create or modify a section it does not own."""

    def __init__(self, section_id: str, section_owner: str, attempted_role: str):
        self.section_id = section_id
        self.section_owner = section_owner
        self.attempted_role = attempted_role
        super().__init__(
            f"Agent with role '{attempted_role}' is not authorized to update section "
            f"'{section_id}' owned by '{section_owner}'."
        )


class DependencyValidationError(DesignEngineError):
    """Raised when an agent cannot execute due to missing prerequisite sections or data."""

    def __init__(self, agent_role: str, missing_dependencies: list[str]):
        self.agent_role = agent_role
        self.missing_dependencies = missing_dependencies
        super().__init__(
            f"Agent '{agent_role}' failed dependency validation. Missing prerequisite sections: "
            f"{', '.join(missing_dependencies)}."
        )


class ContractValidationError(DesignEngineError):
    """Raised when an agent lacks required input contracts before execution."""

    def __init__(self, agent_role: str, missing_contracts: list[str]):
        self.agent_role = agent_role
        self.missing_contracts = missing_contracts
        super().__init__(
            f"Agent '{agent_role}' failed contract validation. Missing required contracts: "
            f"{', '.join(missing_contracts)}."
        )


class AgentRegistryError(DesignEngineError):
    """Raised when errors occur during agent registration, unregistration, or lookup."""

    pass


class AgentExecutionError(DesignEngineError):
    """Raised when an agent fails during execution after exhausting retries."""

    def __init__(self, agent_role: str, message: str, original_exception: Exception | None = None):
        self.agent_role = agent_role
        self.original_exception = original_exception
        super().__init__(f"Execution of agent '{agent_role}' failed: {message}")


class SDCValidationError(DesignEngineError):
    """Raised when SharedDesignContext validation or structure checks fail."""

    pass


class CircularDependencyError(DesignEngineError):
    """Raised when circular dependencies are detected in the orchestrator agent pipeline graph."""

    def __init__(self, cycle: list[str]):
        self.cycle = cycle
        super().__init__(f"Circular dependency detected in agent workflow: {' -> '.join(cycle)}")


class LLMStructuredOutputError(DesignEngineError):
    """Raised when structured LLM output generation fails validation after exhausting max retries."""

    def __init__(
        self,
        agent: str,
        model: str,
        provider: str = "OpenRouter",
        attempts: int = 2,
        reason: str = "Structured response failed Pydantic validation",
        validation_errors: str = "",
    ):
        self.agent = agent
        self.model = model
        self.provider = provider
        self.attempts = attempts
        self.reason = reason
        self.validation_errors = validation_errors
        super().__init__(
            f"Structured LLM request failed after {attempts} attempt(s). "
            f"Provider={provider}, Model={model}, Agent={agent}. "
            f"Reason: {reason}"
        )

