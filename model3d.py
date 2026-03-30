"""
model3d.py - Advanced 3D Scene Generator with Vibrant Colors and Furniture
"""

import json
import math
from typing import List, Dict

class ThreeDModelBuilder:
    def __init__(self):
        self.wall_height = 3.0
        self.vibrant_colors = {
            'load_bearing': '#FF6B6B',
            'partition': '#C9AE8C',
            'living_room_wall': '#FF6B6B',
            'bedroom_wall': '#4ECDC4',
            'kitchen_wall': '#FFE66D',
            'bathroom_wall': '#95E1D3',
            'dining_room_wall': '#F9D56E',
            'hallway_wall': '#B83B5E',
            'office_wall': '#6C5B7B',
            'default_wall': '#C06C84',
            'glass': '#88CCFF',
            'door': '#F39C12',
            'furniture': '#E67E22'
        }
    
    def generate_vibrant_3d_model(self, walls: List[Dict], rooms: List[Dict], 
                                   doors: List[Dict], windows: List[Dict], 
                                   furniture_placement: Dict, output_path: str):
        """Generate Three.js HTML file with vibrant colors and furniture"""
        
        # Prepare data for JavaScript
        walls_js = []
        for w in walls:
            walls_js.append({
                'start': [float(w['start'][0]), float(w['start'][1])],
                'end': [float(w['end'][0]), float(w['end'][1])],
                'is_load_bearing': bool(w.get('is_load_bearing', False)),
                'length': float(w['length'])
            })
        
        rooms_js = []
        for room in rooms:
            rooms_js.append({
                'id': room['id'],
                'type': room['type'],
                'name': room['name'],
                'polygon': room['polygon'],
                'centroid': room['centroid'],
                'area': room['area']
            })
        
        doors_js = []
        for door in doors:
            doors_js.append({
                'position': door['position'],
                'width': door['width'],
                'height': door['height'],
                'start': door['start'],
                'end': door['end']
            })
        
        windows_js = []
        for window in windows:
            windows_js.append({
                'position': window['position'],
                'width': window['width'],
                'height': window['height'],
                'start': window['start'],
                'end': window['end']
            })
        
        furniture_js = furniture_placement
        
        # Room colors mapping
        room_colors = {
            'living_room': '#FF6B6B',
            'bedroom': '#4ECDC4',
            'kitchen': '#FFE66D',
            'bathroom': '#95E1D3',
            'dining_room': '#F9D56E',
            'hallway': '#B83B5E',
            'office': '#6C5B7B',
            'default': '#C06C84'
        }
        
        walls_json = json.dumps(walls_js)
        rooms_json = json.dumps(rooms_js)
        doors_json = json.dumps(doors_js)
        windows_json = json.dumps(windows_js)
        furniture_json = json.dumps(furniture_js)
        room_colors_json = json.dumps(room_colors)
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Floor AI - Vibrant 3D Model</title>
    <style>
        body {{ margin: 0; overflow: hidden; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        #info {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(0,0,0,0.85);
            color: white;
            padding: 15px 20px;
            border-radius: 12px;
            pointer-events: none;
            z-index: 100;
            font-size: 14px;
            backdrop-filter: blur(10px);
            border-left: 4px solid #FF6B6B;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        .legend {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 12px;
            pointer-events: none;
            backdrop-filter: blur(5px);
            font-family: monospace;
        }}
        .controls-hint {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: rgba(0,0,0,0.6);
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 11px;
            pointer-events: none;
            font-family: monospace;
        }}
        .color-dot {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 6px;
        }}
    </style>
