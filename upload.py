# 导入必要的Python模块
import os  # 操作系统相关功能，用于文件路径操作
from glob import glob  # 文件路径匹配工具，可以用通配符搜索文件
import requests  # HTTP请求库，用于发送网络请求
#abcdef
# 车辆编号对应表 - 每个列表对应一个车次的车辆编号信息
# 格式：车厢序号\t车辆编号
num_list = [
    """
    1	998551
    2	60512
    3	675920
    4	060520
    5	673296
    6	673972
    7	554359
    8	893339
    9	030851
    10	347810
    11	348832
    12	XXXXXX  # 这个车厢编号未知或有问题
    13	350487
    14	348827
    15	350526
    """,
    """
    1	676224
    2	676213
    3	676228
    4	676230
    5	676204
    6	676211
    7	554414
    8	893385
    9	350700
    10	356966
    11	353051
    12	353894
    13	350690
    14	350685
    15	350702
    """,
    """
    1	354736
    2	352676
    3	354740
    4	353744
    5	352175
    6	354739
    7	358279
    8	356974
    9	894029
    10	680941
    11	680972
    12	679628
    13	678175
    """,
    """
    1	206567
    2	030238
    3	030236
    4	347808  # 这是你选中的那一行
    5	347668
    6	347890
    7	348841
    8	080029
    9	553409
    10	673312
    11	671884
    12	671881
    13	060102
    14	673964
    15	998834
    """
]

# 车次基本信息 - 每个字典对应一个车次的详细信息
public_info = [
    {
        "recordStation": "合九线合肥上行到达",  # 记录站点
        "travelDirection": "上行",  # 行驶方向
        "bureau": "上海铁路局",  # 所属铁路局
        "section": "合肥整备所",  # 整备段
        "totalSequence": 15,  # 总车厢数
        "vehicleInfo": "K1072"  # 车次号
    },
    {
        "recordStation": "沪昆线杭州下行到达",
        "travelDirection": "下行",
        "bureau": "上海铁路局",
        "section": "徐州整备所",
        "totalSequence": 13,
        "vehicleInfo": "K5687"
    },
    {
        "recordStation": "沪昆线杭州下行到达",
        "travelDirection": "下行",
        "bureau": "上海铁路局",
        "section": "徐州整备所",
        "totalSequence": 13,
        "vehicleInfo": "K5687"
    },
    {
        "recordStation": "京沪线上海上海南下行到达",
        "travelDirection": "下行",
        "bureau": "上海铁路局",
        "section": "阜阳整备所",
        "totalSequence": 15,
        "vehicleInfo": "K8361"
    }
]

# 图片文件夹路径列表 - 存放各个车次检测图片的文件夹
images_root_list = [
    r"D:\tvds-system\TV故障及全列图片\5.5-K1072\2025年05月05日10时21分27秒京九线北京西上行到达(固安)探测站K1072车次列车车辆信息及故障信息过车图片",
    r"D:\tvds-system\TV故障及全列图片\5.6-K92\2025年05月06日11时44分04秒合九线合肥上行到达探测站K92车次列车车辆信息及故障信息过车图片",
    r"D:\tvds-system\TV故障及全列图片\5.10-K5687\2025年05月10日08时01分53秒沪昆线杭州下行到达探测站K5687车次列车车辆信息及故障信息过车图片",
    r"D:\tvds-system\TV故障及全列图片\5.12-K8361\2025年05月12日07时24分03秒京沪线上海上海南下行到达探测站K8361车次列车车辆信息及故障信息过车图片"
]

# 监控方向与数字编号的对应关系
# 用于将中文方向名称转换为数字编号
direction_to_num = {
    '右侧': 0,  # 车辆右侧监控
    '左侧': 1,  # 车辆左侧监控
    '底中': 2,  # 车辆底部中间监控
    '底右': 3,  # 车辆底部右侧监控
    '底左': 4,  # 车辆底部左侧监控
}


def decode_num_list(num_list_str, car_num):
    """
    从车辆编号列表中查找指定车厢号对应的车辆编号
    
    参数说明：
    :param num_list_str: 车辆编号列表字符串（来自num_list中的某一个）
    :param car_num: 要查找的车厢序号（如"1", "2", "3"等）
    
    返回值：
    :return: 对应的车辆编号（如"998551"）
    
    功能说明：
    这个函数的作用是根据车厢序号找到对应的车辆编号
    比如输入车厢号"4"，返回"347808"
    """
    # 将多行字符串按换行符分割成列表
    lines = num_list_str.strip().split('\n')
    
    # 遍历每一行数据
    for line in lines:
        # 按制表符(\t)分割每行，得到[车厢号, 车辆编号]
        parts = line.strip().split('\t')
        
        # 检查分割结果是否正确，且车厢号匹配
        if len(parts) == 2 and parts[0].strip() == car_num:
            return parts[1].strip()  # 返回对应的车辆编号
    
    # 如果没找到对应的车厢号，抛出异常
    raise ValueError(f"车号 {car_num} 在列表中未找到")


