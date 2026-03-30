"""
model3d.py - Simple 3D Scene Generator
"""

import json
import math
from typing import List, Dict

class ThreeDModelBuilder:
    def __init__(self):
        self.wall_height = 3.0
    
    def generate_vibrant_3d_model(self, walls: List[Dict], rooms: List[Dict], 
                                   doors: List[Dict], windows: List[Dict], 
                                   furniture_placement: Dict, output_path: str):
        """Generate a simple working 3D model"""
        
        # Find bounds for camera positioning
        all_points = []
        for w in walls:
            if w.get('start') and w.get('end'):
                all_points.append(w['start'])
                all_points.append(w['end'])
        
        # Default center if no walls
        center_x, center_z = 5, 5
        width, depth = 10, 10
        
        if all_points:
            xs = [p[0] for p in all_points]
            zs = [p[1] for p in all_points]
            center_x = (min(xs) + max(xs)) / 2
            center_z = (min(zs) + max(zs)) / 2
            width = max(xs) - min(xs)
            depth = max(zs) - min(zs)
        
        # Simple camera position
        camera_x = center_x
        camera_y = 8
        camera_z = center_z + 12
        
        # Prepare wall data
        walls_js = []
        for w in walls:
            if w.get('start') and w.get('end'):
                walls_js.append({
                    'start': [float(w['start'][0]), float(w['start'][1])],
                    'end': [float(w['end'][0]), float(w['end'][1])],
                    'is_load_bearing': bool(w.get('is_load_bearing', False))
                })
        
        # Simple HTML with basic Three.js scene
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Floor Plan</title>
    <style>
        body {{ margin: 0; overflow: hidden; }}
        #info {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            font-family: Arial, sans-serif;
            font-size: 12px;
            pointer-events: none;
            z-index: 100;
        }}
        #controls {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 8px 12px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 11px;
            pointer-events: none;
            z-index: 100;
        }}
    </style>
</head>
<body>
    <div id="info">
        <strong>🏠 Floor Plan 3D Model</strong><br>
        Walls: {len(walls_js)} | Press and drag to rotate | Scroll to zoom
    </div>
    <div id="controls">
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
        
        // Setup camera
        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set({camera_x}, {camera_y}, {camera_z});
        camera.lookAt({center_x}, 0, {center_z});
        
        // Setup renderer
        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        document.body.appendChild(renderer.domElement);
        
        // Controls
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.screenSpacePanning = true;
        
        // Lighting
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(10, 20, 5);
        directionalLight.castShadow = true;
        directionalLight.receiveShadow = true;
        scene.add(directionalLight);
        
        const backLight = new THREE.PointLight(0x4466cc, 0.3);
        backLight.position.set(-5, 5, -5);
        scene.add(backLight);
        
        // Grid helper
        const gridHelper = new THREE.GridHelper(20, 20, 0x88aaff, 0x335588);
        gridHelper.position.y = -0.1;
        scene.add(gridHelper);
        
        // Simple floor
        const floorGeometry = new THREE.PlaneGeometry(18, 18);
        const floorMaterial = new THREE.MeshStandardMaterial({{ color: 0x2c3e50, roughness: 0.5, metalness: 0.1, side: THREE.DoubleSide }});
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.rotation.x = -Math.PI / 2;
        floor.position.y = -0.05;
        floor.receiveShadow = true;
        scene.add(floor);
        
        // Wall data
        const wallData = {json.dumps(walls_js)};
        
        console.log('Creating', wallData.length, 'walls');
        
        // Create walls
        wallData.forEach((wall, index) => {{
            const start = new THREE.Vector3(wall.start[0], 0, wall.start[1]);
            const end = new THREE.Vector3(wall.end[0], 0, wall.end[1]);
            const length = start.distanceTo(end);
            
            if (length < 0.2) return;
            
            const angle = Math.atan2(end.z - start.z, end.x - start.x);
            const color = wall.is_load_bearing ? 0xff6666 : 0xc9ae8c;
            const material = new THREE.MeshStandardMaterial({{ color: color, roughness: 0.3 }});
            
            const wallMesh = new THREE.Mesh(new THREE.BoxGeometry(length, 2.8, 0.2), material);
            wallMesh.position.set((start.x + end.x) / 2, 1.4, (start.z + end.z) / 2);
            wallMesh.rotation.y = angle;
            wallMesh.castShadow = true;
            wallMesh.receiveShadow = true;
            scene.add(wallMesh);
        }});
        
        // Add a simple colored cube at center to verify rendering works
        const testCube = new THREE.Mesh(
            new THREE.BoxGeometry(0.5, 0.5, 0.5),
            new THREE.MeshStandardMaterial({{ color: 0xffaa44 }})
        );
        testCube.position.set({center_x}, 0.5, {center_z});
        testCube.castShadow = true;
        scene.add(testCube);
        
        // Add some floating particles for ambiance
        const particleCount = 300;
        const particlesGeometry = new THREE.BufferGeometry();
        const particlesPositions = new Float32Array(particleCount * 3);
        for (let i = 0; i < particleCount; i++) {{
            particlesPositions[i*3] = (Math.random() - 0.5) * 20;
            particlesPositions[i*3+1] = Math.random() * 5;
            particlesPositions[i*3+2] = (Math.random() - 0.5) * 20;
        }}
        particlesGeometry.setAttribute('position', new THREE.BufferAttribute(particlesPositions, 3));
        const particlesMaterial = new THREE.PointsMaterial({{ color: 0x88aaff, size: 0.05 }});
        const particles = new THREE.Points(particlesGeometry, particlesMaterial);
        scene.add(particles);
        
        // Simple animation
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
        
        console.log('3D Model Loaded Successfully!');
    </script>
</body>
</html>'''
        
        # Write the HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path