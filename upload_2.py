# 导入必要的Python模块
import os
from glob import glob
import requests
import re
import pandas as pd  # 用于处理表格数据
from datetime import datetime
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def find_info_files(folder_path):
    """
    在车次文件夹中查找信息文件
    
    参数说明：
    :param folder_path: 车次文件夹路径
    
    返回值：
    :return: 找到的信息文件路径列表
    
    功能说明：
    在车次文件夹中查找包含车辆信息的文件
    可能是Excel文件、CSV文件或其他格式
    """
    info_files = []
    
    # 查找可能的信息文件
    patterns = [
        "*.xlsx",  # Excel文件
        "*.xls",   # 旧版Excel文件
        "*.csv",   # CSV文件
        "*信息*.txt",  # 包含"信息"的文本文件
        "*列车*.txt",  # 包含"列车"的文本文件
    ]
    
    for pattern in patterns:
        files = glob(os.path.join(folder_path, pattern))
        info_files.extend(files)
    
    return info_files

def parse_vehicle_info_from_file(file_path):
    """
    从信息文件中解析车辆数据
    
    参数说明：
    :param file_path: 信息文件路径
    
    返回值：
    :return: (车辆编号字典, 列车基本信息字典)
    
    功能说明：
    根据文件类型，解析车辆编号和列车基本信息
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext in ['.xlsx', '.xls']:
            # 处理Excel文件
            return parse_excel_file(file_path)
        elif file_ext == '.csv':
            # 处理CSV文件
            return parse_csv_file(file_path)
        elif file_ext == '.txt':
            # 处理文本文件
            return parse_text_file(file_path)
        else:
            print(f"不支持的文件格式: {file_ext}")
            return {}, {}
    except Exception as e:
        print(f"解析文件 {file_path} 时出错: {e}")
        return {}, {}

def parse_excel_file(file_path):
    """
    解析Excel文件中的车辆信息
    
    参数说明：
    :param file_path: Excel文件路径
    
    返回值：
    :return: (车辆编号字典, 列车基本信息字典)
    
    功能说明：
    从Excel文件中提取车辆编号表和列车基本信息
    适配新的Excel格式：第一张表为列车信息，第二张表为车辆信息
    """
    try:
        # 读取Excel文件的所有工作表
        excel_file = pd.ExcelFile(file_path)
        
        vehicle_numbers = {}
        train_info = {}
        
        # 处理第一张表：列车信息
        if len(excel_file.sheet_names) >= 1:
            first_sheet = excel_file.sheet_names[0]
            
            # 读取时不使用第一行作为列名，这样可以读取到实际的表头
            df1 = pd.read_excel(file_path, sheet_name=first_sheet, header=None)
            
            # 从第一张表提取列车基本信息
            # 遍历所有单元格，查找包含关键信息的内容
            for i, row in df1.iterrows():
                for j, cell in enumerate(row):
                    if pd.notna(cell):
                        cell_str = str(cell).strip()
                        
                        # 提取车次信息（查找包含K、T、G等车次号的内容）
                        if re.search(r'[KGTD]\d+', cell_str):
                            match = re.search(r'([KGTD]\d+)', cell_str)
                            if match:
                                train_info['vehicleInfo'] = match.group(1)
                        
                        # 提取探测站信息（查找包含"线"和"到达"的内容）
                        if '线' in cell_str and ('到达' in cell_str or '探测站' in cell_str):
                            train_info['recordStation'] = cell_str
                        
                        # 提取运行方向
                        if cell_str in ['上行', '下行']:
                            train_info['travelDirection'] = cell_str
                        
                        # 提取担当局（查找包含"铁路局"的内容）
                        if '铁路局' in cell_str:
                            train_info['bureau'] = cell_str
                        
                        # 提取客整所（查找包含"所"的内容，但不是"客整所"标签本身）
                        if '所' in cell_str and cell_str != '客整所' and len(cell_str) > 2:
                            train_info['section'] = cell_str
        
        # 处理第二张表：车辆信息
        if len(excel_file.sheet_names) >= 2:
            second_sheet = excel_file.sheet_names[1]
            
            # 同样不使用第一行作为列名
            df2 = pd.read_excel(file_path, sheet_name=second_sheet, header=None)
            
            # 查找表头行（通常包含"序号"、"车号"等字段）
            header_row = -1
            seq_col = -1
            vehicle_col = -1
            
            for i, row in df2.iterrows():
                row_values = [str(cell).strip() if pd.notna(cell) else '' for cell in row]
                
                # 查找包含"序号"和"车号"的行
                if any('序号' in val for val in row_values) and any('车号' in val for val in row_values):
                    header_row = i
                    # 找到序号列和车号列的位置
                    for j, val in enumerate(row_values):
                        if '序号' in val:
                            seq_col = j
                        elif '车号' in val:
                            vehicle_col = j
                    break
            
            # 如果找到了表头，从下一行开始提取数据
            if header_row >= 0 and seq_col >= 0 and vehicle_col >= 0:
                for i in range(header_row + 1, len(df2)):
                    try:
                        seq_cell = df2.iloc[i, seq_col]
                        vehicle_cell = df2.iloc[i, vehicle_col]
                        
                        if pd.notna(seq_cell) and pd.notna(vehicle_cell):
                            seq = str(int(float(seq_cell)))
                            vehicle_id = str(vehicle_cell).strip()
                            
                            # 修改：包含所有车号（包括XXXXX等无效车号）
                            if vehicle_id:  # 只要车号不为空就包含
                                vehicle_numbers[seq] = vehicle_id
                    except Exception as e:
                        continue
            else:
                # 如果没找到标准表头，尝试从第2行开始，假设第1列是序号，第2列是车号
                for i in range(1, len(df2)):  # 跳过第一行（可能是表头）
                    try:
                        if len(df2.columns) >= 2:
                            seq_cell = df2.iloc[i, 0]  # 第一列作为序号
                            vehicle_cell = df2.iloc[i, 1]  # 第二列作为车号
                            
                            if pd.notna(seq_cell) and pd.notna(vehicle_cell):
                                # 检查是否是数字（序号应该是数字）
                                try:
                                    seq = str(int(float(seq_cell)))
                                    vehicle_id = str(vehicle_cell).strip()
                                    
                                    # 修改：包含所有车号（包括XXXXX等无效车号）
                                    if vehicle_id:  # 只要车号不为空就包含
                                        vehicle_numbers[seq] = vehicle_id
                                except ValueError:
                                    # 如果第一列不是数字，跳过这一行
                                    continue
                    except Exception as e:
                        continue
        
        return vehicle_numbers, train_info
        
    except Exception as e:
        print(f"解析Excel文件时出错: {e}")
        import traceback
        traceback.print_exc()
        return {}, {}

def parse_csv_file(file_path):
    """
    解析CSV文件中的车辆信息
    
    参数说明：
    :param file_path: CSV文件路径
    
    返回值：
    :return: (车辆编号字典, 列车基本信息字典)
    
    功能说明：
    从CSV文件中提取车辆编号表和列车基本信息
    """
    try:
        # 尝试不同的编码格式
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            print(f"无法解码CSV文件: {file_path}")
            return {}, {}
        
        vehicle_numbers = {}
        train_info = {}
        
        # 查找车辆信息
        if '辆序' in df.columns and '车号' in df.columns:
            for _, row in df.iterrows():
                if pd.notna(row['辆序']) and pd.notna(row['车号']):
                    vehicle_numbers[str(int(row['辆序']))] = str(row['车号'])
        
        # 提取列车基本信息
        train_info = extract_train_info_from_dataframe(df)
        
        return vehicle_numbers, train_info
        
    except Exception as e:
        print(f"解析CSV文件时出错: {e}")
        return {}, {}

def parse_text_file(file_path):
    """
    解析文本文件中的车辆信息
    
    参数说明：
    :param file_path: 文本文件路径
    
    返回值：
    :return: (车辆编号字典, 列车基本信息字典)
    
    功能说明：
    从文本文件中提取车辆编号表和列车基本信息
    适用于结构化的文本数据
    """
    vehicle_numbers = {}
    train_info = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式提取信息
        # 提取车次信息
        train_pattern = r'车次[：:]*\s*([A-Z]?\d+)'
        train_match = re.search(train_pattern, content)
        if train_match:
            train_info['vehicleInfo'] = train_match.group(1)
        
        # 提取探测站信息
        station_pattern = r'探测站[：:]*\s*([^\n]+)'
        station_match = re.search(station_pattern, content)
        if station_match:
            train_info['recordStation'] = station_match.group(1).strip()
        
        # 提取运行方向
        direction_pattern = r'运行方向[：:]*\s*([上下]行)'
        direction_match = re.search(direction_pattern, content)
        if direction_match:
            train_info['travelDirection'] = direction_match.group(1)
        
        # 提取担当局
        bureau_pattern = r'担当局[：:]*\s*([^\n]+)'
        bureau_match = re.search(bureau_pattern, content)
        if bureau_match:
            train_info['bureau'] = bureau_match.group(1).strip()
        
        # 提取客整所
        section_pattern = r'客整所[：:]*\s*([^\n]+)'
        section_match = re.search(section_pattern, content)
        if section_match:
            train_info['section'] = section_match.group(1).strip()
        
        # 提取总辆数
        total_pattern = r'总辆数[：:]*\s*(\d+)'
        total_match = re.search(total_pattern, content)
        if total_match:
            train_info['totalSequence'] = int(total_match.group(1))
        
        # 提取车辆编号信息（假设格式为：序号 车号）
        vehicle_pattern = r'(\d+)\s+(\d{6})'
        vehicle_matches = re.findall(vehicle_pattern, content)
        for seq, vehicle_id in vehicle_matches:
            vehicle_numbers[seq] = vehicle_id
        
    except Exception as e:
        print(f"解析文本文件时出错: {e}")
    
    return vehicle_numbers, train_info

def extract_train_info_from_dataframe(df):
    """
    从DataFrame中提取列车基本信息
    
    参数说明：
    :param df: pandas DataFrame对象
    
    返回值：
    :return: 列车基本信息字典
    
    功能说明：
    在DataFrame中查找列车的基本信息字段
    """
    train_info = {}
    
    # 定义要查找的字段映射
    field_mapping = {
        '车次': 'vehicleInfo',
        '探测站': 'recordStation', 
        '运行方向': 'travelDirection',
        '担当局': 'bureau',
        '客整所': 'section',
        '总辆数': 'totalSequence'
    }
    
    # 在DataFrame中查找这些字段
    for col in df.columns:
        for chinese_name, english_name in field_mapping.items():
            if chinese_name in str(col):
                # 获取该列的第一个非空值
                values = df[col].dropna()
                if not values.empty:
                    value = values.iloc[0]
                    if english_name == 'totalSequence':
                        try:
                            train_info[english_name] = int(value)
                        except:
                            pass
                    else:
                        train_info[english_name] = str(value)
    
    return train_info

def generate_num_list_string(vehicle_numbers):
    """
    根据车辆编号字典生成num_list格式的字符串
    
    参数说明：
    :param vehicle_numbers: 车辆编号字典 {辆序: 车号}
    
    返回值：
    :return: 格式化的字符串
    
    功能说明：
    将车辆编号字典转换为原代码中num_list的格式
    """
    lines = ['    """']
    
    # 按辆序排序
    sorted_items = sorted(vehicle_numbers.items(), key=lambda x: int(x[0]))
    
    for seq, vehicle_id in sorted_items:
        lines.append(f'    {seq}\t{vehicle_id}')
    
    lines.append('    """')
    
    return '\n'.join(lines)

