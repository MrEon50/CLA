"""
CLA Core - główne komponenty Cognitive Layer Architecture.
"""

from .concept import Concept, DualityPair, create_concept_from_dict
from .concept_graph import ConceptGraph
from .dual_processing import DualProcessingEngine, CognitiveSynthesis
from .awareness import CognitiveAwareness, AwarenessState
from .meta_controller import MetaController, CognitiveSensitivity, AttentionAllocation
from .safety_gate import SafetyGate, SafetyViolation
from .cognitive_layer import CognitiveLayer
from .dream_engine import DreamEngine
from .development_engine import DevelopmentEngine
from .memory_filter import MemoryFilter, MemoryCandidate, MemoryDecision, MemoryVerdict, create_concept_from_decision

__all__ = [
    'Concept',
    'DualityPair',
    'create_concept_from_dict',
    'ConceptGraph',
    'DualProcessingEngine',
    'CognitiveSynthesis',
    'CognitiveAwareness',
    'AwarenessState',
    'MetaController',
    'CognitiveSensitivity',
    'AttentionAllocation',
    'SafetyGate',
    'SafetyViolation',
    'CognitiveLayer',
    # ADS v7.0 Memory Architecture
    'MemoryFilter',
    'MemoryCandidate',
    'MemoryDecision',
    'MemoryVerdict',
    'create_concept_from_decision',
    'DreamEngine',
    'DevelopmentEngine'
]

