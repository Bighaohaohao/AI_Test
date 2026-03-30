"""
需求管理路由
"""
from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Requirement, Module

router = APIRouter(prefix="/api/requirements", tags=["需求管理"])


@router.post("")
async def create_requirement(
    source_type: str = Form(...),
    content: str = Form(...),
    module_id: str = Form(...),
    figma_file_id: str = Form(None),
    figma_node_id: str = Form(None),
    raw_data: str = Form(None),
    db: Session = Depends(get_db)
):
    """创建需求"""
    try:
        # 验证模块是否存在
        module = db.query(Module).filter(Module.id == module_id).first()
        if not module:
            return {"success": False, "error": "功能模块不存在"}
        
        requirement = Requirement(
            source_type=source_type,
            content=content,
            module_id=module_id,
            figma_file_id=figma_file_id,
            figma_node_id=figma_node_id,
            raw_data=raw_data,
            status="active"
        )
        db.add(requirement)
        db.commit()
        db.refresh(requirement)
        
        return {
            "success": True,
            "id": requirement.id,
            "module_id": module_id,
            "module_name": module.name,
            "message": "需求已保存"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("")
async def get_requirements(
    skip: int = 0,
    limit: int = 100,
    module_id: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    """获取需求列表"""
    query = db.query(Requirement).join(Module)
    
    if module_id:
        query = query.filter(Requirement.module_id == module_id)
    if status:
        query = query.filter(Requirement.status == status)
    
    total = query.count()
    requirements = query.order_by(Requirement.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": [
            {
                "id": r.id,
                "source_type": r.source_type,
                "content": r.content[:200] + "..." if len(r.content) > 200 else r.content,
                "module_id": r.module_id,
                "module_name": r.module.name if r.module else '',
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in requirements
        ]
    }


@router.get("/{requirement_id}")
async def get_requirement_detail(requirement_id: str, db: Session = Depends(get_db)):
    """获取需求详情"""
    req = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="需求不存在")
    
    return {
        "id": req.id,
        "source_type": req.source_type,
        "content": req.content,
        "module_id": req.module_id,
        "module_name": req.module.name if req.module else '',
        "figma_file_id": req.figma_file_id,
        "figma_node_id": req.figma_node_id,
        "status": req.status,
        "created_at": req.created_at.isoformat() if req.created_at else None
    }
