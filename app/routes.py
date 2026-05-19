from flask import render_template, request, jsonify, send_file, redirect, url_for
import pandas as pd
import os
from app import app
from app.database import init_database, insert_data, get_all_months, check_month_exists, delete_month_data
from app.analyzer import analyze_month, export_to_excel

# Initialize database on app start
with app.app_context():
    init_database()

@app.route('/')
def index():
    months = get_all_months()
    return render_template('index.html', months=months)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '未上传文件'}), 400
    
    file = request.files['file']
    month = request.form.get('month', '')
    
    if file.filename == '':
        return jsonify({'success': False, 'error': '未选择文件'}), 400
    
    if not month:
        return jsonify({'success': False, 'error': '请输入月份'}), 400
    
    try:
        # Parse Excel file
        df = pd.read_excel(file, engine='openpyxl')
        
        # Validate columns
        required_columns = ['时间', '模态', '模型', 'Token', '收入', '调用次数']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'success': False, 'error': f'缺少必要字段: {", ".join(missing_columns)}'}), 400
        
        # Clean data
        df = df.dropna(subset=['时间', '模态', '模型', 'Token', '收入', '调用次数'])
        
        if df.empty:
            return jsonify({'success': False, 'error': '数据清洗后没有有效数据'}), 400
        
        # Check if month exists and delete if needed
        if check_month_exists(month):
            delete_month_data(month)
        
        # Insert data
        count = 0
        for _, row in df.iterrows():
            insert_data(
                month=month,
                modality=str(row['模态']).strip(),
                model=str(row['模型']).strip(),
                token=float(row['Token']),
                revenue=float(row['收入']),
                calls=float(row['调用次数'])
            )
            count += 1
        
        # Save the uploaded file
        file.seek(0)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{month}_{file.filename}')
        file.save(save_path)
        
        return jsonify({'success': True, 'count': count, 'month': month})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/months')
def get_months():
    months = get_all_months()
    return jsonify({'success': True, 'months': months})

@app.route('/api/analyze/<month>')
def analyze(month):
    try:
        data, error = analyze_month(month)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download/<month>')
def download(month):
    try:
        data, error = analyze_month(month)
        if error:
            return redirect(url_for('index'))
        
        output_path = export_to_excel(data, month)
        return send_file(output_path, as_attachment=True, download_name=f'分析结果_{month}.xlsx')
    except Exception as e:
        return redirect(url_for('index'))