def validate_train_data_completeness(train_info, vehicle_numbers, train_index):
    """
    验证列车数据的完整性
    
    参数说明：
    :param train_info: 列车基本信息字典
    :param vehicle_numbers: 车辆编号字典 {辆序: 车号}
    :param train_index: 列车序号（用于显示）
    
    返回值：
    :return: (is_complete, missing_info_list)
    
    功能说明：
    检查列车数据是否包含所有必需的信息字段
    对无效车号只提醒，不阻止上传；对关键信息缺失则报错阻止上传
    """
    missing_info = []  # 严重错误，会阻止上传
    warning_info = []  # 警告信息，不阻止上传
    
    # 检查整车信息的必需字段（这些缺失会阻止上传）
    required_train_fields = {
        'vehicleInfo': '车次',
        'recordStation': '探测站', 
        'travelDirection': '运行方向',
        'bureau': '担当局',
        'section': '客整所'
    }
    
    print(f"\n正在验证第 {train_index} 个列车的数据完整性...")
    
    # 验证整车信息（缺失会报错）
    for field, field_name in required_train_fields.items():
        if field not in train_info or not train_info[field] or train_info[field] in ['未知', '未知站点', '未知铁路局', '未知整备所']:
            missing_info.append(f"【整车信息】缺失：{field_name}")
    
    # 验证车号信息
    if not vehicle_numbers or len(vehicle_numbers) == 0:
        missing_info.append("【车号信息】完全缺失：未提取到任何车辆编号")
    else:
        # 定义无效车号的模式
        invalid_vehicle_patterns = [
            'XXXXX',     # 常见的占位符
            'xxxxx',     # 小写版本
            'X' * 5,     # 5个X
            'X' * 6,     # 6个X
            '未知',       # 中文未知
            '空白',       # 空白标记
            '无',         # 无
            '0' * 5,     # 5个0
            '0' * 6,     # 6个0
        ]
        
        # 检查无效车号和空车号
        invalid_vehicles = []
        empty_vehicles = []
        valid_sequences = []
        
        for seq, vehicle_id in vehicle_numbers.items():
            vehicle_id_clean = str(vehicle_id).strip() if vehicle_id else ''
            
            # 检查是否为空（空车号算严重错误）
            if not vehicle_id_clean:
                empty_vehicles.append(seq)
                continue
            
            # 检查是否为无效车号（无效车号只是警告）
            is_invalid = False
            for pattern in invalid_vehicle_patterns:
                if vehicle_id_clean.upper() == pattern.upper():
                    invalid_vehicles.append((seq, vehicle_id_clean))
                    is_invalid = True
                    break
            
            # 如果不是无效车号，则认为是有效的
            if not is_invalid:
                valid_sequences.append(int(seq))
        
        # 空车号算严重错误（会阻止上传）
        if empty_vehicles:
            missing_info.append(f"【车号信息】车号为空：辆序 {', '.join(empty_vehicles)}")
        
        # 无效车号只是警告（不阻止上传）
        if invalid_vehicles:
            invalid_details = [f"辆序{seq}(车号:{vehicle_id})" for seq, vehicle_id in invalid_vehicles]
            warning_info.append(f"【车号信息】发现无效车号：{', '.join(invalid_details)}")
        
        # 检查有效车号的连续性（不连续只是警告）
        if valid_sequences:
            valid_sequences.sort()
            # 检查从1开始到最大辆序是否连续
            max_seq = max(valid_sequences)
            expected_sequences = list(range(1, max_seq + 1))
            
            missing_sequences = []
            for expected_seq in expected_sequences:
                if expected_seq not in valid_sequences:
                    missing_sequences.append(expected_seq)
            
            if missing_sequences:
                warning_info.append(f"【车号信息】有效辆序不连续：缺失辆序 {', '.join(map(str, missing_sequences))}")
    
    # 显示验证结果
    has_errors = len(missing_info) > 0
    has_warnings = len(warning_info) > 0
    
    if has_errors:
        print(f"❌ 第 {train_index} 个列车数据不完整（将跳过上传）：")
        for info in missing_info:
            print(f"   - {info}")
    
    if has_warnings:
        print(f"⚠️  第 {train_index} 个列车数据警告（不影响上传）：")
        for info in warning_info:
            print(f"   - {info}")
    
    if not has_errors and not has_warnings:
        print(f"✅ 第 {train_index} 个列车数据完整")
    elif not has_errors:
        print(f"✅ 第 {train_index} 个列车数据可以上传（有警告但不影响）")
    
    # 只有严重错误才返回False，警告不影响上传
    return not has_errors, missing_info

