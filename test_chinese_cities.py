#!/usr/bin/env python3
"""测试中国城市距离矩阵工厂"""

from src.smart_decision_miniproject.TSP_datamodel.distance_matrix_factory import ChineseCityDistanceMatrixFactory

def test_chinese_cities():
    """测试中国城市距离计算"""
    cities = ['北京', '上海', '广州', '深圳']
    
    factory = ChineseCityDistanceMatrixFactory(cities)
    distance_matrix = factory.create_distance_matrix()
    
    print("中国城市距离矩阵测试：")
    print(f"城市列表: {cities}")
    print(distance_matrix)
    
    # 测试一些已知距离
    beijing_shanghai = distance_matrix.get_distance_between_sites_by_name('北京', '上海')
    print(f"北京到上海距离: {beijing_shanghai} 公里")
    
    guangzhou_shenzhen = distance_matrix.get_distance_between_sites_by_name('广州', '深圳')
    print(f"广州到深圳距离: {guangzhou_shenzhen} 公里")

if __name__ == "__main__":
    test_chinese_cities()