</head>
<body>
    <div id="info">
        <strong style="font-size: 16px;">🏠 Floor AI - Vibrant 3D Model</strong><br>
        <div style="margin-top: 8px;">
            <div><span class="color-dot" style="background: #FF6B6B;"></span> Load-bearing walls</div>
            <div><span class="color-dot" style="background: #C9AE8C;"></span> Partition walls</div>
            <div><span class="color-dot" style="background: #4ECDC4;"></span> Rooms (vibrant colors)</div>
            <div><span class="color-dot" style="background: #F39C12;"></span> Doors</div>
            <div><span class="color-dot" style="background: #88CCFF;"></span> Windows</div>
            <div><span class="color-dot" style="background: #E67E22;"></span> Furniture</div>
        </div>
    </div>
    <div class="legend">
        🖱️ Mouse drag to rotate | Right-click to pan | Scroll to zoom
    </div>
    <div class="controls-hint">
        🎨 Vibrant 3D Experience
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
        
        // Setup scene
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0a0a2a);
        scene.fog = new THREE.FogExp2(0x0a0a2a, 0.008);
        
        // Setup camera
        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(12, 8, 14);
        camera.lookAt(7.5, 1.5, 6);
        
        // Setup renderer
        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        document.body.appendChild(renderer.domElement);
        
        // CSS2 Renderer for text labels
        const labelRenderer = new CSS2DRenderer();
        labelRenderer.setSize(window.innerWidth, window.innerHeight);
        labelRenderer.domElement.style.position = 'absolute';
        labelRenderer.domElement.style.top = '0px';
        labelRenderer.domElement.style.left = '0px';
        labelRenderer.domElement.style.pointerEvents = 'none';
        document.body.appendChild(labelRenderer.domElement);
        
        // Controls
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.rotateSpeed = 1.0;
        controls.zoomSpeed = 1.2;
        controls.panSpeed = 0.8;
        
        // Lighting
        const ambientLight = new THREE.AmbientLight(0x404060, 0.6);
        scene.add(ambientLight);
        
        const mainLight = new THREE.DirectionalLight(0xfff5e6, 1.2);
        mainLight.position.set(8, 12, 5);
        mainLight.castShadow = true;
        mainLight.receiveShadow = true;
        mainLight.shadow.mapSize.width = 2048;
        mainLight.shadow.mapSize.height = 2048;
        scene.add(mainLight);
        
        const fillLight = new THREE.PointLight(0x4466cc, 0.4);
        fillLight.position.set(5, 4, 8);
        scene.add(fillLight);
        
        const backLight = new THREE.PointLight(0xffaa66, 0.3);
        backLight.position.set(-3, 5, -5);
        scene.add(backLight);
        
        const rimLight = new THREE.PointLight(0xff8866, 0.5);
        rimLight.position.set(10, 6, -8);
        scene.add(rimLight);
        
        // Grid helper with vibrant color
        const gridHelper = new THREE.GridHelper(30, 20, 0x88aaff, 0x335588);
        gridHelper.position.y = -0.05;
        scene.add(gridHelper);
        
        // Floor slab with translucent effect
        const floorGeometry = new THREE.BoxGeometry(18, 0.1, 15);
        const floorMaterial = new THREE.MeshStandardMaterial({{ color: 0x2c3e50, roughness: 0.5, metalness: 0.1, transparent: true, opacity: 0.7 }});
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.position.set(7.5, -0.05, 6);
        floor.receiveShadow = true;
        scene.add(floor);
        
        // Data from backend
        const wallData = {walls_json};
        const roomData = {rooms_json};
        const doorData = {doors_json};
        const windowData = {windows_json};
        const furnitureData = {furniture_json};
        const roomColors = {room_colors_json};
        
        // Create vibrant rooms (floors)
        roomData.forEach(room => {{
            if (room.polygon && room.polygon.length >= 3) {{
                const shape = new THREE.Shape();
                const points = room.polygon;
                shape.moveTo(points[0][0], points[0][1]);
                for (let i = 1; i < points.length; i++) {{
                    shape.lineTo(points[i][0], points[i][1]);
                }}
                shape.closePath();
                
                const color = roomColors[room.type] || roomColors['default'];
                const geometry = new THREE.ShapeGeometry(shape);
                const material = new THREE.MeshStandardMaterial({{
                    color: color,
                    roughness: 0.4,
                    metalness: 0.05,
                    side: THREE.DoubleSide,
                    transparent: true,
                    opacity: 0.85
                }});
                const floorMesh = new THREE.Mesh(geometry, material);
                floorMesh.rotation.x = -Math.PI / 2;
                floorMesh.position.y = 0;
                floorMesh.receiveShadow = true;
                scene.add(floorMesh);
                
                // Add room label
                const div = document.createElement('div');
                div.textContent = room.name;
                div.style.color = '#ffffff';
                div.style.fontSize = '14px';
                div.style.fontWeight = 'bold';
                div.style.backgroundColor = 'rgba(0,0,0,0.7)';
                div.style.padding = '4px 12px';
                div.style.borderRadius = '20px';
                div.style.borderLeft = `3px solid ${{color}}`;
                div.style.fontFamily = 'sans-serif';
                const label = new CSS2DObject(div);
                label.position.set(room.centroid[0], 0.1, room.centroid[1]);
                scene.add(label);
            }}
        }});
        
        // Create walls
        wallData.forEach(wall => {{
            const start = new THREE.Vector3(wall.start[0], 0, wall.start[1]);
            const end = new THREE.Vector3(wall.end[0], 0, wall.end[1]);
            const length = start.distanceTo(end);
            const angle = Math.atan2(end.z - start.z, end.x - start.x);
            
            const color = wall.is_load_bearing ? '#FF6B6B' : '#C9AE8C';
            const material = new THREE.MeshStandardMaterial({{ color: color, roughness: 0.3, metalness: 0.1 }});
            
            const wallMesh = new THREE.Mesh(new THREE.BoxGeometry(length, 3.0, 0.2), material);
            wallMesh.position.set((start.x + end.x) / 2, 1.5, (start.z + end.z) / 2);
            wallMesh.rotation.y = angle;
            wallMesh.castShadow = true;
            wallMesh.receiveShadow = true;
            scene.add(wallMesh);
        }});
        
        // Create doors
        doorData.forEach(door => {{
            const start = new THREE.Vector3(door.start[0], 0, door.start[1]);
            const end = new THREE.Vector3(door.end[0], 0, door.end[1]);
            const center = new THREE.Vector3((start.x + end.x) / 2, 1.1, (start.z + end.z) / 2);
            const width = start.distanceTo(end);
            
            const doorMaterial = new THREE.MeshStandardMaterial({{ color: '#F39C12', roughness: 0.2, metalness: 0.3 }});
            const doorMesh = new THREE.Mesh(new THREE.BoxGeometry(width, 2.2, 0.08), doorMaterial);
            doorMesh.position.copy(center);
            doorMesh.castShadow = true;
            scene.add(doorMesh);
        }});
        
        // Create windows
        windowData.forEach(window => {{
            const start = new THREE.Vector3(window.start[0], 0, window.start[1]);
            const end = new THREE.Vector3(window.end[0], 0, window.end[1]);
            const center = new THREE.Vector3((start.x + end.x) / 2, 1.5, (start.z + end.z) / 2);
            const width = start.distanceTo(end);
            
            const glassMaterial = new THREE.MeshPhysicalMaterial({{ 
                color: '#88CCFF', 
                metalness: 0.9, 
                roughness: 0.1,
                transparent: true,
                opacity: 0.6,
                emissive: '#224466'
            }});
            const windowMesh = new THREE.Mesh(new THREE.BoxGeometry(width, 1.2, 0.05), glassMaterial);
            windowMesh.position.copy(center);
            windowMesh.castShadow = true;
            scene.add(windowMesh);
        }});
        
        // Create furniture
        Object.values(furnitureData).forEach(roomFurniture => {{
            if (roomFurniture.furniture) {{
                roomFurniture.furniture.forEach(item => {{
                    const material = new THREE.MeshStandardMaterial({{ color: item.color, roughness: 0.4, metalness: 0.1 }});
                    const geometry = new THREE.BoxGeometry(item.size[0], item.size[2], item.size[1]);
                    const furnitureMesh = new THREE.Mesh(geometry, material);
                    furnitureMesh.position.set(item.position[0], item.size[2] / 2, item.position[2]);
                    furnitureMesh.castShadow = true;
                    furnitureMesh.receiveShadow = true;
                    scene.add(furnitureMesh);
                    
                    // Add furniture label
                    const div = document.createElement('div');
                    div.textContent = item.name;
                    div.style.color = '#ddd';
                    div.style.fontSize = '10px';
                    div.style.backgroundColor = 'rgba(0,0,0,0.6)';
                    div.style.padding = '2px 6px';
                    div.style.borderRadius = '12px';
                    div.style.fontFamily = 'monospace';
                    const label = new CSS2DObject(div);
                    label.position.set(item.position[0], item.size[2] + 0.2, item.position[2]);
                    scene.add(label);
                }});
            }}
        }});
        
        // Add decorative columns at corners
        const cornerMaterial = new THREE.MeshStandardMaterial({{ color: '#FFAA66', metalness: 0.4, roughness: 0.2 }});
        const corners = [[0,0], [15,0], [15,12], [0,12]];
        corners.forEach(corner => {{
            const column = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.25, 3.0, 8), cornerMaterial);
            column.position.set(corner[0], 1.5, corner[1]);
            column.castShadow = true;
            scene.add(column);
        }});
        
        // Add floating particles for ambiance
        const particleCount = 500;
        const particlesGeometry = new THREE.BufferGeometry();
        const particlesPositions = new Float32Array(particleCount * 3);
        for (let i = 0; i < particleCount; i++) {{
            particlesPositions[i*3] = (Math.random() - 0.5) * 30;
            particlesPositions[i*3+1] = Math.random() * 6;
            particlesPositions[i*3+2] = (Math.random() - 0.5) * 25;
        }}
        particlesGeometry.setAttribute('position', new THREE.BufferAttribute(particlesPositions, 3));
        const particlesMaterial = new THREE.PointsMaterial({{ color: '#88AAFF', size: 0.05, transparent: true, opacity: 0.4 }});
        const particles = new THREE.Points(particlesGeometry, particlesMaterial);
        scene.add(particles);
        
        // Animation loop
        let time = 0;
        function animate() {{
            requestAnimationFrame(animate);
            time += 0.01;
            
            // Animate particles
            particles.rotation.y = time * 0.05;
            particles.rotation.x = Math.sin(time * 0.1) * 0.1;
            
            controls.update();
            renderer.render(scene, camera);
            labelRenderer.render(scene, camera);
        }}
        animate();
        
        // Handle window resize
        window.addEventListener('resize', onWindowResize, false);
        function onWindowResize() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
            labelRenderer.setSize(window.innerWidth, window.innerHeight);
        }}
        
        console.log('Vibrant 3D Model Loaded Successfully');
    </script>
</body>
</html>'''
        with open(output_path, 'w',encoding = 'utf-8') as f:
            f.write(html)
        return output_path    


