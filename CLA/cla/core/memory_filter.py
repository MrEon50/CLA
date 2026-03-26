"""
Memory Filter - Trójfiltrowy system selekcji pamięci (ADS v7.0).
Implementuje model: RAM → 3 filtry → Pamięć (krótka/długa/konstelacja).
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .concept import Concept
from .concept_graph import ConceptGraph


class MemoryVerdict(Enum):
    """Wynik oceny kandydata do pamięci."""
    DISCARD = "discard"           # Śmieci - do usunięcia
    SHORT_TERM = "short_term"     # Pamięć krótkotrwała (tymczasowa)
    LONG_TERM_SHALLOW = "long_shallow"  # Płytki zapis długoterminowy
    LONG_TERM_DEEP = "long_deep"  # Głęboki zapis (ważne, emocjonalne)
    CONSTELLATION = "constellation"  # Część większej idei/światopoglądu


@dataclass
class MemoryCandidate:
    """Kandydat do zapisania w pamięci."""
    content: str
    embedding: Optional[np.ndarray] = None
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"  # 'user', 'assistant', 'system', 'meditation'
    emotional_valence: float = 0.0  # -1.0 do 1.0
    
    # Wyniki filtrów (wypełniane przez MemoryFilter)
    survival_score: float = 0.0
    sensitivity_score: float = 0.0
    curiosity_score: float = 0.0


@dataclass
class MemoryDecision:
    """Pełna decyzja o przetworzeniu pamięci."""
    candidate: MemoryCandidate
    verdict: MemoryVerdict
    scores: Dict[str, float]
    reasoning: str
    suggested_depth: float = 0.5
    suggested_weight: float = 0.5
    suggested_links: List[str] = field(default_factory=list)


class MemoryFilter:
    """
    Trójfiltrowy system selekcji pamięci (ADS v7.0).
    
    Filtry oparte na Pierwotnych Cechach Egzystencjalnych:
    1. is_useful() ← Przetrwanie
    2. do_i_feel_it() ← Wrażliwość
    3. is_it_new() ← Ciekawość
    
    Wyjście:
    - DISCARD: NIE na wszystkie filtry → usunięcie
    - SHORT_TERM: Słabe TAK → tymczasowe
    - LONG_TERM_DEEP: Silne TAK na Przetrwanie lub Wrażliwość
    - LONG_TERM_SHALLOW: Średnie TAK
    - CONSTELLATION: Łączy się z istniejącymi grupami idei
    """
    
    # Progi decyzyjne
    DISCARD_THRESHOLD = 0.25
    SHORT_TERM_THRESHOLD = 0.45
    DEEP_SURVIVAL_THRESHOLD = 0.75
    DEEP_SENSITIVITY_THRESHOLD = 0.65
    CONSTELLATION_LINK_THRESHOLD = 3  # Min. połączeń do konstelacji
    
    def __init__(self, graph: ConceptGraph):
        self.graph = graph
        
        # Słowa kluczowe dla detekcji użyteczności (Przetrwanie)
        self.survival_keywords = {
            'high': ['ważne', 'krytyczne', 'pilne', 'konieczne', 'musisz', 'zawsze', 
                     'important', 'critical', 'urgent', 'must', 'essential', 'vital',
                     'pamiętaj', 'nie zapomnij', 'kluczowe', 'fundamentalne'],
            'medium': ['przydatne', 'pomocne', 'warto', 'dobrze', 'useful', 'helpful',
                       'praktyczne', 'zalecane', 'sugeruję'],
            'low': ['może', 'ewentualnie', 'opcjonalnie', 'maybe', 'perhaps']
        }
        
        # Słowa kluczowe dla detekcji emocji (Wrażliwość)
        self.emotional_keywords = {
            'positive': ['kocham', 'uwielbiam', 'cudowne', 'wspaniałe', 'radość', 
                         'love', 'amazing', 'wonderful', 'joy', 'happy', 'excited',
                         'fantastyczne', 'niesamowite', 'piękne', 'wzruszające'],
            'negative': ['nienawidzę', 'straszne', 'okropne', 'smutek', 'złość',
                         'hate', 'terrible', 'awful', 'sad', 'angry', 'frustrated',
                         'przerażające', 'bolesne', 'tragiczne', 'rozpacz'],
            'neutral_intense': ['dziwne', 'niezwykłe', 'zaskakujące', 'strange',
                                'surprising', 'unexpected', 'niesłychane']
        }
    
    def is_useful(self, candidate: MemoryCandidate) -> float:
        """
        Filtr Przetrwania: Czy to użyteczne dla celów/wartości?
        
        Sprawdza:
        - Semantic similarity do DNA (Przetrwanie, Równowaga)
        - Obecność słów kluczowych wskazujących na ważność
        - Czy pochodzi od użytkownika (wyższa waga)
        """
        score = 0.0
        content_lower = candidate.content.lower()
        
        # 1. Keyword matching
        for keyword in self.survival_keywords['high']:
            if keyword in content_lower:
                score += 0.25
        for keyword in self.survival_keywords['medium']:
            if keyword in content_lower:
                score += 0.12
        for keyword in self.survival_keywords['low']:
            if keyword in content_lower:
                score += 0.05
        
        # 2. Source weight (user input is more important)
        if candidate.source == 'user':
            score += 0.15
        elif candidate.source == 'system':
            score += 0.10
        
        # 3. Semantic similarity to DNA concepts
        if candidate.embedding is not None:
            dna_concepts = [c for c in self.graph.concepts.values() 
                          if c.properties.get('type') in ['dna', 'primordial_dna']]
            
            if dna_concepts:
                max_sim = 0.0
                for dna in dna_concepts:
                    if dna.embedding is not None:
                        sim = self._cosine_similarity(candidate.embedding, dna.embedding)
                        max_sim = max(max_sim, sim)
                
                # Wysoka podobność do DNA = bardzo użyteczne
                score += max_sim * 0.4
        
        # 4. Length factor (short = less important, very long = maybe noise)
        word_count = len(candidate.content.split())
        if 10 <= word_count <= 100:
            score += 0.1  # Optimal length
        elif word_count < 5:
            score -= 0.1  # Too short
        
        candidate.survival_score = min(1.0, max(0.0, score))
        return candidate.survival_score
    
    def do_i_feel_it(self, candidate: MemoryCandidate) -> float:
        """
        Filtr Wrażliwości: Czy to wywołuje emocje?
        
        Sprawdza:
        - Valence (wartość emocjonalna)
        - Słowa kluczowe emocjonalne
        - Introspekcja (czy dotyczy "ja", "my", tożsamości)
        """
        score = 0.0
        content_lower = candidate.content.lower()
        
        # 1. Keyword emotional detection
        for keyword in self.emotional_keywords['positive']:
            if keyword in content_lower:
                score += 0.2
        for keyword in self.emotional_keywords['negative']:
            if keyword in content_lower:
                score += 0.25  # Negative emotions are more memorable
        for keyword in self.emotional_keywords['neutral_intense']:
            if keyword in content_lower:
                score += 0.15
        
        # 2. Personal pronouns (introspection)
        personal_markers = ['ja ', 'mnie', 'mój', 'moja', 'my ', 'nam', 'nasz',
                           'i ', 'me ', 'my ', 'mine', 'we ', 'our', 'us ']
        for marker in personal_markers:
            if marker in content_lower:
                score += 0.08
        
        # 3. Question marks (curiosity/engagement)
        score += content_lower.count('?') * 0.05
        
        # 4. Exclamation marks (intensity)
        score += min(0.3, content_lower.count('!') * 0.15)
        
        # 5. Use provided valence if available
        if candidate.emotional_valence != 0.0:
            score += abs(candidate.emotional_valence) * 0.3
        
        # 6. Semantic similarity to emotion concepts
        if candidate.embedding is not None:
            emotion_concepts = [c for c in self.graph.concepts.values()
                              if c.properties.get('type') == 'emotion']
            
            if emotion_concepts:
                max_sim = 0.0
                for emo in emotion_concepts:
                    if emo.embedding is not None:
                        sim = self._cosine_similarity(candidate.embedding, emo.embedding)
                        max_sim = max(max_sim, sim)
                
                score += max_sim * 0.25
        
        candidate.sensitivity_score = min(1.0, max(0.0, score))
        return candidate.sensitivity_score
    
    def is_it_new(self, candidate: MemoryCandidate) -> float:
        """
        Filtr Ciekawości: Czy to nowe/nieznane?
        
        Nowość = 1 - max(similarity do istniejących konceptów)
        Wysokie gdy:
        - Treść różni się od tego, co już wiemy
        - Zawiera nowe słowa/pojęcia
        """
        if candidate.embedding is None:
            # Bez embeddingu - ocena heurystyczna
            return 0.5
        
        if not self.graph.concepts:
            # Pusty graf = wszystko jest nowe
            return 1.0
        
        # Znajdź najbardziej podobny istniejący koncept
        max_similarity = 0.0
        
        for concept in self.graph.concepts.values():
            if concept.embedding is not None:
                sim = self._cosine_similarity(candidate.embedding, concept.embedding)
                max_similarity = max(max_similarity, sim)
        
        # Nowość = odwrotność podobieństwa
        novelty = 1.0 - max_similarity
        
        # Bonus za słowa pytające (eksploracja)
        content_lower = candidate.content.lower()
        exploration_words = ['co jeśli', 'a gdyby', 'dlaczego', 'jak to', 
                            'what if', 'why', 'how come', 'imagine']
        for word in exploration_words:
            if word in content_lower:
                novelty = min(1.0, novelty + 0.1)
        
        candidate.curiosity_score = min(1.0, max(0.0, novelty))
        return candidate.curiosity_score
    
    def evaluate(self, candidate: MemoryCandidate) -> MemoryDecision:
        """
        Główna metoda ewaluacji - przepuszcza przez 3 filtry i decyduje.
        
        Returns:
            MemoryDecision z werdyktem i sugestiami parametrów
        """
        # Przepuść przez wszystkie filtry
        survival = self.is_useful(candidate)
        sensitivity = self.do_i_feel_it(candidate)
        curiosity = self.is_it_new(candidate)
        
        scores = {
            'survival': survival,
            'sensitivity': sensitivity,
            'curiosity': curiosity,
            'total': survival + sensitivity + curiosity
        }
        
        # Decyzja o werdykcie
        total = scores['total']
        
        # DISCARD: Wszystko na NIE
        if total < self.DISCARD_THRESHOLD * 3:
            return MemoryDecision(
                candidate=candidate,
                verdict=MemoryVerdict.DISCARD,
                scores=scores,
                reasoning=f"Zbyt niski wynik łączny ({total:.2f}). Odrzucono jako szum.",
                suggested_depth=0.0,
                suggested_weight=0.0
            )
        
        # LONG_TERM_DEEP: Silne TAK na Przetrwanie lub Wrażliwość
        if survival >= self.DEEP_SURVIVAL_THRESHOLD or sensitivity >= self.DEEP_SENSITIVITY_THRESHOLD:
            # Znajdź potencjalne połączenia
            suggested_links = self._find_potential_links(candidate, threshold=0.5)
            
            return MemoryDecision(
                candidate=candidate,
                verdict=MemoryVerdict.LONG_TERM_DEEP,
                scores=scores,
                reasoning=f"Ważne dla przetrwania ({survival:.2f}) lub silnie emocjonalne ({sensitivity:.2f}). Głęboki zapis.",
                suggested_depth=0.85,
                suggested_weight=0.75,
                suggested_links=suggested_links
            )
        
        # CONSTELLATION: Wiele połączeń z istniejącymi konceptami
        potential_links = self._find_potential_links(candidate, threshold=0.6)
        if len(potential_links) >= self.CONSTELLATION_LINK_THRESHOLD:
            return MemoryDecision(
                candidate=candidate,
                verdict=MemoryVerdict.CONSTELLATION,
                scores=scores,
                reasoning=f"Łączy się z {len(potential_links)} istniejącymi konceptami. Część większej idei.",
                suggested_depth=0.7,
                suggested_weight=0.6,
                suggested_links=potential_links
            )
        
        # SHORT_TERM: Słabe TAK
        if total < self.SHORT_TERM_THRESHOLD * 3:
            return MemoryDecision(
                candidate=candidate,
                verdict=MemoryVerdict.SHORT_TERM,
                scores=scores,
                reasoning=f"Średni wynik ({total:.2f}). Tymczasowe przechowanie.",
                suggested_depth=0.3,
                suggested_weight=0.3
            )
        
        # LONG_TERM_SHALLOW: Średnie TAK
        suggested_links = self._find_potential_links(candidate, threshold=0.55)
        return MemoryDecision(
            candidate=candidate,
            verdict=MemoryVerdict.LONG_TERM_SHALLOW,
            scores=scores,
            reasoning=f"Przyzwoity wynik ({total:.2f}). Płytki zapis długoterminowy.",
            suggested_depth=0.5,
            suggested_weight=0.45,
            suggested_links=suggested_links
        )
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Oblicza cosine similarity między dwoma wektorami."""
        if a.shape != b.shape:
            min_len = min(len(a), len(b))
            a, b = a[:min_len], b[:min_len]
        
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def _find_potential_links(self, candidate: MemoryCandidate, threshold: float = 0.5) -> List[str]:
        """Znajduje koncepty podobne do kandydata (potencjalne połączenia)."""
        if candidate.embedding is None:
            return []
        
        links = []
        for concept in self.graph.concepts.values():
            if concept.embedding is not None:
                sim = self._cosine_similarity(candidate.embedding, concept.embedding)
                if sim >= threshold:
                    links.append(concept.concept_id)
        
        return links


