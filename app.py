from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import uuid
import numpy as np
from werkzeug.utils import secure_filename

from parser import FloorPlanParser
from model3d import ThreeDModelBuilder
from materials import MaterialAnalyzer

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(STATIC_FOLDER, 'models'), exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ================== IMPORTANT FIX ==================
def convert_types(obj):
    """Recursively convert NumPy types to Python native types"""
    if isinstance(obj, dict):
        return {k: convert_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_types(i) for i in obj]
    elif isinstance(obj, tuple):
        return [convert_types(i) for i in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif hasattr(obj, "item"):  # handles generic numpy scalars
        return obj.item()
    return obj
# ==================================================

parser = FloorPlanParser()
model_builder = ThreeDModelBuilder()
material_analyzer = MaterialAnalyzer()

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
        
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        filepath = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{filename}")
        file.save(filepath)

        use_fallback = request.form.get('use_fallback') == 'true'

        walls, rooms, doors, windows, error = parser.parse_floor_plan(filepath)

        if (walls is None or len(walls) == 0) and use_fallback:
            walls, rooms, doors, windows = parser.get_fallback_data()
        elif walls is None or len(walls) == 0:
            return jsonify({'error': error or 'No walls detected'}), 400

        walls = parser.classify_load_bearing(walls)

        recommendations = material_analyzer.get_recommendations()
        furniture_placement = material_analyzer.suggest_furniture_placement(rooms)

        model_file = f"{unique_id}_model.html"
        model_path = os.path.join(STATIC_FOLDER, 'models', model_file)

        model_builder.generate_vibrant_3d_model(
            walls, rooms, doors, windows, furniture_placement, model_path
        )

        response = {
            'success': True,
            'walls': walls,
            'rooms': rooms,
            'doors': doors,
            'windows': windows,
            'recommendations': recommendations,
            'furniture_placement': furniture_placement,
            'model_url': f'/static/models/{model_file}',
            'stats': {
                'total_walls': len(walls),
                'load_bearing': sum(1 for w in walls if w.get('is_load_bearing')),
                'total_rooms': len(rooms),
                'total_area': sum(r.get('area', 0) for r in rooms),
                'total_doors': len(doors),
                'total_windows': len(windows),
            },
            'color_schemes': material_analyzer.get_room_colors(rooms)
        }

        # FINAL SAFETY FIX
        response = convert_types(response)

        return jsonify(response)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run()
    
