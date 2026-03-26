"""
Meta-Controller - system alokacji uwagi i modulacji intensywności.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from .concept import Concept, DualityPair


@dataclass
class AttentionAllocation:
    """Wynik alokacji uwagi."""
    
    focus_concepts: List[Concept]  # Na czym się skupić
    attention_mode: str  # 'global', 'local', 'balanced'
    processing_depth: str  # 'shallow', 'deep'
    urgency: float  # 0.0 (can wait) - 1.0 (urgent)


class CognitiveSensitivity:
    """
    Wrażliwość i intensywność reakcji poznawczych.
    
    Moduluje jak SILNIE system reaguje na różne typy tarcia.
    """
    
    def __init__(self):
        # Wrażliwość na różne kategorie
        self.sensitivity = {
            'emotional': 0.7,
            'cognitive': 0.9,
            'moral': 0.8
        }
        
        # Intensywność reakcji
        self.intensity_modifiers = {
            'amplify': 1.5,  # Wzmocnienie
            'dampen': 0.5,   # Wyciszenie
            'neutral': 1.0   # Bez zmiany
        }
    
    def modulate_friction(
        self, 
        friction: float, 
        category: str,
        context: Optional[str] = None
    ) -> float:
        """
        Moduluj tarcie poznawcze według wrażliwości i kontekstu.
        
        Args:
            friction: Surowe tarcie
            category: Kategoria dualności
            context: Kontekst sytuacyjny
        
        Returns:
            Zmodulowane tarcie
        """
        # Wrażliwość na kategorię
        sensitivity = self.sensitivity.get(category, 0.5)
        
        # Modyfikator intensywności z kontekstu
        modifier = self._get_intensity_modifier(context)
        
        # Modulowane tarcie
        modulated = friction * sensitivity * modifier
        
        return min(1.0, modulated)
    
    def _get_intensity_modifier(self, context: Optional[str]) -> float:
        """Określ modyfikator intensywności z kontekstu."""
        if not context:
            return self.intensity_modifiers['neutral']
        
        context_lower = context.lower()
        
        # Krytyczne sytuacje - wzmocnienie
        if any(word in context_lower for word in ['critical', 'urgent', 'important', 'life']):
            return self.intensity_modifiers['amplify']
        
        # Rutynowe sytuacje - wyciszenie
        if any(word in context_lower for word in ['routine', 'minor', 'trivial']):
            return self.intensity_modifiers['dampen']
        
        return self.intensity_modifiers['neutral']


class MetaController:
    """
    Meta-Controller - zarządza uwagą i priorytetami.
    
    Decyduje:
    - Na czym się skupić (alokacja uwagi)
    - Jak głęboko przetwarzać (shallow vs deep)
    - Jak szybko reagować (fast vs slow)
    - Jak intensywnie (amplify vs dampen)
    """
    
    def __init__(self):
        self.sensitivity = CognitiveSensitivity()
        
        # Historia decyzji
        self.decision_history = []
    
    def allocate_attention(
        self,
        active_concepts: List[Concept],
        context: Optional[str] = None,
        awareness_state: Optional[Any] = None
    ) -> AttentionAllocation:
        """
        Zdecyduj na czym się skupić (ADS v5.6: Dynamiczny Kompas).
        """
        if not active_concepts:
            return AttentionAllocation(
                focus_concepts=[],
                attention_mode='balanced',
                processing_depth='shallow',
                urgency=0.0
            )

        # --- ADS v5.7: DYNAMICZNY KOMPAS WARTOŚCI ---
        # Dostosuj wagę priorytetów w zależności od nastroju/tarcia
        vt = getattr(awareness_state, 'vitality', 0.5) if awareness_state else 0.5
        fc = getattr(awareness_state, 'friction', 0.0) if awareness_state else 0.0
        
        # Jeśli tarcie jest wysokie, szukaj stabilności (DNA)
        if fc > 0.7:
            # Tryb 'Deep DNA' - skup się na pojęciach o najwyższym Depth/Weight
            focus_concepts = sorted(active_concepts, key=lambda c: (c.depth + c.weight), reverse=True)[:3]
            attention_mode = 'local'
            processing_depth = 'deep'
        # Jeśli witalność jest wysoka, bądź otwarty na nowość (Emergence)
        elif vt > 0.7:
            focus_concepts = sorted(active_concepts, key=lambda c: c.activation, reverse=True)[:7]
            attention_mode = 'global'
            processing_depth = 'shallow'
        else:
            # Balanced
            focus_concepts = sorted(active_concepts, key=lambda c: c.activation, reverse=True)[:5]
            attention_mode = 'balanced'
            processing_depth = 'medium'
        
        # Oblicz metryki dla pilności
        avg_activation = sum(c.activation for c in active_concepts) / len(active_concepts)
        num_emergent = sum(1 for c in active_concepts if c.is_emergent)
        
        # Określ pilność
        urgency = self._calculate_urgency(context, avg_activation, num_emergent)
        
        allocation = AttentionAllocation(
            focus_concepts=focus_concepts,
            attention_mode=attention_mode,
            processing_depth=processing_depth,
            urgency=urgency
        )
        
        self.decision_history.append({
            'allocation': allocation,
            'context': context,
            'num_concepts': len(active_concepts)
        })
        
        return allocation
    
    def _calculate_urgency(
        self, 
        context: Optional[str], 
        avg_activation: float,
        num_emergent: int
    ) -> float:
        """Oblicz pilność sytuacji."""
        urgency = 0.5  # Baseline
        
        # Wysoka aktywacja → wyższa pilność
        urgency += avg_activation * 0.3
        
        # Dużo emergentnych konceptów → wyższa pilność (nowa sytuacja)
        urgency += (num_emergent / 10.0) * 0.2
        
        # Kontekst
        if context:
            context_lower = context.lower()
            if any(word in context_lower for word in ['urgent', 'critical', 'emergency']):
                urgency += 0.3
            elif any(word in context_lower for word in ['routine', 'normal']):
                urgency -= 0.2
        
        return max(0.0, min(1.0, urgency))
    
    def select_primary_duality(
        self, 
        dualities: List[DualityPair],
        context: Optional[str] = None
    ) -> Optional[DualityPair]:
        """
        Wybierz najważniejszą dualność do przetworzenia.
        
        Kryteria:
        - Siła tarcia (friction)
        - Kategoria (wrażliwość)
        - Kontekst (intensywność)
        """
        if not dualities:
            return None
        
        # Moduluj tarcie każdej dualności
        scored_dualities = []
        for duality in dualities:
            modulated_friction = self.sensitivity.modulate_friction(
                duality.friction,
                duality.category,
                context
            )
            scored_dualities.append((duality, modulated_friction))
        
        # Wybierz najwyżej ocenioną
        scored_dualities.sort(key=lambda x: x[1], reverse=True)
        
        return scored_dualities[0][0] if scored_dualities else None
    
    def __repr__(self):
        return f"MetaController(decisions={len(self.decision_history)})"

