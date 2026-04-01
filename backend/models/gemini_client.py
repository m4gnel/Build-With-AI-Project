"""
gemini_client.py — Gemini AI Integration for Enhanced RAG Generation
=====================================================================

Provides LLM-powered generation to replace template-based responses when
a Gemini API key is available. Falls back gracefully to templates if not.

Usage:
    Set environment variable: GEMINI_API_KEY=your_key_here
    The system automatically detects and uses it.
"""

import os
import logging
import time
from datetime import datetime

logger = logging.getLogger("SupplyChainAI.Gemini")


class GeminiClient:
    """
    Wrapper around Google Gemini API for supply chain intelligence generation.
    
    Features:
    - Graceful fallback if no API key or SDK installed
    - Rate limiting (respects free tier limits)
    - Structured prompting with supply chain context
    - Response caching to minimize API calls
    """

    def __init__(self):
        self.client = None
        self.model_name = "gemini-2.5-flash"
        self.is_available = False
        self.api_calls = 0
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_call_time = 0
        self.min_call_interval = 1.0  # 1 second between calls (rate limiting)

        self._initialize()

    def _initialize(self):
        """Try to initialize Gemini client. Fail silently if not available."""
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()

        if not api_key:
            logger.info("GEMINI_API_KEY not set — using template-based generation (still works great!)")
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=api_key)

            # Test connection with a minimal request
            test_response = self.client.models.generate_content(
                model=self.model_name,
                contents="Reply with exactly: OK",
                config={
                    "max_output_tokens": 5,
                    "temperature": 0,
                }
            )
            if test_response and test_response.text:
                self.is_available = True
                logger.info(f"✅ Gemini AI connected successfully (model: {self.model_name})")
            else:
                logger.warning("Gemini API responded but with empty content — falling back to templates")

        except ImportError:
            logger.info("google-genai package not installed. Install with: pip install google-genai")
        except Exception as e:
            logger.warning(f"Gemini initialization failed: {str(e)} — using template fallback")

    def generate(self, prompt, system_context=None, max_tokens=1024, temperature=0.7):
        """
        Generate text using Gemini AI.

        Args:
            prompt: The user query or generation prompt
            system_context: System-level context about the supply chain state
            max_tokens: Maximum response length
            temperature: Creativity (0=deterministic, 1=creative)

        Returns:
            dict with 'text', 'model', 'tokens_used', or None if unavailable
        """
        if not self.is_available:
            return None

        # Check cache
        cache_key = f"{prompt[:100]}:{temperature}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached["timestamp"] < self.cache_ttl:
                return {**cached["response"], "cached": True}

        # Rate limiting
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_call_interval:
            time.sleep(self.min_call_interval - elapsed)

        try:
            # Build full prompt with supply chain context
            full_prompt = self._build_prompt(prompt, system_context)

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                }
            )

            self.last_call_time = time.time()
            self.api_calls += 1

            if response and response.text:
                result = {
                    "text": response.text.strip(),
                    "model": self.model_name,
                    "api_calls_total": self.api_calls,
                    "cached": False,
                    "generated_at": datetime.now().isoformat(),
                }

                # Cache the response
                self.cache[cache_key] = {
                    "response": result,
                    "timestamp": time.time(),
                }

                return result

            return None

        except Exception as e:
            logger.warning(f"Gemini generation failed: {str(e)}")
            return None

    def generate_rag_response(self, query, retrieved_chunks, disruption_context=None):
        """
        Generate an enhanced RAG response using retrieved context + Gemini.

        This is the core RAG-LLM integration: retrieved documents provide
        factual grounding, and Gemini synthesizes a coherent intelligence report.
        """
        if not self.is_available:
            return None

        # Build context from retrieved chunks
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks[:5]):
            doc_id = chunk.get("doc_id", f"DOC-{i+1}")
            title = chunk.get("doc_title", "Unknown")
            text = chunk.get("chunk_text", "")
            score = chunk.get("hybrid_score", 0)
            context_parts.append(f"[Source {doc_id}: {title} (relevance: {score:.2f})]\n{text}")

        context_block = "\n\n".join(context_parts)

        disruption_info = ""
        if disruption_context:
            disruption_info = f"""
ACTIVE DISRUPTION:
- Type: {disruption_context.get('type', 'unknown')}
- Location: {disruption_context.get('location', 'unknown')}
- Severity: {disruption_context.get('severity', 'unknown')}
"""

        prompt = f"""You are an AI Supply Chain Intelligence Analyst. Based on the retrieved knowledge base documents below, generate a concise, actionable intelligence report.

{disruption_info}

QUERY: {query}

RETRIEVED KNOWLEDGE BASE DOCUMENTS:
{context_block}

Generate a response that:
1. Synthesizes findings across ALL retrieved sources (don't just repeat one)
2. Provides specific, actionable recommendations with estimated impact
3. Includes risk severity assessment (Low/Medium/High/Critical)
4. Mentions specific numbers and timeframes from the source documents
5. Keep response under 200 words — be dense and actionable, not verbose

FORMAT:
🔍 ANALYSIS: [2-3 sentence synthesis]
⚠️ RISK LEVEL: [Low/Medium/High/Critical] — [1 sentence justification]
📋 RECOMMENDATIONS:
1. [Action 1 with expected impact]
2. [Action 2 with expected impact]
3. [Action 3 with expected impact]
💰 ESTIMATED IMPACT: [Cost/time savings estimate]"""

        result = self.generate(prompt, max_tokens=600, temperature=0.4)
        if result:
            result["generation_type"] = "gemini_rag"
            result["sources_used"] = len(retrieved_chunks)
        return result

    def generate_decision_justification(self, decision_type, decision_title, risk_context, retrieved_evidence):
        """Generate AI-powered justification for a supply chain decision."""
        if not self.is_available:
            return None

        evidence_text = "\n".join([f"- {e[:200]}" for e in (retrieved_evidence or [])[:3]])

        prompt = f"""You are an AI Decision Engine for supply chain optimization. Provide a brief, data-driven justification for the following decision.

DECISION: {decision_title}
TYPE: {decision_type}
RISK CONTEXT: {risk_context}

SUPPORTING EVIDENCE:
{evidence_text}

Generate a 2-3 sentence justification that:
1. References specific data points from the evidence
2. Quantifies the expected benefit
3. Sounds confident and professional

Keep it under 80 words."""

        result = self.generate(prompt, max_tokens=200, temperature=0.3)
        return result["text"] if result else None

    def answer_freeform_query(self, question, retrieved_chunks):
        """Answer a free-form user question using RAG context + Gemini."""
        if not self.is_available:
            return None

        context = "\n".join([
            f"[{c.get('doc_id', '?')}: {c.get('doc_title', '?')}] {c.get('chunk_text', '')[:300]}"
            for c in retrieved_chunks[:5]
        ])

        prompt = f"""You are a Supply Chain AI Assistant. Answer the user's question using ONLY the retrieved knowledge base documents below. If the documents don't contain relevant information, say so honestly.

USER QUESTION: {question}

KNOWLEDGE BASE CONTEXT:
{context}

Provide a helpful, concise answer (under 150 words). Reference specific source documents when possible."""

        result = self.generate(prompt, max_tokens=400, temperature=0.5)
        if result:
            result["generation_type"] = "gemini_freeform"
        return result

    def _build_prompt(self, prompt, system_context=None):
        """Build the full prompt with optional system context."""
        if system_context:
            return f"""[SYSTEM CONTEXT]
{system_context}

[USER REQUEST]
{prompt}"""
        return prompt

    def get_status(self):
        """Return current Gemini integration status."""
        return {
            "available": self.is_available,
            "model": self.model_name if self.is_available else None,
            "api_calls_made": self.api_calls,
            "cache_size": len(self.cache),
            "status": "connected" if self.is_available else "template_fallback",
        }
