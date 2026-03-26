"""
Demonstracja działania Cognitive Layer Architecture.

Pokazuje:
1. Dualność poznawczą (GLOBAL <-> LOCAL)
2. Dualność emocjonalną (LOVE <-> HATE)
3. Dualność moralną (UNIVERSAL <-> CONTEXTUAL)
4. Pełny cykl poznawczy z świadomością
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cla.core import CognitiveLayer


def print_separator(title):
    """Helper do wyświetlania separatorów."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def demo_cognitive_duality():
    """Demonstracja dualności poznawczej: GLOBAL <-> LOCAL."""
    
    print_separator("DEMO 1: Dualność Poznawcza (GLOBAL <-> LOCAL)")
    
    cla = CognitiveLayer(identity="CLA Demo System")
    
    # Scenariusz: Analiza problemu - potrzeba zarówno globalnego jak i lokalnego widoku
    input_concepts = [
        {
            'name': 'GLOBAL',
            'embedding': np.array([1.0, 0.0, 0.0, 0.5]),
            'activation': 0.9,
            'duality_category': 'cognitive',
            'properties': {
                'scope': 'whole_system',
                'detail': 'low',
                'speed': 'fast',
                'description': 'See the forest'
            }
        },
        {
            'name': 'LOCAL',
            'embedding': np.array([-1.0, 0.0, 0.0, -0.5]),
            'activation': 0.9,
            'duality_category': 'cognitive',
            'properties': {
                'scope': 'single_element',
                'detail': 'high',
                'speed': 'slow',
                'description': 'See the trees'
            }
        }
    ]
    
    context = "Analyzing complex system - need both overview and details"
    
    result = cla.process(input_concepts, context)
    
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        print(f"\n[SYNTHESIS] SYNTEZA POZNAWCZA:")
        print(f"  Nowy koncept: {result['synthesis']['new_concept']}")
        print(f"  Typ: {result['synthesis']['type']}")
        print(f"  Pewność: {result['synthesis']['confidence']:.2f}")
        print(f"\n  Reasoning:")
        print(f"  {result['synthesis']['reasoning']}")
        
        print(f"\n[DUALITY] DUALNOŚĆ:")
        print(f"  {result['duality']['pole_a']} <-> {result['duality']['pole_b']}")
        print(f"  Kategoria: {result['duality']['category']}")
        print(f"  Tarcie: {result['duality']['friction']:.2f}")
        
        print(f"\n[ATTENTION] UWAGA:")
        print(f"  Tryb: {result['attention']['mode']}")
        print(f"  Głębokość: {result['attention']['depth']}")
        print(f"  Pilność: {result['attention']['urgency']:.2f}")
        
        print(f"\n[AWARENESS] ŚWIADOMOŚĆ:")
        awareness = result['awareness']
        print(f"  Tożsamość: {awareness['identity']}")
        print(f"  Ton emocjonalny: {awareness['current_state']['emotional_tone']:.2f}")
        print(f"  Pewność: {awareness['current_state']['certainty']:.2f}")
        print(f"  Obciążenie poznawcze: {awareness['current_state']['cognitive_load']:.2f}")


def demo_emotional_duality():
    """Demonstracja dualności emocjonalnej: LOVE <-> HATE."""
    
    print_separator("DEMO 2: Dualność Emocjonalna (LOVE <-> HATE)")
    
    cla = CognitiveLayer(identity="Emotional Intelligence System")
    
    # Scenariusz: Ambiwałencja - kocham kogoś ale jestem zły na to co zrobił
    input_concepts = [
        {
            'name': 'LOVE',
            'embedding': np.array([1.0, 1.0, 0.0, 0.8]),
            'activation': 0.85,
            'duality_category': 'emotional',
            'properties': {
                'valence': 1.0,
                'arousal': 0.8,
                'approach': True,
                'description': 'Deep affection and care'
            }
        },
        {
            'name': 'HATE',
            'embedding': np.array([-1.0, -1.0, 0.0, -0.8]),
            'activation': 0.75,
            'duality_category': 'emotional',
            'properties': {
                'valence': -1.0,
                'arousal': 0.8,
                'approach': False,
                'description': 'Intense negative emotion'
            }
        }
    ]
    
    context = "Conflicting emotions toward same person - love them but angry at their actions"
    
    result = cla.process(input_concepts, context)
    
    if result['status'] == 'success':
        print(f"[SYNTHESIS] SYNTEZA EMOCJONALNA:")
        print(f"  Nowy koncept: {result['synthesis']['new_concept']}")
        print(f"  Typ: {result['synthesis']['type']}")
        
        print(f"\n  Właściwości:")
        for key, value in result['synthesis']['properties'].items():
            if key not in ['integrates', 'type', 'coping_strategies']:
                print(f"    {key}: {value}")
        
        print(f"\n  Strategie radzenia sobie:")
        for strategy in result['synthesis']['properties'].get('coping_strategies', []):
            print(f"    * {strategy}")
        
        print(f"\n  Reasoning:")
        print(f"  {result['synthesis']['reasoning']}")


