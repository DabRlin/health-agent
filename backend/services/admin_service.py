"""
管理员服务
"""
import logging
from typing import Optional, List, Tuple
from database import SessionLocal, Account, User, HealthKnowledge

logger = logging.getLogger(__name__)


class AdminService:
    """管理员服务类"""

    # ==================== 用户管理 ====================

    @classmethod
    def list_users(cls) -> List[dict]:
        """获取所有用户账户列表"""
        db = SessionLocal()
        try:
            accounts = db.query(Account).order_by(Account.id).all()
            result = []
            for acc in accounts:
                user = acc.user
                result.append({
                    "id": acc.id,
                    "username": acc.username,
                    "role": acc.role or 'user',
                    "is_active": acc.is_active,
                    "last_login": acc.last_login.isoformat() if acc.last_login else None,
                    "created_at": acc.created_at.isoformat() if acc.created_at else None,
                    "user_id": acc.user_id,
                    "user_name": user.name if user else None,
                })
            return result
        finally:
            db.close()

    @classmethod
    def toggle_user_active(cls, account_id: int) -> Tuple[bool, Optional[str]]:
        """启用/禁用用户账户"""
        db = SessionLocal()
        try:
            account = db.query(Account).filter(Account.id == account_id).first()
            if not account:
                return False, "账户不存在"
            if account.role == 'admin':
                return False, "不能禁用管理员账户"
            account.is_active = not account.is_active
            db.commit()
            return True, None
        except Exception as e:
            db.rollback()
            logger.exception("切换用户状态失败")
            return False, "操作失败"
        finally:
            db.close()

    @classmethod
    def reset_user_password(cls, account_id: int, new_password: str) -> Tuple[bool, Optional[str]]:
        """重置用户密码"""
        from werkzeug.security import generate_password_hash
        if not new_password or len(new_password) < 6:
            return False, "密码至少6位"
        db = SessionLocal()
        try:
            account = db.query(Account).filter(Account.id == account_id).first()
            if not account:
                return False, "账户不存在"
            account.password = generate_password_hash(new_password)
            db.commit()
            return True, None
        except Exception as e:
            db.rollback()
            logger.exception("重置密码失败")
            return False, "操作失败"
        finally:
            db.close()

    # ==================== 知识库管理 ====================

    @classmethod
    def list_knowledge(cls, category: Optional[str] = None) -> List[dict]:
        """获取知识库列表"""
        db = SessionLocal()
        try:
            q = db.query(HealthKnowledge).order_by(HealthKnowledge.id)
            if category:
                q = q.filter(HealthKnowledge.category == category)
            items = q.all()
            return [{
                "id": item.id,
                "category": item.category,
                "subcategory": item.subcategory,
                "title": item.title,
                "keywords": item.keywords,
                "content": item.content,
                "reference_data": item.reference_data,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            } for item in items]
        finally:
            db.close()

    @classmethod
    def get_knowledge(cls, item_id: int) -> Optional[dict]:
        """获取单条知识"""
        db = SessionLocal()
        try:
            item = db.query(HealthKnowledge).filter(HealthKnowledge.id == item_id).first()
            if not item:
                return None
            return {
                "id": item.id,
                "category": item.category,
                "subcategory": item.subcategory,
                "title": item.title,
                "keywords": item.keywords,
                "content": item.content,
                "reference_data": item.reference_data,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
        finally:
            db.close()

    @classmethod
    def create_knowledge(cls, data: dict) -> Tuple[bool, Optional[dict], Optional[str]]:
        """新增知识条目"""
        title = (data.get('title') or '').strip()
        category = (data.get('category') or '').strip()
        content = (data.get('content') or '').strip()
        if not title or not category or not content:
            return False, None, "标题、分类、内容不能为空"

        db = SessionLocal()
        try:
            item = HealthKnowledge(
                category=category,
                subcategory=(data.get('subcategory') or '').strip() or None,
                title=title,
                keywords=(data.get('keywords') or '').strip() or None,
                content=content,
                reference_data=data.get('reference_data'),
            )
            db.add(item)
            db.commit()
            return True, {"id": item.id, "title": item.title}, None
        except Exception as e:
            db.rollback()
            logger.exception("新增知识条目失败")
            return False, None, "创建失败"
        finally:
            db.close()

    @classmethod
    def update_knowledge(cls, item_id: int, data: dict) -> Tuple[bool, Optional[str]]:
        """更新知识条目"""
        db = SessionLocal()
        try:
            item = db.query(HealthKnowledge).filter(HealthKnowledge.id == item_id).first()
            if not item:
                return False, "条目不存在"

            for field in ('category', 'subcategory', 'title', 'keywords', 'content'):
                if field in data:
                    setattr(item, field, (data[field] or '').strip() or None)
            if 'reference_data' in data:
                item.reference_data = data['reference_data']

            db.commit()
            return True, None
        except Exception as e:
            db.rollback()
            logger.exception("更新知识条目失败")
            return False, "更新失败"
        finally:
            db.close()

    @classmethod
    def delete_knowledge(cls, item_id: int) -> Tuple[bool, Optional[str]]:
        """删除知识条目"""
        db = SessionLocal()
        try:
            item = db.query(HealthKnowledge).filter(HealthKnowledge.id == item_id).first()
            if not item:
                return False, "条目不存在"
            db.delete(item)
            db.commit()
            return True, None
        except Exception as e:
            db.rollback()
            logger.exception("删除知识条目失败")
            return False, "删除失败"
        finally:
            db.close()

    # ==================== 统计概览 ====================

    @classmethod
    def get_stats(cls) -> dict:
        """获取管理后台统计数据"""
        db = SessionLocal()
        try:
            from database import HealthRecord, Consultation, RiskAssessment
            return {
                "user_count": db.query(Account).count(),
                "active_user_count": db.query(Account).filter(Account.is_active == True).count(),
                "knowledge_count": db.query(HealthKnowledge).count(),
                "consultation_count": db.query(Consultation).count(),
                "record_count": db.query(HealthRecord).count(),
                "assessment_count": db.query(RiskAssessment).count(),
            }
        finally:
            db.close()