def auto_generate_from_folders(base_directory):
    """
    自动从文件夹中生成列车数据
    
    参数说明：
    :param base_directory: 包含列车数据文件夹的根目录
    
    返回值：
    :return: (num_list, public_info, images_root_list)
    
    功能说明：
    扫描指定目录下的所有列车文件夹，自动解析Excel文件并生成所需的数据结构
    只有数据完整的列车才会被包含在结果中
    """
    num_list = []
    public_info = []
    images_root_list = []
    
    if not os.path.exists(base_directory):
        print(f"目录不存在: {base_directory}")
        return num_list, public_info, images_root_list
    
    # 递归查找所有包含列车信息的文件夹
    def find_train_folders(directory, depth=0):
        """递归查找列车文件夹"""
        if depth > 3:  # 限制递归深度，避免无限递归
            return []
        
        train_folders = []
        
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                
                if os.path.isdir(item_path):
                    # 检查是否是列车信息文件夹（包含关键词）
                    keywords = ["车次列车车辆信息", "列车车辆信息", "车辆信息"]
                    if any(keyword in item for keyword in keywords):
                        train_folders.append(item_path)
                    else:
                        # 继续递归查找子文件夹
                        train_folders.extend(find_train_folders(item_path, depth + 1))
        except PermissionError:
            pass
        except Exception as e:
            pass
        
        return train_folders
    
    # 查找所有列车文件夹
    train_folders = find_train_folders(base_directory)
    
    if not train_folders:
        print("未找到任何列车数据文件夹")
        return num_list, public_info, images_root_list
    
    print(f"找到 {len(train_folders)} 个列车文件夹，开始处理...")
    
    # 用于统计验证结果
    total_trains = 0
    complete_trains = 0
    incomplete_trains = []
    
    # 处理每个列车文件夹
    for folder_path in train_folders:
        folder_name = os.path.basename(folder_path)
        total_trains += 1
        
        try:
            # 查找信息文件
            info_files = find_info_files(folder_path)
            
            if not info_files:
                incomplete_trains.append((total_trains, folder_name, ["未找到信息文件"]))
                continue
            
            # 解析信息文件（优先处理包含"列车信息"或"车辆信息"的文件）
            target_file = None
            for file_path in info_files:
                file_name = os.path.basename(file_path)
                if "列车信息" in file_name or "车辆信息" in file_name:
                    target_file = file_path
                    break
            
            if not target_file:
                target_file = info_files[0]  # 如果没有找到特定文件，使用第一个
            
            # 解析文件内容
            vehicle_numbers, train_info = parse_vehicle_info_from_file(target_file)
            
            # 补充缺失的信息（从文件夹名称中提取）
            if 'recordStation' not in train_info or not train_info['recordStation']:
                folder_info = parse_folder_name_simple(folder_name)
                train_info.update(folder_info)
            
            # 验证数据完整性
            is_complete, missing_info = validate_train_data_completeness(train_info, vehicle_numbers, total_trains)
            
            if not is_complete:
                # 数据不完整，记录但不添加到结果中
                incomplete_trains.append((total_trains, folder_name, missing_info))
                print(f"⚠️  跳过第 {total_trains} 个列车（数据不完整）")
                continue
            
            # 数据完整，添加到结果中
            complete_trains += 1
            
            # 确保所有必需字段都存在（设置默认值）
            default_info = {
                'totalSequence': len(vehicle_numbers)
            }
            
            for key, default_value in default_info.items():
                if key not in train_info:
                    train_info[key] = default_value
            
            # 生成num_list字符串
            num_str = generate_num_list_string(vehicle_numbers)
            num_list.append(num_str)
            public_info.append(train_info)
            images_root_list.append(folder_path)
            
            print(f"✓ 第 {total_trains} 个列车验证通过: {train_info['vehicleInfo']} ({len(vehicle_numbers)}辆车)")
            
        except Exception as e:
            incomplete_trains.append((total_trains, folder_name, [f"处理异常: {str(e)}"]))
            print(f"✗ 第 {total_trains} 个列车处理失败: {folder_name}")
            continue
    
    # 显示验证总结
    print("\n" + "="*80)
    print("【数据完整性验证总结】")
    print(f"总计扫描: {total_trains} 个列车文件夹")
    print(f"数据完整: {complete_trains} 个列车")
    print(f"数据不完整: {len(incomplete_trains)} 个列车")
    
    if incomplete_trains:
        print("\n❌ 数据不完整的列车详情：")
        for train_index, folder_name, missing_info in incomplete_trains:
            print(f"\n第 {train_index} 个列车: {folder_name}")
            for info in missing_info:
                print(f"   - {info}")
        
        print("\n⚠️  以上列车因数据不完整将不会被上传")
        print("💡 请检查并补充缺失信息后重新运行程序")
    
    if complete_trains == 0:
        print("\n❌ 没有找到数据完整的列车，程序将不会进行上传")
        return [], [], []
    else:
        print(f"\n✅ 共有 {complete_trains} 个列车数据完整，可以进行上传")
    
    print("="*80)
    return num_list, public_info, images_root_list

