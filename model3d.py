"""
model3d.py - 3D Model Generator
Purpose: Convert wall and room data into a Three.js 3D model
"""

import json
import os

class ThreeJSExporter:
    def __init__(self, walls, rooms, floor_height=3.0):
        self.walls = walls
        self.rooms = rooms
        self.floor_height = floor_height
    
    def generate_html(self, output_path):
        """Generate HTML file with Three.js 3D model"""
        
        # Prepare data for JavaScript
        walls_js = self._prepare_walls_json()
        rooms_js = self._prepare_rooms_json()
        
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
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
        #controls-hint {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(0,0,0,0.5);
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
            pointer-events: none;
        }}
    </style>
</head>
<body>
    <div id="info">
        <strong>🏠 Floor AI - 3D Model</strong><br>
        Load-bearing walls: <span style="color:#ffaa66">Orange</span> | Partition walls: <span style="color:#c9b896">Tan</span>
    </div>
    <div id="controls-hint">
        🖱️ Mouse drag to rotate | Right-click drag to pan | Scroll to zoom
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
        import {{ CSS2DRenderer, CSS2DObject }} from 'three/addons/renderers/CSS2DRenderer.js';
        
        // --- Setup Scene ---
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x111122);
        scene.fog = new THREE.FogExp2(0x111122, 0.008);
        
        // --- Cameras ---
        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(12, 8, 14);
        camera.lookAt(7.5, 1.5, 6);
        
        // --- Renderers ---
        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        document.body.appendChild(renderer.domElement);
        
        const labelRenderer = new CSS2DRenderer();
        labelRenderer.setSize(window.innerWidth, window.innerHeight);
        labelRenderer.domElement.style.position = 'absolute';
        labelRenderer.domElement.style.top = '0px';
        labelRenderer.domElement.style.left = '0px';
        labelRenderer.domElement.style.pointerEvents = 'none';
        document.body.appendChild(labelRenderer.domElement);
        
        // --- Controls ---
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.rotateSpeed = 1.0;
        controls.zoomSpeed = 1.2;
        controls.panSpeed = 0.8;
        
        // --- Lighting ---
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x404060);
        scene.add(ambientLight);
        
        // Directional light (sun)
        const dirLight = new THREE.DirectionalLight(0xffffff, 1);
        dirLight.position.set(5, 10, 7);
        dirLight.castShadow = true;
        dirLight.receiveShadow = true;
        dirLight.shadow.mapSize.width = 1024;
        dirLight.shadow.mapSize.height = 1024;
        scene.add(dirLight);
        
        // Fill light from below
        const fillLight = new THREE.PointLight(0x4466cc, 0.3);
        fillLight.position.set(7.5, -1, 6);
        scene.add(fillLight);
        
        // Back fill
        const backLight = new THREE.PointLight(0xffaa66, 0.2);
        backLight.position.set(0, 3, 12);
        scene.add(backLight);
        
        // --- Helper: Grid ---
        const gridHelper = new THREE.GridHelper(30, 20, 0x88aaff, 0x335588);
        gridHelper.position.y = -0.05;
        scene.add(gridHelper);
        
        // --- Floor Slab ---
        const floorGeometry = new THREE.BoxGeometry(15.2, 0.1, 12.2);
        const floorMaterial = new THREE.MeshStandardMaterial({{ color: 0x666688, roughness: 0.7, metalness: 0.1 }});
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.position.set(7.5, -0.05, 6);
        floor.receiveShadow = true;
        floor.castShadow = false;
        scene.add(floor);
        
        // --- Wall Materials ---
        const partitionMaterial = new THREE.MeshStandardMaterial({{ color: 0xc9b896, roughness: 0.6, metalness: 0.05 }});
        const loadBearingMaterial = new THREE.MeshStandardMaterial({{ color: 0xd49466, roughness: 0.4, metalness: 0.1, emissive: 0x331100 }});
        
        // --- Build Walls from Data ---
        const wallData = {walls_js};
        
        wallData.forEach(wall => {{
            const start = new THREE.Vector3(wall.start[0], 0, wall.start[1]);
            const end = new THREE.Vector3(wall.end[0], 0, wall.end[1]);
            const length = start.distanceTo(end);
            const angle = Math.atan2(end.z - start.z, end.x - start.x);
            
            const geometry = new THREE.BoxGeometry(length, {self.floor_height}, 0.2);
            const material = wall.is_load_bearing ? loadBearingMaterial : partitionMaterial;
            const mesh = new THREE.Mesh(geometry, material);
            
            const centerX = (start.x + end.x) / 2;
            const centerZ = (start.z + end.z) / 2;
            mesh.position.set(centerX, {self.floor_height} / 2, centerZ);
            mesh.rotation.y = angle;
            mesh.castShadow = true;
            mesh.receiveShadow = true;
            scene.add(mesh);
        }});
        
        // --- Room Labels (CSS2D) and Wireframes ---
        const roomData = {rooms_js};
        
        roomData.forEach(room => {{
            // Wireframe outline
            const points = room.polygon.map(p => new THREE.Vector3(p[0], 0.05, p[1]));
            const lineGeometry = new THREE.BufferGeometry().setFromPoints(points.concat([points[0]]));
            const lineMaterial = new THREE.LineBasicMaterial({{ color: 0x44ffaa, linewidth: 1 }});
            const wireframe = new THREE.Line(lineGeometry, lineMaterial);
            scene.add(wireframe);
            
            // CSS2D Label
            const div = document.createElement('div');
            div.textContent = `${{room.name}}\n${{room.area.toFixed(1)}} m²`;
            div.style.color = 'white';
            div.style.fontSize = '14px';
            div.style.fontWeight = 'bold';
            div.style.textShadow = '1px 1px 0px black';
            div.style.backgroundColor = 'rgba(0,0,0,0.6)';
            div.style.padding = '4px 8px';
            div.style.borderRadius = '4px';
            div.style.borderLeft = `3px solid ${{room.name === 'Living Room' ? '#44ffaa' : '#ffaa44'}}`;
            div.style.fontFamily = 'sans-serif';
            
            const label = new CSS2DObject(div);
            label.position.set(room.center[0], 1.2, room.center[1]);
            scene.add(label);
        }});
        
        // --- Add Simple Columns at Corners for Visual Reference ---
        const columnMaterial = new THREE.MeshStandardMaterial({{ color: 0xaaaaaa, metalness: 0.3, roughness: 0.5 }});
        const corners = [[0,0], [15,0], [15,12], [0,12]];
        corners.forEach(corner => {{
            const columnGeo = new THREE.BoxGeometry(0.3, {self.floor_height}, 0.3);
            const column = new THREE.Mesh(columnGeo, columnMaterial);
            column.position.set(corner[0], {self.floor_height}/2, corner[1]);
            column.castShadow = true;
            scene.add(column);
        }});
        
        // --- Simple Sky Sphere (optional) ---
        // Just add a subtle gradient background via scene color (already set)
        
        // --- Animation Loop ---
        function animate() {{
            requestAnimationFrame(animate);
            controls.update(); // Update controls
            renderer.render(scene, camera);
            labelRenderer.render(scene, camera);
        }}
        animate();
        
        // --- Handle Window Resize ---
        window.addEventListener('resize', onWindowResize, false);
        function onWindowResize() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
            labelRenderer.setSize(window.innerWidth, window.innerHeight);
        }}
        
        // Small delay to ensure controls work properly
        setTimeout(() => {{
            controls.update();
        }}, 100);
    </script>
</body>
</html>'''
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _prepare_walls_json(self):
        """Convert walls to JSON for embedding"""
        walls_data = []
        for wall in self.walls:
            walls_data.append({
                'start': [wall['start'][0], wall['start'][1]],
                'end': [wall['end'][0], wall['end'][1]],
                'is_load_bearing': wall.get('is_load_bearing', False)
            })
        return json.dumps(walls_data)
    
    def _prepare_rooms_json(self):
        """Convert rooms to JSON for embedding"""
        rooms_data = []
        for room in self.rooms:
            # Calculate center from polygon if not present
            if 'centroid' in room:
                center = room['centroid']
            else:
                polygon = room.get('polygon', [])
                if polygon:
                    xs = [p[0] for p in polygon]
                    ys = [p[1] for p in polygon]
                    center = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
                else:
                    center = (0, 0)
            
            rooms_data.append({
                'name': room.get('name', 'Room'),
                'area': room.get('area', 0),
                'polygon': room.get('polygon', []),
                'center': [center[0], center[1]]
            })
        return json.dumps(rooms_data)