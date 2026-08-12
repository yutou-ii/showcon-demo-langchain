import os

os.environ.setdefault("OPENAI_API_KEY", "test_key")
os.environ.setdefault(
    "OPENAI_BASE_URL",
    "https://models.example.test/v1",
)
os.environ.setdefault("OPENAI_MODEL", "test-model")