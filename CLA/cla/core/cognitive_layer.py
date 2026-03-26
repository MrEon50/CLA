"""
Cognitive Layer Architecture (CLA) - główna klasa integrująca wszystkie komponenty.
"""

from typing import Dict, List, Optional, Any
import numpy as np

from .concept import Concept, create_concept_from_dict
from .concept_graph import ConceptGraph
from .dual_processing import DualProcessingEngine, CognitiveSynthesis
from .awareness import CognitiveAwareness
from .meta_controller import MetaController
from .safety_gate import SafetyGate


class CognitiveLayer:
    """
    Cognitive Layer Architecture - warstwa kognitywna dla AGI.
    
    Integruje:
    - ConceptGraph: Pamięć konceptualna (substrat relacyjny)
    - DualProcessingEngine: Mechanizm tarcia poznawczego i syntezy
    - CognitiveAwareness: Świadomość z modelem "JA"
    - MetaController: Alokacja uwagi i modulacja intensywności
    - SafetyGate: Bezpieczeństwo i invariants
    """
    
    def __init__(self, identity: str = "Cognitive AI System"):
        # Warstwa 2: Pamięć
        self.concept_graph = ConceptGraph(decay_rate=0.1)
        
        # Warstwa 3: Cognition
        self.dual_engine = DualProcessingEngine(self.concept_graph)
        self.awareness = CognitiveAwareness(identity=identity)
        self.meta_controller = MetaController()
        
        # Warstwa 4: Safety
        self.safety_gate = SafetyGate()
        
        # Historia interakcji
        self.interaction_history = []
    
    def process(
        self, 
        input_concepts: List[Dict[str, Any]],
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Pełny cykl poznawczy.
        
        Args:
            input_concepts: Lista konceptów jako dictionaries
            context: Kontekst sytuacyjny
        
        Returns:
            Dict z decyzją, wyjaśnieniem, świadomością
        """
        # === FAZA 1: DODAJ KONCEPTY DO GRAFU ===
        concepts = []
        for concept_data in input_concepts:
            concept = create_concept_from_dict(concept_data)
            concept_id = self.concept_graph.add_concept(concept)
            concepts.append(concept)
        
        # === FAZA 2: SPREADING ACTIVATION ===
        # Aktywuj koncepty i propaguj po grafie
        source_ids = [c.concept_id for c in concepts]
        self.concept_graph.spreading_activation(source_ids, initial_activation=1.0)
        
        # Pobierz aktywne koncepty
        active_concepts = self.concept_graph.get_active_concepts(threshold=0.3)
        
        # === FAZA 3: ŚWIADOMOŚĆ ===
        # Aktualizuj świadomość
        self.awareness.update_awareness(active_concepts, context)
        
        # === FAZA 4: META-CONTROLLER ===
        # Alokuj uwagę (ADS v5.7: Uwzględnij stan świadomości dla kompasu)
        attention = self.meta_controller.allocate_attention(
            active_concepts, 
            context,
            awareness_state=self.awareness.current_state # Przekaż aktualny nastrój
        )
        
        # === FAZA 5: DUAL PROCESSING ===
        # Przetwarzaj z focus concepts
        synthesis = self.dual_engine.process(attention.focus_concepts, context)
        
        # === FAZA 6: SAFETY CHECK ===
        if synthesis:
            is_safe, violation = self.safety_gate.check_synthesis(synthesis, context)
            
            if not is_safe:
                # Naruszenie bezpieczeństwa
                self.safety_gate.log_violation(violation)
                
                return {
                    'status': 'rejected',
                    'reason': 'safety_violation',
                    'violation': {
                        'invariant': violation.invariant,
                        'severity': violation.severity,
                        'description': violation.description,
                        'recommendation': violation.recommendation
                    },
                    'awareness': self.awareness.introspect()
                }
            
            # Dodaj nowy koncept emergentny do grafu
            self.concept_graph.add_concept(synthesis.new_concept)
            
            # Połącz z rodzicami
            for parent_id in synthesis.new_concept.parent_concepts:
                self.concept_graph.link_concepts(
                    synthesis.new_concept.concept_id,
                    parent_id,
                    strength=0.8,
                    rel_type='synthesized_from'
                )
            
            result = {
                'status': 'success',
                'synthesis': {
                    'new_concept': synthesis.new_concept.name,
                    'type': synthesis.synthesis_type,
                    'reasoning': synthesis.reasoning,
                    'confidence': synthesis.confidence,
                    'properties': synthesis.new_concept.properties
                },
                'duality': {
                    'pole_a': synthesis.source_duality.pole_a.name,
                    'pole_b': synthesis.source_duality.pole_b.name,
                    'category': synthesis.source_duality.category,
                    'friction': synthesis.source_duality.friction
                },
                'attention': {
                    'mode': attention.attention_mode,
                    'depth': attention.processing_depth,
                    'urgency': attention.urgency
                },
                'awareness': self.awareness.introspect()
            }
        else:
            # Brak znaczącego tarcia
            result = {
                'status': 'no_synthesis',
                'reason': 'insufficient_friction',
                'active_concepts': [c.name for c in active_concepts],
                'attention': {
                    'mode': attention.attention_mode,
                    'depth': attention.processing_depth,
                    'urgency': attention.urgency
                },
                'awareness': self.awareness.introspect()
            }
        
        # === FAZA 7: ZANIK ===
        # Naturalny zanik aktywacji
        self.concept_graph.decay_all()
        
        # Zapisz w historii
        self.interaction_history.append({
            'context': context,
            'result': result
        })
        
        return result
    
    def learn_from_feedback(
        self, 
        feedback: Dict[str, Any]
    ):
        """
        Uczenie z feedbacku użytkownika.
        
        Args:
            feedback: Dict z oceną decyzji
        """
        outcome = feedback.get('outcome', 'unknown')
        
        # Aktualizuj świadomość
        self.awareness.update_awareness(
            active_concepts=[],
            context=feedback.get('context', ''),
            decision=feedback.get('decision'),
            outcome=outcome
        )
        
        # Aktualizuj shared grounding jeśli podane
        if 'shared_grounding' in feedback:
            self.safety_gate.update_shared_grounding(feedback['shared_grounding'])
    
    def get_status(self) -> Dict[str, Any]:
        """Pobierz status systemu."""
        return {
            'identity': self.awareness.self_model['identity'],
            'concept_graph': {
                'total_concepts': len(self.concept_graph),
                'active_concepts': len(self.concept_graph.get_active_concepts())
            },
            'awareness': self.awareness.introspect(),
            'safety': self.safety_gate.get_safety_report(),
            'interactions': len(self.interaction_history)
        }
    
    def __repr__(self):
        return f"CognitiveLayer(concepts={len(self.concept_graph)}, interactions={len(self.interaction_history)})"

