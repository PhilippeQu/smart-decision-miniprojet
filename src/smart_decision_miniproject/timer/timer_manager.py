
"""
时间管理器模块

提供对多个计时器的统一管理功能
"""

from typing import Dict, List, Optional
from .timer import Timer


class TimerManager:
    """时间管理器类，用于管理多个计时器"""
    
    def __init__(self):
        """初始化时间管理器"""
        self.timers: Dict[str, Timer] = {}
        self.active_timers: List[str] = []
    
    def create_timer(self, name: str) -> Timer:
        """
        创建一个新的计时器
        
        Args:
            name: 计时器名称
            
        Returns:
            Timer: 创建的计时器实例
        """
        if name in self.timers:
            print(f"警告: 计时器 '{name}' 已存在，将覆盖原有计时器")
        
        timer = Timer(name)
        self.timers[name] = timer
        return timer
    
    def get_timer(self, name: str) -> Optional[Timer]:
        """
        获取指定名称的计时器
        
        Args:
            name: 计时器名称
            
        Returns:
            Timer: 计时器实例，如果不存在则返回 None
        """
        return self.timers.get(name)
    
    def start_timer(self, name: str) -> None:
        """
        启动指定计时器
        
        Args:
            name: 计时器名称
        """
        if name not in self.timers:
            self.create_timer(name)
        
        timer = self.timers[name]
        timer.start()
        
        if name not in self.active_timers:
            self.active_timers.append(name)
    
    def stop_timer(self, name: str) -> Optional[float]:
        """
        停止指定计时器
        
        Args:
            name: 计时器名称
            
        Returns:
            float: 经过的时间，如果计时器不存在或未启动则返回 None
        """
        if name not in self.timers:
            print(f"错误: 计时器 '{name}' 不存在")
            return None
        
        timer = self.timers[name]
        try:
            elapsed = timer.stop()
            if name in self.active_timers:
                self.active_timers.remove(name)
            return elapsed
        except RuntimeError as e:
            print(f"错误: {e}")
            return None
    
    def stop_all_timers(self) -> Dict[str, float]:
        """
        停止所有活动的计时器
        
        Returns:
            Dict[str, float]: 所有计时器的耗时结果
        """
        results = {}
        for timer_name in self.active_timers.copy():
            elapsed = self.stop_timer(timer_name)
            if elapsed is not None:
                results[timer_name] = elapsed
        return results
    
    def get_timer_status(self, name: str) -> str:
        """
        获取计时器状态
        
        Args:
            name: 计时器名称
            
        Returns:
            str: 计时器状态描述
        """
        if name not in self.timers:
            return "不存在"
        
        timer = self.timers[name]
        if timer.start_time is not None and timer.end_time is None:
            return "运行中"
        elif timer.elapsed_time is not None:
            return f"已完成 (耗时: {timer.elapsed_time:.6f}秒)"
        else:
            return "未启动"
    
    def list_timers(self) -> None:
        """列出所有计时器及其状态"""
        if not self.timers:
            print("没有任何计时器")
            return
        
        print("\n计时器列表:")
        print("-" * 50)
        for name, timer in self.timers.items():
            status = self.get_timer_status(name)
            print(f"  {name}: {status}")
        print("-" * 50)
    
    def get_active_timers(self) -> List[str]:
        """
        获取所有活动的计时器名称
        
        Returns:
            List[str]: 活动计时器名称列表
        """
        return self.active_timers.copy()
    
    def remove_timer(self, name: str) -> bool:
        """
        移除指定计时器
        
        Args:
            name: 计时器名称
            
        Returns:
            bool: 是否成功移除
        """
        if name not in self.timers:
            print(f"错误: 计时器 '{name}' 不存在")
            return False
        
        # 如果计时器正在运行，先停止它
        if name in self.active_timers:
            self.stop_timer(name)
        
        del self.timers[name]
        print(f"计时器 '{name}' 已移除")
        return True
    
    def clear_all(self) -> None:
        """清除所有计时器"""
        self.stop_all_timers()
        self.timers.clear()
        self.active_timers.clear()
        print("所有计时器已清除")
    
    def print_summary(self) -> None:
        """打印管理器摘要信息"""
        total_timers = len(self.timers)
        active_count = len(self.active_timers)
        completed_count = 0
        
        print("\n时间管理器摘要:")
        print("=" * 40)
        print(f"总计时器数量: {total_timers}")
        print(f"活动计时器数量: {active_count}")
        
        # 统计已完成的计时器
        for name, timer in self.timers.items():
            if timer.elapsed_time is not None:
                completed_count += 1
                print(f"  {name}: {timer.elapsed_time:.6f}秒")
        
        print(f"已完成计时器数量: {completed_count}")
        
        if self.active_timers:
            print(f"\n活动中的计时器: {', '.join(self.active_timers)}")
        
        print("=" * 40)


# 全局时间管理器实例
default_manager = TimerManager()