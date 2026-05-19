import pandas as pd
import os
from flask import current_app
from app.database import get_data_by_month

def parse_month(month_str):
    try:
        parts = month_str.split('.')
        if len(parts) == 2:
            year = int(parts[0])
            month = int(parts[1])
            return year, month
        return None, None
    except:
        return None, None

def get_previous_month(current_month):
    year, month = parse_month(current_month)
    if year is None or month is None:
        return None
    
    if month == 1:
        prev_month = f"{year - 1}.12"
    else:
        prev_month = f"{year}.{month - 1}"
    
    return prev_month

def calculate_mom_and_delta(current_value, previous_value):
    if previous_value is None:
        return {'mom': None, 'delta': None}
    
    delta = current_value - previous_value
    mom = delta / previous_value if previous_value != 0 else None
    
    return {'mom': mom, 'delta': delta}

def analyze_by_model(current_data, previous_data):
    result = []
    
    prev_dict = {}
    for item in previous_data:
        key = (item['modality'], item['model'])
        prev_dict[key] = {
            'token': item['token'],
            'revenue': item['revenue'],
            'calls': item['calls']
        }
    
    for item in current_data:
        key = (item['modality'], item['model'])
        analysis_item = item.copy()
        
        if key in prev_dict:
            token_result = calculate_mom_and_delta(item['token'], prev_dict[key]['token'])
            revenue_result = calculate_mom_and_delta(item['revenue'], prev_dict[key]['revenue'])
            calls_result = calculate_mom_and_delta(item['calls'], prev_dict[key]['calls'])
            
            analysis_item['token_mom'] = token_result['mom']
            analysis_item['token_delta'] = token_result['delta']
            analysis_item['revenue_mom'] = revenue_result['mom']
            analysis_item['revenue_delta'] = revenue_result['delta']
            analysis_item['calls_mom'] = calls_result['mom']
            analysis_item['calls_delta'] = calls_result['delta']
        else:
            analysis_item['token_mom'] = None
            analysis_item['token_delta'] = None
            analysis_item['revenue_mom'] = None
            analysis_item['revenue_delta'] = None
            analysis_item['calls_mom'] = None
            analysis_item['calls_delta'] = None
        
        result.append(analysis_item)
    
    return result

def aggregate_by_modality(data):
    if not data:
        return {}
    
    aggregated = {}
    for item in data:
        modality = item['modality']
        if modality not in aggregated:
            aggregated[modality] = {'token': 0, 'revenue': 0, 'calls': 0}
        aggregated[modality]['token'] += item['token']
        aggregated[modality]['revenue'] += item['revenue']
        aggregated[modality]['calls'] += item['calls']
    
    return aggregated

def analyze_by_modality(current_data, previous_data):
    current_agg = aggregate_by_modality(current_data)
    previous_agg = aggregate_by_modality(previous_data)
    
    result = []
    all_modalities = set(current_agg.keys()).union(set(previous_agg.keys()))
    
    for modality in all_modalities:
        current_token = current_agg.get(modality, {}).get('token', 0)
        current_revenue = current_agg.get(modality, {}).get('revenue', 0)
        current_calls = current_agg.get(modality, {}).get('calls', 0)
        prev_token = previous_agg.get(modality, {}).get('token') if modality in previous_agg else None
        prev_revenue = previous_agg.get(modality, {}).get('revenue') if modality in previous_agg else None
        prev_calls = previous_agg.get(modality, {}).get('calls') if modality in previous_agg else None
        
        token_result = calculate_mom_and_delta(current_token, prev_token)
        revenue_result = calculate_mom_and_delta(current_revenue, prev_revenue)
        calls_result = calculate_mom_and_delta(current_calls, prev_calls)
        
        result.append({
            'modality': modality,
            'token': current_token,
            'revenue': current_revenue,
            'calls': current_calls,
            'token_mom': token_result['mom'],
            'token_delta': token_result['delta'],
            'revenue_mom': revenue_result['mom'],
            'revenue_delta': revenue_result['delta'],
            'calls_mom': calls_result['mom'],
            'calls_delta': calls_result['delta']
        })
    
    return sorted(result, key=lambda x: x['modality'])

