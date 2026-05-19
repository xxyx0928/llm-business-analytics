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

def calculate_mom(current_data, previous_data):
    result = []
    
    prev_dict = {}
    for item in previous_data:
        key = (item['modality'], item['model'])
        prev_dict[key] = {
            'token': item['token'],
            'revenue': item['revenue']
        }
    
    for item in current_data:
        key = (item['modality'], item['model'])
        analysis_item = item.copy()
        
        if key in prev_dict:
            prev_token = prev_dict[key]['token']
            prev_revenue = prev_dict[key]['revenue']
            
            analysis_item['token_mom'] = (item['token'] - prev_token) / prev_token if prev_token != 0 else None
            analysis_item['revenue_mom'] = (item['revenue'] - prev_revenue) / prev_revenue if prev_revenue != 0 else None
        else:
            analysis_item['token_mom'] = None
            analysis_item['revenue_mom'] = None
        
        result.append(analysis_item)
    
    return result

def analyze_month(month):
    current_data = get_data_by_month(month)
    if not current_data:
        return None, f"未找到月份 {month} 的数据"
    
    previous_month = get_previous_month(month)
    if previous_month is None:
        return None, f"无法解析月份格式: {month}"
    
    previous_data = get_data_by_month(previous_month)
    if not previous_data:
        result = []
        for item in current_data:
            item_with_mom = item.copy()
            item_with_mom['token_mom'] = None
            item_with_mom['revenue_mom'] = None
            result.append(item_with_mom)
        return result, None
    
    result = calculate_mom(current_data, previous_data)
    return result, None

def export_to_excel(data, month):
    df = pd.DataFrame(data)
    df.columns = ['时间', '模态', '模型', 'Token', '收入', 'Token MoM', '收入 MoM']
    
    output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], f'分析结果_{month}.xlsx')
    df.to_excel(output_path, index=False, engine='openpyxl')
    
    return output_path
