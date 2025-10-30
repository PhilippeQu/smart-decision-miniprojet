import random
from abc import ABC, abstractmethod

from smart_decision_miniproject.TSP_datamodel.distance_matrix import DistanceMatrix
from smart_decision_miniproject.TSP_datamodel.geo_utils import GeoUtils


class BaseDistanceMatrixFactory(ABC):
    """Abstract base class for distance matrix factories."""

    @abstractmethod
    def create_distance_matrix(self) -> DistanceMatrix:
        pass


class RandomDistanceMatrixFactory(BaseDistanceMatrixFactory):

    def __init__(self, dimension: int, min_distance: int, max_distance: int):
        self.dimension = dimension
        self.min_distance = min_distance
        self.max_distance = max_distance

    def __str__(self):
        return f"RandomDistanceMatrixFactory(dimension={self.dimension}, min_distance={self.min_distance}, max_distance={self.max_distance})"

    def create_distance_matrix(self) -> DistanceMatrix:

        distance_matrix = DistanceMatrix(self.dimension)
        for i in range(self.dimension):
            for j in range(i + 1, self.dimension):
                distance = random.randint(self.min_distance, self.max_distance)
                distance_matrix.set_distance_between_sites_by_name(
                    f"site_{i}", f"site_{j}", distance
                )
        return distance_matrix

class GeographicDistanceMatrixFactory(BaseDistanceMatrixFactory):

    def __init__(self, site_name_list:list):
        self.site_name_list = site_name_list
        self.dimension = len(site_name_list)    
    
    def create_distance_matrix(self) -> DistanceMatrix:
        distance_matrix = DistanceMatrix(self.dimension)
        distance_matrix.set_site_name_list(self.site_name_list)
        for i in range(self.dimension):
            for j in range(i + 1, self.dimension):
                distance = GeoUtils.calculate_distance(
                    self.site_name_list[i], self.site_name_list[j]
                )
                distance_matrix.set_distance_between_sites_by_name(
                    self.site_name_list[i], self.site_name_list[j], distance
                )
        return distance_matrix

