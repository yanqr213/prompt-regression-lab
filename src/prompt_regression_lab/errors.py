"""Custom errors for prompt_regression_lab."""


class PromptRegressionLabError(Exception):
    """Base exception for the package."""


class SuiteFormatError(PromptRegressionLabError):
    """Raised when a suite file cannot be parsed or validated."""


class AssertionExecutionError(PromptRegressionLabError):
    """Raised when an assertion cannot be evaluated."""
