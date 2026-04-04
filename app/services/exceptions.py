class IngestionPipelineError(RuntimeError):
    # raises this when a known ingestion step fails and i want route-level error mapping.
    pass


class LLMProviderError(RuntimeError):
    # raises this when local/model provider calls fail in predictable ways.
    pass


class IncidentAnalysisError(RuntimeError):
    # raises this when the incident analyzer cannot produce a reliable root cause.
    pass