class ChineseCityDistanceMatrixFactory(BaseDistanceMatrixFactory):
    """中国城市距离矩阵工厂，使用预定义的距离数据"""
    
    # 预定义的中国主要城市间距离（公里）
    CITY_DISTANCES = {
        ('北京', '上海'): 1067,
        ('北京', '广州'): 1884,
        ('北京', '深圳'): 1943,
        ('北京', '天津'): 120,
        ('北京', '重庆'): 1447,
        ('北京', '杭州'): 1132,
        ('北京', '南京'): 899,
        ('北京', '武汉'): 1040,
        ('北京', '成都'): 1517,
        ('北京', '西安'): 1030,
        ('北京', '沈阳'): 631,
        ('北京', '青岛'): 550,
        ('北京', '大连'): 651,
        ('北京', '厦门'): 1550,
        ('北京', '苏州'): 1020,
        ('北京', '宁波'): 1180,
        ('北京', '无锡'): 1000,
        ('北京', '长沙'): 1250,
        ('北京', '昆明'): 2100,
        ('上海', '广州'): 1213,
        ('上海', '深圳'): 1247,
        ('上海', '天津'): 1000,
        ('上海', '重庆'): 1447,
        ('上海', '杭州'): 165,
        ('上海', '南京'): 266,
        ('上海', '武汉'): 695,
        ('上海', '成都'): 1650,
        ('上海', '西安'): 1200,
        ('上海', '沈阳'): 1100,
        ('上海', '青岛'): 630,
        ('上海', '大连'): 850,
        ('上海', '厦门'): 830,
        ('上海', '苏州'): 84,
        ('上海', '宁波'): 188,
        ('上海', '无锡'): 128,
        ('上海', '长沙'): 850,
        ('上海', '昆明'): 1900,
        ('广州', '深圳'): 120,
        ('广州', '天津'): 1800,
        ('广州', '重庆'): 1050,
        ('广州', '杭州'): 1050,
        ('广州', '南京'): 1100,
        ('广州', '武汉'): 850,
        ('广州', '成都'): 1200,
        ('广州', '西安'): 1300,
        ('广州', '沈阳'): 2000,
        ('广州', '青岛'): 1500,
        ('广州', '大连'): 1900,
        ('广州', '厦门'): 480,
        ('广州', '苏州'): 1100,
        ('广州', '宁波'): 950,
        ('广州', '无锡'): 1050,
        ('广州', '长沙'): 350,
        ('广州', '昆明'): 1200,
        ('深圳', '天津'): 1850,
        ('深圳', '重庆'): 1100,
        ('深圳', '杭州'): 1100,
        ('深圳', '南京'): 1150,
        ('深圳', '武汉'): 900,
        ('深圳', '成都'): 1250,
        ('深圳', '西安'): 1350,
        ('深圳', '沈阳'): 2050,
        ('深圳', '青岛'): 1550,
        ('深圳', '大连'): 1950,
        ('深圳', '厦门'): 450,
        ('深圳', '苏州'): 1150,
        ('深圳', '宁波'): 1000,
        ('深圳', '无锡'): 1100,
        ('深圳', '长沙'): 400,
        ('深圳', '昆明'): 1250,
        ('天津', '重庆'): 1350,
        ('天津', '杭州'): 1050,
        ('天津', '南京'): 800,
        ('天津', '武汉'): 950,
        ('天津', '成都'): 1400,
        ('天津', '西安'): 950,
        ('天津', '沈阳'): 550,
        ('天津', '青岛'): 450,
        ('天津', '大连'): 550,
        ('天津', '厦门'): 1450,
        ('天津', '苏州'): 950,
        ('天津', '宁波'): 1100,
        ('天津', '无锡'): 920,
        ('天津', '长沙'): 1150,
        ('天津', '昆明'): 2000,
        ('重庆', '杭州'): 1350,
        ('重庆', '南京'): 1200,
        ('重庆', '武汉'): 800,
        ('重庆', '成都'): 308,
        ('重庆', '西安'): 680,
        ('重庆', '沈阳'): 1650,
        ('重庆', '青岛'): 1350,
        ('重庆', '大连'): 1700,
        ('重庆', '厦门'): 1100,
        ('重庆', '苏州'): 1300,
        ('重庆', '宁波'): 1400,
        ('重庆', '无锡'): 1250,
        ('重庆', '长沙'): 750,
        ('重庆', '昆明'): 650,
        ('杭州', '南京'): 280,
        ('杭州', '武汉'): 680,
        ('杭州', '成都'): 1500,
        ('杭州', '西安'): 1100,
        ('杭州', '沈阳'): 1200,
        ('杭州', '青岛'): 700,
        ('杭州', '大连'): 1000,
        ('杭州', '厦门'): 750,
        ('杭州', '苏州'): 150,
        ('杭州', '宁波'): 150,
        ('杭州', '无锡'): 200,
        ('杭州', '长沙'): 750,
        ('杭州', '昆明'): 1800,
        ('南京', '武汉'): 480,
        ('南京', '成都'): 1300,
        ('南京', '西安'): 900,
        ('南京', '沈阳'): 950,
        ('南京', '青岛'): 500,
        ('南京', '大连'): 800,
        ('南京', '厦门'): 850,
        ('南京', '苏州'): 200,
        ('南京', '宁波'): 350,
        ('南京', '无锡'): 150,
        ('南京', '长沙'): 650,
        ('南京', '昆明'): 1700,
        ('武汉', '成都'): 850,
        ('武汉', '西安'): 630,
        ('武汉', '沈阳'): 1100,
        ('武汉', '青岛'): 800,
        ('武汉', '大连'): 1200,
        ('武汉', '厦门'): 750,
        ('武汉', '苏州'): 650,
        ('武汉', '宁波'): 700,
        ('武汉', '无锡'): 600,
        ('武汉', '长沙'): 350,
        ('武汉', '昆明'): 1200,
        ('成都', '西安'): 650,
        ('成都', '沈阳'): 1800,
        ('成都', '青岛'): 1500,
        ('成都', '大连'): 1900,
        ('成都', '厦门'): 1300,
        ('成都', '苏州'): 1500,
        ('成都', '宁波'): 1600,
        ('成都', '无锡'): 1450,
        ('成都', '长沙'): 1000,
        ('成都', '昆明'): 650,
        ('西安', '沈阳'): 1150,
        ('西安', '青岛'): 900,
        ('西安', '大连'): 1250,
        ('西安', '厦门'): 1200,
        ('西安', '苏州'): 1050,
        ('西安', '宁波'): 1200,
        ('西安', '无锡'): 1000,
        ('西安', '长沙'): 800,
        ('西安', '昆明'): 1100,
        ('沈阳', '青岛'): 650,
        ('沈阳', '大连'): 350,
        ('沈阳', '厦门'): 1650,
        ('沈阳', '苏州'): 1050,
        ('沈阳', '宁波'): 1200,
        ('沈阳', '无锡'): 1000,
        ('沈阳', '长沙'): 1400,
        ('沈阳', '昆明'): 2200,
        ('青岛', '大连'): 450,
        ('青岛', '厦门'): 1100,
        ('青岛', '苏州'): 600,
        ('青岛', '宁波'): 750,
        ('青岛', '无锡'): 550,
        ('青岛', '长沙'): 1000,
        ('青岛', '昆明'): 1900,
        ('大连', '厦门'): 1400,
        ('大连', '苏州'): 850,
        ('大连', '宁波'): 1000,
        ('大连', '无锡'): 800,
        ('大连', '长沙'): 1300,
        ('大连', '昆明'): 2100,
        ('厦门', '苏州'): 800,
        ('厦门', '宁波'): 650,
        ('厦门', '无锡'): 750,
        ('厦门', '长沙'): 500,
        ('厦门', '昆明'): 1400,
        ('苏州', '宁波'): 200,
        ('苏州', '无锡'): 50,
        ('苏州', '长沙'): 700,
        ('苏州', '昆明'): 1750,
        ('宁波', '无锡'): 180,
        ('宁波', '长沙'): 750,
        ('宁波', '昆明'): 1800,
        ('无锡', '长沙'): 650,
        ('无锡', '昆明'): 1700,
        ('长沙', '昆明'): 1000,
    }

    def __init__(self, site_name_list: list):
        self.site_name_list = site_name_list
        self.dimension = len(site_name_list)
    
    def _get_distance(self, city1: str, city2: str) -> float:
        """获取两个城市间的距离"""
        if city1 == city2:
            return 0.0
        
        # 尝试正向查找
        key = (city1, city2)
        if key in self.CITY_DISTANCES:
            return float(self.CITY_DISTANCES[key])
        
        # 尝试反向查找
        key = (city2, city1)
        if key in self.CITY_DISTANCES:
            return float(self.CITY_DISTANCES[key])
        
        # 如果找不到预定义距离，使用简单的估算方法
        # 基于城市名字生成一个伪随机但一致的距离
        import hashlib
        combined = city1 + city2
        hash_value = int(hashlib.md5(combined.encode()).hexdigest()[:8], 16)
        return float(500 + (hash_value % 2000))  # 500-2500公里范围
    
    def create_distance_matrix(self) -> DistanceMatrix:
        distance_matrix = DistanceMatrix(self.dimension)
        distance_matrix.set_site_name_list(self.site_name_list)
        
        for i in range(self.dimension):
            for j in range(i + 1, self.dimension):
                distance = self._get_distance(
                    self.site_name_list[i], self.site_name_list[j]
                )
                distance_matrix.set_distance_between_sites_by_name(
                    self.site_name_list[i], self.site_name_list[j], distance
                )
        
        return distance_matrix

if __name__ == "__main__":
    random_factory = RandomDistanceMatrixFactory(dimension=10, min_distance=10, max_distance=100)
    random_distance_matrix = random_factory.create_distance_matrix()
    print(random_distance_matrix)

    geographic_factory = GeographicDistanceMatrixFactory(site_name_list=["Beijing", "Shanghai", "Paris", "London"])
    geographic_distance_matrix = geographic_factory.create_distance_matrix()
    print(geographic_distance_matrix)