
╔══════════════════════════════════════════════════════════════════════════════╗
║                         INSTRUKCJE ROZBUDOWY VPRM                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│                      1. DODANIE CLIP EMBEDDINGS                              │
└──────────────────────────────────────────────────────────────────────────────┘

DLACZEGO: CLIP pozwala na semantyczne rozumienie obrazów

KOD:
----
# Instalacja: pip install sentence-transformers

class CLIPFeatureExtractor:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer('clip-ViT-B-32')
    
    def encode_image(self, image: np.ndarray) -> np.ndarray:
        from PIL import Image
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        embedding = self.model.encode(pil_image)
        return embedding

# Integracja w VPRMSystem:
# W __init__:
self.clip_extractor = CLIPFeatureExtractor()

# W match_pattern():
if rule.complexity_level in ["COMPLEX", "COMPOSITE"]:
    embedding = self.clip_extractor.encode_image(image)
    # Porównaj z rule.visual_embedding używając cosine similarity

┌──────────────────────────────────────────────────────────────────────────────┐
│                      2. DODANIE YOLO OBJECT DETECTION                        │
└──────────────────────────────────────────────────────────────────────────────┘

DLACZEGO: Detekcja konkretnych obiektów (przyciski, ikony, etc.)

KOD:
----
# Instalacja: pip install ultralytics

class YOLODetector:
    def __init__(self):
        from ultralytics import YOLO
        self.model = YOLO('yolov8n.pt')  # Nano model (szybki)
    
    def detect_objects(self, image: np.ndarray) -> List[Dict]:
        results = self.model(image, verbose=False)
        detections = []
        
        for result in results:
            for box in result.boxes:
                detections.append({
                    "class": result.names[int(box.cls)],
                    "confidence": float(box.conf),
                    "bbox": box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                })
        
        return detections

# Użycie w FeatureExtractors:
@staticmethod
def detect_objects_yolo(image: np.ndarray) -> List[Dict]:
    detector = YOLODetector()
    return detector.detect_objects(image)

┌──────────────────────────────────────────────────────────────────────────────┐
│                      3. GUI OVERLAY DLA FEEDBACKU                            │
└──────────────────────────────────────────────────────────────────────────────┘

DLACZEGO: Użytkownik musi widzieć co system rozpoznaje i móc to potwierdzić

KOD (Tkinter - prosty):
-----------------------
import tkinter as tk
from tkinter import ttk

class VPRMOverlay:
    def __init__(self, vprm: VPRMCognitiveVision):
        self.vprm = vprm
        self.root = tk.Tk()
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.8)
        
        # Frame z wykrytymi wzorcami
        self.frame = ttk.Frame(self.root)
        self.frame.pack()
        
        self.update_overlay()
    
    def update_overlay(self):
        # Pobierz stan
        state = self.vprm.get_current_visual_state()
        
        if state:
            for match in state['matches']:
                # Pokaż każdy wykryty wzorzec
                label = ttk.Label(
                    self.frame, 
                    text=f"{match['rule_name']} ({match['confidence']:.0%})"
                )
                label.pack()
                
                # Przyciski ✓/✗
                btn_frame = ttk.Frame(self.frame)
                btn_frame.pack()
                
                ttk.Button(
                    btn_frame, 
                    text="✓",
                    command=lambda rid=match['rule_id']: 
                        self.vprm.confirm_detection(rid, True)
                ).pack(side=tk.LEFT)
                
                ttk.Button(
                    btn_frame, 
                    text="✗",
                    command=lambda rid=match['rule_id']: 
                        self.vprm.confirm_detection(rid, False)
                ).pack(side=tk.LEFT)
        
        # Odśwież co 500ms
        self.root.after(500, self.update_overlay)
    
    def run(self):
        self.root.mainloop()

┌──────────────────────────────────────────────────────────────────────────────┐
│                      4. ZAAWANSOWANE PASSIVE LEARNING                        │
└──────────────────────────────────────────────────────────────────────────────┘

