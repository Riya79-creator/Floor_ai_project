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
        """Extract walls, rooms, doors, and windows with improved preprocessing"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None, None, None, None, "Could not load image"
            
            # Resize image to a standard size for consistent processing
            height, width = img.shape[:2]
            original_scale = self.scale
            
            if width > 1200:
                scale_factor = 1200 / width
                new_width = 1200
                new_height = int(height * scale_factor)
                img = cv2.resize(img, (new_width, new_height))
                self.scale = original_scale * scale_factor
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding for better line detection
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                            cv2.THRESH_BINARY_INV, 11, 2)
            
            # Remove small noise
            kernel = np.ones((2,2), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            # Detect edges
            edges = cv2.Canny(binary, 50, 150)
            
            # Dilate edges to connect broken lines
            kernel = np.ones((3,3), np.uint8)
            edges = cv2.dilate(edges, kernel, iterations=1)
            
            # Detect walls
            walls = self._detect_walls(edges)
            
            # Detect rooms
            rooms = self._detect_rooms(edges, img.shape)
            
            # Detect doors and windows
            doors, windows = self._detect_openings(binary)
            
            # Reset scale if changed
            self.scale = original_scale
            
            return walls, rooms, doors, windows, None
            
        except Exception as e:
            return None, None, None, None, str(e)
    
    def _detect_walls(self, edges: np.ndarray) -> List[Dict]:
        """Detect walls using Hough Line Transform with better parameters"""
        # More sensitive parameters for better wall detection
        lines = cv2.HoughLinesP(
            edges, 
            rho=1, 
            theta=np.pi/180, 
            threshold=30,  # Reduced from 50
            minLineLength=25,  # Reduced from 40
            maxLineGap=15  # Increased from 10
        )
        
        walls = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                length = np.hypot(x2 - x1, y2 - y1) * self.scale
                
                # Filter walls by length - include shorter walls
                if length > 0.3:  # Reduced from 0.5
                    walls.append({
                        'start': (float(x1 * self.scale), float(y1 * self.scale)),
                        'end': (float(x2 * self.scale), float(y2 * self.scale)),
                        'pixel_start': (x1, y1),
                        'pixel_end': (x2, y2),
                        'length': float(length)
                    })
        
        # Sort walls by length
        walls.sort(key=lambda x: x['length'], reverse=True)
        
        # Only merge walls if they're very close and aligned
        walls = self._merge_walls_smart(walls)
        
        return walls
    
    def _merge_walls_smart(self, walls: List[Dict], angle_threshold: float = 10, 
                           distance_threshold: float = 0.2) -> List[Dict]:
        """Intelligently merge walls that are collinear and close"""
        if not walls:
            return walls
            
        merged = []
        used = [False] * len(walls)
        
        for i in range(len(walls)):
            if used[i]:
                continue
                
            current = walls[i]
            current_angle = self._get_wall_angle(current)
            merged_points = [(current['start'], current['end'])]
            used[i] = True
            
            for j in range(i + 1, len(walls)):
                if used[j]:
                    continue
                    
                wall_angle = self._get_wall_angle(walls[j])
                angle_diff = abs(current_angle - wall_angle)
                angle_diff = min(angle_diff, 180 - angle_diff)
                
                if angle_diff > angle_threshold:
                    continue
                
                # Check if walls are close enough
                if self._are_walls_aligned(current, walls[j], distance_threshold):
                    merged_points.append((walls[j]['start'], walls[j]['end']))
                    used[j] = True
            
            if len(merged_points) > 1:
                merged_wall = self._combine_multiple_walls(merged_points)
                merged.append(merged_wall)
            else:
                merged.append(current)
        
        return merged
    
    def _get_wall_angle(self, wall: Dict) -> float:
        """Calculate wall angle in degrees"""
        dx = wall['end'][0] - wall['start'][0]
        dy = wall['end'][1] - wall['start'][1]
        if dx == 0 and dy == 0:
            return 0
        angle = np.degrees(np.arctan2(dy, dx))
        return angle % 180
    
    def _are_walls_aligned(self, wall1: Dict, wall2: Dict, threshold: float) -> bool:
        """Check if walls are aligned and close enough to merge"""
        # Get endpoints
        points1 = [wall1['start'], wall1['end']]
        points2 = [wall2['start'], wall2['end']]
        
        # Check distance between closest endpoints
        min_dist = float('inf')
        for p1 in points1:
            for p2 in points2:
                dist = np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
                min_dist = min(min_dist, dist)
        
        return min_dist < threshold
    
    def _combine_multiple_walls(self, wall_points: List[Tuple]) -> Dict:
        """Combine multiple wall segments into one"""
        all_points = []
        for start, end in wall_points:
            all_points.append(start)
            all_points.append(end)
        
        # Find min and max points
        all_points.sort()
        start = all_points[0]
        end = all_points[-1]
        length = np.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        
        return {
            'start': start,
            'end': end,
            'length': float(length)
        }
    
    def _detect_rooms(self, edges: np.ndarray, shape: Tuple) -> List[Dict]:
        """Detect rooms with better contour processing"""
        # Use morphological operations to close gaps
        kernel = np.ones((3,3), np.uint8)
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
        dilated = cv2.dilate(closed, kernel, iterations=1)
        
        # Find contours with hierarchy to get internal rooms
        contours, hierarchy = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        rooms = []
        min_room_area = 2000  # Reduced from 5000 for better detection
        
        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            
            # Filter by area and aspect ratio
            if area > min_room_area and area < 100000:  # Upper bound to filter noise
                perimeter = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.01 * perimeter, True)  # More precise approximation
                
                # Skip if too few points
                if len(approx) < 3:
                    continue
                
                # Convert to world coordinates
                polygon = [(float(p[0][0] * self.scale), float(p[0][1] * self.scale)) for p in approx]
                
                # Calculate centroid
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = float(M["m10"] / M["m00"] * self.scale)
                    cy = float(M["m01"] / M["m00"] * self.scale)
                else:
                    cx, cy = polygon[0] if polygon else (0, 0)
                
                # Get bounding box
                bbox = cv2.boundingRect(cnt)
                
                # Determine room type with better logic
                bbox_area = bbox[2] * bbox[3]
                aspect_ratio = bbox[2] / bbox[3] if bbox[3] > 0 else 1
                
                # Room type classification
                if area > 25000:
                    room_type = 'living_room'
                elif 15000 < area <= 25000:
                    room_type = 'bedroom'
                elif 8000 < area <= 15000:
                    room_type = 'kitchen' if aspect_ratio < 1.2 else 'dining_room'
                elif area <= 8000:
                    room_type = 'bathroom' if aspect_ratio < 1.3 else 'hallway'
                else:
                    room_type = 'office'
                
                rooms.append({
                    'id': f'room_{i}',
                    'type': room_type,
                    'name': room_type.replace('_', ' ').title(),
                    'area': float(area * self.scale * self.scale),
                    'polygon': polygon,
                    'centroid': [cx, cy],
                    'bounding_box': [
                        float(bbox[0] * self.scale), 
                        float(bbox[1] * self.scale), 
                        float(bbox[2] * self.scale), 
                        float(bbox[3] * self.scale)
                    ]
                })
        
        return rooms
    
    def _detect_openings(self, binary: np.ndarray) -> Tuple[List, List]:
        """Detect doors and windows using contour detection"""
        edges_thick = cv2.Canny(binary, 30, 100)
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
                
                position = [(x + w/2) * self.scale, (y + h/2) * self.scale]
                start = [x * self.scale, y * self.scale]
                end = [(x + w) * self.scale, (y + h) * self.scale]
                
                if aspect > 1.5:
                    windows.append({
                        'position': position,
                        'width': float(w * self.scale),
                        'height': float(h * self.scale),
                        'start': start,
                        'end': end
                    })
                else:
                    doors.append({
                        'position': position,
                        'width': float(w * self.scale),
                        'height': float(h * self.scale),
                        'start': start,
                        'end': end
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
    