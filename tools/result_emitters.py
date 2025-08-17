"""
结构化结果发射工具 (兼容性导入)

此文件保留作为向后兼容入口，所有工具已迁移至 tools/emitters/ 模块化结构。

推荐使用新的导入方式：
from tools.emitters import emit_fundamental_analysis
或
from tools.emitters.analyst_emitters import emit_fundamental_analysis
"""

# 为保持向后兼容，重新导出所有工具
from .emitters import *