DLACZEGO: Automatyczne wykrywanie wzorców bez feedbacku użytkownika

KOD:
----
# Dodaj do VPRMCognitiveVision:

def mine_interaction_patterns(self, min_frequency: int = 10):
    """Wykryj wzorce z historii interakcji"""
    
    # Użyj sklearn do clusteringu
    from sklearn.cluster import DBSCAN
    
    # Zbierz wszystkie interakcje
    interactions = list(self.vprm.spatial_memory.interaction_history)
    
    if len(interactions) < min_frequency:
        return []
    
    # Wyciągnij pozycje
    positions = np.array([log['cursor'] for log in interactions])
    
    # DBSCAN clustering
    clustering = DBSCAN(eps=50, min_samples=min_frequency)
    labels = clustering.fit_predict(positions)
    
    # Dla każdego klastra
    learned_patterns = []
    for cluster_id in set(labels):
        if cluster_id == -1:  # Noise
            continue
        
        # Punkty w klastrze
        cluster_mask = labels == cluster_id
        cluster_points = positions[cluster_mask]
        
        # Środek klastra
        center_x = int(np.mean(cluster_points[:, 0]))
        center_y = int(np.mean(cluster_points[:, 1]))
        
        # Stwórz regułę
        pattern_rule = VisualRule(
            id=f"mined_pattern_{cluster_id}_{int(time.time())}",
            name=f"Auto-discovered Pattern {cluster_id}",
            rtype=HEURISTIC,
            spatial_region=(center_x - 30, center_y - 30, 60, 60),
            complexity_level="COMPOUND",
            tags={"auto_mined", "interaction_based"},
            category="UI_ELEMENT"
        )
        
        self.vprm.add_rule(pattern_rule)
        learned_patterns.append(pattern_rule)
        
        logger.info(f"Mined pattern at ({center_x}, {center_y}) "
                   f"from {len(cluster_points)} interactions")
    
    return learned_patterns

┌──────────────────────────────────────────────────────────────────────────────┐
│                      5. INTEGRACJA Z BAZĄ DANYCH                             │
└──────────────────────────────────────────────────────────────────────────────┘

DLACZEGO: Trwałe przechowywanie wzorców, współdzielenie między użytkownikami

KOD (SQLite):
-------------
import sqlite3

