from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time


class GeoUtils:
    @staticmethod
    def calculate_distance(site1_name: str, site2_name: str) -> int:
        """
        计算两个地点之间的距离（以公里为单位，返回整数）
        
        Args:
            site1_name (str): 第一个地点的名称
            site2_name (str): 第二个地点的名称
            
        Returns:
            int: 两地点之间的距离，以公里为单位（四舍五入到整数）
            
        Raises:
            ValueError: 如果无法找到地点的坐标
            
        Example:
            >>> distance = GeoUtils.calculate_distance("Paris", "London")
            >>> print(distance)  # 约 344 公里
        """
        # 创建地理编码器，增加超时设置
        geolocator = Nominatim(
            user_agent="smart_decision_miniproject",
            timeout=10 # type: ignore
        )
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # 获取两个地点的坐标
                location1 = geolocator.geocode(site1_name)
                if location1 is None:
                    raise ValueError(f"无法找到地点: {site1_name}")
                
                # 稍微延迟以避免请求过于频繁
                time.sleep(0.5)
                
                location2 = geolocator.geocode(site2_name)
                if location2 is None:
                    raise ValueError(f"无法找到地点: {site2_name}")
                
                # 提取经纬度 - 使用 getattr 安全访问属性
                try:
                    lat1 = getattr(location1, 'latitude', None)
                    lon1 = getattr(location1, 'longitude', None)
                    lat2 = getattr(location2, 'latitude', None)
                    lon2 = getattr(location2, 'longitude', None)
                    
                    if lat1 is None or lon1 is None:
                        raise ValueError(f"无法获取 {site1_name} 的坐标")
                    if lat2 is None or lon2 is None:
                        raise ValueError(f"无法获取 {site2_name} 的坐标")
                        
                    coords1 = (lat1, lon1)
                    coords2 = (lat2, lon2)
                except AttributeError:
                    raise ValueError("坐标访问错误")
                
                # 计算距离
                distance = geodesic(coords1, coords2).kilometers
                
                # 返回四舍五入到整数的距离
                return round(distance)
                
            except ValueError:
                # 重新抛出 ValueError 以保持错误信息
                raise
            except Exception as e:
                if attempt == max_retries - 1:  # 最后一次尝试
                    raise ValueError(f"计算距离时出错 (尝试 {max_retries} 次后失败): {str(e)}")
                else:
                    print(f"尝试 {attempt + 1} 失败，{retry_delay} 秒后重试: {str(e)}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
        
        raise ValueError("未知错误")  # 理论上不会到达这里


def main():
    """
    测试 GeoUtils.calculate_distance 方法的主函数
    """
    print("=== GeoUtils 距离计算测试 ===\n")
    
    # 测试用例列表：(地点1, 地点2, 预期大概距离)
    test_cases = [
        ("Beijing", "Shanghai", "约 1000 公里"),
        ("Paris", "London", "约 340 公里"),
        ("New York", "Los Angeles", "约 3900 公里"),
        ("Tokyo", "Osaka", "约 400 公里"),
        ("广州", "深圳", "约 120 公里")
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, (city1, city2, expected) in enumerate(test_cases, 1):
        print(f"测试 {i}/{total_tests}: {city1} -> {city2}")
        print(f"预期距离: {expected}")
        
        try:
            distance = GeoUtils.calculate_distance(city1, city2)
            print(f"计算结果: {distance} 公里")
            print("✓ 成功\n")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 失败: {e}\n")
    
    # 输出测试总结
    print("=" * 40)
    print(f"测试完成: {success_count}/{total_tests} 个测试通过")
    
    if success_count == total_tests:
        print("🎉 所有测试都成功通过！")
    elif success_count > 0:
        print("⚠️  部分测试通过，可能存在网络问题")
    else:
        print("❌ 所有测试都失败，请检查网络连接")


if __name__ == "__main__":
    main()