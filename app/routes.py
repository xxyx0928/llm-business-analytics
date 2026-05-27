from flask import render_template, request, jsonify, send_file, redirect, url_for
import pandas as pd
import os
from app import app
from app.database import init_database, init_scenario_database, insert_data, insert_scenario_data, get_all_months, check_month_exists, delete_month_data
from app.analyzer import analyze_month, export_to_excel, analyze_trend

# Initialize database on app start
with app.app_context():
    init_database()
    init_scenario_database()

@app.route('/')
def index():
    months = get_all_months()
    return render_template('index.html', months=months)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '未上传文件'}), 400
    
    file = request.files['file']
    company = request.form.get('company', '')
    month = request.form.get('month', '')
    
    if file.filename == '':
        return jsonify({'success': False, 'error': '未选择文件'}), 400
    
    if not company:
        return jsonify({'success': False, 'error': '请选择公司'}), 400
    
    if not month:
        return jsonify({'success': False, 'error': '请输入月份'}), 400
    
    try:
        # Parse Excel file - Sheet1 (模型数据)
        df = pd.read_excel(file, engine='openpyxl', sheet_name=0)
        
        # Validate columns
        required_columns = ['时间', '模态', '模型', 'Token', '收入']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'success': False, 'error': f'缺少必要字段: {", ".join(missing_columns)}'}), 400
        
        # Clean data - 调用次数为可选字段
        df = df.dropna(subset=['时间', '模态', '模型', 'Token', '收入'])
        
        if df.empty:
            return jsonify({'success': False, 'error': '数据清洗后没有有效数据'}), 400
        
        # Check if month exists and delete if needed
        if check_month_exists(company, month):
            delete_month_data(company, month)
        
        # Insert data (Sheet1)
        count = 0
        for _, row in df.iterrows():
            calls = float(row['调用次数']) if '调用次数' in df.columns and pd.notna(row['调用次数']) else 0.0
            insert_data(
                company=company,
                month=month,
                modality=str(row['模态']).strip(),
                model=str(row['模型']).strip(),
                token=float(row['Token']),
                revenue=float(row['收入']),
                calls=calls
            )
            count += 1
        
        # Parse Excel file - Sheet2 (场景数据)
        try:
            df_scenario = pd.read_excel(file, engine='openpyxl', sheet_name=1)
            
            # Validate scenario columns - 场景必填，调用次数和Token可选
            if '场景' in df_scenario.columns:
                df_scenario = df_scenario.dropna(subset=['场景'])
                df_scenario['场景'] = df_scenario['场景'].astype(str)
                
                for _, row in df_scenario.iterrows():
                    scenario_calls = float(row['调用次数']) if '调用次数' in df_scenario.columns and pd.notna(row['调用次数']) else 0.0
                    scenario_token = float(row['Token']) if 'Token' in df_scenario.columns and pd.notna(row['Token']) else 0.0
                    
                    insert_scenario_data(
                        company=company,
                        month=month,
                        scenario=str(row['场景']).strip(),
                        calls=scenario_calls,
                        token=scenario_token
                    )
        except Exception as scenario_error:
            # 如果第二个sheet不存在或有错误，继续处理，不影响主数据上传
            print(f"警告：读取场景数据失败: {scenario_error}")
        
        # Save the uploaded file
        file.seek(0)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{company}_{month}_{file.filename}')
        file.save(save_path)
        
        return jsonify({'success': True, 'count': count, 'company': company, 'month': month})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/months')
def get_months():
    data = get_all_months()
    result = [{'company': row[0], 'month': row[1]} for row in data]
    return jsonify({'success': True, 'data': result})

@app.route('/api/analyze/<company>/<month>')
def analyze(company, month):
    try:
        data, error = analyze_month(company, month)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/delete/<company>/<month>', methods=['DELETE'])
def delete_data(company, month):
    try:
        delete_month_data(company, month)
        return jsonify({'success': True, 'message': f'已删除 {company} {month} 的数据'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download/<company>/<month>')
def download(company, month):
    try:
        data, error = analyze_month(company, month)
        if error:
            return redirect(url_for('index'))
        
        output_path = export_to_excel(data, company, month)
        return send_file(output_path, as_attachment=True, download_name=f'{company}_分析结果_{month}.xlsx')
    except Exception as e:
        return redirect(url_for('index'))

@app.route('/api/trend/<company>')
def trend(company):
    try:
        data, error = analyze_trend(company)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