class VPRMDatabase:
    def __init__(self, db_path: str = "vprm_patterns.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                name TEXT,
                type TEXT,
                category TEXT,
                complexity_level TEXT,
                visual_features TEXT,
                spatial_region TEXT,
                tags TEXT,
                post_mean REAL,
                post_var REAL,
                observations INTEGER,
                success_rate REAL,
                created_at REAL
            )
        ''')
        
        self.conn.commit()
    
    def save_rule(self, rule: VisualRule):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO patterns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rule.id,
            rule.name,
            rule.type,
            rule.category,
            rule.complexity_level,
            json.dumps(rule.visual_features.to_dict()),
            json.dumps(rule.spatial_region) if rule.spatial_region else None,
            json.dumps(list(rule.tags)),
            rule.post_mean,
            rule.post_var,
            rule.observations,
            rule.get_success_rate(),
            rule.created_at
        ))
        
        self.conn.commit()
    
    def load_all_rules(self) -> List[VisualRule]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM patterns')
        
        rules = []
        for row in cursor.fetchall():
            # Rekonstrukcja reguły z DB
            # ... (podobnie jak w load_from_json)
            pass
        
        return rules

# Użycie w VPRMCognitiveVision:
# W __init__:
self.db = VPRMDatabase()

# W save_learned_patterns:
for rule in self.vprm.rules.values():
    self.db.save_rule(rule)

┌──────────────────────────────────────────────────────────────────────────────┐
│                      6. DODANIE OPTICAL FLOW (Detekcja Ruchu)               │
└──────────────────────────────────────────────────────────────────────────────┘

DLACZEGO: Wykrywanie ruchomych obiektów, animacji

KOD:
----
class OpticalFlowDetector:
    def __init__(self):
        self.prev_gray = None
    
    def detect_motion(self, frame: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if self.prev_gray is None:
            self.prev_gray = gray
            return np.zeros_like(gray)
        
        # Oblicz optical flow
        flow = cv2.calcOpticalFlowFarneback(
            self.prev_gray, gray, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )
        
        # Magnitude ruchu
        magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        
        self.prev_gray = gray
        return magnitude

# Użycie w VPRMCognitiveVision:
# W __init__:
self.motion_detector = OpticalFlowDetector()

# W _processing_loop:
motion_map = self.motion_detector.detect_motion(roi)
if np.mean(motion_map) > threshold:
    # Wykryto ruch!
    pass

┌──────────────────────────────────────────────────────────────────────────────┐
│                      7. EXPORT DO ONNX/TensorFlow                            │
└──────────────────────────────────────────────────────────────────────────────┘

DLACZEGO: Szybsze wykonanie, możliwość użycia GPU

KOD:
----
# Jeśli używasz PyTorch do treningu reguł:

import torch
import torch.nn as nn

class RuleNetwork(nn.Module):
    '''Neural network dla uczenia reguł'''
    def __init__(self, input_dim: int):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        return self.layers(x)

# Export do ONNX:
model = RuleNetwork(input_dim=100)
dummy_input = torch.randn(1, 100)

torch.onnx.export(
    model,
    dummy_input,
    "vprm_rule_network.onnx",
    export_params=True,
    opset_version=11,
    input_names=['features'],
    output_names=['confidence']
)

# Użycie ONNX Runtime:
import onnxruntime as ort

session = ort.InferenceSession("vprm_rule_network.onnx")
result = session.run(
    None,
    {"features": features_array}
)

┌──────────────────────────────────────────────────────────────────────────────┐
│                      8. MULTI-MONITOR SUPPORT                                │
└──────────────────────────────────────────────────────────────────────────────┘

KOD:
----
from screeninfo import get_monitors

class MultiMonitorVPRM(VPRMCognitiveVision):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.monitors = get_monitors()
    
    def _extract_foveated_roi(self, screen, cursor, radius):
        # Określ na którym monitorze jest kursor
        for monitor in self.monitors:
            if (monitor.x <= cursor[0] < monitor.x + monitor.width and
                monitor.y <= cursor[1] < monitor.y + monitor.height):
                
                # Capture tylko tego monitora
                monitor_screenshot = ImageGrab.grab(bbox=(
                    monitor.x, monitor.y,
                    monitor.x + monitor.width,
                    monitor.y + monitor.height
                ))
                
                # Relatywne współrzędne kursora
                rel_x = cursor[0] - monitor.x
                rel_y = cursor[1] - monitor.y
                
                return super()._extract_foveated_roi(
                    np.array(monitor_screenshot),
                    (rel_x, rel_y),
                    radius
                )
        
        return super()._extract_foveated_roi(screen, cursor, radius)

════════════════════════════════════════════════════════════════════════════════

KOLEJNOŚĆ ROZBUDOWY (Rekomendowana):
=====================================

1. ✓ Podstawowa wersja (już jest w tym pliku)
2. → GUI Overlay dla feedbacku (najprostsza wartość dodana)
3. → CLIP embeddings (semantyczne rozumienie)
4. → Baza danych SQLite (trwałość)
5. → YOLO object detection (dokładniejsza detekcja)
6. → Optical flow (ruch i animacje)
7. → Zaawansowane passive learning (auto-mining)
8. → Export ONNX (optymalizacja)
9. → Multi-monitor (jeśli potrzebne)

════════════════════════════════════════════════════════════════════════════════
