from src.smart_decision_miniproject.solver.VRP import solve_solomon_vrp

def test_solomon_parser():
    """测试Solomon数据解析器"""
    
    # 测试数据
    test_data = """C101

VEHICLE
NUMBER     CAPACITY
  25         200

CUSTOMER
CUST NO.  XCOORD.   YCOORD.    DEMAND   READY TIME  DUE DATE   SERVICE   TIME
 
    0      40         50          0          0       1236          0   
    1      45         68         10        912        967         90   
    2      45         70         30        825        870         90   
    3      42         66         10         65        146         90   
    4      42         68         10        727        782         90   
    5      42         65         10         15         67         90   
    6      40         69         20        621        702         90   
    7      40         66         20        170        225         90   
"""

    print("=== 测试Solomon数据解析 ===")
    
    try:
        result = solve_solomon_vrp(test_data)
        
        print("✓ 解析成功!")
        print(f"客户数量: {len(result.customers)}")
        print(f"使用车辆数: {result.num_vehicles_used}")
        print(f"总距离: {result.total_distance:.2f}")
        print(f"求解时间: {result.solve_time:.3f}秒")
        
        print("\n路径详情:")
        for i, route in enumerate(result.routes):
            if route:
                total_demand = sum(result.customers[j].demand for j in route) if route else 0
                print(f"车辆 {i+1}: 路径 {route}, 总需求: {total_demand}")
        
        print("\n统计信息:")
        stats = result.get_statistics()
        for key, value in stats.items():
            if key != 'routes_details':
                print(f"  {key}: {value}")
                
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_solomon_parser()