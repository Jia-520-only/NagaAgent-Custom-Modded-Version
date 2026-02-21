"""
数据验证器

提供常用的数据验证函数

作者: NagaAgent Team
版本: 1.0.0
"""

import re
import logging
from typing import Any, Optional, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class Validator:
    """数据验证器"""

    @staticmethod
    def is_not_empty(value: Any, field_name: str = "value") -> bool:
        """检查非空

        Args:
            value: 待检查的值
            field_name: 字段名称（用于日志）

        Returns:
            是否非空
        """
        if value is None:
            logger.debug(f"[Validator] {field_name} 为 None")
            return False

        if isinstance(value, str) and not value.strip():
            logger.debug(f"[Validator] {field_name} 为空字符串")
            return False

        if isinstance(value, (list, dict)) and len(value) == 0:
            logger.debug(f"[Validator] {field_name} 为空集合")
            return False

        return True

    @staticmethod
    def is_url(url: str) -> bool:
        """检查是否为有效URL

        Args:
            url: 待检查的URL

        Returns:
            是否为有效URL
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception as e:
            logger.debug(f"[Validator] URL验证失败: {e}")
            return False

    @staticmethod
    def is_email(email: str) -> bool:
        """检查是否为有效邮箱

        Args:
            email: 待检查的邮箱

        Returns:
            是否为有效邮箱
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def is_integer(value: Any, min_val: Optional[int] = None, max_val: Optional[int] = None) -> bool:
        """检查是否为整数

        Args:
            value: 待检查的值
            min_val: 最小值（可选）
            max_val: 最大值（可选）

        Returns:
            是否为整数
        """
        if not isinstance(value, int):
            try:
                value = int(value)
            except (ValueError, TypeError):
                return False

        if min_val is not None and value < min_val:
            logger.debug(f"[Validator] 值 {value} 小于最小值 {min_val}")
            return False

        if max_val is not None and value > max_val:
            logger.debug(f"[Validator] 值 {value} 大于最大值 {max_val}")
            return False

        return True

    @staticmethod
    def is_float(value: Any, min_val: Optional[float] = None, max_val: Optional[float] = None) -> bool:
        """检查是否为浮点数

        Args:
            value: 待检查的值
            min_val: 最小值（可选）
            max_val: 最大值（可选）

        Returns:
            是否为浮点数
        """
        if not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                return False

        if min_val is not None and value < min_val:
            logger.debug(f"[Validator] 值 {value} 小于最小值 {min_val}")
            return False

        if max_val is not None and value > max_val:
            logger.debug(f"[Validator] 值 {value} 大于最大值 {max_val}")
            return False

        return True

    @staticmethod
    def is_string(value: Any, min_length: Optional[int] = None, max_length: Optional[int] = None) -> bool:
        """检查是否为字符串

        Args:
            value: 待检查的值
            min_length: 最小长度（可选）
            max_length: 最大长度（可选）

        Returns:
            是否为字符串
        """
        if not isinstance(value, str):
            return False

        if min_length is not None and len(value) < min_length:
            logger.debug(f"[Validator] 字符串长度 {len(value)} 小于最小长度 {min_length}")
            return False

        if max_length is not None and len(value) > max_length:
            logger.debug(f"[Validator] 字符串长度 {len(value)} 大于最大长度 {max_length}")
            return False

        return True

    @staticmethod
    def is_list(value: Any, item_type: type = None, min_length: Optional[int] = None, max_length: Optional[int] = None) -> bool:
        """检查是否为列表

        Args:
            value: 待检查的值
            item_type: 列表项类型（可选）
            min_length: 最小长度（可选）
            max_length: 最大长度（可选）

        Returns:
            是否为列表
        """
        if not isinstance(value, list):
            return False

        if item_type is not None:
            for item in value:
                if not isinstance(item, item_type):
                    logger.debug(f"[Validator] 列表项类型不匹配: {type(item)} != {item_type}")
                    return False

        if min_length is not None and len(value) < min_length:
            logger.debug(f"[Validator] 列表长度 {len(value)} 小于最小长度 {min_length}")
            return False

        if max_length is not None and len(value) > max_length:
            logger.debug(f"[Validator] 列表长度 {len(value)} 大于最大长度 {max_length}")
            return False

        return True

    @staticmethod
    def is_dict(value: Any, required_keys: Optional[List[str]] = None) -> bool:
        """检查是否为字典

        Args:
            value: 待检查的值
            required_keys: 必需键列表（可选）

        Returns:
            是否为字典
        """
        if not isinstance(value, dict):
            return False

        if required_keys:
            for key in required_keys:
                if key not in value:
                    logger.debug(f"[Validator] 字典缺少必需键: {key}")
                    return False

        return True

    @staticmethod
    def is_boolean(value: Any) -> bool:
        """检查是否为布尔值

        Args:
            value: 待检查的值

        Returns:
            是否为布尔值
        """
        return isinstance(value, bool)

    @staticmethod
    def is_json(value: str) -> bool:
        """检查是否为有效JSON字符串

        Args:
            value: 待检查的字符串

        Returns:
            是否为有效JSON
        """
        try:
            import json
            json.loads(value)
            return True
        except (json.JSONDecodeError, TypeError):
            return False

    @staticmethod
    def is_ipv4(ip: str) -> bool:
        """检查是否为IPv4地址

        Args:
            ip: 待检查的IP地址

        Returns:
            是否为IPv4地址
        """
        pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        return re.match(pattern, ip) is not None

    @staticmethod
    def is_port(port: Any) -> bool:
        """检查是否为有效端口号

        Args:
            port: 待检查的端口号

        Returns:
            是否为有效端口号
        """
        return Validator.is_integer(port, min_val=1, max_val=65535)

    @staticmethod
    def validate_params(params: dict, schema: dict) -> tuple[bool, Optional[str]]:
        """根据模式验证参数

        Args:
            params: 参数字典
            schema: 参数模式字典

        Returns:
            (是否有效, 错误消息)
        """
        # 检查必需参数
        for param_name, param_schema in schema.items():
            required = param_schema.get('required', False)

            if required and param_name not in params:
                return False, f"缺少必需参数: {param_name}"

            # 如果参数不存在且有默认值，跳过验证
            if param_name not in params:
                continue

            value = params[param_name]
            param_type = param_schema.get('type')

            # 类型验证
            if param_type == 'string' and not Validator.is_string(value):
                return False, f"参数类型错误: {param_name} 应为 string"

            elif param_type == 'integer' and not Validator.is_integer(value):
                return False, f"参数类型错误: {param_name} 应为 integer"

            elif param_type == 'float' and not Validator.is_float(value):
                return False, f"参数类型错误: {param_name} 应为 float"

            elif param_type == 'boolean' and not Validator.is_boolean(value):
                return False, f"参数类型错误: {param_name} 应为 boolean"

            elif param_type == 'array' and not Validator.is_list(value):
                return False, f"参数类型错误: {param_name} 应为 array"

            elif param_type == 'object' and not Validator.is_dict(value):
                return False, f"参数类型错误: {param_name} 应为 object"

            # 枚举值验证
            if 'enum' in param_schema:
                if value not in param_schema['enum']:
                    return False, f"参数值无效: {param_name} 应为 {param_schema['enum']} 之一"

            # 范围验证
            if 'minimum' in param_schema and isinstance(value, (int, float)):
                if value < param_schema['minimum']:
                    return False, f"参数值过小: {param_name} >= {param_schema['minimum']}"

            if 'maximum' in param_schema and isinstance(value, (int, float)):
                if value > param_schema['maximum']:
                    return False, f"参数值过大: {param_name} <= {param_schema['maximum']}"

        return True, None
