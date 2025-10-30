"""
时间测量器模块

提供多种方式测量算法执行时间：
- 上下文管理器
- 装饰器
- 手动计时
"""

import time
import functools
from typing import Optional, Callable, Any, Dict, List
from contextlib import contextmanager


class Timer:
    """时间测量器类，支持多种计时方式"""
    
    def __init__(self, name: str = "Timer"):
        """
        初始化计时器
        
        Args:
            name: 计时器名称，用于标识不同的计时器
        """
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed_time: Optional[float] = None
        self.records: Dict[str, Any] = {}
    
    def start(self) -> None:
        """开始计时"""
        self.start_time = time.perf_counter()
        print(f"[{self.name}] 开始计时...")
    
    def stop(self) -> float:
        """
        停止计时
        
        Returns:
            float: 经过的时间（秒）
        """
        if self.start_time is None:
            raise RuntimeError("计时器尚未启动，请先调用 start() 方法")
        
        self.end_time = time.perf_counter()
        self.elapsed_time = self.end_time - self.start_time
        
        # 记录本次计时
        self.records.update({
            'start_time': self.start_time,
            'end_time': self.end_time,
            'elapsed_time': self.elapsed_time,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        print(f"[{self.name}] 计时结束，耗时: {self.elapsed_time:.6f} 秒")
        return self.elapsed_time
    
    def get_elapsed_time(self) -> Optional[float]:
        """获取最后一次的计时结果"""
        return self.elapsed_time
    
    # 上下文管理器支持
    def __enter__(self):
        """进入上下文时开始计时"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时停止计时"""
        self.stop()