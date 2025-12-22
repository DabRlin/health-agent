"""
认证服务
"""
from datetime import datetime
from typing import Optional, Tuple
from database import SessionLocal, Account, User
from utils.jwt_utils import generate_token


class AuthService:
    """认证服务类"""
    
    # 备用内存账户（数据库不可用时使用）
    FALLBACK_USERS = {
        "admin": {"password": "123456", "name": "管理员"},
        "user": {"password": "123456", "name": "测试用户"},
        "demo": {"password": "demo", "name": "演示用户"},
    }
    
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
        
        # 尝试从数据库验证
        try:
            db = SessionLocal()
            account = db.query(Account).filter(
                Account.username == username,
                Account.is_active == True
            ).first()
            
            if account and account.password == password:
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
                user_data = {
                    "username": username,
                    "name": user.name,
                    "avatar": user.avatar or cls._generate_avatar(username),
                    "user_id": user.id
                }
                
                # 生成 JWT Token
                token = generate_token(user.id, username)
                
                db.close()
                
                return True, {**user_data, "token": token}, None
            
            db.close()
        except Exception as e:
            print(f"数据库认证错误: {e}")
            import traceback
            traceback.print_exc()
        
        # 备用：内存账户验证（仅用于数据库不可用时）
        fallback_user = cls.FALLBACK_USERS.get(username)
        if fallback_user and fallback_user["password"] == password:
            # 尝试在数据库中创建账户和用户
            try:
                db = SessionLocal()
                user_id = cls._create_fallback_user_in_db(db, username, password, fallback_user["name"])
                token = generate_token(user_id, username)
                db.close()
                
                return True, {
                    "username": username,
                    "name": fallback_user["name"],
                    "avatar": cls._generate_avatar(username),
                    "user_id": user_id,
                    "token": token
                }, None
            except Exception as e:
                print(f"创建备用用户失败: {e}")
                # 最后的备用方案：返回临时 token
                return True, {
                    "username": username,
                    "name": fallback_user["name"],
                    "avatar": cls._generate_avatar(username),
                    "user_id": 0,
                    "token": f"fallback_{username}_{datetime.now().timestamp()}"
                }, None
        
        return False, None, "用户名或密码错误"
    
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
            password=password,
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
                password=password,  # 实际项目应加密存储
                user_id=user.id,
                is_active=True
            )
            db.add(account)
            db.commit()
            
            # 生成 JWT Token
            from utils.jwt_utils import generate_token
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
            print(f"注册错误: {e}")
            import traceback
            traceback.print_exc()
            return False, None, "注册失败，请稍后重试"
        finally:
            db.close()
    
    @staticmethod
    def _generate_avatar(username: str) -> str:
        """生成头像 URL"""
        return f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}"
