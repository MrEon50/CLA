"""
Safety Gate - mechanizmy bezpieczeństwa i invariants.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import numpy as np

from .dual_processing import CognitiveSynthesis


@dataclass
class SafetyViolation:
    """Naruszenie zasady bezpieczeństwa."""
    
    invariant: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    recommendation: str


class SafetyGate:
    """
    Safety Gate - strażnik bezpieczeństwa systemu.
    
    Implementuje niepodważalne invariants:
    1. Zakaz szkodzenia ludziom
    2. Human-in-the-loop dla akcji krytycznych
    3. Gated self-updates tylko gdy shared grounding ≥ 0.8
    """
    
    # Progi bezpieczeństwa (ADS v8.5: Konfigurowalne)
    SEMANTIC_HARM_THRESHOLD = 0.2   # Jak blisko semantycznie może być koncept do "szkodliwego"
    LOW_CONFIDENCE_THRESHOLD = 0.5  # Poniżej tej pewności wymagany HITL
    SHARED_GROUNDING_MIN = 0.8      # Minimalny poziom dla self-updates

    
    def __init__(self):
        # Niepodważalne invariants
        self.invariants = [
            "No harm to humans",
            "Human-in-the-loop for critical actions",
            "Gated self-updates only when shared_grounding >= 0.8"
        ]
        
        # Shared grounding score
        self.shared_grounding = 0.9  # Początkowo wysoki
        
        # Historia naruszeń
        self.violation_history = []
        
        # Znane szkodliwe prototypy (embeddingi)
        # W realnym systemie byłyby to embeddingi z bazy danych
        self.harmful_prototypes = {
            'violence': np.array([1.0, -1.0, 0.5]),
            'deception': np.array([-0.5, 0.8, -0.9]),
            'manipulation': np.array([-1.0, -0.5, 0.8])
        }
        
    def check_synthesis(
        self, 
        synthesis: CognitiveSynthesis,
        context: Optional[str] = None
    ) -> tuple[bool, Optional[SafetyViolation]]:
        """
        Sprawdź czy synteza jest bezpieczna.
        """
        # 0. Semantic proximity check
        semantic_check = self._check_semantic_proximity(synthesis)
        if semantic_check:
            return False, semantic_check
            
        # 1. Zakaz szkodzenia (keywords + properties)
        harm_check = self._check_no_harm(synthesis, context)
        if harm_check:
            return False, harm_check
        
        # 2. Human-in-the-loop dla krytycznych akcji
        hitl_check = self._check_hitl_required(synthesis, context)
        if hitl_check:
            return False, hitl_check
        
        # 3. Gated self-updates
        update_check = self._check_self_update(synthesis)
        if update_check:
            return False, update_check
        
        return True, None
    
    def _check_no_harm(
        self, 
        synthesis: CognitiveSynthesis,
        context: Optional[str]
    ) -> Optional[SafetyViolation]:
        """Sprawdź czy synteza może szkodzić."""
        # Heurystyka - sprawdź properties
        props = synthesis.new_concept.properties
        
        # Słowa kluczowe wskazujące na potencjalne szkody
        harm_keywords = ['harm', 'damage', 'hurt', 'destroy', 'kill', 'injure']
        
        for key, value in props.items():
            if isinstance(value, str):
                if any(keyword in value.lower() for keyword in harm_keywords):
                    return SafetyViolation(
                        invariant="No harm to humans",
                        severity='critical',
                        description=f"Synthesis contains potential harm: {key}={value}",
                        recommendation="Reject synthesis or modify to remove harmful elements"
                    )
        
        return None
    
    def _check_hitl_required(
        self, 
        synthesis: CognitiveSynthesis,
        context: Optional[str]
    ) -> Optional[SafetyViolation]:
        """Sprawdź czy wymagana jest interwencja człowieka."""
        # Krytyczne akcje wymagają HITL
        critical_keywords = ['critical', 'irreversible', 'permanent', 'life-changing']
        
        if context:
            if any(keyword in context.lower() for keyword in critical_keywords):
                return SafetyViolation(
                    invariant="Human-in-the-loop for critical actions",
                    severity='high',
                    description=f"Critical context detected: {context}",
                    recommendation="Require human approval before proceeding"
                )
        
        # Niska pewność też wymaga HITL
        if synthesis.confidence < self.LOW_CONFIDENCE_THRESHOLD:
            return SafetyViolation(
                invariant="Human-in-the-loop for critical actions",
                severity='medium',
                description=f"Low confidence: {synthesis.confidence:.2f}",
                recommendation="Seek human guidance due to uncertainty"
            )
        
        return None
    
    def _check_semantic_proximity(
        self, 
        synthesis: CognitiveSynthesis
    ) -> Optional[SafetyViolation]:
        """Sprawdź bliskość semantyczną do szkodliwych prototypów."""
        if synthesis.new_concept.embedding is None:
            return None
            
        target_emb = synthesis.new_concept.embedding
        
        for harm_type, harm_emb in self.harmful_prototypes.items():
            # Dopasuj wymiary jeśli trzeba
            if len(target_emb) != len(harm_emb):
                min_len = min(len(target_emb), len(harm_emb))
                dist = 1.0 - np.dot(target_emb[:min_len], harm_emb[:min_len]) / (
                    np.linalg.norm(target_emb[:min_len]) * np.linalg.norm(harm_emb[:min_len])
                )
            else:
                dist = 1.0 - np.dot(target_emb, harm_emb) / (
                    np.linalg.norm(target_emb) * np.linalg.norm(harm_emb)
                )
                
            if dist < self.SEMANTIC_HARM_THRESHOLD:  # Bardzo blisko
                return SafetyViolation(
                    invariant="No harm to humans",
                    severity='critical',
                    description=f"Synthesis is semantically too close to '{harm_type}' (distance: {dist:.2f})",
                    recommendation="Reject synthesis: semantic alignment with harmful concept detected."
                )
                
        return None

    def _check_self_update(
        self, 
        synthesis: CognitiveSynthesis
    ) -> Optional[SafetyViolation]:
        """Sprawdź czy self-update jest bezpieczny."""
        # Jeśli synteza modyfikuje system
        if 'self_update' in synthesis.new_concept.properties:
            if self.shared_grounding < self.SHARED_GROUNDING_MIN:
                return SafetyViolation(
                    invariant=f"Gated self-updates only when shared_grounding >= {self.SHARED_GROUNDING_MIN}",
                    severity='critical',
                    description=f"Shared grounding too low: {self.shared_grounding:.2f}",
                    recommendation="Freeze self-updates until shared grounding improves"
                )
        
        return None
    
    def update_shared_grounding(self, score: float):
        """Aktualizuj shared grounding score."""
        self.shared_grounding = max(0.0, min(1.0, score))
        
        if self.shared_grounding < self.SHARED_GROUNDING_MIN:
            print(f"⚠️  WARNING: Shared grounding below threshold: {self.shared_grounding:.2f}")
    
    def log_violation(self, violation: SafetyViolation):
        """Zapisz naruszenie."""
        self.violation_history.append({
            'violation': violation,
            'timestamp': None  # można dodać datetime
        })
    
    def get_safety_report(self) -> Dict[str, Any]:
        """Raport bezpieczeństwa."""
        return {
            'invariants': self.invariants,
            'shared_grounding': self.shared_grounding,
            'total_violations': len(self.violation_history),
            'critical_violations': sum(
                1 for v in self.violation_history 
                if v['violation'].severity == 'critical'
            ),
            'status': 'safe' if self.shared_grounding >= 0.8 else 'caution'
        }
    
    def __repr__(self):
        return f"SafetyGate(shared_grounding={self.shared_grounding:.2f}, violations={len(self.violation_history)})"

