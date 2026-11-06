from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-4.1-mini",
    input="Explain Agentic AI in one simple sentence."
)

print(response.output_text)