import logging
from typing import Dict, List, Set
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)

class NLPService:
    """Enhanced NLP analysis with multi-domain support"""
    
    def __init__(self):
        logger.info(f"Loading sentence transformer: {settings.SENTENCE_TRANSFORMER_MODEL}")
        self.model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
        
        # Multi-domain technical keywords
        self.domain_keywords = {
            'computer_science': {
                'algorithm', 'complexity', 'array', 'linked list', 'stack', 'queue',
                'tree', 'graph', 'hash', 'sorting', 'searching', 'recursion',
                'dynamic programming', 'greedy', 'backtracking', 'divide and conquer',
                'time complexity', 'space complexity', 'big o', 'optimization',
                'data structure', 'binary search', 'traversal', 'pointer', 'heap',
                'binary tree', 'trie', 'dp', 'dfs', 'bfs', 'dijkstra'
            },
            'business': {
                'strategy', 'customer', 'market', 'revenue', 'growth', 'competitive',
                'brand', 'vision', 'mission', 'objective', 'stakeholder', 'value',
                'innovation', 'digital', 'transformation', 'roi', 'kpi', 'metrics',
                'analytics', 'customer-centric', 'engagement', 'retention', 'acquisition',
                'business model', 'value proposition', 'competitive advantage'
            },
            'finance': {
                'investment', 'portfolio', 'risk', 'return', 'asset', 'liability',
                'equity', 'debt', 'dividend', 'capital', 'valuation', 'cash flow',
                'profit', 'loss', 'margin', 'financial', 'accounting', 'balance sheet',
                'income statement', 'liquidity', 'solvency', 'insurance', 'premium'
            },
            'science': {
                'hypothesis', 'experiment', 'theory', 'data', 'analysis', 'research',
                'variable', 'control', 'observation', 'measurement', 'methodology',
                'conclusion', 'evidence', 'statistical', 'correlation', 'causation'
            },
            'mathematics': {
                'equation', 'function', 'variable', 'constant', 'derivative', 'integral',
                'matrix', 'vector', 'probability', 'statistics', 'theorem', 'proof',
                'calculation', 'formula', 'geometric', 'algebraic', 'trigonometric'
            }
        }
        
        # Engagement indicators (enhanced)
        self.engagement_patterns = {
            'questions': [
                r'\?',
                r'\b(what|when|where|why|how|who|which|whose|whom)\b[^.]*\?',
                r'\b(can you|could you|would you|do you|did you|will you|have you)\b',
                r'\b(isn\'t it|doesn\'t it|aren\'t they|right)\b\?',
            ],
            'interactive_phrases': [
                r'\b(let\'s|let us)\b',
                r'\b(you can|you should|you might|you could|try to|try this)\b',
                r'\b(think about|consider|imagine|suppose|assume)\b',
                r'\b(understand|see how|notice|observe|look at)\b',
                r'\b(example|for instance|such as|like this)\b',
                r'\b(now|next|first|second|finally|remember)\b',
                r'\b(important|key point|note that|keep in mind)\b',
            ],
            'rhetorical_questions': [
                r'\bdo you know\b',
                r'\bhave you ever\b',
                r'\bcan you imagine\b',
            ],
            'direct_address': [
                r'\byou\b',
                r'\byour\b',
                r'\byou\'re\b',
                r'\byou\'ll\b',
                r'\bwe\b',
                r'\bour\b',
                r'\bus\b',
            ]
        }
    
    def detect_domain(self, transcript: str) -> str:
        """Auto-detect domain from transcript"""
        transcript_lower = transcript.lower()
        domain_scores = {}
        
        for domain, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in transcript_lower)
            domain_scores[domain] = score
        
        # Return domain with highest score, default to 'general'
        if max(domain_scores.values()) > 0:
            return max(domain_scores, key=domain_scores.get)
        return 'general'
    
    async def analyze_engagement(self, transcript: str) -> Dict:
        """
        Enhanced engagement analysis
        
        Returns:
        - qna_pairs: detected Q&A interactions
        - question_count: questions asked
        - interaction_moments: interactive phrases
        - rhetorical_questions: engagement questions
        - direct_address_count: speaker addressing audience
        """
        try:
            logger.info("Analyzing engagement")
            
            transcript_lower = transcript.lower()
            
            # Count questions (multiple patterns)
            question_count = 0
            for pattern in self.engagement_patterns['questions']:
                question_count += len(re.findall(pattern, transcript_lower))
            
            # Count rhetorical questions specifically
            rhetorical_count = 0
            for pattern in self.engagement_patterns['rhetorical_questions']:
                rhetorical_count += len(re.findall(pattern, transcript_lower))
            
            # Count interaction phrases
            interaction_moments = 0
            for phrase in self.engagement_patterns['interactive_phrases']:
                interaction_moments += len(re.findall(phrase, transcript_lower))
            
            # Count direct address (audience engagement)
            direct_address_count = 0
            for pattern in self.engagement_patterns['direct_address']:
                direct_address_count += len(re.findall(pattern, transcript_lower))
            
            # Detect Q&A pairs (questions followed by explanations)
            sentences = [s.strip() for s in transcript.split('.') if s.strip()]
            qna_pairs = 0
            for i in range(len(sentences) - 1):
                if '?' in sentences[i]:
                    # Check if next sentence provides explanation (>5 words)
                    if len(sentences[i + 1].split()) > 5:
                        qna_pairs += 1
            
            return {
                "qna_pairs": qna_pairs,
                "question_count": question_count,
                "interaction_moments": interaction_moments,
                "rhetorical_questions": rhetorical_count,
                "direct_address_count": direct_address_count
            }
        
        except Exception as e:
            logger.error(f"Error analyzing engagement: {e}")
            raise
    
    async def analyze_technical_depth(self, transcript: str, domain: str = None) -> Dict:
        """
        Enhanced technical depth analysis with domain detection
        
        Returns:
        - concept_count: technical concepts mentioned
        - technical_terms: list of technical terms found
        - domain: detected or specified domain
        - concept_correctness_score: semantic correctness
        - depth_score: overall technical depth
        """
        try:
            logger.info("Analyzing technical depth")
            
            transcript_lower = transcript.lower()
            
            # Auto-detect domain if not provided
            if domain is None:
                domain = self.detect_domain(transcript)
            
            logger.info(f"Detected domain: {domain}")
            
            # Get relevant keywords for domain
            if domain in self.domain_keywords:
                relevant_keywords = self.domain_keywords[domain]
            else:
                # Combine all keywords for general content
                relevant_keywords = set()
                for keywords in self.domain_keywords.values():
                    relevant_keywords.update(keywords)
            
            # Find technical terms
            found_terms = []
            for term in relevant_keywords:
                if term in transcript_lower:
                    found_terms.append(term)
            
            concept_count = len(found_terms)
            
            # Semantic analysis for concept correctness
            sentences = [s.strip() for s in transcript.split('.') if len(s.strip()) > 10]
            
            if len(sentences) > 1:
                # Encode sentences
                embeddings = self.model.encode(sentences)
                
                # Check semantic coherence (sentences should be related)
                similarities = []
                for i in range(len(embeddings) - 1):
                    sim = cosine_similarity(
                        embeddings[i].reshape(1, -1),
                        embeddings[i + 1].reshape(1, -1)
                    )[0][0]
                    similarities.append(sim)
                
                # Higher coherence = better concept correctness
                concept_correctness = float(np.mean(similarities)) if similarities else 0.5
            else:
                concept_correctness = 0.5
            
            # Calculate depth score based on technical density
            word_count = len(transcript.split())
            if word_count > 0:
                # Adjusted: more lenient for business/general content
                technical_density = concept_count / word_count
                if domain in ['computer_science', 'mathematics', 'science']:
                    depth_score = min(1.0, technical_density * 100)
                else:
                    # More lenient for business/general domains
                    depth_score = min(1.0, technical_density * 50)
            else:
                depth_score = 0.0
            
            return {
                "concept_count": concept_count,
                "technical_terms": found_terms[:15],  # Top 15
                "domain": domain,
                "concept_correctness_score": round(concept_correctness, 3),
                "depth_score": round(depth_score, 3)
            }
        
        except Exception as e:
            logger.error(f"Error analyzing technical depth: {e}")
            raise