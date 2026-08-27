from __future__ import annotations

from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

from .config import Settings


def build_credential() -> DefaultAzureCredential:
    return DefaultAzureCredential(exclude_interactive_browser_credential=True)


def build_openai_client(settings: Settings) -> AzureOpenAI:
    if settings.azure_openai_api_key:
        return AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )
    token_provider = get_bearer_token_provider(
        build_credential(), "https://cognitiveservices.azure.com/.default"
    )
    return AzureOpenAI(
        azure_ad_token_provider=token_provider,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
    )


def build_cosmos_client(settings: Settings) -> CosmosClient:
    credential = settings.azure_cosmos_key or build_credential()
    return CosmosClient(settings.azure_cosmos_endpoint, credential=credential)