def parse_folder_name_simple(folder_name):
    """
    简单解析文件夹名称（备用方案）
    
    参数说明：
    :param folder_name: 文件夹名称
    
    返回值：
    :return: 提取的信息字典
    
    功能说明：
    当信息文件中没有完整信息时，从文件夹名称中提取基本信息
    """
    info = {}
    
    # 提取车次号
    train_pattern = r'([A-Z]?\d+)车次'
    train_match = re.search(train_pattern, folder_name)
    if train_match:
        info['vehicleInfo'] = train_match.group(1)
    
    # 提取方向
    if '上行' in folder_name:
        info['travelDirection'] = '上行'
    elif '下行' in folder_name:
        info['travelDirection'] = '下行'
    
    # 提取线路和站点信息
    if '京九线' in folder_name:
        info['recordStation'] = '京九线北京西上行到达'
        info['bureau'] = '北京铁路局'
    elif '合九线' in folder_name:
        info['recordStation'] = '合九线合肥上行到达'
        info['bureau'] = '上海铁路局'
    elif '沪昆线' in folder_name:
        info['recordStation'] = '沪昆线杭州下行到达'
        info['bureau'] = '上海铁路局'
    elif '京沪线' in folder_name:
        info['recordStation'] = '京沪线上海上海南下行到达'
        info['bureau'] = '上海铁路局'
    
    return info

