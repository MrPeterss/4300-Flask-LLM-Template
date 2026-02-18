"""
Example usage of the 4300Spark Python client

To run this example:
1. Install the package: pip install -e .
2. Set your API key below or via environment variable
3. Run: python example_usage.py
"""

import os
from infosci_spark_client import LLMClient

# Set API_KEY environment variable
API_KEY = os.getenv("API_KEY", "your-api-key")


def example_basic_chat():
    """Example 1: Basic non-streaming chat"""
    print("=" * 70)
    print("Example 1: Basic Chat (Non-Streaming)")
    print("Returns dict with 'content' and 'reasoning'")
    print("=" * 70)
    
    client = LLMClient(api_key=API_KEY)
    
    response = client.chat([
        {"role": "user", "content": "What is Python? Answer in 10 words."}
    ])
    
    print(f"Type: {type(response)}")
    print(f"Content: {response['content']}")
    print(f"Reasoning: {response['reasoning'][:100] if response['reasoning'] else '(empty)'}")
    print()


def example_streaming_chat():
    """Example 2: Streaming chat"""
    print("=" * 70)
    print("Example 2: Streaming Chat")
    print("Response appears in real-time")
    print("=" * 70)
    
    client = LLMClient(api_key=API_KEY)
    
    print("Content: ", end="", flush=True)
    content_parts = []
    
    for chunk in client.chat([
        {"role": "user", "content": "Count from 1 to 5"}
    ], stream=True):
        # Each chunk is a dict with 'content' and 'reasoning' keys
        if chunk['content']:
            content_parts.append(chunk['content'])
            print(chunk['content'], end="", flush=True)
    
    print(f"\n\nFull response: {''.join(content_parts)}")
    print()


def example_streaming_with_thinking():
    """Example 3: Streaming with reasoning"""
    print("=" * 70)
    print("Example 3: Streaming with Thinking")
    print("Stream both content and reasoning")
    print("=" * 70)
    
    client = LLMClient(api_key=API_KEY)
    
    content_parts = []
    reasoning_parts = []
    
    print("Streaming...\n")
    
    for chunk in client.chat([
        {"role": "user", "content": "Say hello in 3 words"}
    ], stream=True, show_thinking=True):
        if chunk['content']:
            content_parts.append(chunk['content'])
            print(chunk['content'], end="", flush=True)
        if chunk['reasoning']:
            reasoning_parts.append(chunk['reasoning'])
            print(chunk['reasoning'], end="", flush=True)   

    print("\n\nStreaming complete")

    print(f"\nContent: {''.join(content_parts)}")
    print(f"Reasoning: {''.join(reasoning_parts)[:50]}...")
    print()

def example_conversation():
    """Example 4: Multi-turn conversation"""
    print("=" * 70)
    print("Example 4: Multi-Turn Conversation")
    print("Maintain context across messages")
    print("=" * 70)
    
    client = LLMClient(api_key=API_KEY)
    
    messages = []
    
    # First turn
    messages.append({"role": "user", "content": "What is 5+3?"})
    print("User: What is 5+3?")
    response1 = client.chat(messages)
    print(f"AI: {response1['content']}")
    messages.append({"role": "assistant", "content": response1['content']})
    
    # Second turn - has context from first
    messages.append({"role": "user", "content": "What is that number minus 2?"})
    print("\nUser: What is that number minus 2?")
    response2 = client.chat(messages)
    print(f"AI: {response2['content']}")
    print("(Notice: AI remembered the previous answer!)\n")


def example_reasoning_levels():
    """Example 5: Control reasoning with reasoning_level"""
    print("=" * 70)
    print("Example 5: Reasoning Levels")
    print("Control how much the model thinks (includes show_thinking=True)")
    print("=" * 70)
    
    client = LLMClient(api_key=API_KEY)
    messages = [{"role": "user", "content": "What is AI? Answer in 5 words."}]
    
    for level in ['low', 'medium', 'high']:
        response = client.chat(messages, show_thinking=True, reasoning_level=level)
        print(f"\n{level.upper()} reasoning:")
        print(f"  Content: {response['content']}")
        print(f"  Reasoning depth: {len(response['reasoning'])} chars")
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("4300Spark Package - Example Usage")
    print("All responses return dicts with 'content' and 'reasoning'")
    print("=" * 70 + "\n")
    
    # Run examples (comment out any you don't want)
    example_basic_chat()
    example_streaming_chat()
    example_streaming_with_thinking()
    example_conversation()
    example_reasoning_levels()
