"""
parser.py - AI-based Floor Plan Parser with Wall, Door, Window, and Room Detection
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional

class FloorPlanParser:
    def __init__(self):
        self.scale = 0.05  # 20 pixels = 1 meter
        self.grid_size = 0.2
        self.wall_thickness = 0.2
        
    def parse_floor_plan(self, image_path: str) -> Tuple[List, List, List, List, Optional[str]]:
        """Extract walls, rooms, doors, and windows from floor plan image"""
        img = cv2.imread(image_path)
        if img is None:
            return None, None, None, None, "Could not load image"
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        # Detect walls using Hough Lines
        walls = self._detect_walls(edges)
        
        # Detect rooms from contours
        rooms = self._detect_rooms(edges, img.shape)
        
        # Detect doors and windows
        doors, windows = self._detect_openings(blurred)
        
        return walls, rooms, doors, windows, None
    
    def _detect_walls(self, edges: np.ndarray) -> List[Dict]:
        """Detect walls using Hough Line Transform"""
        lines = cv2.HoughLinesP(
            edges, 
            rho=1, 
            theta=np.pi/180, 
            threshold=50, 
            minLineLength=40, 
            maxLineGap=10
        )
        
        walls = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                length = np.hypot(x2 - x1, y2 - y1) * self.scale
                
                if length > 0.5:  # Filter tiny walls
                    walls.append({
                        'start': (float(x1 * self.scale), float(y1 * self.scale)),
                        'end': (float(x2 * self.scale), float(y2 * self.scale)),
                        'length': float(length)
                    })
        
        # Merge nearby walls
        walls = self._merge_walls(walls)
        
        return walls
    
    def _merge_walls(self, walls: List[Dict], threshold: float = 0.3) -> List[Dict]:
        """Merge nearby walls to simplify the model"""
        if not walls:
            return walls
            
        merged = []
        used = [False] * len(walls)
        
        for i in range(len(walls)):
            if used[i]:
                continue
                
            current = walls[i]
            merged_wall = current.copy()
            used[i] = True
            
            for j in range(i + 1, len(walls)):
                if used[j]:
                    continue
                    
                if self._are_walls_close(current, walls[j], threshold):
                    merged_wall = self._combine_walls(merged_wall, walls[j])
                    used[j] = True
            
            merged.append(merged_wall)
        
        return merged
    
    def _are_walls_close(self, wall1: Dict, wall2: Dict, threshold: float) -> bool:
        """Check if two walls are close enough to merge"""
        points1 = [wall1['start'], wall1['end']]
        points2 = [wall2['start'], wall2['end']]
        
        for p1 in points1:
            for p2 in points2:
                dist = np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
                if dist < threshold:
                    return True
        return False
    
    def _combine_walls(self, wall1: Dict, wall2: Dict) -> Dict:
        """Combine two walls into one"""
        all_points = [wall1['start'], wall1['end'], wall2['start'], wall2['end']]
        all_points.sort()
        
        start = all_points[0]
        end = all_points[-1]
        length = np.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        
        return {
            'start': start,
            'end': end,
            'length': length
        }
    
    def _detect_rooms(self, edges: np.ndarray, shape: Tuple) -> List[Dict]:
        """Detect rooms from contours"""
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        rooms = []
        room_types = ['living_room', 'bedroom', 'kitchen', 'bathroom', 'dining_room', 'hallway', 'office']
        
        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            if area > 5000:  # Minimum room area
                perimeter = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * perimeter, True)
                polygon = [(float(p[0][0] * self.scale), float(p[0][1] * self.scale)) for p in approx]
                
                # Calculate centroid
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = float(M["m10"] / M["m00"] * self.scale)
                    cy = float(M["m01"] / M["m00"] * self.scale)
                else:
                    cx, cy = polygon[0]
                
                # Determine room type based on area and aspect ratio
                bbox = cv2.boundingRect(cnt)
                aspect_ratio = bbox[2] / bbox[3] if bbox[3] > 0 else 1
                
                if area > 20000:
                    room_type = 'living_room'
                elif aspect_ratio > 1.5:
                    room_type = 'hallway'
                elif area < 8000:
                    room_type = 'bathroom'
                else:
                    room_type = room_types[i % len(room_types)]
                
                rooms.append({
                    'id': f'room_{i}',
                    'type': room_type,
                    'name': room_type.replace('_', ' ').title(),
                    'area': float(area * self.scale * self.scale),
                    'polygon': polygon,
                    'centroid': [cx, cy],
                    'bounding_box': [
                        bbox[0] * self.scale, 
                        bbox[1] * self.scale, 
                        bbox[2] * self.scale, 
                        bbox[3] * self.scale
                    ]
                })
        
        return rooms
    
    def _detect_openings(self, blurred: np.ndarray) -> Tuple[List, List]:
        """Detect doors and windows using edge detection"""
        edges_thick = cv2.Canny(blurred, 30, 100)
        kernel = np.ones((5,5), np.uint8)
        edges_thick = cv2.dilate(edges_thick, kernel, iterations=1)
        
        openings, _ = cv2.findContours(edges_thick, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        doors = []
        windows = []
        
        for opening in openings:
            area = cv2.contourArea(opening)
            if 500 < area < 5000:
                x, y, w, h = cv2.boundingRect(opening)
                aspect = w / h if h > 0 else 0
                
                if aspect > 1.5:
                    windows.append({
                        'position': [(x + w/2) * self.scale, (y + h/2) * self.scale],
                        'width': w * self.scale,
                        'height': h * self.scale,
                        'start': [x * self.scale, y * self.scale],
                        'end': [(x + w) * self.scale, (y + h) * self.scale]
                    })
                else:
                    doors.append({
                        'position': [(x + w/2) * self.scale, (y + h/2) * self.scale],
                        'width': w * self.scale,
                        'height': h * self.scale,
                        'start': [x * self.scale, y * self.scale],
                        'end': [(x + w) * self.scale, (y + h) * self.scale]
                    })
        
        return doors, windows
    
    def classify_load_bearing(self, walls: List[Dict]) -> List[Dict]:
        """Classify walls as load bearing based on position and length"""
        if not walls:
            return walls
        
        xs = [w['start'][0] for w in walls] + [w['end'][0] for w in walls]
        ys = [w['start'][1] for w in walls] + [w['end'][1] for w in walls]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        for wall in walls:
            start, end = wall['start'], wall['end']
            is_exterior = (abs(start[0] - min_x) < 0.5 or abs(start[0] - max_x) < 0.5 or
                          abs(start[1] - min_y) < 0.5 or abs(start[1] - max_y) < 0.5 or
                          abs(end[0] - min_x) < 0.5 or abs(end[0] - max_x) < 0.5 or
                          abs(end[1] - min_y) < 0.5 or abs(end[1] - max_y) < 0.5)
            wall['is_load_bearing'] = is_exterior or wall['length'] > 6.0
        
        return walls
    
    def get_fallback_data(self):
        """Provide fallback data when detection fails"""
        walls = [
            {'start': (0,0), 'end': (15,0), 'length': 15},
            {'start': (15,0), 'end': (15,12), 'length': 12},
            {'start': (15,12), 'end': (0,12), 'length': 15},
            {'start': (0,12), 'end': (0,0), 'length': 12},
            {'start': (7.5,0), 'end': (7.5,12), 'length': 12},
            {'start': (3,0), 'end': (3,4), 'length': 4},
            {'start': (3,4), 'end': (7.5,4), 'length': 4.5},
            {'start': (10.5,0), 'end': (10.5,4), 'length': 4},
            {'start': (10.5,4), 'end': (15,4), 'length': 4.5},
            {'start': (7.5,6), 'end': (15,6), 'length': 7.5},
            {'start': (0,8), 'end': (3,8), 'length': 3},
        ]
        
        rooms = [
            {'id': 'room_0', 'type': 'bedroom', 'name': 'Bedroom 1', 'area': 12, 
             'polygon': [(0,0),(3,0),(3,4),(0,4)], 'centroid': [1.5, 2]},
            {'id': 'room_1', 'type': 'bedroom', 'name': 'Bedroom 2', 'area': 18, 
             'polygon': [(10.5,0),(15,0),(15,4),(10.5,4)], 'centroid': [12.75, 2]},
            {'id': 'room_2', 'type': 'bedroom', 'name': 'Bedroom 3', 'area': 12, 
             'polygon': [(0,4),(3,4),(3,8),(0,8)], 'centroid': [1.5, 6]},
            {'id': 'room_3', 'type': 'kitchen', 'name': 'Kitchen', 'area': 45, 
             'polygon': [(7.5,6),(15,6),(15,12),(7.5,12)], 'centroid': [11.25, 9]},
            {'id': 'room_4', 'type': 'living_room', 'name': 'Living Room', 'area': 18, 
             'polygon': [(3,4),(7.5,4),(7.5,6),(3,6)], 'centroid': [5.25, 5]},
            {'id': 'room_5', 'type': 'hallway', 'name': 'Foyer', 'area': 12, 
             'polygon': [(0,8),(3,8),(3,12),(0,12)], 'centroid': [1.5, 10]},
            {'id': 'room_6', 'type': 'bathroom', 'name': 'Bathroom', 'area': 12, 
             'polygon': [(7.5,0),(10.5,0),(10.5,4),(7.5,4)], 'centroid': [9, 2]},
        ]
        
        doors = []
        windows = []
        
        return walls, rooms, doors, windows