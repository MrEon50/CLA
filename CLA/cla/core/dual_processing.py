"""
Dual Processing Engine - serce mechanizmu tarcia poznawczego.
Wykrywa dualności, mierzy napięcie, tworzy syntezę.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from .concept import Concept, DualityPair
from .concept_graph import ConceptGraph


@dataclass
class CognitiveSynthesis:
    """
    Wynik syntezy poznawczej - nowy koncept emergentny.
    """
    
    new_concept: Concept
    source_duality: DualityPair
    synthesis_type: str  # 'integration', 'transcendence', 'balance'
    
    # Wyjaśnienie
    reasoning: str
    confidence: float
    
    # Właściwości syntezy
    common_features: List[str]
    integrated_differences: Dict[str, Any]


class DualProcessingEngine:
    """
    Mechanizm przetwarzania dualnego - tworzy syntezę z napięć poznawczych.
    
    Proces:
    1. Wykryj dualności w aktywnych konceptach
    2. Zmierz tarcie poznawcze
    3. Wybierz najważniejsze napięcie
    4. Stwórz syntezę (nowy koncept emergentny)
    """
    
    def __init__(self, concept_graph: ConceptGraph):
        self.concept_graph = concept_graph
        
        # Predefiniowane dualności (można rozszerzać)
        self.known_dualities = {
            'emotional': [
                ('LOVE', 'HATE'),
                ('FEAR', 'CALM'),
                ('SADNESS', 'JOY'),
                ('ANGER', 'PEACE')
            ],
            'cognitive': [
                ('ANALYTICAL', 'INTUITIVE'),
                ('GLOBAL', 'LOCAL'),
                ('PROBABILISTIC', 'DETERMINISTIC'),
                ('FAST', 'SLOW'),
                ('SHALLOW', 'DEEP')
            ],
            'moral': [
                ('UNIVERSAL', 'CONTEXTUAL'),
                ('ALTRUISTIC', 'EGOISTIC'),
                ('TRUTH', 'LOYALTY'),
                ('JUSTICE', 'MERCY')
            ]
        }
    
    def process(
        self, 
        active_concepts: List[Concept],
        context: Optional[str] = None
    ) -> Optional[CognitiveSynthesis]:
        """
        Główna metoda przetwarzania (ADS v5.6: Beauty-Driven).
        """
        # 1. Znajdź dualności
        dualities = self.concept_graph.find_dualities(active_concepts)
        
        if not dualities:
            return None
        
        # 2. Wybierz najsilniejsze tarcie
        # Ale przefiltruj przez Beauty Index (B = Depth / complexity)
        # complexity = friction + entropy (ilość aktywnych pojęć)
        best_synthesis = None
        max_beauty = -1.0
        
        for duality in dualities:
            if duality.friction < 0.3: continue
            
            # Oblicz potencjalny Beauty Index dla tej pary
            depth = (duality.pole_a.depth + duality.pole_b.depth) / 2
            complexity = duality.friction + (len(active_concepts) * 0.05) + 0.1
            beauty = depth / complexity
            
            if beauty > max_beauty:
                max_beauty = beauty
                # 4. Stwórz syntezę czasową, by sprawdzić jej parametry
                candidate = self.synthesize(duality, context)
                if candidate:
                    best_synthesis = candidate
        
        return best_synthesis
    
    def synthesize(
        self, 
        duality: DualityPair, 
        context: Optional[str] = None
    ) -> CognitiveSynthesis:
        """
        Stwórz syntezę z dualności.
        
        Proces:
        1. Znajdź wspólne cechy (invariants)
        2. Znajdź różnice (variants)
        3. Integruj na wyższym poziomie abstrakcji
        4. Stwórz nowy koncept emergentny
        """
        pole_a = duality.pole_a
        pole_b = duality.pole_b
        
        # 1. Wspólne cechy
        common_features = self._find_common_features(pole_a, pole_b)
        
        # 2. Różnice
        differences = self._find_differences(pole_a, pole_b)
        
        # 3. Typ syntezy zależy od kategorii
        if duality.category == 'emotional':
            synthesis = self._synthesize_emotional(pole_a, pole_b, common_features, differences, context)
        elif duality.category == 'cognitive':
            synthesis = self._synthesize_cognitive(pole_a, pole_b, common_features, differences, context)
        elif duality.category == 'moral':
            synthesis = self._synthesize_moral(pole_a, pole_b, common_features, differences, context)
        else:
            synthesis = self._synthesize_generic(pole_a, pole_b, common_features, differences, context)
        
        return synthesis
    
    def _find_common_features(self, concept_a: Concept, concept_b: Concept) -> List[str]:
        """Znajdź wspólne cechy między konceptami."""
        common = []
        
        # Wspólne properties
        keys_a = set(concept_a.properties.keys())
        keys_b = set(concept_b.properties.keys())
        common_keys = keys_a & keys_b
        
        for key in common_keys:
            if concept_a.properties[key] == concept_b.properties[key]:
                common.append(f"{key}={concept_a.properties[key]}")
        
        return common
    
    def _find_differences(self, concept_a: Concept, concept_b: Concept) -> Dict[str, Any]:
        """Znajdź różnice między konceptami."""
        differences = {
            concept_a.name: {},
            concept_b.name: {}
        }
        
        # Różne properties
        all_keys = set(concept_a.properties.keys()) | set(concept_b.properties.keys())
        
        for key in all_keys:
            val_a = concept_a.properties.get(key)
            val_b = concept_b.properties.get(key)
            
            if val_a != val_b:
                differences[concept_a.name][key] = val_a
                differences[concept_b.name][key] = val_b
        
        return differences
    
    def _synthesize_cognitive(
        self, 
        pole_a: Concept, 
        pole_b: Concept,
        common: List[str],
        differences: Dict[str, Any],
        context: Optional[str]
    ) -> CognitiveSynthesis:
        """Synteza poznawcza - np. GLOBAL ↔ LOCAL."""
        
        # Przykład: GLOBAL ↔ LOCAL → HIERARCHICAL_REASONING
        if pole_a.name == 'GLOBAL' and pole_b.name == 'LOCAL':
            new_concept = Concept(
                name='HIERARCHICAL_REASONING',
                properties={
                    'mechanism': 'multi_scale_analysis',
                    'strategy': [
                        'Start with global overview',
                        'Identify critical local areas',
                        'Zoom into details',
                        'Validate against global context',
                        'Iterate between scales'
                    ],
                    'integrates': [pole_a.name, pole_b.name],
                    'type': 'cognitive_synthesis'
                },
                weight=0.7,
                is_emergent=True,
                parent_concepts=[pole_a.concept_id, pole_b.concept_id],
                emergence_context=context,
                duality_category='cognitive'
            )
            
            reasoning = (
                f"Detected tension between {pole_a.name} (activation={pole_a.activation:.2f}) "
                f"and {pole_b.name} (activation={pole_b.activation:.2f}). "
                f"Created HIERARCHICAL_REASONING to integrate both perspectives: "
                f"use global view to guide, local view to validate."
            )
        
        # ANALYTICAL ↔ INTUITIVE → INTEGRATED_THINKING
        elif pole_a.name == 'ANALYTICAL' and pole_b.name == 'INTUITIVE':
            new_concept = Concept(
                name='INTEGRATED_THINKING',
                properties={
                    'mechanism': 'dual_mode_cognition',
                    'strategy': [
                        'Use intuition for hypothesis generation',
                        'Use analysis for validation',
                        'Iterate between modes',
                        'Trust intuition when time-constrained',
                        'Trust analysis when stakes are high'
                    ],
                    'integrates': [pole_a.name, pole_b.name],
                    'type': 'cognitive_synthesis'
                },
                weight=0.7,
                is_emergent=True,
                parent_concepts=[pole_a.concept_id, pole_b.concept_id],
                emergence_context=context,
                duality_category='cognitive'
            )
            
            reasoning = (
                f"Synthesized {pole_a.name} and {pole_b.name} into INTEGRATED_THINKING: "
                f"use both modes complementarily based on context."
            )
        
        else:
            # Generic cognitive synthesis
            new_concept = self._create_generic_synthesis(pole_a, pole_b, 'cognitive', context)
            reasoning = f"Generic cognitive synthesis of {pole_a.name} and {pole_b.name}"
        
        # Oblicz embedding jako średnia ważona
        if pole_a.embedding is not None and pole_b.embedding is not None:
            new_concept.embedding = (pole_a.embedding + pole_b.embedding) / 2
        
        return CognitiveSynthesis(
            new_concept=new_concept,
            source_duality=DualityPair(pole_a, pole_b, 'cognitive'),
            synthesis_type='integration',
            reasoning=reasoning,
            confidence=0.7,
            common_features=common,
            integrated_differences=differences
        )

    def _synthesize_emotional(
        self,
        pole_a: Concept,
        pole_b: Concept,
        common: List[str],
        differences: Dict[str, Any],
        context: Optional[str]
    ) -> CognitiveSynthesis:
        """Synteza emocjonalna - np. LOVE ↔ HATE."""

        # LOVE ↔ HATE → AMBIVALENCE
        if pole_a.name == 'LOVE' and pole_b.name == 'HATE':
            new_concept = Concept(
                name='AMBIVALENCE',
                properties={
                    'valence': 0.0,  # Neutralizacja
                    'arousal': 1.0,  # Wysokie pobudzenie
                    'complexity': 'high',
                    'description': 'Simultaneous conflicting emotions toward same target',
                    'coping_strategies': [
                        'Acknowledge both feelings',
                        'Understand context of each',
                        'Accept complexity',
                        'Avoid forced resolution'
                    ],
                    'integrates': [pole_a.name, pole_b.name],
                    'type': 'emotional_synthesis'
                },
                weight=0.8,
                is_emergent=True,
                parent_concepts=[pole_a.concept_id, pole_b.concept_id],
                emergence_context=context,
                duality_category='emotional'
            )

            reasoning = (
                f"Detected simultaneous {pole_a.name} and {pole_b.name} toward same target. "
                f"This is AMBIVALENCE - a complex emotional state that integrates both. "
                f"Not a compromise, but a higher-order emotional understanding."
            )

        # FEAR ↔ CALM → COURAGE
        elif pole_a.name == 'FEAR' and pole_b.name == 'CALM':
            new_concept = Concept(
                name='COURAGE',
                properties={
                    'valence': 0.3,
                    'arousal': 0.6,
                    'description': 'Acting despite fear, not absence of fear',
                    'mechanism': 'Acknowledge fear but choose calm action',
                    'integrates': [pole_a.name, pole_b.name],
                    'type': 'emotional_synthesis'
                },
                weight=0.8,
                is_emergent=True,
                parent_concepts=[pole_a.concept_id, pole_b.concept_id],
                emergence_context=context,
                duality_category='emotional'
            )

            reasoning = (
                f"COURAGE emerges from tension between {pole_a.name} and {pole_b.name}. "
                f"It's not absence of fear, but calm action despite fear."
            )

        else:
            new_concept = self._create_generic_synthesis(pole_a, pole_b, 'emotional', context)
            reasoning = f"Generic emotional synthesis of {pole_a.name} and {pole_b.name}"

        if pole_a.embedding is not None and pole_b.embedding is not None:
            new_concept.embedding = (pole_a.embedding + pole_b.embedding) / 2

        return CognitiveSynthesis(
            new_concept=new_concept,
            source_duality=DualityPair(pole_a, pole_b, 'emotional'),
            synthesis_type='transcendence',
            reasoning=reasoning,
            confidence=0.75,
            common_features=common,
            integrated_differences=differences
        )

    def _synthesize_moral(
        self,
        pole_a: Concept,
        pole_b: Concept,
        common: List[str],
        differences: Dict[str, Any],
        context: Optional[str]
    ) -> CognitiveSynthesis:
        """Synteza moralna - np. UNIVERSAL ↔ CONTEXTUAL."""

        # UNIVERSAL ↔ CONTEXTUAL → CONTEXTUAL_ETHICS
        if pole_a.name == 'UNIVERSAL' and pole_b.name == 'CONTEXTUAL':
            new_concept = Concept(
                name='CONTEXTUAL_ETHICS',
                properties={
                    'principle': 'Universal values applied with contextual wisdom',
                    'mechanism': [
                        'Start with universal principles',
                        'Examine specific context',
                        'Weigh competing values',
                        'Make situated judgment',
                        'Remain accountable to principles'
                    ],
                    'integrates': [pole_a.name, pole_b.name],
                    'type': 'moral_synthesis'
                },
                weight=0.85,
                is_emergent=True,
                parent_concepts=[pole_a.concept_id, pole_b.concept_id],
                emergence_context=context,
                duality_category='moral'
            )

            reasoning = (
                f"Synthesized {pole_a.name} and {pole_b.name} ethics into CONTEXTUAL_ETHICS: "
                f"universal principles guide, but context determines application."
            )

        # ALTRUISTIC ↔ EGOISTIC → ENLIGHTENED_SELF_INTEREST
        elif pole_a.name == 'ALTRUISTIC' and pole_b.name == 'EGOISTIC':
            new_concept = Concept(
                name='ENLIGHTENED_SELF_INTEREST',
                properties={
                    'principle': 'Helping others serves long-term self-interest',
                    'mechanisms': [
                        'Build social capital',
                        'Create reciprocity networks',
                        'Gain reputation',
                        'Psychological rewards',
                        'Sustainable communities'
                    ],
                    'integrates': [pole_a.name, pole_b.name],
                    'type': 'moral_synthesis'
                },
                weight=0.8,
                is_emergent=True,
                parent_concepts=[pole_a.concept_id, pole_b.concept_id],
                emergence_context=context,
                duality_category='moral'
            )

            reasoning = (
                f"Resolved tension between {pole_a.name} and {pole_b.name} through "
                f"ENLIGHTENED_SELF_INTEREST: altruism and self-interest align in long term."
            )

        else:
            new_concept = self._create_generic_synthesis(pole_a, pole_b, 'moral', context)
            reasoning = f"Generic moral synthesis of {pole_a.name} and {pole_b.name}"

        if pole_a.embedding is not None and pole_b.embedding is not None:
            new_concept.embedding = (pole_a.embedding + pole_b.embedding) / 2

        return CognitiveSynthesis(
            new_concept=new_concept,
            source_duality=DualityPair(pole_a, pole_b, 'moral'),
            synthesis_type='integration',
            reasoning=reasoning,
            confidence=0.8,
            common_features=common,
            integrated_differences=differences
        )

    def _synthesize_generic(
        self,
        pole_a: Concept,
        pole_b: Concept,
        common: List[str],
        differences: Dict[str, Any],
        context: Optional[str]
    ) -> CognitiveSynthesis:
        """Dynamiczna synteza dla nieznanych dualności."""
        
        # 1. Wygeneruj nazwę i właściwości
        name = self._generate_synthesis_name(pole_a, pole_b)
        merged_props = self._merge_properties(pole_a, pole_b)
        
        # 2. Stwórz nowy koncept
        new_concept = Concept(
            name=name,
            properties={
                **merged_props,
                'integrates': [pole_a.name, pole_b.name],
                'type': 'dynamic_synthesis',
                'emergence_reason': 'unrecognized_duality'
            },
            weight=(pole_a.weight + pole_b.weight) / 2,
            is_emergent=True,
            parent_concepts=[pole_a.concept_id, pole_b.concept_id],
            emergence_context=context,
            duality_category='generic'
        )
        
        if pole_a.embedding is not None and pole_b.embedding is not None:
            new_concept.embedding = (pole_a.embedding + pole_b.embedding) / 2
            
        reasoning = (
            f"Dynamic synthesis created {name} from {pole_a.name} and {pole_b.name}. "
            f"Fused {len(merged_props)} properties. "
            f"This represents a novel balance between the two poles."
        )

        return CognitiveSynthesis(
            new_concept=new_concept,
            source_duality=DualityPair(pole_a, pole_b, 'generic'),
            synthesis_type='balance',
            reasoning=reasoning,
            confidence=0.5,
            common_features=common,
            integrated_differences=differences
        )

    def _generate_synthesis_name(self, pole_a: Concept, pole_b: Concept) -> str:
        """Generuj czytelną nazwę dla nowej syntezy."""
        # Prosta logika: Prefixy i połączenia
        # Np. LOGIC + EMOTION -> LOGIC_EMOTION_BALANCE
        return f"{pole_a.name}_{pole_b.name}_INTEGRATION"

    def _merge_properties(self, pole_a: Concept, pole_b: Concept) -> Dict[str, Any]:
        """Semantyczne łączenie właściwości dwóch konceptów."""
        merged = {}
        
        # Wszystkie klucze
        all_keys = set(pole_a.properties.keys()) | set(pole_b.properties.keys())
        
        for key in all_keys:
            val_a = pole_a.properties.get(key)
            val_b = pole_b.properties.get(key)
            
            if val_a is not None and val_b is not None:
                if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                    # Średnia dla wartości numerycznych
                    merged[f"balanced_{key}"] = (val_a + val_b) / 2
                elif val_a == val_b:
                    # To samo - zachowaj
                    merged[key] = val_a
                else:
                    # Różne - stwórz spektrum
                    merged[f"spectrum_{key}"] = f"{val_a} <-> {val_b}"
            elif val_a is not None:
                merged[key] = val_a
            else:
                merged[key] = val_b
                
        return merged

    def _create_generic_synthesis(
        self,
        pole_a: Concept,
        pole_b: Concept,
        category: str,
        context: Optional[str]
    ) -> Concept:
        """Helper do tworzenia generycznej syntezy (do użytku wewnętrznego)."""
        name = self._generate_synthesis_name(pole_a, pole_b)
        merged_props = self._merge_properties(pole_a, pole_b)

        return Concept(
            name=name,
            properties={
                **merged_props,
                'integrates': [pole_a.name, pole_b.name],
                'type': f'{category}_synthesis',
                'description': f'Synthesis of {pole_a.name} and {pole_b.name}'
            },
            weight=(pole_a.weight + pole_b.weight) / 2,
            is_emergent=True,
            parent_concepts=[pole_a.concept_id, pole_b.concept_id],
            emergence_context=context,
            duality_category=category
        )

