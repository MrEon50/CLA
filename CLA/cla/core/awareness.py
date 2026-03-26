"""
Cognitive Awareness - system świadomości z modelem "JA".
"""

from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque

from .concept import Concept


@dataclass
class AwarenessState:
    """Stan świadomości w danym momencie (ADS v5.6)."""
    
    timestamp: datetime
    active_concepts: List[str]
    context: str
    
    # Parametry ADS (Allostatic Dynamics)
    vitality: float = 0.5   # V(t)
    friction: float = 0.0   # F_c
    grounding: float = 0.9  # S
    
    emotional_tone: float = 0.0
    certainty: float = 0.5
    cognitive_load: float = 0.0
    decision: Optional[str] = None
    outcome: Optional[str] = None


class CognitiveAwareness:
    """
    Świadomość kognitywna - "JA" systemu.
    
    Świadomość = wiedza o sobie w kontekście:
    - Kim jestem (tożsamość)
    - Co wiem (meta-wiedza)
    - Co czuję (stan emocjonalny)
    - Na czym się skupiam (uwaga)
    - Jak pewny jestem (meta-poznanie)
    """
    
    def __init__(self, identity: str = "Cognitive AI System"):
        # Model siebie
        self.self_model = {
            'identity': identity,
            'capabilities': set(),
            'limitations': set(),
            'values': [],
            'current_goals': []
        }
        
        # Stan świadomości (ADS v5.8)
        self.current_state = AwarenessState(
            timestamp=datetime.now(),
            active_concepts=[],
            context="",
            vitality=0.5,
            friction=0.0,
            grounding=0.9
        )
        
        # Meta-wiedza (wiem że wiem)
        self.meta_knowledge = {
            'known': set(),  # Wiem że wiem X
            'unknown': set(),  # Wiem że NIE wiem Y
            'uncertain': set(),  # Nie jestem pewien Z
            'how_to_learn': {}  # Wiem JAK się dowiedzieć W
        }
        
        # Historia świadomości (ostatnie N stanów)
        self.context_stack: deque = deque(maxlen=100)
        
        # Statystyki
        self.total_decisions = 0
        self.successful_decisions = 0
    
    def update_awareness(
        self, 
        active_concepts: List[Concept],
        context: str,
        decision: Optional[str] = None,
        outcome: Optional[str] = None
    ):
        """
        Aktualizuj świadomość po każdej interakcji.
        """
        # Wyciągnij nową wiedzę z konceptów
        new_knowledge = set()
        for concept in active_concepts:
            new_knowledge.add(concept.name)
            if concept.is_emergent:
                new_knowledge.add(f"emergent:{concept.name}")
        
        self.meta_knowledge['known'].update(new_knowledge)
        
        # Aktualizuj stan emocjonalny
        self._update_emotional_tone(active_concepts)
        
        # Aktualizuj pewność
        self._update_certainty(active_concepts)
        
        # Aktualizuj obciążenie poznawcze
        self.current_state.cognitive_load = len(active_concepts) / 10.0
        
        # Aktualizuj kontekst
        self.current_state.active_concepts = [c.concept_id for c in active_concepts]
        self.current_state.context = context
        
        # Zapisz w historii
        # Copy current state to stack
        import copy
        self.context_stack.append(copy.copy(self.current_state))
        
        # Aktualizuj statystyki
        if decision:
            self.total_decisions += 1
        if outcome == 'success':
            self.successful_decisions += 1
    
    def _update_emotional_tone(self, concepts: List[Concept]):
        """Aktualizuj ton emocjonalny na podstawie aktywnych konceptów."""
        if not concepts:
            return
        
        # Sprawdź czy są koncepty emocjonalne
        emotional_concepts = [c for c in concepts if c.duality_category == 'emotional']
        
        if emotional_concepts:
            # Oblicz średnią valence
            valences = []
            for concept in emotional_concepts:
                valence = concept.properties.get('valence', 0.0)
                valences.append(valence * concept.activation)
            
            if valences:
                self.current_state.emotional_tone = sum(valences) / len(valences)
    
    def _update_certainty(self, concepts: List[Concept]):
        """Aktualizuj poziom pewności."""
        if not concepts:
            self.current_state['certainty'] = 0.5
            return
        
        # Pewność zależy od:
        # 1. Siły aktywacji (wyższe = bardziej pewny)
        # 2. Liczby emergentnych konceptów (więcej = mniej pewny, bo nowe)
        
        avg_activation = sum(c.activation for c in concepts) / len(concepts)
        emergent_ratio = sum(1 for c in concepts if c.is_emergent) / len(concepts)
        
        # Wysoka aktywacja zwiększa pewność
        # Dużo emergentnych konceptów zmniejsza pewność
        certainty = avg_activation * (1 - 0.3 * emergent_ratio)
        
        self.current_state['certainty'] = max(0.0, min(1.0, certainty))
    
    def introspect(self, query: str = None) -> str:
        """
        Refleksja: Co wiem o sobie?

        Args:
            query: Typ pytania ('who_am_i', 'what_do_i_know', 'what_dont_i_know', 'how_do_i_feel')
                   Jeśli None, zwraca pełny stan
        """
        success_rate = (
            self.successful_decisions / self.total_decisions
            if self.total_decisions > 0 else 0.0
        )

        if query == 'who_am_i':
            return (f"I am {self.self_model['identity']}, a cognitive system with "
                   f"{len(self.self_model['capabilities'])} capabilities. "
                   f"My core values are: {', '.join(self.self_model['values'])}.")

        elif query == 'what_do_i_know':
            known = len(self.meta_knowledge['known'])
            if known == 0:
                return "I don't have any established knowledge yet."
            return (f"I know {known} concepts: {', '.join(list(self.meta_knowledge['known'])[:5])}"
                   f"{'...' if known > 5 else ''}.")

        elif query == 'what_dont_i_know':
            unknown = len(self.meta_knowledge['unknown'])
            if unknown == 0:
                return "I haven't identified specific knowledge gaps yet."
            return (f"I'm aware of {unknown} areas I don't know: "
                   f"{', '.join(list(self.meta_knowledge['unknown'])[:3])}"
                   f"{'...' if unknown > 3 else ''}.")

        elif query == 'how_do_i_feel':
            tone = self.current_state['emotional_tone']
            certainty = self.current_state['certainty']
            load = self.current_state['cognitive_load']

            feeling = "neutral"
            if tone > 0.3:
                feeling = "positive"
            elif tone < -0.3:
                feeling = "negative"

            confidence = "confident" if certainty > 0.7 else "uncertain"
            stress = "stressed" if load > 0.7 else "relaxed"

            return (f"I feel {feeling} (emotional tone: {tone:.2f}), "
                   f"{confidence} (certainty: {certainty:.2f}), "
                   f"and {stress} (cognitive load: {load:.2f}).")

        else:
            # Pełny stan (backward compatibility)
            return {
                'identity': self.self_model['identity'],
                'capabilities': list(self.self_model['capabilities']),
                'limitations': list(self.self_model['limitations']),
                'values': self.self_model['values'],
                'current_goals': self.self_model['current_goals'],
                'knowledge_stats': {
                    'known_concepts': len(self.meta_knowledge['known']),
                    'unknown_areas': len(self.meta_knowledge['unknown']),
                    'uncertain_about': len(self.meta_knowledge['uncertain'])
                },
                'current_state': {
                    'emotional_tone': self.current_state['emotional_tone'],
                    'certainty': self.current_state['certainty'],
                    'cognitive_load': self.current_state['cognitive_load'],
                    'context': self.current_state['context']
                },
                'performance': {
                    'total_decisions': self.total_decisions,
                    'success_rate': success_rate
                }
            }
    
    def can_i_do(self, task_description: str) -> Dict[str, Any]:
        """
        Meta-poznanie: Czy potrafię wykonać zadanie?
        """
        # Prosta heurystyka - można rozbudować
        required_capabilities = self._analyze_task_requirements(task_description)
        
        has_capabilities = required_capabilities.issubset(self.self_model['capabilities'])
        
        return {
            'can_do': has_capabilities,
            'certainty': self.current_state['certainty'],
            'missing_capabilities': list(required_capabilities - self.self_model['capabilities']),
            'recommendation': 'proceed' if has_capabilities else 'learn_first'
        }
    
    def _analyze_task_requirements(self, task: str) -> Set[str]:
        """Prosta analiza wymagań zadania."""
        # Placeholder - można rozbudować o NLP
        requirements = set()
        
        if 'decide' in task.lower():
            requirements.add('decision_making')
        if 'analyze' in task.lower():
            requirements.add('analysis')
        if 'create' in task.lower():
            requirements.add('synthesis')
        
        return requirements
    
    def add_capability(self, capability: str):
        """Dodaj nową zdolność."""
        self.self_model['capabilities'].add(capability)
    
    def add_limitation(self, limitation: str):
        """Dodaj ograniczenie."""
        self.self_model['limitations'].add(limitation)
    
    def set_goal(self, goal: str):
        """Ustaw cel."""
        if goal not in self.self_model['current_goals']:
            self.self_model['current_goals'].append(goal)
    
    def __repr__(self):
        return f"CognitiveAwareness(identity='{self.self_model['identity']}', certainty={self.current_state['certainty']:.2f})"