def decode_num_list(num_list_str, car_num):
    """
    从车辆编号列表中查找指定车厢号对应的车辆编号
    
    参数说明：
    :param num_list_str: 车辆编号列表字符串
    :param car_num: 车厢号
    
    返回值：
    :return: 车辆编号
    
    功能说明：
    解析num_list字符串，查找指定车厢号对应的车辆编号
    """
    lines = num_list_str.strip().split('\n')
    
    for line in lines:
        parts = line.strip().split('\t')
        if len(parts) == 2 and parts[0].strip() == car_num:
            return parts[1].strip()
    
    raise ValueError(f"车号 {car_num} 在列表中未找到")

def upload_data_to_server(num_list, public_info, images_root_list):
    """
    上传数据到服务器
    
    参数说明：
    :param num_list: 车辆编号列表
    :param public_info: 列车基本信息列表
    :param images_root_list: 图片文件夹路径列表
    
    功能说明：
    将提取的列车数据和图片上传到后端服务器
    """
    # 后端API接口地址 - 修改为新的IP地址
    upload_url = "http://10.0.100.211:8082/api/v1/railway-vehicle"
    
    # 监控方向与数字编号的对应关系
    direction_to_num = {
        '右侧': 0, '左侧': 1, '底中': 2, '底右': 3, '底左': 4,
    }
    
    total_uploaded = 0
    total_failed = 0
    
    # 处理每个车次的图片数据
    for i, root_dir in enumerate(images_root_list):
        print(f"\n正在上传第 {i+1} 个列车的数据...")
        
        # 使用glob搜索指定目录下的所有jpg图片文件
        from glob import glob
        images_list = glob(os.path.join(root_dir, "*.jpg"))
        images_list.sort()
        
        if not images_list:
            print(f"  ❌ 未找到图片文件，跳过第 {i+1} 个列车")
            continue
        
        # 创建字典，用于按车厢号分组存储图片路径
        car_num_dict = {}
        
        # 遍历所有图片文件，按车厢号分组
        for image_path in images_list:
            try:
                image_name = os.path.basename(image_path)
                car_num, direction_num = split_seq_direction(image_name)
                
                if car_num not in car_num_dict:
                    car_num_dict[car_num] = []
                
                car_num_dict[car_num].append(image_path)
            except Exception as e:
                print(f"  ⚠️  解析图片文件名失败: {image_name} - {e}")
                continue
        
        if not car_num_dict:
            print(f"  ❌ 无法解析任何图片文件名，跳过第 {i+1} 个列车")
            continue
        
        # 获取当前车次的基本信息
        vehicleInfo = public_info[i]
        
        # 按车厢号排序，确保上传顺序正确
        car_num_list = sorted(list(car_num_dict.items()), key=lambda x: int(x[0]))
        
        car_success = 0
        car_failed = 0
        
        # 遍历每个车厢，准备上传数据
        for car_num, image_paths in car_num_list:
            try:
                # 获取车辆编号
                vehicle_identity = decode_num_list(num_list[i], car_num)
                
                # 构造要上传的数据字典
                data = {
                    'recordStation': vehicleInfo['recordStation'],
                    'travelDirection': vehicleInfo['travelDirection'],
                    'vehicleInfo': vehicleInfo['vehicleInfo'],
                    'vehicleIdentity': vehicle_identity,
                    'bureau': vehicleInfo['bureau'],
                    'section': vehicleInfo['section'],
                    'vehicleSeq': car_num,
                    'totalSequence': vehicleInfo['totalSequence'],
                }
                
                # 准备文件上传列表
                files = []
                
                # 遍历当前车厢的所有图片
                for image_path in image_paths:
                    f = open(image_path, 'rb')
                    files.append(('imageFiles', f))
                
                # 发送POST请求上传数据和文件
                response = requests.post(upload_url, data=data, files=files)
                
                # 关闭所有打开的文件
                for f in files:
                    f[1].close()
                
                # 检查上传结果
                if response.status_code == 200:
                    print(f"  ✅ 车厢 {car_num} (车号: {vehicle_identity}) 上传成功")
                    car_success += 1
                    total_uploaded += 1
                else:
                    print(f"  ❌ 车厢 {car_num} (车号: {vehicle_identity}) 上传失败: {response.text}")
                    car_failed += 1
                    total_failed += 1
                    
            except ValueError as e:
                print(f"  ❌ 车厢 {car_num} 跳过上传: {e}")
                car_failed += 1
                total_failed += 1
            except Exception as e:
                print(f"  ❌ 车厢 {car_num} 上传异常: {e}")
                car_failed += 1
                total_failed += 1
        
        print(f"  第 {i+1} 个列车上传完成: 成功 {car_success} 辆，失败 {car_failed} 辆")
    
    # 上传总结
    print("\n" + "="*80)
    print("上传完成！")
    print(f"总计上传成功: {total_uploaded} 辆车")
    print(f"总计上传失败: {total_failed} 辆车")
    
    if total_failed > 0:
        print("\n⚠️  部分数据上传失败，请检查：")
        print("   1. 网络连接是否正常")
        print("   2. 服务器地址是否正确")
        print("   3. 车号信息是否完整")

