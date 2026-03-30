"""
测试用例管理路由
"""
import json
from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, TestCase, Module, Requirement

router = APIRouter(prefix="/api/test-cases", tags=["测试用例"])


@router.post("/batch")
async def save_test_cases(
    cases: str = Form(...),
    requirement_id: str = Form(...),
    ai_model: str = Form(None),
    is_edited: str = Form("false"),
    db: Session = Depends(get_db)
):
    """批量保存测试用例"""
    try:
        cases_data = json.loads(cases)
        
        # 获取需求信息
        requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
        if not requirement:
            return {"success": False, "error": "需求不存在"}
        
        saved_count = 0
        
        for case_data in cases_data:
            # 检查是否有编辑记录
            original_values = case_data.get('_original_values', {}) or {}
            # 确保是 dict 类型
            if not isinstance(original_values, dict):
                original_values = {}
            edited_fields = list(original_values.keys()) if original_values else []
            
            # 确保所有 JSON 字段都是字符串类型
            edited_fields_str = json.dumps(edited_fields) if edited_fields else None
            original_values_str = json.dumps(original_values) if original_values else None
            
            # 辅助函数：确保字段是字符串（如果是列表则拼接）
            def ensure_string(value):
                if isinstance(value, list):
                    return '\n'.join(str(v) for v in value)
                return str(value) if value is not None else ''
            
            test_case = TestCase(
                case_id=case_data.get('case_id'),
                module_id=requirement.module_id,
                requirement_id=requirement_id,
                case_name=ensure_string(case_data.get('case_name', '')),
                precondition=ensure_string(case_data.get('precondition', '')),
                steps=ensure_string(case_data.get('steps', '')),
                expected_result=ensure_string(case_data.get('expected_result', '')),
                priority=ensure_string(case_data.get('priority', 'P1')),
                case_type=ensure_string(case_data.get('case_type', '功能测试')),
                source='ai',
                ai_model=ai_model,
                status='draft',
                # 如果在生成页面编辑过，标记为人工修订
                is_edited='true' if (is_edited == 'true' and edited_fields) else 'false',
                edited_fields=edited_fields_str,
                original_values=original_values_str,
                edit_reason='生成页面人工修订' if (is_edited == 'true' and edited_fields) else None
            )
            db.add(test_case)
            saved_count += 1
        
        db.commit()
        return {"success": True, "message": f"成功保存 {saved_count} 条测试用例"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("")
async def get_test_cases(
    skip: int = 0,
    limit: int = 100,
    module_id: str = None,
    module: str = None,  # 支持按模块名称筛选
    requirement: str = None,  # 支持按需求内容筛选
    case_type: str = None,
    priority: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    """获取测试用例列表"""
    query = db.query(TestCase).join(Module).outerjoin(Requirement)
    
    if module_id:
        query = query.filter(TestCase.module_id == module_id)
    if module:
        query = query.filter(Module.name.contains(module))
    if requirement:
        query = query.filter(Requirement.content.contains(requirement))
    if case_type:
        query = query.filter(TestCase.case_type == case_type)
    if priority:
        query = query.filter(TestCase.priority == priority)
    if status:
        query = query.filter(TestCase.status == status)
    
    total = query.count()
    # 按自增ID降序排序，确保分页稳定
    cases = query.order_by(TestCase.auto_id.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": [
            {
                "id": c.id,
                "case_id": c.case_id,
                "module_id": c.module_id,
                "module_name": c.module.name if c.module else '',
                "case_name": c.case_name,
                "steps": c.steps,
                "expected_result": c.expected_result,
                "priority": c.priority,
                "case_type": c.case_type,
                "status": c.status,
                "is_edited": c.is_edited,
                "edit_reason": c.edit_reason,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in cases
        ]
    }


@router.get("/{case_id}")
async def get_test_case_detail(case_id: str, db: Session = Depends(get_db)):
    """获取测试用例详情"""
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    
    return {
        "id": case.id,
        "case_id": case.case_id,
        "module_id": case.module_id,
        "module_name": case.module.name if case.module else '',
        "requirement_id": case.requirement_id,
        "requirement_content": case.requirement.content if case.requirement else '',
        "case_name": case.case_name,
        "precondition": case.precondition,
        "steps": case.steps,
        "expected_result": case.expected_result,
        "priority": case.priority,
        "case_type": case.case_type,
        "source": case.source,
        "ai_model": case.ai_model,
        "is_edited": case.is_edited,
        "edited_fields": case.edited_fields,
        "edit_reason": case.edit_reason,
        "original_values": case.original_values,
        "status": case.status,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None
    }


@router.put("/{case_id}")
async def update_test_case(
    case_id: str,
    case_name: str = Form(None),
    precondition: str = Form(None),
    steps: str = Form(None),
    expected_result: str = Form(None),
    priority: str = Form(None),
    case_type: str = Form(None),
    status: str = Form(None),
    is_edited: str = Form(None),
    edit_reason: str = Form(None),
    db: Session = Depends(get_db)
):
    """更新测试用例"""
    import json
    
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    
    edited_fields = []
    original_values = {}
    
    # 辅助函数：标准化字符串（处理换行符差异）
    def normalize_str(s):
        if s is None:
            return ''
        return str(s).replace('\r\n', '\n').replace('\r', '\n').strip()
    
    if case_name and normalize_str(case_name) != normalize_str(case.case_name):
        original_values["case_name"] = case.case_name
        case.case_name = case_name
        edited_fields.append("case_name")
    if precondition is not None and normalize_str(precondition) != normalize_str(case.precondition):
        original_values["precondition"] = case.precondition
        case.precondition = precondition
        edited_fields.append("precondition")
    if steps and normalize_str(steps) != normalize_str(case.steps):
        original_values["steps"] = case.steps
        case.steps = steps
        edited_fields.append("steps")
    if expected_result and normalize_str(expected_result) != normalize_str(case.expected_result):
        original_values["expected_result"] = case.expected_result
        case.expected_result = expected_result
        edited_fields.append("expected_result")
    if priority and normalize_str(priority) != normalize_str(case.priority):
        original_values["priority"] = case.priority
        case.priority = priority
        edited_fields.append("priority")
    if case_type and normalize_str(case_type) != normalize_str(case.case_type):
        original_values["case_type"] = case.case_type
        case.case_type = case_type
        edited_fields.append("case_type")
    # 状态修改不记入人工修订
    if status and status != case.status:
        case.status = status
    
    # 标记人工修订（仅当核心字段被修改时）
    if is_edited == "true" or edited_fields:
        case.is_edited = "true"
        case.edited_fields = json.dumps(edited_fields) if edited_fields else case.edited_fields
        case.original_values = json.dumps(original_values) if original_values else case.original_values
        if edit_reason:
            case.edit_reason = edit_reason
    
    db.commit()
    return {"success": True, "message": "用例已更新", "edited_fields": edited_fields}


@router.delete("/{case_id}")
async def delete_test_case(case_id: str, db: Session = Depends(get_db)):
    """删除测试用例"""
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    
    db.delete(case)
    db.commit()
    
    return {"success": True, "message": "用例已删除"}
