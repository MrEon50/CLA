"""
Podstawowe klasy dla reprezentacji konceptów w CLA.
"""

import numpy as np
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Concept:
    """
    Pojedynczy koncept w przestrzeni poznawczej.
    
    Koncept to nie tylko embedding, ale struktura semantyczna z:
    - Tożsamością (name, id)
    - Reprezentacją (embedding)
    - Stanem (activation, weight)
    - Relacjami (links do innych konceptów)
    - Historią (kiedy powstał, jak ewoluował)
    """
    
    name: str
    concept_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Reprezentacja semantyczna
    embedding: Optional[np.ndarray] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # Stan dynamiczny
    activation: float = 0.0  # 0.0 - 1.0, jak silnie aktywny TERAZ
    weight: float = 0.5      # 0.0 - 1.0, jak ważny OGÓLNIE (Salience w ADS)
    depth: float = 0.5       # 0.0 - 1.0, odporność na wygasanie (Depth w ADS)
    valence: float = 0.0     # -1.0 do 1.0, ładunek emocjonalny/wartościowy
    
    # Relacje
    # {concept_id: (strength, relation_type)}
    # relation_type: 'generic', 'is_a', 'causes', 'hinders', 'synthesized_from', 'antonym'
    links: Dict[str, Tuple[float, str]] = field(default_factory=dict) 
    
    # Status Inkubacji (ADS v5.6)
    is_incubating: bool = False
    
    # Metadata temporalne
    created_at: datetime = field(default_factory=datetime.now)
    era: str = "genesis"  # Obecna era poznawcza
    last_activated: Optional[datetime] = None
    activation_count: int = 0
    
    # Emergencja
    parent_concepts: List[str] = field(default_factory=list)  # IDs konceptów-rodziców
    is_emergent: bool = False  # Czy powstał przez syntezę
    emergence_context: Optional[str] = None
    
    # Kategoria dualności
    duality_category: Optional[str] = None  # 'emotional', 'cognitive', 'moral'
    
    # ADS v7.0: Primordial DNA priority (1-5, None dla nie-DNA)
    # 1=Przetrwanie, 2=Równowaga, 3=Wspólnota, 4=Wrażliwość, 5=Ciekawość
    primordial_priority: Optional[int] = None
    
    # ADS v7.0: Memory tier classification
    # 'short', 'long_shallow', 'long_deep', 'constellation', None
    memory_tier: Optional[str] = None
    
    def activate(self, strength: float = 1.0):
        """Aktywuj koncept z daną siłą."""
        self.activation = min(1.0, self.activation + strength)
        self.last_activated = datetime.now()
        self.activation_count += 1
    
    def decay(self, rate: float = 0.1):
        """Naturalny zanik aktywacji."""
        self.activation = max(0.0, self.activation - rate)
    
    def link_to(self, other_concept_id: str, strength: float, rel_type: str = 'generic'):
        """Stwórz lub wzmocnij link do innego konceptu z określonym typem relacji."""
        self.links[other_concept_id] = (strength, rel_type)
    
    def get_link_strength(self, other_concept_id: str) -> float:
        """Pobierz siłę linku do innego konceptu."""
        if other_concept_id in self.links:
            return self.links[other_concept_id][0]
        return 0.0
        
    def get_link_type(self, other_concept_id: str) -> str:
        """Pobierz typ relacji."""
        if other_concept_id in self.links:
            return self.links[other_concept_id][1]
        return 'none'
    
    def __repr__(self):
        return f"Concept('{self.name}', activation={self.activation:.2f}, weight={self.weight:.2f}, depth={self.depth:.2f})"


@dataclass
class DualityPair:
    """
    Para konceptów w relacji dualności (przeciwieństwa).
    """
    
    pole_a: Concept
    pole_b: Concept
    category: str  # 'emotional', 'cognitive', 'moral'
    
    # Miary napięcia
    opposition: float = 0.0  # Jak bardzo są przeciwstawne (0-1)
    friction: float = 0.0  # Tarcie poznawcze (0-1)
    
    # Kontekst
    context: Optional[str] = None
    
    def calculate_opposition(self) -> float:
        """
        Oblicz jak bardzo koncepty są przeciwstawne.
        Używa cosine distance w przestrzeni embeddingów.
        """
        if self.pole_a.embedding is not None and self.pole_b.embedding is not None:
            # Cosine similarity
            similarity = np.dot(self.pole_a.embedding, self.pole_b.embedding) / (
                np.linalg.norm(self.pole_a.embedding) * np.linalg.norm(self.pole_b.embedding)
            )
            # Opposition = 1 - similarity
            self.opposition = 1.0 - similarity
        else:
            # Fallback: jeśli brak embeddingów, użyj heurystyki
            self.opposition = 0.7  # Domyślnie średnia przeciwstawność
        
        return self.opposition
    
    def calculate_friction(self) -> float:
        """
        Oblicz tarcie poznawcze.
        
        Tarcie = aktywacja_A × aktywacja_B × przeciwstawność
        
        Wysokie tarcie gdy:
        - Oba koncepty są silnie aktywne
        - Są bardzo przeciwstawne
        """
        self.friction = (
            self.pole_a.activation * 
            self.pole_b.activation * 
            self.opposition
        )
        
        return self.friction
    
    def __repr__(self):
        return (f"DualityPair({self.pole_a.name} ↔ {self.pole_b.name}, "
                f"friction={self.friction:.2f})")


def create_concept_from_dict(data: Dict[str, Any]) -> Concept:
    """Helper do tworzenia konceptu z dictionary."""
    embedding = data.get('embedding')
    if embedding is not None and not isinstance(embedding, np.ndarray):
        embedding = np.array(embedding)
    
    return Concept(
        name=data['name'],
        embedding=embedding,
        properties=data.get('properties', {}),
        activation=data.get('activation', 0.0),
        weight=data.get('weight', 0.5),
        depth=data.get('depth', 0.5),
        valence=data.get('valence', 0.0),
        is_incubating=data.get('is_incubating', False),
        duality_category=data.get('duality_category'),
        primordial_priority=data.get('primordial_priority'),
        memory_tier=data.get('memory_tier')
    )

