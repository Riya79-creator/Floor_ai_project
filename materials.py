"""
materials.py - Material Recommendation Engine
Complete error-free version with proper JSON serialization
"""

from typing import List, Dict
import json

class MaterialDatabase:
    """Database of construction materials with properties"""
    
    def __init__(self):
        self.materials = {
            'AAC Blocks': {
                'cost_per_m2': 25.0,
                'strength_mpa': 4.0,
                'durability': 7,
                'density_kg_m3': 600,
                'thermal': 0.18,
                'best_for': ['partition', 'non_load_bearing'],
                'pros': 'Lightweight, good insulation, fast construction',
                'cons': 'Lower strength, not for heavy loads'
            },
            'Red Brick': {
                'cost_per_m2': 35.0,
                'strength_mpa': 7.0,
                'durability': 8,
                'density_kg_m3': 1800,
                'thermal': 0.6,
                'best_for': ['load_bearing', 'exterior'],
                'pros': 'Strong, durable, widely available',
                'cons': 'Heavy, slower construction'
            },
            'RCC': {
                'cost_per_m2': 85.0,
                'strength_mpa': 25.0,
                'durability': 10,
                'density_kg_m3': 2400,
                'thermal': 1.7,
                'best_for': ['slab', 'column', 'foundation'],
                'pros': 'Very strong, earthquake resistant',
                'cons': 'Expensive, requires curing time'
            },
            'Steel Frame': {
                'cost_per_m2': 120.0,
                'strength_mpa': 250.0,
                'durability': 9,
                'density_kg_m3': 7850,
                'thermal': 45.0,
                'best_for': ['long_span', 'column', 'beam'],
                'pros': 'Highest strength, long spans possible',
                'cons': 'Most expensive, requires fireproofing'
            },
            'Hollow Concrete Block': {
                'cost_per_m2': 30.0,
                'strength_mpa': 5.0,
                'durability': 8,
                'density_kg_m3': 1200,
                'thermal': 0.4,
                'best_for': ['load_bearing', 'long_span'],
                'pros': 'Good strength-to-weight, economical',
                'cons': 'Requires skilled labor'
            },
            'Fly Ash Brick': {
                'cost_per_m2': 22.0,
                'strength_mpa': 5.5,
                'durability': 7,
                'density_kg_m3': 1400,
                'thermal': 0.45,
                'best_for': ['partition', 'non_load_bearing'],
                'pros': 'Eco-friendly, consistent quality, cheap',
                'cons': 'Lower durability than red brick'
            },
            'Precast Concrete': {
                'cost_per_m2': 65.0,
                'strength_mpa': 30.0,
                'durability': 9,
                'density_kg_m3': 2400,
                'thermal': 1.6,
                'best_for': ['structural_wall', 'slab', 'fast_build'],
                'pros': 'Factory quality, fast installation',
                'cons': 'Transportation cost, less flexible'
            }
        }
    
    def get_material(self, name: str) -> Dict:
        """Get material by name"""
        return self.materials.get(name, {})