def demo_moral_duality():
    """Demonstracja dualności moralnej: UNIVERSAL <-> CONTEXTUAL."""
    
    print_separator("DEMO 3: Dualność Moralna (UNIVERSAL <-> CONTEXTUAL)")
    
    cla = CognitiveLayer(identity="Ethical Reasoning System")
    
    # Scenariusz: Dylemat etyczny - uniwersalne zasady vs kontekst sytuacyjny
    input_concepts = [
        {
            'name': 'UNIVERSAL',
            'embedding': np.array([0.0, 1.0, 1.0, 0.0]),
            'activation': 0.8,
            'duality_category': 'moral',
            'properties': {
                'type': 'rule-based',
                'scope': 'all_situations',
                'description': 'Universal moral principles'
            }
        },
        {
            'name': 'CONTEXTUAL',
            'embedding': np.array([0.0, -1.0, -1.0, 0.0]),
            'activation': 0.8,
            'duality_category': 'moral',
            'properties': {
                'type': 'situation-based',
                'scope': 'specific_context',
                'description': 'Context-dependent ethics'
            }
        }
    ]
    
    context = "Ethical dilemma: Should I lie to protect a friend? Truth vs Loyalty"
    
    result = cla.process(input_concepts, context)
    
    if result['status'] == 'success':
        print(f"[SYNTHESIS] SYNTEZA MORALNA:")
        print(f"  Nowy koncept: {result['synthesis']['new_concept']}")
        
        print(f"\n  Zasada:")
        print(f"  {result['synthesis']['properties']['principle']}")
        
        print(f"\n  Mechanizm:")
        for step in result['synthesis']['properties']['mechanism']:
            print(f"    {step}")
        
        print(f"\n  Reasoning:")
        print(f"  {result['synthesis']['reasoning']}")


def demo_full_cycle():
    """Demonstracja pełnego cyklu z feedbackiem."""
    
    print_separator("DEMO 4: Pełny Cykl Poznawczy z Feedbackiem")
    
    cla = CognitiveLayer(identity="Learning System")
    
    # Pierwsza interakcja
    print("[IN] Interakcja 1: ANALYTICAL <-> INTUITIVE")
    
    input_concepts = [
        {
            'name': 'ANALYTICAL',
            'embedding': np.array([1.0, 0.0, 1.0, 0.0]),
            'activation': 0.9,
            'duality_category': 'cognitive',
            'properties': {'mode': 'logical', 'speed': 'slow'}
        },
        {
            'name': 'INTUITIVE',
            'embedding': np.array([-1.0, 0.0, -1.0, 0.0]),
            'activation': 0.85,
            'duality_category': 'cognitive',
            'properties': {'mode': 'gut_feeling', 'speed': 'fast'}
        }
    ]
    
    result1 = cla.process(input_concepts, "Decision under time pressure")
    
    if result1['status'] == 'success':
        print(f"  [OK] Synteza: {result1['synthesis']['new_concept']}")
        print(f"  [OK] Pewność: {result1['synthesis']['confidence']:.2f}")
    
    # Feedback pozytywny
    print("\n[OUT] Feedback: Decyzja była dobra!")
    cla.learn_from_feedback({
        'decision': result1.get('synthesis', {}).get('new_concept'),
        'outcome': 'success',
        'context': 'Decision under time pressure',
        'shared_grounding': 0.9
    })
    
    # Status systemu
    print("\n[STATS] Status systemu:")
    status = cla.get_status()
    print(f"  Koncepty w grafie: {status['concept_graph']['total_concepts']}")
    print(f"  Aktywne koncepty: {status['concept_graph']['active_concepts']}")
    print(f"  Interakcje: {status['interactions']}")
    print(f"  Shared grounding: {status['safety']['shared_grounding']:.2f}")
    print(f"  Status bezpieczeństwa: {status['safety']['status']}")
    
    print("\n  Świadomość:")
    print(f"    Znane koncepty: {status['awareness']['knowledge_stats']['known_concepts']}")
    print(f"    Decyzje: {status['awareness']['performance']['total_decisions']}")
    print(f"    Sukces: {status['awareness']['performance']['success_rate']:.0%}")


if __name__ == '__main__':
    print("\n" + "X "*20)
    print("  COGNITIVE LAYER ARCHITECTURE - DEMONSTRACJA")
    print("X "*20)
    
    demo_cognitive_duality()
    demo_emotional_duality()
    demo_moral_duality()
    demo_full_cycle()
    
    print("\n" + "="*70)
    print("  [EXIT] DEMONSTRACJA ZAKOŃCZONA")
    print("="*70 + "\n")