def main():
    """
    主函数：自动生成并处理列车数据
    
    功能说明：
    1. 从文件夹中的信息文件自动提取数据
    2. 生成num_list、public_info、images_root_list
    3. 按顺序输出：整车信息 -> 车号信息 -> 图片信息
    4. 上传数据到服务器
    """
    # 设置列车数据的根目录
    base_dir = r"D:\tvds-system\TV故障及全列图片"
    
    print("开始自动扫描和生成列车数据...")
    
    try:
        # 自动生成数据
        num_list, public_info, images_root_list = auto_generate_from_folders(base_dir)
        
        if not images_root_list:
            print("未找到任何列车数据文件夹")
            return
        
        print(f"\n成功提取 {len(images_root_list)} 个列车的信息")
        print("="*80)
        
        # 遍历每个列车，按顺序输出信息
        for i, info in enumerate(public_info):
            print(f"\n第 {i+1} 个列车信息：")
            print("-"*50)
            
            # 1. 先获取整车信息
            print("【整车信息】")
            print(f"  车次：{info['vehicleInfo']}")
            print(f"  探测站：{info['recordStation']}")
            print(f"  运行方向：{info['travelDirection']}")
            print(f"  担当局：{info['bureau']}")
            print(f"  客整所：{info['section']}")
            if 'totalSequence' in info:
                print(f"  总辆数：{info['totalSequence']}")
            
            # 2. 然后是车号信息
            print("\n【车号信息】")
            vehicle_numbers = {}
            if i < len(num_list):
                lines = num_list[i].strip().split('\n')
                for line in lines:
                    if '\t' in line:
                        parts = line.strip().split('\t')
                        if len(parts) == 2 and parts[0].isdigit():
                            vehicle_numbers[parts[0]] = parts[1]
            
            if vehicle_numbers:
                # 按辆序排序显示
                sorted_vehicles = sorted(vehicle_numbers.items(), key=lambda x: int(x[0]))
                for seq_num, vehicle_id in sorted_vehicles:
                    print(f"  辆序 {seq_num}：车号 {vehicle_id}")
                print(f"  共计：{len(vehicle_numbers)} 辆车")
            else:
                print("  未提取到车号信息")
            
            # 3. 最后是图片信息
            print("\n【图片信息】")
            if i < len(images_root_list):
                root_dir = images_root_list[i]
                # 获取图片文件
                from glob import glob
                images_list = glob(os.path.join(root_dir, "*.jpg"))
                images_list.sort()
                
                if images_list:
                    # 按车厢号分组统计图片
                    car_image_count = {}
                    for image_path in images_list:
                        try:
                            image_name = os.path.basename(image_path)
                            car_num, direction_num = split_seq_direction(image_name)
                            
                            if car_num not in car_image_count:
                                car_image_count[car_num] = 0
                            car_image_count[car_num] += 1
                        except Exception as e:
                            continue
                    
                    # 显示图片统计信息
                    if car_image_count:
                        sorted_cars = sorted(car_image_count.items(), key=lambda x: int(x[0]))
                        for car_num, count in sorted_cars:
                            print(f"  车厢 {car_num}：{count} 张图片")
                        print(f"  图片总数：{sum(car_image_count.values())} 张")
                        print(f"  图片路径：{root_dir}")
                    else:
                        print(f"  图片总数：{len(images_list)} 张")
                        print(f"  图片路径：{root_dir}")
                else:
                    print("  未找到图片文件")
            else:
                print("  未找到图片路径")
            
            print("="*80)
        
        # 总结信息
        total_vehicles = sum(len(num_list[i].strip().split('\n')) for i in range(len(num_list)) if num_list[i].strip())
        print(f"\n【总结】")
        print(f"成功处理 {len(images_root_list)} 个列车")
        print(f"总计提取 {total_vehicles} 辆车的信息")
        
        # 添加上传功能
        print("\n" + "="*80)
        print("开始上传数据到服务器...")
        upload_data_to_server(num_list, public_info, images_root_list)
        
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()

