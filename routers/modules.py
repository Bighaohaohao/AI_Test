"""
功能模块管理路由
"""
from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Module

router = APIRouter(prefix="/api/modules", tags=["功能模块"])


@router.get("")
async def get_modules(
    is_active: str = "true",
    db: Session = Depends(get_db)
):
    """获取功能模块列表"""
    query = db.query(Module)
    if is_active != "all":
        query = query.filter(Module.is_active == is_active)
    modules = query.order_by(Module.sort_order).all()
    
    return {
        "items": [
            {
                "id": m.id,
                "name": m.name,
                "description": m.description,
                "sort_order": m.sort_order,
                "is_active": m.is_active,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in modules
        ]
    }


@router.post("")
async def create_module(
    name: str = Form(...),
    description: str = Form(None),
    sort_order: int = Form(0),
    db: Session = Depends(get_db)
):
    """创建功能模块"""
    try:
        # 检查是否已存在
        existing = db.query(Module).filter(Module.name == name).first()
        if existing:
            return {"success": False, "error": "模块名称已存在"}
        
        module = Module(
            name=name,
            description=description,
            sort_order=sort_order,
            is_active="true"
        )
        db.add(module)
        db.commit()
        db.refresh(module)
        
        return {"success": True, "id": module.id, "message": "模块创建成功"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.put("/{module_id}")
async def update_module(
    module_id: str,
    name: str = Form(None),
    description: str = Form(None),
    sort_order: int = Form(None),
    is_active: str = Form(None),
    db: Session = Depends(get_db)
):
    """更新功能模块"""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    
    if name:
        module.name = name
    if description is not None:
        module.description = description
    if sort_order is not None:
        module.sort_order = sort_order
    if is_active:
        module.is_active = is_active
    
    db.commit()
    return {"success": True, "message": "模块已更新"}


@router.delete("/{module_id}")
async def delete_module(module_id: str, db: Session = Depends(get_db)):
    """删除功能模块"""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    
    db.delete(module)
    db.commit()
    
    return {"success": True, "message": "模块已删除"}