def split_seq_direction(name):
    """
    解析图片文件名，提取车厢号和监控方向信息
    
    参数说明：
    :param name: 图片文件名（如"10车右侧监控部位图片.jpg"）
    
    返回值：
    :return: 车厢号（如"10"）, 方向编号（如0表示右侧）
    
    功能说明：
    这个函数解析图片文件名，提取出车厢序号和监控方向
    文件名格式："车厢号+车+方向+监控部位图片.jpg"
    """
    # 以"车"字为分隔符分割文件名
    parts = name.split('车')
    
    # 检查分割结果，应该正好分成2部分
    if len(parts) != 2:
        raise ValueError("文件名格式不正确，应包含'车'字")
    
    # 第一部分是车厢号
    car_num = parts[0].strip()
    
    # 第二部分包含方向信息，提取"监控"前面的部分
    direction_part = parts[1].split('监控')[0].strip()
    
    # 将中文方向转换为数字编号
    direction_num = direction_to_num[direction_part]
    
    return car_num, direction_num


# 后端API接口地址 - 用于上传车辆检测数据
upload_url = "http://192.168.188.1:8080/api/v1/railway-vehicle"

# 主程序循环 - 处理每个车次的图片数据
for i, root_dir in enumerate(images_root_list):
    # 临时ID（这里写死了，实际项目中可能需要动态生成）
    _id = "asdbabsdbasb"
    
    # 打印当前处理的车次索引，方便调试
    print(i)
    
    # 使用glob搜索指定目录下的所有jpg图片文件
    # os.path.join()安全地拼接文件路径
    # "*.jpg"是通配符，匹配所有jpg文件
    images_list = glob(os.path.join(root_dir, "*.jpg"))
    
    # 对图片文件列表进行排序，确保处理顺序一致
    images_list.sort()
    
    # 创建字典，用于按车厢号分组存储图片路径
    # 结构：{"车厢号": [图片路径1, 图片路径2, ...]}
    car_num_dict = {}
    
    # 遍历所有图片文件，按车厢号分组
    for image_path in images_list:
        # 从完整路径中提取文件名
        image_name = os.path.basename(image_path)
        
        # 解析文件名，获取车厢号和监控方向
        car_num, direction_num = split_seq_direction(image_name)
        
        # 如果这个车厢号还没有记录，创建新的列表
        if car_num not in car_num_dict:
            car_num_dict[car_num] = []
        
        # 将图片路径添加到对应车厢号的列表中
        car_num_dict[car_num].append(image_path)
    
    # 获取当前车次的基本信息
    vehicleInfo = public_info[i]
    
    # 按车厢号排序，确保上传顺序正确
    # key=lambda x: int(x[0]) 表示按车厢号的数值大小排序
    car_num_list = sorted(list(car_num_dict.items()), key=lambda x: int(x[0]))
    
    # 遍历每个车厢，准备上传数据
    for car_num, image_paths in car_num_list:
        # 构造要上传的数据字典
        data = {
            'recordStation': vehicleInfo['recordStation'],  # 记录站点
            'travelDirection': vehicleInfo['travelDirection'],  # 行驶方向
            'vehicleInfo': vehicleInfo['vehicleInfo'],  # 车次信息
            'vehicleIdentity': decode_num_list(num_list[i], car_num),  # 车辆编号
            'bureau': vehicleInfo['bureau'],  # 铁路局
            'section': vehicleInfo['section'],  # 整备段
            'vehicleSeq': car_num,  # 车厢序号
            'totalSequence': vehicleInfo['totalSequence'],  # 总车厢数
        }
        
        # 准备文件上传列表
        files = []
        
        # 遍历当前车厢的所有图片
        for image_path in image_paths:
            # 以二进制只读模式打开图片文件
            # 'rb'中的'r'表示读取，'b'表示二进制模式
            f = open(image_path, 'rb')
            
            # 将文件对象添加到上传列表
            # ('imageFiles', f)是HTTP multipart格式要求的元组
            files.append(('imageFiles', f))
        
        # 发送POST请求上传数据和文件
        # data参数包含表单数据，files参数包含文件数据
        response = requests.post(upload_url, data=data, files=files)
        
        # 重要：关闭所有打开的文件，释放系统资源
        # 这是良好的编程习惯，避免文件句柄泄露
        for f in files:
            f[1].close()  # f[1]是文件对象，f[0]是字段名
        
        # 检查上传结果并打印状态信息
        if response.status_code == 200:
            print(f"车号 {car_num} 的数据上传成功")
        else:
            print(f"车号 {car_num} 的数据上传失败: {response.text}")
