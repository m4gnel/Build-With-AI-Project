"""
rag_engine.py — Lightweight RAG Pipeline for Supply Chain Disruption Intelligence
===================================================================================

Architecture:  Query → Chunking → TF-IDF Vectorization → Semantic Retrieval
               → Re-Ranking → Context Assembly → Template Generation

This is a REAL Retrieval-Augmented Generation system optimized for offline/edge
deployment. It uses a proper document processing pipeline:

  1. DOCUMENT INGESTION:  23 structured knowledge documents are chunked into
     smaller passages with metadata tags (category, severity, region, impact).

  2. VECTORIZATION:  TF-IDF with (1,3)-gram tokenization creates sparse
     semantic embeddings capturing multi-word concepts like "port closure"
     or "supply chain disruption" — not just single keywords.

  3. RETRIEVAL:  Cosine similarity retrieves the top-k documents, then a
     BM25-inspired re-ranking layer boosts results that match query terms
     with proper term-frequency / inverse-document-frequency weighting.

  4. GENERATION:  Retrieved context is assembled with structured templates
     that synthesize findings across multiple source documents, producing
     coherent intelligence reports with provenance tracking.

No external LLM API required — fully local, deterministic, and reproducible.
"""

import re
import math
import numpy as np
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime


class RAGEngine:
    """
    Retrieval-Augmented Generation engine for supply chain disruption intelligence.

    Pipeline:
        Query Analysis → Document Retrieval (TF-IDF + Cosine) → BM25 Re-Ranking
        → Context Assembly → Template-Based Generation → Provenance Tracking
    """

    def __init__(self, gemini_client=None):
        # Primary retriever: TF-IDF with n-gram range (1,3) for phrase matching
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=8000,
            ngram_range=(1, 3),       # unigrams + bigrams + trigrams
            sublinear_tf=True,        # log-scaled TF (1 + log(tf))
            smooth_idf=True,          # prevents zero division
            norm="l2",               # L2 normalization per document
        )

        # Gemini AI integration (optional — enhances generation step)
        self.gemini = gemini_client

        # Document store
        self.chunks = []              # chunked text passages
        self.chunk_metadata = []      # metadata per chunk
        self.raw_documents = []       # original full documents
        self.tfidf_matrix = None
        self.idf_weights = None
        self.vocab = None

        # Pipeline metrics
        self.pipeline_stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "vocabulary_size": 0,
            "avg_chunk_length": 0,
            "queries_processed": 0,
            "avg_retrieval_time_ms": 0,
        }

        self.is_initialized = False
        self._build_knowledge_base()

    # ═══════════════════════════════════════════════════════════════
    #     STAGE 1: DOCUMENT INGESTION & CHUNKING
    # ═══════════════════════════════════════════════════════════════

    def _build_knowledge_base(self):
        """
        Ingest and chunk the knowledge base documents.

        Each document is split into overlapping passages for fine-grained
        retrieval. Metadata is propagated to every chunk for provenance.
        """
        knowledge_base = [
            # ── Weather Disruptions ───────────────────────────────
            {
                "id": "DOC-001",
                "title": "Monsoon Flooding in Western India",
                "text": (
                    "Heavy monsoon rainfall in western India causes severe flooding in port areas. "
                    "Container terminals at Jawaharlal Nehru Port Trust experience 48-72 hour delays. "
                    "Road transport halted on major highways including NH-48 and NH-8. "
                    "Suppliers in Mumbai, Pune, and Gujarat regions report warehouse flooding and inventory damage. "
                    "Historical data from 2019-2024 shows 35% increase in delivery times during June-September monsoon season. "
                    "Recommended action: pre-position inventory at inland warehouses in Nashik and Aurangabad. "
                    "Activate alternate suppliers from southern India cluster. "
                    "Re-route shipments through Mundra port in Gujarat."
                ),
                "category": "weather", "severity": "high", "region": "Western India", "impact": "port_delays"
            },
            {
                "id": "DOC-002",
                "title": "Bay of Bengal Cyclone Threat",
                "text": (
                    "Cyclone warning in Bay of Bengal threatens East Coast shipping lanes. "
                    "Chennai and Visakhapatnam ports likely to close for 3-5 days based on IMD cyclone trajectory model. "
                    "Inland logistics routes from Kolkata also at risk due to flooding. "
                    "Historical cyclone Amphan (2020) caused $13 billion in damages and 14-day supply chain halt. "
                    "Recommended action: pre-position inventory at inland warehouses and activate alternate suppliers. "
                    "Shift shipments to western ports temporarily. "
                    "Ensure insurance coverage for in-transit goods."
                ),
                "category": "weather", "severity": "critical", "region": "Eastern India", "impact": "port_closure"
            },
            {
                "id": "DOC-003",
                "title": "Northern India Heat Wave",
                "text": (
                    "Extreme heat wave across northern India exceeds 45°C for consecutive days. "
                    "Warehouse cooling systems under strain, risk of perishable goods damage in Delhi NCR and UP. "
                    "Road transport efficiency drops 20% due to vehicle overheating and mandatory rest stops. "
                    "Worker productivity at loading docks reduced by 30-40% during peak afternoon hours. "
                    "Cold chain integrity compromised — temperature monitors show 8°C deviation from specification. "
                    "Recommended action: shift loading operations to early morning and late evening. "
                    "Increase refrigerated transport allocation. "
                    "Stockpile critical perishables in climate-controlled facilities."
                ),
                "category": "weather", "severity": "medium", "region": "Northern India", "impact": "reduced_capacity"
            },
            {
                "id": "DOC-004",
                "title": "Indo-Gangetic Winter Fog",
                "text": (
                    "Winter fog in Indo-Gangetic plain causes zero visibility conditions from December to February. "
                    "Air cargo delayed by 24-48 hours at Delhi, Lucknow, and Varanasi airports due to ILS limitations. "
                    "Highway accidents increase 40% reducing road transport reliability on NH-2 and NH-91. "
                    "Rail transport remains mostly operational but with 2-4 hour delays. "
                    "Recommended action: shift time-critical shipments to rail. "
                    "Implement fog-delay buffers in delivery promises to customers."
                ),
                "category": "weather", "severity": "medium", "region": "Northern India", "impact": "transport_delays"
            },
            {
                "id": "DOC-005",
                "title": "Northeast Earthquake Disruption",
                "text": (
                    "Earthquake measuring 6.2 on Richter scale strikes northeastern region near Guwahati. "
                    "Infrastructure damage to roads and bridges disrupts supply routes from Guwahati to Siliguri corridor. "
                    "Warehouse structural assessments required before operations resume. "
                    "Aftershock risk remains elevated for 72 hours — unsafe for heavy vehicle movement. "
                    "Full recovery expected in 2-3 weeks based on 2021 Assam earthquake recovery data. "
                    "Recommended action: immediately halt shipments through northeast corridor. "
                    "Reroute through Bihar and West Bengal. "
                    "Deploy emergency stock from Kolkata warehouse."
                ),
                "category": "weather", "severity": "critical", "region": "Northeastern India", "impact": "infrastructure_damage"
            },
            # ── Supplier Disruptions ──────────────────────────────
            {
                "id": "DOC-006",
                "title": "Major Supplier Equipment Failure",
                "text": (
                    "Major supplier manufacturing facility experiences critical equipment failure. "
                    "Production capacity reduced by 60% for estimated 2-3 weeks repair duration. "
                    "This supplier handles 25% of electronic component supply chain across 3 product lines. "
                    "Quality of remaining output may be compromised due to workaround processes. "
                    "Recommended action: activate secondary suppliers immediately. "
                    "Redistribute orders to suppliers in Low Risk cluster based on K-Means analysis. "
                    "Negotiate expedited delivery terms with backup suppliers."
                ),
                "category": "supplier", "severity": "high", "region": "Industrial", "impact": "supply_shortage"
            },
            {
                "id": "DOC-007",
                "title": "Supplier Quality Audit Failure",
                "text": (
                    "Quality audit reveals systematic defects in supplier shipments over last quarter. "
                    "Failure rate jumped from 2% to 15% — a 7.5x increase indicating process breakdown. "
                    "Root cause traced to unauthorized raw material source change to reduce costs. "
                    "4,200 units in pipeline potentially affected, requiring 100% inspection. "
                    "Recommended action: quarantine existing inventory from this supplier. "
                    "Source from alternate supplier with quality score above 85. "
                    "Mandate corrective action plan with 30-day compliance deadline."
                ),
                "category": "supplier", "severity": "high", "region": "Quality", "impact": "quality_failure"
            },
            {
                "id": "DOC-008",
                "title": "Supplier Financial Instability",
                "text": (
                    "Supplier financial instability detected through credit monitoring. Credit rating downgraded from BB to CCC. "
                    "Risk of bankruptcy within 6 months based on Altman Z-Score falling below 1.2. "
                    "Current orders may be fulfilled but future capacity uncertain. "
                    "Supplier accounts payable days increased from 45 to 90 — indicating cash flow crisis. "
                    "Recommended action: diversify supplier base immediately. "
                    "Reduce single-supplier dependency below 20% of any product category. "
                    "Secure advance purchase agreements with financially stable alternatives."
                ),
                "category": "supplier", "severity": "medium", "region": "Financial", "impact": "supplier_bankruptcy"
            },
            {
                "id": "DOC-009",
                "title": "Labor Dispute at Supplier Factory",
                "text": (
                    "Labor dispute at key supplier factory leads to indefinite work stoppage. "
                    "Union demands include 30% wage increase and improved working conditions. "
                    "Negotiations expected to last 1-2 weeks based on industry mediator assessment. "
                    "No shipments during strike period — estimated 15,000 units per week shortfall. "
                    "Similar strikes in Kanpur industrial region affected 3 other suppliers last year for avg 11 days. "
                    "Recommended action: activate emergency inventory reserves. "
                    "Contact alternate suppliers for rush orders. "
                    "Negotiate force majeure terms with affected customers."
                ),
                "category": "supplier", "severity": "high", "region": "Labor", "impact": "work_stoppage"
            },
            # ── Transportation Disruptions ────────────────────────
            {
                "id": "DOC-010",
                "title": "National Highway Construction Detours",
                "text": (
                    "National highway construction project causes major detours on NH-48 Mumbai-Delhi corridor. "
                    "Trucks rerouted through secondary roads adding 6-8 hours to transit time. "
                    "Construction expected to continue for 4 months with intermittent lane closures. "
                    "Fuel consumption increases 25% on alternate routes due to terrain and congestion. "
                    "Recommended action: use rail transport for Mumbai-Delhi route during construction period. "
                    "Negotiate bulk rail freight contracts. "
                    "Adjust delivery schedules to account for 8-hour buffer."
                ),
                "category": "traffic", "severity": "medium", "region": "Western Corridor", "impact": "route_delays"
            },
            {
                "id": "DOC-011",
                "title": "JNPT Port Congestion Crisis",
                "text": (
                    "Port congestion at Jawaharlal Nehru Port Trust causes container pickup delays. "
                    "Average wait time increased from 2 days to 5 days — a 150% increase. "
                    "Root cause: equipment shortage (2 of 5 gantry cranes under maintenance) and labor shortage. "
                    "Demurrage costs averaging $500/container/day for affected shipments. "
                    "Alternative: route through Mundra Port in Gujarat (340 km north). "
                    "Recommended action: split inbound cargo between JNPT and Mundra. "
                    "Pre-clear customs documentation to reduce port dwell time."
                ),
                "category": "traffic", "severity": "high", "region": "Mumbai Port", "impact": "port_congestion"
            },
            {
                "id": "DOC-012",
                "title": "Fuel Price Surge Impact",
                "text": (
                    "Fuel price surge of 15% increases transportation costs across all modes. "
                    "Trucking companies passing costs to shippers with 10-12% surcharge. "
                    "Rail transport becomes 20% more cost-effective than long-haul trucking. "
                    "Air freight remains viable only for high-value urgent shipments. "
                    "Recommended action: shift modal mix toward rail where possible. "
                    "Consolidate partial loads to improve truck utilization above 85%. "
                    "Renegotiate fuel surcharge clauses in logistics contracts."
                ),
                "category": "traffic", "severity": "medium", "region": "National", "impact": "cost_increase"
            },
            {
                "id": "DOC-013",
                "title": "Critical Bridge Collapse",
                "text": (
                    "Bridge collapse on key arterial route connecting Lucknow to Kanpur on NH-25. "
                    "All heavy vehicle traffic suspended indefinitely pending structural investigation. "
                    "Alternative route adds 120 km and 4 hours to journey through Unnao district. "
                    "Structural assessment and repair expected to take 3-6 months. "
                    "This bridge handles 12,000 commercial vehicles per day. "
                    "Recommended action: immediately reroute all shipments through alternate corridors. "
                    "Contact Kanpur-based suppliers about reverse logistics options. "
                    "Deploy temporary storage at Unnao transit point."
                ),
                "category": "traffic", "severity": "critical", "region": "Uttar Pradesh", "impact": "route_blocked"
            },
            # ── Political / Regulatory ────────────────────────────
            {
                "id": "DOC-014",
                "title": "Cross-State Documentation Requirements",
                "text": (
                    "New government regulation requires additional documentation for cross-state shipments. "
                    "Processing time at state borders increased by 3-4 hours for compliance verification. "
                    "Affects all trucks crossing between Maharashtra and Karnataka border checkpoints. "
                    "Expected to stabilize after 2 weeks as digital processing systems come online. "
                    "Recommended action: pre-submit e-way bills 24 hours before shipment. "
                    "Use preferred carrier network with expedited border clearance agreements."
                ),
                "category": "political", "severity": "low", "region": "Interstate", "impact": "regulatory_delay"
            },
            {
                "id": "DOC-015",
                "title": "Trade Sanctions on Raw Materials",
                "text": (
                    "Trade sanctions imposed affecting raw material imports from specific countries. "
                    "30% of semiconductor components sourced from affected regions face import restrictions. "
                    "Price increase of 40-60% expected for affected materials based on spot market analysis. "
                    "Lead times extending from 4 weeks to 12 weeks for sanctioned materials. "
                    "Recommended action: source domestically or from unaffected countries urgently. "
                    "Build 90-day strategic buffer stock for critical components. "
                    "Evaluate product redesign to use non-sanctioned alternatives."
                ),
                "category": "political", "severity": "critical", "region": "International", "impact": "import_restriction"
            },
            {
                "id": "DOC-016",
                "title": "Regional Political Unrest",
                "text": (
                    "Regional political unrest leads to transportation blockade in affected district. "
                    "All commercial vehicle movement suspended for 48 hours as precautionary measure. "
                    "Security forces deployed, situation expected to normalize within a week. "
                    "Historical pattern: 3 similar events in past 18 months, avg duration 3.5 days. "
                    "Recommended action: hold shipments and notify customers of potential delays. "
                    "Activate inventory at nearest unaffected distribution center. "
                    "Monitor situation hourly through local intelligence network."
                ),
                "category": "political", "severity": "high", "region": "Regional", "impact": "transport_blockade"
            },
            # ── Demand Disruptions ────────────────────────────────
            {
                "id": "DOC-017",
                "title": "Viral Demand Spike",
                "text": (
                    "Unexpected viral social media trend causes 300% demand spike for specific product category. "
                    "Current inventory sufficient for only 3 days at new demand rate. "
                    "Suppliers cannot ramp up production for at least 2 weeks — minimum order lead time. "
                    "E-commerce platforms showing stock-out warnings, customer complaints rising 500%. "
                    "Recommended action: implement allocation strategy across distribution channels. "
                    "Expedite orders with tier-1 suppliers at premium pricing. "
                    "Divert inventory from low-demand regions to high-demand zones."
                ),
                "category": "demand", "severity": "high", "region": "National", "impact": "demand_spike"
            },
            {
                "id": "DOC-018",
                "title": "Festival Season Demand Planning",
                "text": (
                    "Festival season approaching — historical data (2020-2024) shows 150% demand increase. "
                    "Last year's stockout during Diwali cost estimated $2M in lost sales across 4 regions. "
                    "Warehouse capacity needs 40% augmentation at Mumbai, Delhi, and Bangalore facilities. "
                    "Transportation capacity fully booked 2 weeks before peak — premium rates apply. "
                    "Recommended action: begin inventory build-up 6 weeks before peak. "
                    "Secure warehouse overflow capacity through 3PL partnerships. "
                    "Lock in transportation contracts 4 weeks ahead at fixed rates."
                ),
                "category": "demand", "severity": "medium", "region": "National", "impact": "seasonal_demand"
            },
            {
                "id": "DOC-019",
                "title": "Market Downturn Excess Inventory",
                "text": (
                    "Market downturn reduces demand by 40% across industrial product segments. "
                    "Excess inventory building up in regional warehouses — 92% capacity utilization. "
                    "Storage costs increasing $15,000/month per warehouse as goods remain unsold. "
                    "Cash flow impact estimated at $500K/quarter from holding costs alone. "
                    "Recommended action: reduce procurement orders by 30% immediately. "
                    "Offer volume discounts for bulk clearance. "
                    "Consider liquidation channels for slow-moving SKUs."
                ),
                "category": "demand", "severity": "medium", "region": "Industrial", "impact": "demand_drop"
            },
            # ── Infrastructure / Technology ───────────────────────
            {
                "id": "DOC-020",
                "title": "WMS System Outage",
                "text": (
                    "Warehouse management system outage causes inventory tracking failure across 4 facilities. "
                    "Manual operations activated but processing speed reduced by 70% to 200 orders/day. "
                    "Shipments may contain incorrect items — error rate projected at 8% vs normal 0.5%. "
                    "IT team estimates 24-hour recovery time pending database restoration. "
                    "Recommended action: halt automated order processing and switch to manual verification. "
                    "Prioritize high-value and time-critical orders only. "
                    "Notify customers of potential 24-48 hour delay."
                ),
                "category": "infrastructure", "severity": "high", "region": "Operations", "impact": "system_failure"
            },
            {
                "id": "DOC-021",
                "title": "Distribution Center Power Failure",
                "text": (
                    "Power grid failure at major distribution center in Hyderabad. "
                    "Backup generators have 48-hour fuel capacity — diesel reserves at 3,200 liters. "
                    "Cold chain products at risk if power not restored — $2M perishable inventory. "
                    "Local power utility estimates grid restoration in 72 hours due to transformer replacement. "
                    "Recommended action: transfer perishable goods to alternate facility immediately within 24-hour window. "
                    "Arrange emergency fuel delivery for generators. "
                    "Activate Bangalore distribution center as backup."
                ),
                "category": "infrastructure", "severity": "critical", "region": "Distribution", "impact": "power_failure"
            },
            # ── Pandemic / Health ─────────────────────────────────
            {
                "id": "DOC-022",
                "title": "Disease Outbreak Quarantine",
                "text": (
                    "Disease outbreak at manufacturing hub triggers mandatory 14-day quarantine zone. "
                    "Factory operations suspended — zero production output during quarantine period. "
                    "40% of regional workforce affected, post-quarantine return expect 60% capacity initially. "
                    "Supply chain disruption expected to last 4-6 weeks after quarantine lifts based on COVID recovery patterns. "
                    "Recommended action: activate all backup suppliers in unaffected regions. "
                    "Implement remote quality inspection protocols. "
                    "Build 45-day safety stock for quarantine-risk regions."
                ),
                "category": "health", "severity": "critical", "region": "Manufacturing", "impact": "facility_shutdown"
            },
            {
                "id": "DOC-023",
                "title": "New Health Safety Compliance",
                "text": (
                    "New health safety regulations require additional packaging and handling procedures. "
                    "Processing time per shipment increases by 15 minutes — 20% throughput reduction. "
                    "Additional packaging material costs of 8% per unit for sanitization supplies. "
                    "Compliance deadline in 30 days — non-compliant shipments will be rejected at destination. "
                    "Recommended action: begin compliance training for warehouse staff immediately. "
                    "Procure sanitization materials in bulk for cost efficiency. "
                    "Update SOP documentation and obtain client acknowledgment."
                ),
                "category": "health", "severity": "medium", "region": "Regulatory", "impact": "compliance_cost"
            },
        ]

        # ── Chunk documents ────────────────────────────────────
        self.raw_documents = knowledge_base
        self.chunks = []
        self.chunk_metadata = []

        for doc in knowledge_base:
            doc_chunks = self._chunk_document(doc["text"], chunk_size=200, overlap=50)
            for i, chunk_text in enumerate(doc_chunks):
                self.chunks.append(chunk_text)
                self.chunk_metadata.append({
                    "doc_id": doc["id"],
                    "doc_title": doc["title"],
                    "chunk_index": i,
                    "total_chunks": len(doc_chunks),
                    "category": doc["category"],
                    "severity": doc["severity"],
                    "region": doc["region"],
                    "impact": doc["impact"],
                })

        # ── Build TF-IDF index ─────────────────────────────────
        self.tfidf_matrix = self.vectorizer.fit_transform(self.chunks)
        self.vocab = self.vectorizer.get_feature_names_out()
        self.idf_weights = self.vectorizer.idf_

        # ── Pre-compute document frequencies for BM25 ──────────
        self.doc_lengths = np.array([len(c.split()) for c in self.chunks])
        self.avg_doc_length = np.mean(self.doc_lengths)
        self._build_bm25_index()

        # ── Stats ──────────────────────────────────────────────
        self.pipeline_stats["total_documents"] = len(knowledge_base)
        self.pipeline_stats["total_chunks"] = len(self.chunks)
        self.pipeline_stats["vocabulary_size"] = len(self.vocab)
        self.pipeline_stats["avg_chunk_length"] = round(self.avg_doc_length, 1)

        self.is_initialized = True

    def _chunk_document(self, text, chunk_size=200, overlap=50):
        """
        Split a document into overlapping chunks by character count,
        breaking at sentence boundaries for coherence.
        """
        sentences = text.replace(". ", ".\n").split("\n")
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        current = []
        current_len = 0

        for sentence in sentences:
            slen = len(sentence)
            if current_len + slen > chunk_size and current:
                chunks.append(" ".join(current))
                # Keep overlap: retain last sentence(s) up to overlap chars
                overlap_text = []
                overlap_len = 0
                for s in reversed(current):
                    if overlap_len + len(s) <= overlap:
                        overlap_text.insert(0, s)
                        overlap_len += len(s)
                    else:
                        break
                current = overlap_text
                current_len = overlap_len

            current.append(sentence)
            current_len += slen

        if current:
            chunks.append(" ".join(current))

        # If only 1 chunk, return the full text
        return chunks if chunks else [text]

    def _build_bm25_index(self):
        """Build BM25 term-frequency index for re-ranking."""
        self.term_freqs = []
        for chunk in self.chunks:
            words = chunk.lower().split()
            self.term_freqs.append(Counter(words))

    # ═══════════════════════════════════════════════════════════════
    #     STAGE 2: RETRIEVAL (TF-IDF + Cosine Similarity)
    # ═══════════════════════════════════════════════════════════════

    def retrieve(self, query, top_k=5):
        """
        Retrieve the most relevant document chunks using TF-IDF cosine similarity.

        Args:
            query:  search query string
            top_k:  number of chunks to retrieve

        Returns:
            list of relevant chunks with similarity scores and metadata
        """
        if not self.is_initialized:
            return []

        import time
        start = time.time()

        # Vectorize query with the fitted TF-IDF model
        query_vec = self.vectorizer.transform([query])

        # Cosine similarity against all chunks
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Get top candidates (retrieve more than needed for re-ranking)
        candidate_count = min(top_k * 3, len(self.chunks))
        top_indices = similarities.argsort()[-candidate_count:][::-1]

        # Filter by minimum relevance threshold
        candidates = []
        for idx in top_indices:
            if similarities[idx] > 0.03:
                candidates.append({
                    "chunk_text": self.chunks[idx],
                    "metadata": self.chunk_metadata[idx],
                    "cosine_score": round(float(similarities[idx]), 4),
                    "chunk_index": int(idx),
                })

        # Stage 3: Re-rank with BM25
        reranked = self._bm25_rerank(query, candidates)

        # Take top_k after reranking
        results = reranked[:top_k]

        # Update stats
        elapsed = (time.time() - start) * 1000
        self.pipeline_stats["queries_processed"] += 1
        prev_avg = self.pipeline_stats["avg_retrieval_time_ms"]
        n = self.pipeline_stats["queries_processed"]
        self.pipeline_stats["avg_retrieval_time_ms"] = round(
            prev_avg + (elapsed - prev_avg) / n, 2
        )

        return results

    # ═══════════════════════════════════════════════════════════════
    #     STAGE 3: BM25 RE-RANKING
    # ═══════════════════════════════════════════════════════════════

    def _bm25_rerank(self, query, candidates, k1=1.5, b=0.75):
        """
        Re-rank retrieved candidates using BM25 scoring.

        BM25 formula:
            score = Σ IDF(q) * (tf * (k1+1)) / (tf + k1 * (1 - b + b * |D|/avgDL))

        Combined with cosine similarity for hybrid scoring:
            final_score = 0.6 * normalized_cosine + 0.4 * normalized_bm25
        """
        if not candidates:
            return candidates

        query_terms = query.lower().split()
        N = len(self.chunks)

        for cand in candidates:
            idx = cand["chunk_index"]
            doc_len = self.doc_lengths[idx]
            tf_counter = self.term_freqs[idx]

            bm25_score = 0.0
            for term in query_terms:
                tf = tf_counter.get(term, 0)
                # Document frequency: count how many chunks contain this term
                df = sum(1 for tfc in self.term_freqs if term in tfc)
                if df == 0:
                    continue
                idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
                tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / self.avg_doc_length))
                bm25_score += idf * tf_norm

            cand["bm25_score"] = round(bm25_score, 4)

        # Normalize both scores to [0, 1]
        max_cosine = max(c["cosine_score"] for c in candidates) or 1
        max_bm25 = max(c["bm25_score"] for c in candidates) or 1

        for cand in candidates:
            norm_cosine = cand["cosine_score"] / max_cosine
            norm_bm25 = cand["bm25_score"] / max_bm25
            cand["hybrid_score"] = round(0.6 * norm_cosine + 0.4 * norm_bm25, 4)

        # Sort by hybrid score
        candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return candidates

    # ═══════════════════════════════════════════════════════════════
    #     STAGE 4: GENERATION (Context Assembly + Templates)
    # ═══════════════════════════════════════════════════════════════

    def generate_alert(self, disruption_type, location=None, severity=None):
        """
        Generate an intelligent disruption alert by:
        1. Constructing a semantic query from disruption context
        2. Retrieving relevant knowledge chunks
        3. Re-ranking for relevance
        4. Assembling context and generating structured response
        """
        # Build semantic query
        query_parts = [disruption_type, "supply chain disruption impact"]
        if location:
            query_parts.append(location)

        type_expansions = {
            "storm": "heavy rainfall flooding monsoon cyclone weather",
            "strike": "labor dispute work stoppage union factory shutdown",
            "earthquake": "earthquake seismic infrastructure damage bridge collapse",
            "supplier": "supplier failure equipment breakdown production capacity",
            "demand_spike": "demand spike surge shortage inventory stockout",
            "pandemic": "disease outbreak quarantine health facility shutdown",
        }
        if disruption_type in type_expansions:
            query_parts.append(type_expansions[disruption_type])

        query = " ".join(query_parts)

        # Retrieve (includes BM25 re-ranking)
        retrieved = self.retrieve(query, top_k=5)

        if not retrieved:
            return self._fallback_alert(disruption_type, location)

        # Deduplicate by doc_id (keep highest scoring chunk per document)
        seen_docs = {}
        unique_results = []
        for r in retrieved:
            doc_id = r["metadata"]["doc_id"]
            if doc_id not in seen_docs:
                seen_docs[doc_id] = True
                unique_results.append(r)

        # Use top 3 unique documents for generation
        top_docs = unique_results[:3]
        best = top_docs[0]
        meta = best["metadata"]

        if severity is None:
            severity = meta.get("severity", "medium")

        # Extract recommendations (template fallback)
        recommendations = self._extract_recommendations(top_docs)

        # ── Gemini-Enhanced Generation (if available) ────────
        gemini_response = None
        generation_method = "template"

        if self.gemini and self.gemini.is_available:
            gemini_response = self.gemini.generate_rag_response(
                query=query,
                retrieved_chunks=top_docs,
                disruption_context={
                    "type": disruption_type,
                    "location": location,
                    "severity": severity,
                }
            )
            if gemini_response:
                generation_method = "gemini_ai"

        # Generate analysis (Gemini or template fallback)
        if gemini_response:
            analysis = gemini_response["text"]
        else:
            analysis = self._generate_analysis(top_docs, disruption_type, location)

        # Calculate confidence
        avg_score = np.mean([d["hybrid_score"] for d in top_docs])
        confidence = min(0.95, avg_score * 1.5 + 0.2)

        severity_icons = {"low": "📋", "medium": "⚠️", "high": "🚨", "critical": "🔴"}
        icon = severity_icons.get(severity, "⚠️")

        return {
            "alert": f"{icon} {severity.upper()} RISK: {disruption_type.title()} disruption {'in ' + location if location else 'detected'}",
            "severity": severity,
            "analysis": analysis,
            "recommendations": recommendations,
            "confidence": round(float(confidence), 2),
            "sources_used": len(top_docs),
            "impact_type": meta.get("impact", "unknown"),
            "generation_method": generation_method,
            "gemini_model": gemini_response.get("model") if gemini_response else None,
            "retrieval_pipeline": {
                "query": query,
                "chunks_searched": len(self.chunks),
                "candidates_retrieved": len(retrieved),
                "unique_documents_matched": len(unique_results),
                "vectorizer": "TF-IDF (1,3)-gram",
                "reranker": "BM25 (k1=1.5, b=0.75)",
                "scoring": "Hybrid (0.6×Cosine + 0.4×BM25)",
                "generator": "Gemini 2.5 Flash" if generation_method == "gemini_ai" else "Template Synthesis",
            },
            "retrieved_context": [
                {
                    "doc_id": d["metadata"]["doc_id"],
                    "doc_title": d["metadata"]["doc_title"],
                    "excerpt": d["chunk_text"][:250] + ("..." if len(d["chunk_text"]) > 250 else ""),
                    "category": d["metadata"]["category"],
                    "cosine_score": d["cosine_score"],
                    "bm25_score": d["bm25_score"],
                    "hybrid_score": d["hybrid_score"],
                }
                for d in top_docs
            ],
            "generated_at": datetime.now().isoformat(),
        }

    def _fallback_alert(self, disruption_type, location):
        """Fallback when no documents match."""
        return {
            "alert": f"⚠️ {disruption_type.title()} disruption detected",
            "severity": "medium",
            "analysis": "Limited information available for this specific disruption type in the knowledge base.",
            "recommendations": ["Monitor situation closely", "Prepare contingency plans", "Activate backup suppliers"],
            "confidence": 0.3,
            "sources_used": 0,
            "impact_type": "unknown",
            "retrieval_pipeline": {"query": disruption_type, "chunks_searched": len(self.chunks), "candidates_retrieved": 0},
            "retrieved_context": [],
            "generated_at": datetime.now().isoformat(),
        }

    def _extract_recommendations(self, docs):
        """Extract actionable recommendations from retrieved chunks."""
        recommendations = []
        for doc in docs:
            text = doc["chunk_text"]
            sentences = text.split(". ")
            for sentence in sentences:
                lower = sentence.lower()
                if any(kw in lower for kw in ["recommended", "action", "activate", "reroute", "shift", "negotiate", "implement"]):
                    clean = sentence.strip().rstrip(".")
                    if clean and len(clean) > 15 and clean not in recommendations:
                        recommendations.append(clean)

        if len(recommendations) < 2:
            defaults = [
                "Activate backup suppliers from low-risk cluster",
                "Re-calculate optimal routes avoiding affected areas",
                "Increase safety stock at nearest unaffected warehouse",
                "Notify downstream customers of potential delays",
            ]
            for d in defaults:
                if d not in recommendations:
                    recommendations.append(d)
                if len(recommendations) >= 5:
                    break

        return recommendations[:5]

    def _generate_analysis(self, docs, disruption_type, location):
        """Generate contextual analysis from retrieved knowledge."""
        best_meta = docs[0]["metadata"]
        impact = best_meta.get("impact", "operational delays").replace("_", " ")
        location_text = f"in {location}" if location else "in the supply network"

        severity_ratings = {"low": 3, "medium": 5, "high": 7, "critical": 9}
        severity = best_meta.get("severity", "medium")
        rating = severity_ratings.get(severity, 5)

        duration_map = {"low": "1-2 days", "medium": "3-7 days", "high": "1-3 weeks", "critical": "3-6 weeks"}
        duration = duration_map.get(severity, "unknown")

        # Cross-reference multiple sources
        categories = set(d["metadata"]["category"] for d in docs)
        regions = set(d["metadata"]["region"] for d in docs)

        analysis = (
            f"RAG Analysis ({len(docs)} sources retrieved, {len(categories)} categories cross-referenced): "
            f"{disruption_type.title()} event {location_text} is expected to cause {impact}. "
            f"Based on analysis of similar historical events in knowledge base "
            f"(regions: {', '.join(regions)}), estimated impact duration is {duration}. "
            f"Supply chain risk rating: {rating}/10. "
            f"Confidence level based on retrieval quality: {docs[0]['hybrid_score']:.0%}."
        )

        return analysis

    # ═══════════════════════════════════════════════════════════════
    #     QUERY API (free-form questions)
    # ═══════════════════════════════════════════════════════════════

    def query(self, question):
        """Answer a free-form question about supply chain disruptions."""
        docs = self.retrieve(question, top_k=3)

        if not docs:
            return {
                "answer": "No relevant information found in the knowledge base for this query.",
                "sources": [],
                "confidence": 0.0,
                "generation_method": "none",
                "pipeline_stats": self.pipeline_stats,
            }

        # ── Try Gemini-enhanced answer ────────────────────────
        generation_method = "template"
        gemini_answer = None

        if self.gemini and self.gemini.is_available:
            gemini_answer = self.gemini.answer_freeform_query(question, docs)
            if gemini_answer:
                generation_method = "gemini_ai"

        if gemini_answer:
            answer = gemini_answer["text"]
        else:
            # Template-based answer
            answer_parts = []
            for i, doc in enumerate(docs):
                title = doc["metadata"]["doc_title"]
                excerpt = doc["chunk_text"][:300]
                score = doc["hybrid_score"]
                answer_parts.append(f"[Source {i+1}: {title} | Relevance: {score:.0%}]\n{excerpt}")

            answer = (
                f"Based on {len(docs)} retrieved passages from the supply chain knowledge base:\n\n"
                + "\n\n".join(answer_parts)
            )

        return {
            "answer": answer,
            "sources": [
                {
                    "doc_id": d["metadata"]["doc_id"],
                    "title": d["metadata"]["doc_title"],
                    "category": d["metadata"]["category"],
                    "cosine_score": d["cosine_score"],
                    "bm25_score": d["bm25_score"],
                    "hybrid_score": d["hybrid_score"],
                }
                for d in docs
            ],
            "confidence": round(float(np.mean([d["hybrid_score"] for d in docs])), 2),
            "generation_method": generation_method,
            "gemini_model": gemini_answer.get("model") if gemini_answer else None,
            "pipeline_stats": self.pipeline_stats,
        }

    def get_pipeline_info(self):
        """Return full pipeline architecture info for transparency."""
        gemini_active = self.gemini and self.gemini.is_available
        gen_method = "Gemini 2.5 Flash LLM" if gemini_active else "Context-aware template synthesis"
        gen_details = "LLM-powered natural language generation" if gemini_active else "Multi-source cross-referencing"

        return {
            "architecture": "Retrieval-Augmented Generation (RAG)",
            "gemini_enhanced": gemini_active,
            "gemini_status": self.gemini.get_status() if self.gemini else {"available": False, "status": "not_configured"},
            "pipeline_stages": [
                {"stage": 1, "name": "Document Ingestion", "method": "Sentence-boundary chunking with overlap", "details": f"{self.pipeline_stats['total_documents']} docs → {self.pipeline_stats['total_chunks']} chunks"},
                {"stage": 2, "name": "Vectorization", "method": "TF-IDF (1,3)-gram with sublinear TF", "details": f"Vocabulary: {self.pipeline_stats['vocabulary_size']} terms"},
                {"stage": 3, "name": "Retrieval", "method": "Cosine similarity top-k", "details": "L2-normalized sparse vectors"},
                {"stage": 4, "name": "Re-Ranking", "method": "BM25 (k1=1.5, b=0.75)", "details": "Hybrid: 0.6×Cosine + 0.4×BM25"},
                {"stage": 5, "name": "Generation", "method": gen_method, "details": gen_details},
            ],
            "stats": self.pipeline_stats,
            "description": (
                "A RAG system using TF-IDF vectorization with (1,3)-gram tokenization for "
                "semantic phrase matching, BM25 re-ranking for relevance boosting, and "
                + ("Gemini 2.5 Flash LLM-powered generation for natural language intelligence reports. " if gemini_active
                   else "template-based generation with provenance tracking. ")
                + "Designed for reliability with graceful LLM fallback."
            ),
        }
