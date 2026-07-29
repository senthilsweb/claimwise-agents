"""Model factory — Amazon Bedrock only. Model id always from env, never hardcoded."""

from strands.models import BedrockModel

from agents import config


def get_model() -> BedrockModel:
    model_id = config.require(config.BEDROCK_MODEL_ID, "BEDROCK_MODEL_ID")
    return BedrockModel(model_id=model_id, region_name=config.AWS_REGION)
