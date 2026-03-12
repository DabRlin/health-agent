"""
用药管理路由
"""
from flask import Blueprint, request, jsonify
from utils import login_required, get_current_user_id
from database.models import SessionLocal, Medication, User

medication_bp = Blueprint('medication', __name__, url_prefix='/api/medications')


def _get_user_id(db):
    """获取当前登录用户的 user_id（关联 User 表）"""
    account_id = get_current_user_id()
    from database.models import Account
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account or not account.user_id:
        return None
    return account.user_id


def _med_to_dict(m: Medication) -> dict:
    return {
        "id": m.id,
        "name": m.name,
        "med_type": m.med_type,
        "reminders": m.reminders or [],
        "duration_days": m.duration_days,
        "start_date": m.start_date,
        "raw_instructions": m.raw_instructions,
        "contraindications": m.contraindications,
        "side_effects": m.side_effects,
        "storage": m.storage,
        "image_path": m.image_path,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


# ==================== OCR 提取 ====================

@medication_bp.route('/extract', methods=['POST'])
@login_required
def extract_from_image():
    """上传说明书图片，VL 模型提取用药信息（不存库，只返回提取结果供用户确认）"""
    data = request.json or {}
    image_base64 = data.get('image_base64', '')
    image_mime = data.get('image_mime', 'image/jpeg')

    if not image_base64:
        return jsonify({"success": False, "error": "缺少图片数据"}), 400

    from services.vl_service import VLService
    result = VLService.extract_medication_info(image_base64, image_mime)
    if not result:
        return jsonify({"success": False, "error": "说明书识别失败，请确认图片清晰"}), 500

    return jsonify({"success": True, "data": result})


# ==================== CRUD ====================

@medication_bp.route('', methods=['GET'])
@login_required
def list_medications():
    """获取用户的用药列表"""
    db = SessionLocal()
    try:
        user_id = _get_user_id(db)
        if not user_id:
            return jsonify({"success": False, "error": "用户信息不完整"}), 400
        meds = db.query(Medication).filter(
            Medication.user_id == user_id
        ).order_by(Medication.created_at.desc()).all()
        return jsonify({"success": True, "data": [_med_to_dict(m) for m in meds]})
    finally:
        db.close()


@medication_bp.route('', methods=['POST'])
@login_required
def create_medication():
    """保存一条用药记录（OCR 确认后调用）"""
    db = SessionLocal()
    try:
        user_id = _get_user_id(db)
        if not user_id:
            return jsonify({"success": False, "error": "用户信息不完整"}), 400

        data = request.json or {}
        data.pop('image_base64', None)
        data.pop('image_mime', None)

        med = Medication(
            user_id=user_id,
            name=data.get('name', '未知药品'),
            med_type=data.get('med_type', 'oral'),
            reminders=data.get('reminders', []),
            duration_days=data.get('duration_days'),
            start_date=data.get('start_date'),
            raw_instructions=data.get('raw_instructions', ''),
            contraindications=data.get('contraindications', ''),
            side_effects=data.get('side_effects', ''),
            storage=data.get('storage', ''),
            ocr_raw_text=data.get('ocr_raw_text', ''),
            image_path=None,
        )
        db.add(med)
        db.commit()
        db.refresh(med)
        return jsonify({"success": True, "data": _med_to_dict(med)}), 201
    finally:
        db.close()


@medication_bp.route('/<int:med_id>', methods=['GET'])
@login_required
def get_medication(med_id):
    """获取单条用药详情"""
    db = SessionLocal()
    try:
        user_id = _get_user_id(db)
        med = db.query(Medication).filter(
            Medication.id == med_id, Medication.user_id == user_id
        ).first()
        if not med:
            return jsonify({"success": False, "error": "记录不存在"}), 404
        return jsonify({"success": True, "data": _med_to_dict(med)})
    finally:
        db.close()


@medication_bp.route('/<int:med_id>', methods=['PUT'])
@login_required
def update_medication(med_id):
    """更新用药记录（用户修改提醒时间等）"""
    db = SessionLocal()
    try:
        user_id = _get_user_id(db)
        med = db.query(Medication).filter(
            Medication.id == med_id, Medication.user_id == user_id
        ).first()
        if not med:
            return jsonify({"success": False, "error": "记录不存在"}), 404

        data = request.json or {}
        for field in ['name', 'med_type', 'reminders', 'duration_days',
                      'start_date', 'raw_instructions', 'contraindications',
                      'side_effects', 'storage']:
            if field in data:
                setattr(med, field, data[field])
        db.commit()
        return jsonify({"success": True, "data": _med_to_dict(med)})
    finally:
        db.close()


@medication_bp.route('/<int:med_id>', methods=['DELETE'])
@login_required
def delete_medication(med_id):
    """删除用药记录"""
    db = SessionLocal()
    try:
        user_id = _get_user_id(db)
        med = db.query(Medication).filter(
            Medication.id == med_id, Medication.user_id == user_id
        ).first()
        if not med:
            return jsonify({"success": False, "error": "记录不存在"}), 404
        db.delete(med)
        db.commit()
        return jsonify({"success": True, "message": "已删除"})
    finally:
        db.close()