def analyze_total(current_data, previous_data):
    current_token = sum(item['token'] for item in current_data) if current_data else 0
    current_revenue = sum(item['revenue'] for item in current_data) if current_data else 0
    current_calls = sum(item['calls'] for item in current_data) if current_data else 0
    
    prev_token = sum(item['token'] for item in previous_data) if previous_data else None
    prev_revenue = sum(item['revenue'] for item in previous_data) if previous_data else None
    prev_calls = sum(item['calls'] for item in previous_data) if previous_data else None
    
    token_result = calculate_mom_and_delta(current_token, prev_token)
    revenue_result = calculate_mom_and_delta(current_revenue, prev_revenue)
    calls_result = calculate_mom_and_delta(current_calls, prev_calls)
    
    return {
        'token': current_token,
        'revenue': current_revenue,
        'calls': current_calls,
        'token_mom': token_result['mom'],
        'token_delta': token_result['delta'],
        'revenue_mom': revenue_result['mom'],
        'revenue_delta': revenue_result['delta'],
        'calls_mom': calls_result['mom'],
        'calls_delta': calls_result['delta']
    }

def analyze_month(month):
    current_data = get_data_by_month(month)
    if not current_data:
        return None, f"未找到月份 {month} 的数据"
    
    previous_month = get_previous_month(month)
    if previous_month is None:
        return None, f"无法解析月份格式: {month}"
    
    previous_data = get_data_by_month(previous_month)
    
    by_model = analyze_by_model(current_data, previous_data)
    by_modality = analyze_by_modality(current_data, previous_data)
    total = analyze_total(current_data, previous_data)
    
    return {
        'by_model': by_model,
        'by_modality': by_modality,
        'total': total,
        'month': month,
        'previous_month': previous_month if previous_data else None
    }, None

def export_to_excel(data, month):
    output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], f'分析结果_{month}.xlsx')
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        if 'by_model' in data and data['by_model']:
            df_model = pd.DataFrame(data['by_model'])
            df_model = df_model[['month', 'modality', 'model', 'token', 'calls', 'revenue', 'token_delta', 'token_mom', 'calls_delta', 'calls_mom', 'revenue_delta', 'revenue_mom']]
            df_model.columns = ['时间', '模态', '模型', 'Token', '调用次数', '收入', 'Token 增量', 'Token MoM', '调用次数增量', '调用次数 MoM', '收入增量', '收入 MoM']
            df_model.to_excel(writer, sheet_name='按模型分析', index=False)
        
        if 'by_modality' in data and data['by_modality']:
            df_modality = pd.DataFrame(data['by_modality'])
            df_modality = df_modality[['modality', 'token', 'calls', 'revenue', 'token_delta', 'token_mom', 'calls_delta', 'calls_mom', 'revenue_delta', 'revenue_mom']]
            df_modality.columns = ['模态', 'Token', '调用次数', '收入', 'Token 增量', 'Token MoM', '调用次数增量', '调用次数 MoM', '收入增量', '收入 MoM']
            df_modality.to_excel(writer, sheet_name='按模态分析', index=False)
        
        if 'total' in data:
            total_data = [data['total']]
            df_total = pd.DataFrame(total_data)
            df_total = df_total[['token', 'calls', 'revenue', 'token_delta', 'token_mom', 'calls_delta', 'calls_mom', 'revenue_delta', 'revenue_mom']]
            df_total.columns = ['总 Token', '总调用次数', '总收入', 'Token 增量', 'Token MoM', '调用次数增量', '调用次数 MoM', '收入增量', '收入 MoM']
            df_total.to_excel(writer, sheet_name='总计分析', index=False)
    
    return output_path