# 原有的辅助函数保持不变
def split_seq_direction(name):
    """
    解析图片文件名，提取车厢号和监控方向信息
    （保持原有逻辑不变）
    """
    parts = name.split('车')
    if len(parts) != 2:
        raise ValueError("文件名格式不正确，应包含'车'字")
    
    car_num = parts[0].strip()
    direction_part = parts[1].split('监控')[0].strip()
    
    direction_to_num = {
        '右侧': 0, '左侧': 1, '底中': 2, '底右': 3, '底左': 4,
    }
    
    direction_num = direction_to_num[direction_part]
    return car_num, direction_num

class FolderWatcher(FileSystemEventHandler):
    """
    文件夹监听器类
    
    功能说明：
    监听指定目录下的文件夹创建事件，自动处理新增的列车数据文件夹
    """
    
    def __init__(self, base_directory):
        """
        初始化监听器
        
        参数说明：
        :param base_directory: 要监听的根目录
        """
        self.base_directory = base_directory
        self.processed_folders = set()  # 记录已处理的文件夹
        self.load_processed_folders()  # 加载已处理文件夹列表
    
    def load_processed_folders(self):
        """
        加载已处理的文件夹列表
        
        功能说明：
        从记录文件中读取已处理的文件夹列表，避免重复处理
        """
        record_file = os.path.join(self.base_directory, '.processed_folders.txt')
        if os.path.exists(record_file):
            try:
                with open(record_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        folder_path = line.strip()
                        if folder_path:
                            self.processed_folders.add(folder_path)
                print(f"已加载 {len(self.processed_folders)} 个已处理文件夹记录")
            except Exception as e:
                print(f"加载已处理文件夹记录失败: {e}")
    
    def save_processed_folder(self, folder_path):
        """
        保存已处理的文件夹到记录文件
        
        参数说明：
        :param folder_path: 已处理的文件夹路径
        
        功能说明：
        将新处理的文件夹路径追加到记录文件中
        """
        record_file = os.path.join(self.base_directory, '.processed_folders.txt')
        try:
            with open(record_file, 'a', encoding='utf-8') as f:
                f.write(folder_path + '\n')
            self.processed_folders.add(folder_path)
        except Exception as e:
            print(f"保存已处理文件夹记录失败: {e}")
    
    def on_created(self, event):
        """
        文件夹创建事件处理
        
        参数说明：
        :param event: 文件系统事件对象
        
        功能说明：
        当检测到新文件夹创建时，检查是否为列车数据文件夹并进行处理
        """
        if event.is_directory:
            folder_path = event.src_path
            folder_name = os.path.basename(folder_path)
            
            # 检查是否为列车信息文件夹
            keywords = ["车次列车车辆信息", "列车车辆信息", "车辆信息"]
            if any(keyword in folder_name for keyword in keywords):
                # 避免重复处理
                if folder_path not in self.processed_folders:
                    print(f"\n检测到新的列车数据文件夹: {folder_name}")
                    # 延迟处理，确保文件夹内容完全创建
                    threading.Timer(5.0, self.process_new_folder, args=[folder_path]).start()
    
    def process_new_folder(self, folder_path):
        """
        处理新增的列车数据文件夹
        
        参数说明：
        :param folder_path: 新增文件夹的路径
        
        功能说明：
        对新增的列车数据文件夹进行解析、验证和上传
        """
        folder_name = os.path.basename(folder_path)
        
        try:
            print(f"开始处理新文件夹: {folder_name}")
            
            # 查找信息文件
            info_files = find_info_files(folder_path)
            
            if not info_files:
                print(f"❌ 文件夹 {folder_name} 中未找到信息文件，跳过处理")
                return
            
            # 解析信息文件
            target_file = None
            for file_path in info_files:
                file_name = os.path.basename(file_path)
                if "列车信息" in file_name or "车辆信息" in file_name:
                    target_file = file_path
                    break
            
            if not target_file:
                target_file = info_files[0]
            
            # 解析文件内容
            vehicle_numbers, train_info = parse_vehicle_info_from_file(target_file)
            
            # 补充缺失的信息
            if 'recordStation' not in train_info or not train_info['recordStation']:
                folder_info = parse_folder_name_simple(folder_name)
                train_info.update(folder_info)
            
            # 验证数据完整性
            is_complete, missing_info = validate_train_data_completeness(train_info, vehicle_numbers, 1)
            
            if not is_complete:
                print(f"❌ 文件夹 {folder_name} 数据不完整，跳过上传")
                for info in missing_info:
                    print(f"   - {info}")
                return
            
            # 确保所有必需字段都存在
            if 'totalSequence' not in train_info:
                train_info['totalSequence'] = len(vehicle_numbers)
            
            # 生成数据结构
            num_str = generate_num_list_string(vehicle_numbers)
            num_list = [num_str]
            public_info = [train_info]
            images_root_list = [folder_path]
            
            print(f"✅ 文件夹 {folder_name} 数据验证通过，开始上传")
            print(f"   车次: {train_info['vehicleInfo']}")
            print(f"   车辆数: {len(vehicle_numbers)} 辆")
            
            # 上传数据到服务器
            upload_data_to_server(num_list, public_info, images_root_list)
            
            # 记录已处理的文件夹
            self.save_processed_folder(folder_path)
            
            print(f"✅ 文件夹 {folder_name} 处理完成")
            
        except Exception as e:
            print(f"❌ 处理文件夹 {folder_name} 时出错: {e}")
            import traceback
            traceback.print_exc()

def start_folder_monitoring(base_directory):
    """
    启动文件夹监听服务
    
    参数说明：
    :param base_directory: 要监听的根目录
    
    功能说明：
    启动文件系统监听器，实时监控新增文件夹
    """
    if not os.path.exists(base_directory):
        print(f"监听目录不存在: {base_directory}")
        return
    
    print(f"开始监听目录: {base_directory}")
    print("等待新的列车数据文件夹...")
    print("按 Ctrl+C 停止监听")
    
    # 创建监听器
    event_handler = FolderWatcher(base_directory)
    observer = Observer()
    observer.schedule(event_handler, base_directory, recursive=True)
    
    # 启动监听
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止监听...")
        observer.stop()
    
    observer.join()
    print("监听已停止")

def process_existing_folders_once(base_directory):
    """
    一次性处理现有文件夹（可选功能）
    
    参数说明：
    :param base_directory: 包含列车数据文件夹的根目录
    
    功能说明：
    处理目录中现有的所有文件夹，并记录到已处理列表中
    这个函数可以在首次启动监听前运行，避免重复处理现有文件夹
    """
    print("正在处理现有文件夹...")
    
    # 使用原有的批量处理功能
    num_list, public_info, images_root_list = auto_generate_from_folders(base_directory)
    
    if images_root_list:
        # 上传数据
        upload_data_to_server(num_list, public_info, images_root_list)
        
        # 记录所有已处理的文件夹
        watcher = FolderWatcher(base_directory)
        for folder_path in images_root_list:
            watcher.save_processed_folder(folder_path)
        
        print(f"已处理并记录 {len(images_root_list)} 个现有文件夹")
    else:
        print("未找到可处理的现有文件夹")

def main_with_monitoring():
    """
    带监听功能的主函数
    
    功能说明：
    1. 可选择一次性处理现有文件夹
    2. 启动实时监听服务
    3. 只对新增文件夹进行处理
    """
    # 设置列车数据的根目录
    base_dir = r"D:\tvds-system\TV故障及全列图片"
    
    print("=" * 80)
    print("列车数据文件夹监听服务")
    print("=" * 80)
    
    # 询问是否处理现有文件夹
    choice = input("是否先处理现有文件夹？(y/n，默认n): ").strip().lower()
    
    if choice == 'y' or choice == 'yes':
        process_existing_folders_once(base_dir)
        print("\n现有文件夹处理完成，开始监听新增文件夹...\n")
    
    # 启动监听服务
    start_folder_monitoring(base_dir)

# ... existing code ...

# 修改程序入口
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        # 启动监听模式
        main_with_monitoring()
    else:
        # 原有的批量处理模式
        main()