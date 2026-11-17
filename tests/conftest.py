"""Test isolation: the suite never calls a live LLM."""
import os

os.environ["SENTINEL_NARRATOR"] = "0"
