"""Model factory — Amazon Bedrock only. Model id always from env, never hardcoded."""

from strands.models import BedrockModel

from agents import config


def get_model() -> BedrockModel:
    """Build the Bedrock model client every agent shares.

    The id comes from BEDROCK_MODEL_ID (required — fails fast if unset).
    The client is stateless, so one instance is safe to reuse across agents.
    """
    model_id = config.require(config.BEDROCK_MODEL_ID, "BEDROCK_MODEL_ID")
    return BedrockModel(model_id=model_id, region_name=config.AWS_REGION)
