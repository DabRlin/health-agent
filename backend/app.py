"""
HealthAI MVP Backend - Flask API
主入口文件
"""
import sys
import os
import logging

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify
from config import config
from database.models import init_db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """创建 Flask 应用"""
    app = Flask(__name__)
    init_db()
    
    # 配置 CORS
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    # 统一错误处理
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "请求的资源不存在"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "error": "请求方法不允许"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("服务器内部错误")
        return jsonify({"success": False, "error": "服务器内部错误，请稍后重试"}), 500

    # 检查 LLM 配置
    if config.LLM_API_KEY:
        logger.info("LLM Agent 已启用: %s (%s)", config.LLM_BASE_URL, config.LLM_MODEL)
    else:
        logger.warning("未配置 LLM_API_KEY，智能问诊功能不可用")
    
    # 注册蓝图
    from routes import auth_bp, user_bp, health_bp, consultation_bp, risk_bp, trend_bp, exam_bp, admin_bp, medical_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(consultation_bp)
    app.register_blueprint(risk_bp)
    app.register_blueprint(trend_bp)
    app.register_blueprint(exam_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(medical_bp)
    
    return app


# 创建应用实例
app = create_app()


if __name__ == '__main__':
    print("🚀 HealthAI MVP Backend starting...")
    print(f"📍 API running at http://{config.HOST}:{config.PORT}")
    print("=" * 50)
    print("📚 API 路由:")
    print("   /api/auth/*         - 认证相关")
    print("   /api/user/*         - 用户相关")
    print("   /api/metrics/*      - 健康指标")
    print("   /api/records/*      - 健康记录")
    print("   /api/consultation/* - 智能问诊")
    print("   /api/risk/*         - 风险评估")
    print("   /api/trend/*        - 趋势分析")
    print("   /api/exam/*         - 体检报告")
    print("   /api/dashboard      - 首页数据")
    print("=" * 50)
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)
