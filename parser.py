"""
parser.py - Floor Plan Image Parsing
COMPLETELY FIXED - No NumPy types in output
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple

class FloorPlanParser:
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.image = None
        self.gray = None
        self.scale = 0.05
        
    def parse(self) -> Tuple[bool, List[Dict], List[Dict], List[Dict], str]:
        try:
            self.image = cv2.imread(self.image_path)
            if self.image is None:
                return False, [], [], [], "Could not load image"
            
            self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(self.gray, (5, 5), 0)
            _, binary = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY_INV)
            edges = cv2.Canny(binary, 50, 150)
            lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, 
                                     threshold=50, minLineLength=50, maxLineGap=10)
            
            if lines is None:
                return False, [], [], [], "No walls detected"
            
            walls = self._lines_to_walls(lines)
            contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            rooms = self._contours_to_rooms(contours)
            openings = self._detect_openings(edges, lines)
            
            return True, walls, rooms, openings, ""
            
        except Exception as e:
            return False, [], [], [], str(e)
    
    def _lines_to_walls(self, lines) -> List[Dict]:
        walls = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            if abs(angle) < 10 or abs(angle - 180) < 10:
                y = (y1 + y2) // 2
                x1, x2 = min(x1, x2), max(x1, x2)
                y1 = y2 = y
            elif abs(abs(angle) - 90) < 10:
                x = (x1 + x2) // 2
                y1, y2 = min(y1, y2), max(y1, y2)
                x1 = x2 = x
            
            # CRITICAL: Convert EVERYTHING to Python float
            x1_m = float(x1 * self.scale)
            y1_m = float(y1 * self.scale)
            x2_m = float(x2 * self.scale)
            y2_m = float(y2 * self.scale)
            length = float(np.hypot(x2_m - x1_m, y2_m - y1_m))
            
            walls.append({
                'start': (x1_m, y1_m),
                'end': (x2_m, y2_m),
                'length': length,
                'thickness': 0.2,
                'is_load_bearing': False  # Python bool, not NumPy
            })
        
        walls = self._merge_nearby_walls(walls)
        return walls
    
    def _merge_nearby_walls(self, walls, threshold=0.3):
        merged = []
        used = [False] * len(walls)
        
        for i, wall1 in enumerate(walls):
            if used[i]:
                continue
            current = wall1.copy()
            for j, wall2 in enumerate(walls):
                if i != j and not used[j]:
                    if self._are_collinear(current, wall2, threshold):
                        current = self._merge_walls(current, wall2)
                        used[j] = True
            merged.append(current)
            used[i] = True
        return merged
    
    def _are_collinear(self, wall1, wall2, threshold):
        start1, end1 = wall1['start'], wall1['end']
        start2, end2 = wall2['start'], wall2['end']
        
        if abs(start1[1] - end1[1]) < 0.1 and abs(start2[1] - end2[1]) < 0.1:
            diff = abs(start1[1] - start2[1])
            return bool(diff < threshold)  # Convert to Python bool
        elif abs(start1[0] - end1[0]) < 0.1 and abs(start2[0] - end2[0]) < 0.1:
            diff = abs(start1[0] - start2[0])
            return bool(diff < threshold)  # Convert to Python bool
        return False
    
    def _merge_walls(self, wall1, wall2):
        points = [wall1['start'], wall1['end'], wall2['start'], wall2['end']]
        
        if abs(wall1['start'][1] - wall1['end'][1]) < 0.1:
            x_coords = [p[0] for p in points]
            y = wall1['start'][1]
            return {
                'start': (float(min(x_coords)), float(y)),
                'end': (float(max(x_coords)), float(y)),
                'length': float(max(x_coords) - min(x_coords)),
                'thickness': 0.2,
                'is_load_bearing': bool(wall1['is_load_bearing'] or wall2['is_load_bearing'])
            }
        else:
            y_coords = [p[1] for p in points]
            x = wall1['start'][0]
            return {
                'start': (float(x), float(min(y_coords))),
                'end': (float(x), float(max(y_coords))),
                'length': float(max(y_coords) - min(y_coords)),
                'thickness': 0.2,
                'is_load_bearing': bool(wall1['is_load_bearing'] or wall2['is_load_bearing'])
            }
    
    def _contours_to_rooms(self, contours) -> List[Dict]:
        rooms = []
        room_names = ['Living Room', 'Bedroom', 'Kitchen', 'Bathroom', 'Hallway', 'Dining Room']
        
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area < 1000:
                continue
            
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            polygon = []
            for p in approx:
                polygon.append((float(p[0][0] * self.scale), float(p[0][1] * self.scale)))
            
            M = cv2.moments(contour)
            if M['m00'] != 0:
                cx = float(M['m10'] / M['m00'] * self.scale)
                cy = float(M['m01'] / M['m00'] * self.scale)
            else:
                cx, cy = 0.0, 0.0
            
            rooms.append({
                'id': f'room_{i}',
                'name': room_names[i % len(room_names)],
                'polygon': polygon,
                'area': float(area * self.scale * self.scale),
                'centroid': (cx, cy)
            })
        
        return rooms
    
    def _detect_openings(self, edges, lines) -> List[Dict]:
        openings = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            length = np.hypot(x2 - x1, y2 - y1)
            
            gap_count = 0
            for t in np.arange(0, length, 10):
                x = int(x1 + t * (x2 - x1) / length)
                y = int(y1 + t * (y2 - y1) / length)
                
                if 0 <= y < edges.shape[0] and 0 <= x < edges.shape[1] and edges[y, x] < 50:
                    gap_count += 1
                else:
                    if gap_count > 5:
                        openings.append({
                            'position': (float(x * self.scale), float(y * self.scale)),
                            'width': float(gap_count * self.scale),
                            'type': 'door' if gap_count < 15 else 'window'
                        })
                    gap_count = 0
        return openings
    
    def classify_load_bearing_walls(self, walls) -> List[Dict]:
        if not walls:
            return walls
        
        all_x = []
        all_y = []
        for w in walls:
            all_x.append(float(w['start'][0]))
            all_x.append(float(w['end'][0]))
            all_y.append(float(w['start'][1]))
            all_y.append(float(w['end'][1]))
        
        min_x = float(min(all_x))
        max_x = float(max(all_x))
        min_y = float(min(all_y))
        max_y = float(max(all_y))
        center_x = float((min_x + max_x) / 2)
        
        for wall in walls:
            start = wall['start']
            end = wall['end']
            
            # CRITICAL: Convert each comparison to Python bool
            is_exterior = bool(
                abs(start[0] - min_x) < 0.2 or abs(start[0] - max_x) < 0.2 or
                abs(end[0] - min_x) < 0.2 or abs(end[0] - max_x) < 0.2 or
                abs(start[1] - min_y) < 0.2 or abs(start[1] - max_y) < 0.2 or
                abs(end[1] - min_y) < 0.2 or abs(end[1] - max_y) < 0.2
            )
            
            is_center = bool(
                (abs(start[0] - center_x) < 0.3 and abs(end[0] - center_x) < 0.3) or
                (abs(start[1] - center_x) < 0.3 and abs(end[1] - center_x) < 0.3)
            )
            
            is_long = bool(wall['length'] > 6.0)
            
            # Final conversion to Python bool
            wall['is_load_bearing'] = bool(is_exterior or is_center or is_long)
        
        return walls
    
    def detect_spans(self, rooms) -> List[Dict]:
        spans = []
        for room in rooms:
            polygon = room.get('polygon', [])
            if not polygon:
                continue
            
            xs = [float(p[0]) for p in polygon]
            ys = [float(p[1]) for p in polygon]
            
            width = float(max(xs) - min(xs))
            height = float(max(ys) - min(ys))
            
            if width > 5.0:
                spans.append({
                    'room': str(room['name']),
                    'dimension': 'width',
                    'length': float(width),
                    'recommendation': 'Consider intermediate column or steel reinforcement'
                })
            
            if height > 5.0:
                spans.append({
                    'room': str(room['name']),
                    'dimension': 'height',
                    'length': float(height),
                    'recommendation': 'Increase slab thickness or add beam support'
                })
        return spans
    
    def get_manual_fallback(self):
        walls = [
            {'start': (0.0, 0.0), 'end': (15.0, 0.0), 'length': 15.0, 'thickness': 0.2, 'is_load_bearing': True},
            {'start': (15.0, 0.0), 'end': (15.0, 12.0), 'length': 12.0, 'thickness': 0.2, 'is_load_bearing': True},
            {'start': (15.0, 12.0), 'end': (0.0, 12.0), 'length': 15.0, 'thickness': 0.2, 'is_load_bearing': True},
            {'start': (0.0, 12.0), 'end': (0.0, 0.0), 'length': 12.0, 'thickness': 0.2, 'is_load_bearing': True},
            {'start': (7.5, 0.0), 'end': (7.5, 12.0), 'length': 12.0, 'thickness': 0.2, 'is_load_bearing': True},
            {'start': (3.0, 0.0), 'end': (3.0, 4.0), 'length': 4.0, 'thickness': 0.15, 'is_load_bearing': False},
            {'start': (3.0, 4.0), 'end': (7.5, 4.0), 'length': 4.5, 'thickness': 0.15, 'is_load_bearing': False},
            {'start': (10.5, 0.0), 'end': (10.5, 4.0), 'length': 4.0, 'thickness': 0.15, 'is_load_bearing': False},
            {'start': (10.5, 4.0), 'end': (15.0, 4.0), 'length': 4.5, 'thickness': 0.15, 'is_load_bearing': False},
            {'start': (7.5, 6.0), 'end': (15.0, 6.0), 'length': 7.5, 'thickness': 0.15, 'is_load_bearing': False},
            {'start': (0.0, 8.0), 'end': (3.0, 8.0), 'length': 3.0, 'thickness': 0.15, 'is_load_bearing': False},
        ]
        
        rooms = [
            {'id': 'bedroom1', 'name': 'Bedroom 1', 'polygon': [(0.0,0.0), (3.0,0.0), (3.0,4.0), (0.0,4.0)], 'area': 12.0, 'centroid': (1.5, 2.0)},
            {'id': 'bedroom2', 'name': 'Bedroom 2', 'polygon': [(10.5,0.0), (15.0,0.0), (15.0,4.0), (10.5,4.0)], 'area': 18.0, 'centroid': (12.75, 2.0)},
            {'id': 'bedroom3', 'name': 'Bedroom 3', 'polygon': [(0.0,4.0), (3.0,4.0), (3.0,8.0), (0.0,8.0)], 'area': 12.0, 'centroid': (1.5, 6.0)},
            {'id': 'kitchen', 'name': 'Kitchen', 'polygon': [(7.5,6.0), (15.0,6.0), (15.0,12.0), (7.5,12.0)], 'area': 45.0, 'centroid': (11.25, 9.0)},
            {'id': 'living', 'name': 'Living Room', 'polygon': [(3.0,4.0), (7.5,4.0), (7.5,6.0), (3.0,6.0)], 'area': 18.0, 'centroid': (5.25, 5.0)},
            {'id': 'foyer', 'name': 'Foyer', 'polygon': [(0.0,8.0), (3.0,8.0), (3.0,12.0), (0.0,12.0)], 'area': 12.0, 'centroid': (1.5, 10.0)},
            {'id': 'bathroom', 'name': 'Bathroom', 'polygon': [(7.5,0.0), (10.5,0.0), (10.5,4.0), (7.5,4.0)], 'area': 12.0, 'centroid': (9.0, 2.0)},
        ]
        
        return walls, rooms