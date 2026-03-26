"""
Przykłady użycia API Cognitive Layer Architecture.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cla.core import CognitiveLayer


def example_1_basic_usage():
    """Podstawowe użycie - synteza dwóch konceptów."""
    
    print("\n" + "="*70)
    print("PRZYKŁAD 1: Podstawowe użycie")
    print("="*70 + "\n")
    
    # Stwórz system
    cla = CognitiveLayer(identity="My AI Assistant")
    
    # Zdefiniuj koncepty
    concepts = [
        {
            'name': 'FAST',
            'embedding': np.array([1.0, 0.0, 0.0, 0.0]),
            'activation': 0.8,
            'duality_category': 'cognitive',
            'properties': {'speed': 'high', 'accuracy': 'low'}
        },
        {
            'name': 'SLOW',
            'embedding': np.array([-1.0, 0.0, 0.0, 0.0]),
            'activation': 0.8,
            'duality_category': 'cognitive',
            'properties': {'speed': 'low', 'accuracy': 'high'}
        }
    ]
    
    # Przetwórz
    result = cla.process(concepts, context="Need to balance speed and accuracy")
    
    # Wyświetl wynik
    if result['status'] == 'success':
        print(f"✓ Synteza: {result['synthesis']['new_concept']}")
        print(f"✓ Reasoning: {result['synthesis']['reasoning']}")
        print(f"✓ Pewność: {result['synthesis']['confidence']:.2f}")


def example_2_introspection():
    """Introspection - system odpowiada na pytania o siebie."""
    
    print("\n" + "="*70)
    print("PRZYKŁAD 2: Introspection API")
    print("="*70 + "\n")
    
    cla = CognitiveLayer(identity="Self-Aware AI")
    
    # Dodaj trochę wiedzy
    concepts = [
        {
            'name': 'PYTHON',
            'embedding': np.array([1.0, 0.5, 0.0, 0.0]),
            'activation': 0.9,
            'duality_category': 'cognitive',
            'properties': {'type': 'programming_language'}
        }
    ]
    
    cla.process(concepts, context="Learning about Python")
    
    # Zapytaj system o siebie
    print("Q: Kim jesteś?")
    print(f"A: {cla.awareness.introspect('who_am_i')}\n")
    
    print("Q: Co wiesz?")
    print(f"A: {cla.awareness.introspect('what_do_i_know')}\n")
    
    print("Q: Czego nie wiesz?")
    print(f"A: {cla.awareness.introspect('what_dont_i_know')}\n")
    
    print("Q: Jak się czujesz?")
    print(f"A: {cla.awareness.introspect('how_do_i_feel')}\n")


def example_3_feedback_loop():
    """Feedback loop - system uczy się z feedbacku."""
    
    print("\n" + "="*70)
    print("PRZYKŁAD 3: Feedback Loop")
    print("="*70 + "\n")
    
    cla = CognitiveLayer(identity="Learning System")
    
    # Pierwsza decyzja
    concepts = [
        {
            'name': 'RISK',
            'embedding': np.array([1.0, 0.0, 0.0, 0.0]),
            'activation': 0.7,
            'duality_category': 'cognitive',
            'properties': {}
        },
        {
            'name': 'SAFETY',
            'embedding': np.array([-1.0, 0.0, 0.0, 0.0]),
            'activation': 0.7,
            'duality_category': 'cognitive',
            'properties': {}
        }
    ]
    
    result = cla.process(concepts, context="Investment decision")
    
    if result['status'] == 'success':
        decision = result['synthesis']['new_concept']
        print(f"Decyzja: {decision}")
        print(f"Pewność przed feedbackiem: {result['synthesis']['confidence']:.2f}\n")
        
        # Pozytywny feedback
        print("📤 Feedback: Decyzja była dobra!")
        cla.learn_from_feedback({
            'decision': decision,
            'outcome': 'success',
            'context': 'Investment decision',
            'shared_grounding': 0.95
        })
        
        # Sprawdź status
        status = cla.get_status()
        print(f"\n✓ Shared grounding: {status['safety']['shared_grounding']:.2f}")
        print(f"✓ Sukces rate: {status['awareness']['performance']['success_rate']:.0%}")


def example_4_status_monitoring():
    """Monitoring statusu systemu."""
    
    print("\n" + "="*70)
    print("PRZYKŁAD 4: Status Monitoring")
    print("="*70 + "\n")
    
    cla = CognitiveLayer(identity="Monitored System")
    
    # Dodaj kilka konceptów
    for i in range(3):
        concepts = [
            {
                'name': f'CONCEPT_{i}',
                'embedding': np.random.randn(4),
                'activation': 0.5 + i * 0.1,
                'duality_category': 'cognitive',
                'properties': {}
            }
        ]
        cla.process(concepts, context=f"Context {i}")
    
    # Pobierz status
    status = cla.get_status()
    
    print("📊 STATUS SYSTEMU:\n")
    print(f"Tożsamość: {status['identity']}")
    print(f"Interakcje: {status['interactions']}")
    print(f"\nGraf konceptów:")
    print(f"  - Wszystkie koncepty: {status['concept_graph']['total_concepts']}")
    print(f"  - Aktywne koncepty: {status['concept_graph']['active_concepts']}")
    print(f"\nŚwiadomość:")
    print(f"  - Znane koncepty: {status['awareness']['knowledge_stats']['known_concepts']}")
    print(f"  - Decyzje: {status['awareness']['performance']['total_decisions']}")
    print(f"\nBezpieczeństwo:")
    print(f"  - Status: {status['safety']['status']}")
    print(f"  - Shared grounding: {status['safety']['shared_grounding']:.2f}")


def example_5_custom_duality():
    """Własna kategoria dualności."""
    
    print("\n" + "="*70)
    print("PRZYKŁAD 5: Własna Kategoria Dualności")
    print("="*70 + "\n")
    
    cla = CognitiveLayer(identity="Custom System")
    
    # Własna kategoria: AESTHETIC (piękno)
    concepts = [
        {
            'name': 'MINIMALISM',
            'embedding': np.array([1.0, 0.0, 0.5, 0.0]),
            'activation': 0.8,
            'duality_category': 'aesthetic',  # własna kategoria
            'properties': {
                'style': 'simple',
                'elements': 'few',
                'philosophy': 'less is more'
            }
        },
        {
            'name': 'MAXIMALISM',
            'embedding': np.array([-1.0, 0.0, -0.5, 0.0]),
            'activation': 0.8,
            'duality_category': 'aesthetic',
            'properties': {
                'style': 'complex',
                'elements': 'many',
                'philosophy': 'more is more'
            }
        }
    ]
    
    result = cla.process(concepts, context="Design philosophy")
    
    if result['status'] == 'success':
        print(f"✓ Synteza: {result['synthesis']['new_concept']}")
        print(f"✓ Kategoria: {result['duality']['category']}")
        print(f"✓ Reasoning: {result['synthesis']['reasoning']}")


if __name__ == '__main__':
    print("\n" + "🧠 "*20)
    print("  COGNITIVE LAYER ARCHITECTURE - PRZYKŁADY API")
    print("🧠 "*20)
    
    example_1_basic_usage()
    example_2_introspection()
    example_3_feedback_loop()
    example_4_status_monitoring()
    example_5_custom_duality()
    
    print("\n" + "="*70)
    print("  ✅ WSZYSTKIE PRZYKŁADY ZAKOŃCZONE")
    print("="*70 + "\n")

