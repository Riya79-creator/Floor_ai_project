"""
Floor AI - Professional Floor Plan to 3D Model Pipeline
COMPLETE WORKING VERSION
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import uuid
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ============ MATERIAL DATABASE ============
MATERIALS = {
    'Red Brick': {'cost': 35, 'strength': 7.0, 'durability': 8, 'type': 'load_bearing'},
    'AAC Block': {'cost': 25, 'strength': 4.0, 'durability': 7, 'type': 'partition'},
    'RCC': {'cost': 85, 'strength': 25.0, 'durability': 10, 'type': 'slab'},
    'Steel': {'cost': 120, 'strength': 250.0, 'durability': 9, 'type': 'column'},
    'Fly Ash Brick': {'cost': 22, 'strength': 5.5, 'durability': 7, 'type': 'partition'},
    'Precast Concrete': {'cost': 65, 'strength': 30.0, 'durability': 9, 'type': 'structural'}
}

# ============ IMAGE PARSING ============
def parse_floor_plan(image_path):
    """Extract walls and rooms from floor plan image"""
    img = cv2.imread(image_path)
    if img is None:
        return None, None, "Could not load image"
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    # Detect lines (walls)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=50, maxLineGap=10)
    
    if lines is None:
        return None, None, "No walls detected"
    
    # Convert lines to walls (pixels to meters: 20px = 1m)
    scale = 0.05
    walls = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        walls.append({
            'start': (float(x1 * scale), float(y1 * scale)),
            'end': (float(x2 * scale), float(y2 * scale)),
            'length': float(np.hypot(x2 - x1, y2 - y1) * scale)
        })
    
    # Simple room detection from contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rooms = []
    room_names = ['Living Room', 'Bedroom', 'Kitchen', 'Bathroom', 'Hallway', 'Dining Room']
    
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area > 5000:
            perimeter = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * perimeter, True)
            polygon = [(float(p[0][0] * scale), float(p[0][1] * scale)) for p in approx]
            rooms.append({
                'id': f'room_{i}',
                'name': room_names[i % len(room_names)],
                'area': float(area * scale * scale),
                'polygon': polygon
            })
    
    return walls, rooms, None

# ============ LOAD BEARING CLASSIFICATION ============
def classify_load_bearing(walls):
    """Simple rule-based load bearing classification"""
    if not walls:
        return walls
    
    xs = [w['start'][0] for w in walls] + [w['end'][0] for w in walls]
    ys = [w['start'][1] for w in walls] + [w['end'][1] for w in walls]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    for wall in walls:
        start, end = wall['start'], wall['end']
        is_exterior = (abs(start[0] - min_x) < 0.2 or abs(start[0] - max_x) < 0.2 or
                      abs(start[1] - min_y) < 0.2 or abs(start[1] - max_y) < 0.2 or
                      abs(end[0] - min_x) < 0.2 or abs(end[0] - max_x) < 0.2 or
                      abs(end[1] - min_y) < 0.2 or abs(end[1] - max_y) < 0.2)
        wall['is_load_bearing'] = is_exterior or wall['length'] > 6.0
    
    return walls

# ============ MATERIAL RECOMMENDATION ============
def recommend_materials(element_type, span=0):
    """Recommend top 3 materials based on cost-strength tradeoff"""
    suitable = {
        'load_bearing_wall': ['Red Brick', 'Precast Concrete', 'Fly Ash Brick'],
        'partition_wall': ['AAC Block', 'Fly Ash Brick', 'Red Brick'],
        'slab': ['RCC', 'Precast Concrete', 'Steel'],
        'column': ['Steel', 'RCC', 'Precast Concrete']
    }
    
    candidates = suitable.get(element_type, ['Red Brick', 'RCC'])
    recommendations = []
    
    for mat in candidates[:3]:
        data = MATERIALS.get(mat, {})
        if not data:
            continue
        
        cost_score = max(0, 100 - (data['cost'] / 1.2))
        strength_score = min(100, (data['strength'] / 250) * 100)
        
        if element_type in ['load_bearing_wall', 'column']:
            score = strength_score * 0.6 + cost_score * 0.4
        else:
            score = cost_score * 0.6 + strength_score * 0.4
        
        # Generate detailed justification
        if element_type == 'load_bearing_wall':
            justification = f"{mat} provides excellent structural support with {data['strength']} MPa strength. Cost: ${data['cost']}/m². Ideal for main walls."
        elif element_type == 'partition_wall':
            justification = f"{mat} is cost-effective at ${data['cost']}/m² for non-load-bearing walls. Sufficient strength ({data['strength']} MPa) for room division."
        elif element_type == 'slab':
            justification = f"{mat} offers {data['strength']} MPa strength for floor slabs. Handles spans well with durability {data['durability']}/10."
        else:
            justification = f"{mat} recommended for columns. High strength ({data['strength']} MPa) ensures structural integrity."
        
        recommendations.append({
            'material': mat,
            'score': round(score, 1),
            'cost': data['cost'],
            'strength': data['strength'],
            'durability': data['durability'],
            'justification': justification
        })
    
    return recommendations

# ============ EXPLANATION GENERATION ============
def generate_explanation(walls, rooms, recommendations):
    """Generate human-readable explanation"""
    load_bearing_count = sum(1 for w in walls if w.get('is_load_bearing', False))
    total_area = sum(r.get('area', 0) for r in rooms)
    
    explanation = {
        'summary': f"This building has {len(rooms)} rooms covering {total_area:.0f} square meters. "
                   f"Detected {len(walls)} walls, with {load_bearing_count} classified as load-bearing.",
        'structural_analysis': f"Load-bearing walls form the primary structural system. "
                               f"Exterior walls and long spans (>6m) are marked as load-bearing.",
        'material_decisions': f"For load-bearing walls, {recommendations['load_bearing_wall'][0]['material']} is recommended "
                             f"due to its strength-to-cost ratio. For partitions, {recommendations['partition_wall'][0]['material']} "
                             f"offers savings while maintaining adequate strength.",
        'tradeoff_analysis': "The recommendations balance cost and strength: structural elements prioritize strength (60% weight), "
                            "while non-structural elements prioritize cost (60% weight).",
        'recommendations_summary': f"🏛️ Load-bearing walls: {recommendations['load_bearing_wall'][0]['material']}\n"
                                  f"🚪 Partition walls: {recommendations['partition_wall'][0]['material']}\n"
                                  f"🏗️ Floor slab: {recommendations['slab'][0]['material']}\n"
                                  f"📐 Columns: {recommendations['column'][0]['material']}"
    }
    return explanation

# ============ 3D MODEL GENERATION ============
def generate_3d_model(walls, rooms, output_path):
    """Generate Three.js HTML file - FIXED VERSION"""
    
    # Prepare wall data for JavaScript
    walls_js = []
    for w in walls:
        walls_js.append({
            'start': [float(w['start'][0]), float(w['start'][1])],
            'end': [float(w['end'][0]), float(w['end'][1])],
            'is_load_bearing': bool(w.get('is_load_bearing', False))
        })
    
    walls_json = json.dumps(walls_js)
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Floor AI - 3D Model</title>
    <style>
        body {{ margin: 0; overflow: hidden; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        #info {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 10px 15px;
            border-radius: 8px;
            pointer-events: none;
            z-index: 100;
            font-size: 14px;
        }}
        .legend {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(0,0,0,0.5);
            color: white;
            padding: 8px 12px;
            border-radius: 5px;
            font-size: 12px;
            pointer-events: none;
        }}
    </style>
</head>
<body>
    <div id="info">
        <strong>🏠 Floor AI - 3D Model</strong><br>
        🟧 Orange = Load-bearing walls | 🟫 Brown = Partition walls
    </div>
    <div class="legend">
        🖱️ Mouse drag to rotate | Right-click to pan | Scroll to zoom
    </div>
    
    <script type="importmap">
        {{
            "imports": {{
                "three": "https://unpkg.com/three@0.128.0/build/three.module.js",
                "three/addons/": "https://unpkg.com/three@0.128.0/examples/jsm/"
            }}
        }}
    </script>
    
    <script type="module">
        import * as THREE from 'three';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
        
        // Setup scene
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x111122);
        scene.fog = new THREE.FogExp2(0x111122, 0.008);
        
        // Setup camera
        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(12, 8, 14);
        camera.lookAt(7.5, 1.5, 6);
        
        // Setup renderer
        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        document.body.appendChild(renderer.domElement);
        
        // Controls
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.rotateSpeed = 1.0;
        controls.zoomSpeed = 1.2;
        
        // Lighting
        const ambientLight = new THREE.AmbientLight(0x404060);
        scene.add(ambientLight);
        
        const dirLight = new THREE.DirectionalLight(0xffffff, 1);
        dirLight.position.set(5, 10, 7);
        dirLight.castShadow = true;
        dirLight.receiveShadow = true;
        scene.add(dirLight);
        
        const fillLight = new THREE.PointLight(0x4466cc, 0.3);
        fillLight.position.set(7.5, 3, 6);
        scene.add(fillLight);
        
        // Grid helper
        const gridHelper = new THREE.GridHelper(30, 20, 0x88aaff, 0x335588);
        gridHelper.position.y = -0.05;
        scene.add(gridHelper);
        
        // Floor slab
        const floorGeometry = new THREE.BoxGeometry(16, 0.1, 13);
        const floorMaterial = new THREE.MeshStandardMaterial({{ color: 0x666688, roughness: 0.7, metalness: 0.1 }});
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.position.set(7.5, -0.05, 6);
        floor.receiveShadow = true;
        scene.add(floor);
        
        // Wall data from backend
        const wallData = {walls_json};
        
        // Create walls
        wallData.forEach(wall => {{
            const start = new THREE.Vector3(wall.start[0], 0, wall.start[1]);
            const end = new THREE.Vector3(wall.end[0], 0, wall.end[1]);
            const length = start.distanceTo(end);
            const angle = Math.atan2(end.z - start.z, end.x - start.x);
            
            // Color based on load bearing
            const color = wall.is_load_bearing ? 0xd49466 : 0xc9b896;
            const material = new THREE.MeshStandardMaterial({{ color: color, roughness: 0.5, metalness: 0.05 }});
            
            const wallMesh = new THREE.Mesh(new THREE.BoxGeometry(length, 3.0, 0.2), material);
            wallMesh.position.set((start.x + end.x) / 2, 1.5, (start.z + end.z) / 2);
            wallMesh.rotation.y = angle;
            wallMesh.castShadow = true;
            wallMesh.receiveShadow = true;
            scene.add(wallMesh);
        }});
        
        // Add simple columns at corners for visual reference
        const columnMaterial = new THREE.MeshStandardMaterial({{ color: 0xaaaaaa, metalness: 0.3 }});
        const corners = [[0,0], [15,0], [15,12], [0,12]];
        corners.forEach(corner => {{
            const column = new THREE.Mesh(new THREE.BoxGeometry(0.3, 3.0, 0.3), columnMaterial);
            column.position.set(corner[0], 1.5, corner[1]);
            column.castShadow = true;
            scene.add(column);
        }});
        
        // Animation loop
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();
        
        // Handle window resize
        window.addEventListener('resize', onWindowResize, false);
        function onWindowResize() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }}
        
        console.log('3D Model Loaded Successfully');
    </script>
</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return output_path

# ============ FLASK ROUTES ============
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'floor_plan' not in request.files:
            return jsonify({'error': 'No file'}), 400
        
        file = request.files['floor_plan']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        filepath = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{filename}")
        file.save(filepath)
        
        use_fallback = request.form.get('use_fallback') == 'true'
        
        # Parse floor plan
        walls, rooms, error = parse_floor_plan(filepath)
        
        # Use manual fallback if needed
        if (walls is None or len(walls) == 0) and use_fallback:
            walls = [
                {'start': (0,0), 'end': (15,0), 'length': 15, 'is_load_bearing': True},
                {'start': (15,0), 'end': (15,12), 'length': 12, 'is_load_bearing': True},
                {'start': (15,12), 'end': (0,12), 'length': 15, 'is_load_bearing': True},
                {'start': (0,12), 'end': (0,0), 'length': 12, 'is_load_bearing': True},
                {'start': (7.5,0), 'end': (7.5,12), 'length': 12, 'is_load_bearing': True},
                {'start': (3,0), 'end': (3,4), 'length': 4, 'is_load_bearing': False},
                {'start': (3,4), 'end': (7.5,4), 'length': 4.5, 'is_load_bearing': False},
                {'start': (10.5,0), 'end': (10.5,4), 'length': 4, 'is_load_bearing': False},
                {'start': (10.5,4), 'end': (15,4), 'length': 4.5, 'is_load_bearing': False},
                {'start': (7.5,6), 'end': (15,6), 'length': 7.5, 'is_load_bearing': False},
                {'start': (0,8), 'end': (3,8), 'length': 3, 'is_load_bearing': False},
            ]
            rooms = [
                {'name': 'Bedroom 1', 'area': 12, 'polygon': [(0,0),(3,0),(3,4),(0,4)]},
                {'name': 'Bedroom 2', 'area': 18, 'polygon': [(10.5,0),(15,0),(15,4),(10.5,4)]},
                {'name': 'Bedroom 3', 'area': 12, 'polygon': [(0,4),(3,4),(3,8),(0,8)]},
                {'name': 'Kitchen', 'area': 45, 'polygon': [(7.5,6),(15,6),(15,12),(7.5,12)]},
                {'name': 'Living Room', 'area': 18, 'polygon': [(3,4),(7.5,4),(7.5,6),(3,6)]},
                {'name': 'Foyer', 'area': 12, 'polygon': [(0,8),(3,8),(3,12),(0,12)]},
                {'name': 'Bathroom', 'area': 12, 'polygon': [(7.5,0),(10.5,0),(10.5,4),(7.5,4)]},
            ]
        elif walls is None or len(walls) == 0:
            return jsonify({'error': error or 'No walls detected. Try Manual Mode.'}), 400
        
        # Classify walls
        walls = classify_load_bearing(walls)
        
        # Get recommendations
        recommendations = {
            'load_bearing_wall': recommend_materials('load_bearing_wall'),
            'partition_wall': recommend_materials('partition_wall'),
            'slab': recommend_materials('slab'),
            'column': recommend_materials('column')
        }
        
        # Generate explanation
        explanation = generate_explanation(walls, rooms, recommendations)
        
        # Generate 3D model
        model_file = f"{unique_id}_model.html"
        model_path = os.path.join(STATIC_FOLDER, model_file)
        generate_3d_model(walls, rooms, model_path)
        
        # Prepare response
        response = {
            'success': True,
            'walls': [{'start': list(w['start']), 'end': list(w['end']), 
                      'is_load_bearing': w['is_load_bearing']} for w in walls],
            'rooms': rooms,
            'recommendations': recommendations,
            'explanation': explanation,
            'model_url': f'/static/{model_file}',
            'stats': {
                'total_walls': len(walls),
                'load_bearing': sum(1 for w in walls if w['is_load_bearing']),
                'total_rooms': len(rooms),
                'total_area': sum(r.get('area', 0) for r in rooms)
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 FLOOR AI - Professional Pipeline")
    print("="*60)
    print("📍 Open: http://localhost:5000")
    print("📁 Upload floor plan images")
    print("💡 Check 'Manual Mode' if auto-detection fails")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
    