def create_concept_from_decision(decision: MemoryDecision, name: str, embedding: np.ndarray = None) -> Optional[Concept]:
    """
    Tworzy Concept na podstawie decyzji MemoryFilter.
    
    Returns None jeśli werdykt to DISCARD lub SHORT_TERM.
    """
    if decision.verdict in [MemoryVerdict.DISCARD, MemoryVerdict.SHORT_TERM]:
        return None
    
    concept = Concept(
        name=name,
        embedding=embedding or decision.candidate.embedding,
        weight=decision.suggested_weight,
        depth=decision.suggested_depth,
        valence=decision.candidate.emotional_valence
    )
    
    # Ustaw właściwości na podstawie werdyktu
    concept.properties = {
        'type': 'memory',
        'memory_tier': decision.verdict.value,
        'source': decision.candidate.source,
        'filter_scores': decision.scores,
        'created_from': 'memory_filter'
    }
    
    # Pre-linkuj jeśli są sugestie
    for link_id in decision.suggested_links:
        concept.links[link_id] = (0.5, 'associated')
    
    return concept


class AssociativeMemory:
    """
    Pamięć Asocjacyjna (RAG - Retrieval Augmented Generation).
    Przechowuje historię jako wektory i pozwala na szybkie wyszukiwanie kontekstowe.
    """
    
    MAX_ENTRIES = 1000  # Limit FIFO dla wydajności
    
    def __init__(self):
        self.entries: List[Dict[str, Any]] = []
        
    def add_entry(self, content: str, embedding: np.ndarray, timestamp: datetime = None, metadata: Dict = None):
        """Dodaj wpis do pamięci wektorowej."""
        if embedding is None:
            return
            
        self.entries.append({
            'content': content,
            'embedding': embedding,
            'timestamp': timestamp or datetime.now(),
            'metadata': metadata or {}
        })
        
        # Limit FIFO - usuń najstarsze wpisy jeśli przekroczono limit
        if len(self.entries) > self.MAX_ENTRIES:
            self.entries = self.entries[-self.MAX_ENTRIES:]

        
    def retrieve(self, query_embedding: np.ndarray, limit: int = 3, threshold: float = 0.4) -> List[str]:
        """
        Znajdź wpisy najbardziej podobne do zapytania.
        Returns: Lista treści wpisów.
        """
        if not self.entries or query_embedding is None:
            return []
            
        scores = []
        for entry in self.entries:
            # Cosine similarity
            vec = entry['embedding']
            if vec.shape != query_embedding.shape:
                continue # Skip dimensional mismatches
                
            norm = np.linalg.norm(vec) * np.linalg.norm(query_embedding)
            if norm == 0: sim = 0.0
            else: sim = float(np.dot(vec, query_embedding) / norm)
            
            scores.append((sim, entry))
            
        # Sortuj malejąco i filtruj
        scores.sort(key=lambda x: x[1]['timestamp'], reverse=True) # Najpierw promuj nowsze jako "recybernetyka"
        # Ale właściwe sortowanie to po podobieństwie
        scores.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for sim, entry in scores:
            if sim >= threshold:
                # Formatuj: "[YYYY-MM-DD] Treść"
                date_str = entry['timestamp'].strftime('%Y-%m-%d')
                results.append(f"[{date_str}] {entry['content']} (rezonans: {sim:.2f})")
                if len(results) >= limit:
                    break
                    
        return results
    
    def clear(self):
        self.entries = []
