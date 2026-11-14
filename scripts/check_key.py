"""Quick check that the Claude API key in .env works."""
import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("ANTHROPIC_API_KEY is missing from .env")

client = Anthropic()
reply = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=50,
    messages=[{"role": "user", "content": "Say hello as NOVA, an astronaut assistant, in one short sentence."}],
)
print(reply.content[0].text)
