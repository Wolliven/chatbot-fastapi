import os
import unittest
from unittest.mock import patch

from core import chatbot, llm


class FakeLLMClient:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.calls = []

    def generate(self, prompt: str, *, temperature: float = 0.2, json_mode: bool = False) -> str:
        self.calls.append(
            {
                "prompt": prompt,
                "temperature": temperature,
                "json_mode": json_mode,
            }
        )
        return self.response_text


class LLMFactoryTests(unittest.TestCase):
    def tearDown(self) -> None:
        llm.reset_llm_client()

    def test_build_llm_client_selects_gemini_provider(self) -> None:
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "gemini",
                "GEMINI_API_KEY": "test-key",
                "GEMINI_MODEL": "gemini-test",
            },
            clear=False,
        ):
            with patch("core.llm.GeminiLLMClient", return_value="gemini-client") as gemini_client:
                client = llm.build_llm_client()

        self.assertEqual(client, "gemini-client")
        gemini_client.assert_called_once_with(
            api_key="test-key",
            model="gemini-test",
        )

    def test_build_llm_client_selects_ollama_provider(self) -> None:
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "ollama",
                "OLLAMA_BASE_URL": "http://localhost:11434",
                "OLLAMA_MODEL": "gemma3:4b",
                "OLLAMA_TIMEOUT_SECONDS": "45",
            },
            clear=False,
        ):
            with patch("core.llm.OllamaLLMClient", return_value="ollama-client") as ollama_client:
                client = llm.build_llm_client()

        self.assertEqual(client, "ollama-client")
        ollama_client.assert_called_once_with(
            base_url="http://localhost:11434",
            model="gemma3:4b",
            timeout_seconds=45.0,
        )


class ChatbotIntegrationTests(unittest.TestCase):
    def test_process_message_uses_llm_interface(self) -> None:
        fake_client = FakeLLMClient(
            '{"action":"chat","reply_text":"Hello from provider","reservation":null}'
        )

        with patch("core.chatbot.load_information", return_value="Business facts"), patch(
            "core.chatbot.get_llm_client",
            return_value=fake_client,
        ), patch("core.chatbot.log_conversation") as log_conversation:
            decision = chatbot.process_message("Misky", "Hi there")

        self.assertEqual(decision.action, "chat")
        self.assertEqual(decision.reply_text, "Hello from provider")
        self.assertEqual(len(fake_client.calls), 1)
        self.assertTrue(fake_client.calls[0]["json_mode"])
        self.assertEqual(fake_client.calls[0]["temperature"], 0.2)
        log_conversation.assert_called_once()
