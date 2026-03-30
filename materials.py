"""
materials.py - Material Recommendation Engine with Furniture Database
"""

from typing import List, Dict
import json

class MaterialAnalyzer:
    def __init__(self):
        self.material_database = {
            'load_bearing_wall': [
                {'material': 'Red Brick', 'cost': 35, 'strength': 7.0, 'durability': 8, 
                 'justification': 'Excellent structural support with 7 MPa strength. Ideal for main walls.'},
                {'material': 'Precast Concrete', 'cost': 65, 'strength': 30.0, 'durability': 9,
                 'justification': 'High strength (30 MPa) for critical structural elements.'},
                {'material': 'Fly Ash Brick', 'cost': 22, 'strength': 5.5, 'durability': 7,
                 'justification': 'Eco-friendly and cost-effective for moderate loads.'}
            ],
            'partition_wall': [
                {'material': 'AAC Block', 'cost': 25, 'strength': 4.0, 'durability': 7,
                 'justification': 'Lightweight, excellent thermal insulation, fast construction.'},
                {'material': 'Fly Ash Brick', 'cost': 22, 'strength': 5.5, 'durability': 7,
                 'justification': 'Cost-effective and eco-friendly for non-load-bearing walls.'},
                {'material': 'Red Brick', 'cost': 35, 'strength': 7.0, 'durability': 8,
                 'justification': 'Traditional choice with good durability.'}
            ],
            'slab': [
                {'material': 'RCC', 'cost': 85, 'strength': 25.0, 'durability': 10,
                 'justification': 'Standard choice for floor slabs. Excellent durability and strength.'},
                {'material': 'Precast Concrete', 'cost': 65, 'strength': 30.0, 'durability': 9,
                 'justification': 'Factory quality, fast installation, high strength.'},
                {'material': 'Steel', 'cost': 120, 'strength': 250.0, 'durability': 9,
                 'justification': 'Highest strength, ideal for long spans.'}
            ],
            'column': [
                {'material': 'Steel', 'cost': 120, 'strength': 250.0, 'durability': 9,
                 'justification': 'Maximum strength for critical structural support.'},
                {'material': 'RCC', 'cost': 85, 'strength': 25.0, 'durability': 10,
                 'justification': 'Excellent durability and fire resistance.'},
                {'material': 'Precast Concrete', 'cost': 65, 'strength': 30.0, 'durability': 9,
                 'justification': 'Cost-effective with good strength.'}
            ]
        }
        
        self.furniture_database = {
            'living_room': [
                {'name': 'Sectional Sofa', 'size': [2.5, 0.9, 0.8], 'color': '#C44569', 'price': 45000,
                 'reason': 'Perfect for family gatherings and entertainment'},
                {'name': 'Coffee Table', 'size': [1.2, 0.6, 0.5], 'color': '#D9A066', 'price': 15000,
                 'reason': 'Central piece for magazines and beverages'},
                {'name': 'TV Unit', 'size': [1.8, 0.4, 0.6], 'color': '#B0A79E', 'price': 25000,
                 'reason': 'Entertainment center with storage'},
                {'name': 'Accent Chair', 'size': [0.8, 0.8, 0.9], 'color': '#F5CD79', 'price': 12000,
                 'reason': 'Additional seating with style'},
                {'name': 'Bookshelf', 'size': [1.0, 0.3, 2.0], 'color': '#B0A79E', 'price': 18000,
                 'reason': 'Display books and decorative items'}
            ],
            'bedroom': [
                {'name': 'King Bed', 'size': [2.0, 1.8, 0.5], 'color': '#C9AE8C', 'price': 55000,
                 'reason': 'Comfortable sleeping with storage below'},
                {'name': 'Wardrobe', 'size': [2.0, 0.6, 2.2], 'color': '#B0A79E', 'price': 35000,
                 'reason': 'Ample storage for clothes and accessories'},
                {'name': 'Nightstand', 'size': [0.5, 0.5, 0.6], 'color': '#C9AE8C', 'price': 8000,
                 'reason': 'Convenient bedside storage'},
                {'name': 'Dresser', 'size': [1.2, 0.5, 0.8], 'color': '#B0A79E', 'price': 20000,
                 'reason': 'Vanity area with mirror'},
                {'name': 'Vanity', 'size': [1.0, 0.4, 0.8], 'color': '#F8C291', 'price': 15000,
                 'reason': 'Makeup and grooming station'}
            ],
            'kitchen': [
                {'name': 'Kitchen Island', 'size': [2.0, 1.0, 0.9], 'color': '#E58C6F', 'price': 40000,
                 'reason': 'Extra counter space and storage'},
                {'name': 'Cabinets', 'size': [3.0, 0.6, 2.2], 'color': '#D9A066', 'price': 60000,
                 'reason': 'Essential kitchen storage'},
                {'name': 'Refrigerator', 'size': [0.8, 0.8, 1.8], 'color': '#BDC3C7', 'price': 45000,
                 'reason': 'Food preservation and storage'},
                {'name': 'Stove', 'size': [0.6, 0.6, 0.9], 'color': '#2C3E50', 'price': 30000,
                 'reason': 'Cooking essentials'},
                {'name': 'Dining Table', 'size': [1.5, 0.9, 0.8], 'color': '#C9AE8C', 'price': 25000,
                 'reason': 'Casual dining space'}
            ],
            'bathroom': [
                {'name': 'Vanity', 'size': [1.2, 0.5, 0.8], 'color': '#FFFFFF', 'price': 20000,
                 'reason': 'Sink and storage combination'},
                {'name': 'Toilet', 'size': [0.6, 0.4, 0.7], 'color': '#FFFFFF', 'price': 12000,
                 'reason': 'Essential sanitary fixture'},
                {'name': 'Shower', 'size': [1.0, 1.0, 2.2], 'color': '#95E1D3', 'price': 35000,
                 'reason': 'Daily bathing area'},
                {'name': 'Bathtub', 'size': [1.7, 0.7, 0.6], 'color': '#FFFFFF', 'price': 40000,
                 'reason': 'Relaxation and luxury'}
            ],
            'dining_room': [
                {'name': 'Dining Table', 'size': [1.8, 1.0, 0.8], 'color': '#C9AE8C', 'price': 30000,
                 'reason': 'Family dining experience'},
                {'name': 'Dining Chairs', 'size': [0.5, 0.5, 0.9], 'color': '#F9D56E', 'price': 8000,
                 'reason': 'Comfortable seating for meals'},
                {'name': 'Sideboard', 'size': [1.5, 0.4, 0.9], 'color': '#B0A79E', 'price': 22000,
                 'reason': 'Storage for dinnerware and serving items'}
            ],
            'office': [
                {'name': 'Desk', 'size': [1.5, 0.7, 0.8], 'color': '#6C5B7B', 'price': 20000,
                 'reason': 'Work surface for productivity'},
                {'name': 'Office Chair', 'size': [0.6, 0.6, 0.9], 'color': '#F8B195', 'price': 12000,
                 'reason': 'Ergonomic seating for long hours'},
                {'name': 'Bookshelf', 'size': [1.0, 0.3, 2.0], 'color': '#B0A79E', 'price': 18000,
                 'reason': 'Organize books and documents'},
                {'name': 'Filing Cabinet', 'size': [0.4, 0.5, 0.6], 'color': '#95A5A6', 'price': 10000,
                 'reason': 'Secure document storage'}
            ]
        }
        
        self.room_colors = {
            'living_room': '#FF6B6B',
            'bedroom': '#4ECDC4',
            'kitchen': '#FFE66D',
            'bathroom': '#95E1D3',
            'dining_room': '#F9D56E',
            'hallway': '#B83B5E',
            'office': '#6C5B7B',
            'default': '#C06C84'
        }
    
    def get_recommendations(self) -> Dict:
        """Get material recommendations for different elements"""
        recommendations = {}
        
        for element_type, materials in self.material_database.items():
            recommendations[element_type] = []
            for mat in materials:
                # Calculate score based on cost-strength tradeoff
                if element_type in ['load_bearing_wall', 'column']:
                    score = (mat['strength'] / 250) * 60 + (100 - mat['cost'] / 1.2) * 40
                else:
                    score = (100 - mat['cost'] / 1.2) * 60 + (mat['strength'] / 250) * 40
                
                recommendations[element_type].append({
                    'material': mat['material'],
                    'score': round(score, 1),
                    'cost': mat['cost'],
                    'strength': mat['strength'],
                    'durability': mat['durability'],
                    'justification': mat['justification']
                })
        
        return recommendations
    
    def suggest_furniture_placement(self, rooms: List[Dict]) -> Dict:
        """Suggest furniture placement for each room"""
        furniture_placement = {}
        
        for room in rooms:
            room_type = room['type']
            if room_type in self.furniture_database:
                furniture_items = self.furniture_database[room_type]
                room_center = room.get('centroid', [0, 0])
                bbox = room.get('bounding_box', [0, 0, 5, 5])
                
                suggestions = []
                for i, item in enumerate(furniture_items[:4]):  # Top 4 items per room
                    # Calculate position based on room layout
                    pos_x = room_center[0] + (i % 2 - 0.5) * bbox[2] * 0.3
                    pos_z = room_center[1] + (i // 2 - 0.5) * bbox[3] * 0.3
                    
                    suggestions.append({
                        'name': item['name'],
                        'size': item['size'],
                        'color': item['color'],
                        'price': item['price'],
                        'position': [pos_x, 0, pos_z],
                        'reason': item['reason']
                    })
                
                furniture_placement[room_type] = {
                    'furniture': suggestions,
                    'total_cost': sum([f['price'] for f in suggestions])
                }
        
        return furniture_placement
    
    def get_room_colors(self, rooms: List[Dict]) -> Dict:
        """Get vibrant colors for each room"""
        color_schemes = {}
        for room in rooms:
            room_type = room['type']
            color_schemes[room_type] = {
                'wall': self.room_colors.get(room_type, self.room_colors['default']),
                'floor': self.room_colors.get(room_type, self.room_colors['default'])
            }
        return color_schemes
    