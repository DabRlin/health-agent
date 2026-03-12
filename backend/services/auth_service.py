"""
认证服务
"""
import logging
from datetime import datetime
from typing import Optional, Tuple
from werkzeug.security import generate_password_hash, check_password_hash
from database import SessionLocal, Account, User
from utils.jwt_utils import generate_token

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务类"""
    
    @classmethod
    def login(cls, username: str, password: str) -> Tuple[bool, Optional[dict], Optional[str]]:
        """
        用户登录
        
        Returns:
            (success, user_data, error_message)
        """
        if not username or not password:
            return False, None, "请输入用户名和密码"
        
        username = username.strip()
        
        db = SessionLocal()
        try:
            account = db.query(Account).filter(
                Account.username == username,
                Account.is_active == True
            ).first()
            
            if account and cls._verify_password(account.password, password):
                # 如果账户没有关联用户，自动创建一个
                if not account.user_id:
                    new_user = cls._create_user_for_account(db, account)
                    account.user_id = new_user.id
                    db.commit()
                
                # 更新最后登录时间
                account.last_login = datetime.now()
                db.commit()
                
                # 获取关联用户信息
                user = account.user
                role = account.role or 'user'
                user_data = {
                    "username": username,
                    "name": user.name,
                    "avatar": user.avatar or cls._generate_avatar(username),
                    "user_id": user.id,
                    "role": role
                }
                
                # 生成 JWT Token（包含角色）
                token = generate_token(user.id, username, role)
                return True, {**user_data, "token": token}, None
            
            return False, None, "用户名或密码错误"
        except Exception as e:
            logger.exception("数据库认证失败")
            return False, None, "登录服务暂时不可用"
        finally:
            db.close()
    
    @classmethod
    def _create_user_for_account(cls, db, account: Account) -> User:
        """为没有关联用户的账户创建用户"""
        user = User(
            name=account.username,
            avatar=cls._generate_avatar(account.username),
            health_score=80,
            created_at=datetime.now()
        )
        db.add(user)
        db.flush()
        return user
    
    @classmethod
    def _create_fallback_user_in_db(cls, db, username: str, password: str, name: str) -> int:
        """在数据库中创建备用用户和账户"""
        # 检查账户是否已存在
        existing = db.query(Account).filter(Account.username == username).first()
        if existing:
            if existing.user_id:
                return existing.user_id
            # 账户存在但没有用户，创建用户
            user = cls._create_user_for_account(db, existing)
            existing.user_id = user.id
            db.commit()
            return user.id
        
        # 创建新用户
        user = User(
            name=name,
            avatar=cls._generate_avatar(username),
            health_score=80,
            created_at=datetime.now()
        )
        db.add(user)
        db.flush()
        
        # 创建账户
        account = Account(
            username=username,
            password=generate_password_hash(password),
            user_id=user.id,
            is_active=True
        )
        db.add(account)
        db.commit()
        
        return user.id
    
    @classmethod
    def register(cls, username: str, password: str, name: str = None) -> Tuple[bool, Optional[dict], Optional[str]]:
        """
        用户注册
        
        Returns:
            (success, user_data, error_message)
        """
        if not username or not password:
            return False, None, "请输入用户名和密码"
        
        username = username.strip()
        if len(username) < 3:
            return False, None, "用户名至少3个字符"
        if len(password) < 6:
            return False, None, "密码至少6个字符"
        
        db = SessionLocal()
        try:
            # 检查用户名是否已存在
            existing = db.query(Account).filter(Account.username == username).first()
            if existing:
                return False, None, "用户名已存在"
            
            # 创建用户
            user = User(
                name=name or username,
                avatar=cls._generate_avatar(username),
                health_score=80,
                created_at=datetime.now()
            )
            db.add(user)
            db.flush()
            
            # 创建账户
            account = Account(
                username=username,
                password=generate_password_hash(password),
                user_id=user.id,
                is_active=True
            )
            db.add(account)
            db.commit()
            
            # 生成 JWT Token
            token = generate_token(user.id, username)
            
            return True, {
                "username": username,
                "name": user.name,
                "avatar": user.avatar,
                "user_id": user.id,
                "token": token
            }, None
            
        except Exception as e:
            db.rollback()
            logger.exception("注册失败")
            return False, None, "注册失败，请稍后重试"
        finally:
            db.close()
    
    @classmethod
    def change_password(cls, user_id: int, old_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """
        修改密码

        Returns:
            (success, error_message)
        """
        if not old_password or not new_password:
            return False, "请填写完整密码信息"
        if len(new_password) < 6:
            return False, "新密码至少 6 位"

        db = SessionLocal()
        try:
            account = db.query(Account).join(User, Account.user_id == User.id).filter(User.id == user_id).first()
            if not account:
                return False, "账户不存在"
            if not cls._verify_password(account.password, old_password):
                return False, "原密码错误"
            account.password = generate_password_hash(new_password)
            db.commit()
            return True, None
        except Exception as e:
            db.rollback()
            logger.exception("修改密码失败")
            return False, "修改失败，请稍后重试"
        finally:
            db.close()

    @staticmethod
    def _verify_password(stored_password: str, input_password: str) -> bool:
        """验证密码：支持哈希密码和明文旧密码兼容"""
        if stored_password.startswith(('pbkdf2:', 'scrypt:')):
            return check_password_hash(stored_password, input_password)
        # 兼容旧明文密码（迁移期）—— 安全警告
        logger.warning("检测到明文密码存储，建议尽快迁移为哈希格式")
        return stored_password == input_password

    @staticmethod
    def _generate_avatar(username: str) -> str:
        """生成头像 URL"""
        return f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}"