class MaterialRecommender:
    """Recommends materials based on cost-strength tradeoff"""
    
    def __init__(self, db: MaterialDatabase):
        self.db = db
    
    def recommend_for_element(self, element_type: str, span_length: float = 0) -> List[Dict]:
        """
        Recommend top 3 materials for a structural element
        Returns list with material details and scores
        """
        
        # Define which materials are suitable for each element type
        suitability = {
            'load_bearing_wall': ['Red Brick', 'Hollow Concrete Block', 'Precast Concrete'],
            'partition_wall': ['Fly Ash Brick', 'AAC Blocks', 'Red Brick'],
            'slab': ['RCC', 'Precast Concrete', 'Steel Frame'],
            'column': ['RCC', 'Steel Frame', 'Precast Concrete'],
            'beam': ['RCC', 'Steel Frame'],
            'foundation': ['RCC', 'Precast Concrete']
        }
        
        suitable_materials = suitability.get(element_type, ['Red Brick', 'RCC'])
        
        candidates = []
        for material in suitable_materials:
            mat_data = self.db.get_material(material)
            if not mat_data:
                continue
            
            # Calculate tradeoff score
            score = self._calculate_score(mat_data, element_type, span_length)
            
            candidates.append({
                'material': str(material),
                'score': float(round(score, 1)),
                'cost': float(mat_data['cost_per_m2']),
                'strength': float(mat_data['strength_mpa']),
                'durability': int(mat_data['durability']),
                'pros': str(mat_data['pros']),
                'cons': str(mat_data['cons']),
                'justification': str(self._generate_justification(material, mat_data, element_type, span_length))
            })
        
        # Sort by score descending
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        return candidates[:3]
    
    def _calculate_score(self, material: Dict, element_type: str, span_length: float) -> float:
        """Calculate weighted tradeoff score"""
        
        # Different weights based on element type
        if element_type in ['load_bearing_wall', 'column', 'foundation']:
            # Structural elements: strength matters more
            strength_weight = 0.5
            cost_weight = 0.3
            durability_weight = 0.2
        elif element_type == 'slab':
            # Slabs: strength and cost balanced, span matters
            strength_weight = 0.4
            cost_weight = 0.3
            durability_weight = 0.2
        else:
            # Partition walls: cost matters most
            strength_weight = 0.2
            cost_weight = 0.6
            durability_weight = 0.2
        
        # Normalize scores (0-100)
        # Cost: lower is better (max $120/m²)
        cost_score = max(0.0, 100.0 - (material['cost_per_m2'] / 120.0 * 100.0))
        
        # Strength: higher is better (max 250 MPa for steel)
        strength_score = min(100.0, (material['strength_mpa'] / 250.0) * 100.0)
        
        # Durability: already 1-10 scale, multiply by 10
        durability_score = float(material['durability'] * 10)
        
        # Span bonus/penalty
        span_factor = 1.0
        if span_length > 5 and element_type == 'slab':
            if material['strength_mpa'] > 20:
                span_factor = 1.2
            else:
                span_factor = 0.7
        
        total = (cost_score * cost_weight + 
                 strength_score * strength_weight + 
                 durability_score * durability_weight) * span_factor
        
        return float(total)
    
    def _generate_justification(self, material: str, data: Dict, element_type: str, span: float) -> str:
        """Generate human-readable justification for recommendation"""
        
        if element_type == 'load_bearing_wall':
            if material == 'Red Brick':
                return f"Red Brick offers excellent compressive strength ({data['strength_mpa']} MPa) at moderate cost (${data['cost_per_m2']}/m²). Its durability ({data['durability']}/10) ensures long-term structural integrity for load-bearing applications."
            elif material == 'Hollow Concrete Block':
                return f"Hollow Concrete Block provides good strength ({data['strength_mpa']} MPa) while being lighter than solid blocks. Cost-effective at ${data['cost_per_m2']}/m² for load-bearing walls."
            else:
                return f"{material} delivers high strength ({data['strength_mpa']} MPa) for critical load paths, though at higher cost (${data['cost_per_m2']}/m²)."
        
        elif element_type == 'partition_wall':
            if material == 'Fly Ash Brick':
                return f"Fly Ash Brick is the most economical choice (${data['cost_per_m2']}/m²) for non-structural walls. It provides adequate strength and is environmentally friendly."
            elif material == 'AAC Blocks':
                return f"AAC Blocks are lightweight and provide excellent thermal insulation. At ${data['cost_per_m2']}/m², they're ideal for partition walls where strength requirements are lower."
            else:
                return f"{material} can be used for partitions but may be over-specified. Consider cost-saving alternatives."
        
        elif element_type == 'slab':
            if span > 5:
                if material == 'Steel Frame':
                    return f"For this {span:.1f}m span, Steel Frame is optimal despite higher cost (${data['cost_per_m2']}/m²). Its high strength-to-weight ratio enables the long span without intermediate columns."
                elif material == 'RCC':
                    return f"RCC (${data['cost_per_m2']}/m²) can handle this {span:.1f}m span but may need reinforcement. Good balance of cost and performance."
            else:
                if material == 'RCC':
                    return f"RCC is the standard choice for slabs at ${data['cost_per_m2']}/m². Provides excellent durability ({data['durability']}/10) and strength."
        
        return f"{material} recommended for {element_type}. {data['pros']} Cost: ${data['cost_per_m2']}/m², Strength: {data['strength_mpa']} MPa."