"""
合同查询服务

提供合同查询、验证等功能，供 Agent 工具使用。
支持 Redis 缓存加速查询。
"""
import json
import logging
from typing import Optional, Dict, Any
from redis import Redis
from sqlalchemy.orm import Session
from 合同审查.app.core import SessionLocal
from 合同审查.model.contract import Contract

logger = logging.getLogger(__name__)
db = SessionLocal()


class ContractService:
    """合同查询服务

    注入 Redis 客户端用于缓存合同数据，减少数据库查询压力。
    """

    # Redis 缓存键前缀
    CACHE_KEY_PREFIX = "contract:"
    CACHE_TTL = 3600  # 缓存1小时

    def __init__(self, redis_client: Optional[Redis] = None):
        """
        初始化合同服务

        Args:
            redis_client: Redis 客户端实例，为 None 时不使用缓存
        """
        # 注入 Redis 客户端
        self.redis = redis_client
        if redis_client:
            logger.info("ContractService: 使用传入的 Redis 客户端")
        else:
            logger.info("ContractService: 未提供 Redis 客户端，将使用无缓存模式")

    def _get_cache_key(self, key: Optional[str], contract_id: int) -> str:
        """生成缓存键"""
        if key:
            return f"{key}:{contract_id}"
        return f"{self.CACHE_KEY_PREFIX}{contract_id}"

    def _get_cache_key_by_name(self, key: Optional[str], contract_name: str) -> str:
        """根据名称生成缓存键"""
        if key:
            return f"{key}:{contract_name}"
        return f"{self.CACHE_KEY_PREFIX}name:{contract_name}"

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """从 Redis 缓存获取数据"""
        if self.redis is None:
            return None
        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Redis 缓存读取失败: {e}")
        return None

    def _set_to_cache(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """写入 Redis 缓存"""
        if self.redis is None:
            return False
        try:
            ttl = ttl or self.CACHE_TTL
            self.redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
            return True
        except Exception as e:
            logger.warning(f"Redis 缓存写入失败: {e}")
            return False

    def _delete_from_cache(self, key: str) -> bool:
        """从 Redis 缓存删除数据"""
        if self.redis is None:
            return False
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis 缓存删除失败: {e}")
            return False

    def get_contract_by_id(self, contract_id: int, db: Session) -> dict[str, Any] | str:
        """
        根据合同ID查询合同信息

        优先从 Redis 缓存读取，缓存未命中则查询数据库并写入缓存。

        Args:
            contract_id: 合同ID
            db: 数据库会话

        Returns:
            合同信息字典，如果不存在返回提示字符串
        """
        cache_key = self._get_cache_key(None, contract_id)

        # 1. 尝试从缓存读取
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"合同 {contract_id} 缓存命中")
            return cached_data

        # 2. 缓存未命中，查询数据库
        contract = db.query(Contract).filter(Contract.id == contract_id).scalar()
        if contract:
            result = {
                "id": contract.id,
                "contract_name": contract.file_name,
                "file_path": contract.file_path,
                "review_status": contract.review_status,
                "risk_level": contract.risk_level,
                "review_score": contract.review_score,
                "created_at": str(contract.created_at) if contract.created_at else None,
            }
            # 3. 写入缓存
            self._set_to_cache(cache_key, result)
            logger.debug(f"合同 {contract_id} 已缓存")
            return result

        return "根据所提供的合同id，并未查询到相关合同文件"

    def get_contract_by_name(self, contract_name: str, db: Session) -> dict[str, Any] | str:
        """
        根据合同名称查询合同信息

        优先从 Redis 缓存读取，缓存未命中则查询数据库并写入缓存。

        Args:
            contract_name: 合同名称
            db: 数据库会话

        Returns:
            合同信息字典，如果不存在返回提示字符串
        """
        cache_key = self._get_cache_key_by_name(None, contract_name)

        # 1. 尝试从缓存读取
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"合同 '{contract_name}' 缓存命中")
            return cached_data

        # 2. 缓存未命中，查询数据库
        contract = db.query(Contract).filter(Contract.file_name == contract_name).scalar()
        if contract:
            result = {
                "id": contract.id,
                "contract_name": contract.file_name,
                "file_path": contract.file_path,
                "review_status": contract.review_status,
                "risk_level": contract.risk_level,
                "review_score": contract.review_score,
                "created_at": str(contract.created_at) if contract.created_at else None,
            }
            # 3. 写入缓存
            self._set_to_cache(cache_key, result)
            # 同时按ID缓存，方便后续通过ID查询时也能命中
            id_cache_key = self._get_cache_key(None, contract.id)
            self._set_to_cache(id_cache_key, result)
            logger.debug(f"合同 '{contract_name}' (ID: {contract.id}) 已缓存")
            return result

        return "根据所提供的合同名称，并未查询到相关合同文件"

    def check_contract_exists(self, contract_id: Optional[int] = None, contract_name: Optional[str] = None) -> bool:
        """
        检查合同是否存在

        Args:
            contract_id: 合同ID（可选）
            contract_name: 合同名称（可选）

        Returns:
            是否存在
        """
        if contract_id:
            return self.get_contract_by_id(contract_id, db) is not None
        if contract_name:
            return self.get_contract_by_name(contract_name, db) is not None
        return False

    def invalidate_cache(self, contract_id: Optional[int] = None, contract_name: Optional[str] = None) -> bool:
        """
        使缓存失效

        当合同数据更新时调用，清除对应缓存。

        Args:
            contract_id: 合同ID（可选）
            contract_name: 合同名称（可选）

        Returns:
            是否成功
        """
        success = True

        if contract_id:
            key = self._get_cache_key(contract_id)
            if not self._delete_from_cache(key):
                success = False
            else:
                logger.info(f"合同 {contract_id} 缓存已清除")

        if contract_name:
            key = self._get_cache_key_by_name(contract_name)
            if not self._delete_from_cache(key):
                success = False
            else:
                logger.info(f"合同 '{contract_name}' 缓存已清除")

        return success

    def clear_all_cache(self) -> bool:
        """
        清除所有合同缓存

        Returns:
            是否成功
        """
        if self.redis is None:
            return False
        try:
            pattern = f"{self.CACHE_KEY_PREFIX}*"
            keys = list(self.redis.scan_iter(match=pattern))
            if keys:
                self.redis.delete(*keys)
                logger.info(f"已清除 {len(keys)} 个合同缓存")
            return True
        except Exception as e:
            logger.error(f"清除所有缓存失败: {e}")
            return False


# 单例实例
_contract_service: Optional[ContractService] = None


def get_contract_service(redis_client: Optional[Redis] = None) -> ContractService:
    """
    获取合同服务实例（单例模式）

    Args:
        redis_client: 可选的 Redis 客户端，用于首次初始化

    Returns:
        ContractService 实例
    """
    global _contract_service
    if _contract_service is None:
        _contract_service = ContractService(redis_client=redis_client)
    return _contract_service
