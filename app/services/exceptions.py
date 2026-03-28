class IngestionPipelineError(RuntimeError):
    # raises this when a known ingestion step fails and i want route-level error mapping.
    pass
