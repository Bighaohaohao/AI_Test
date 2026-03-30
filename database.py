"""
数据库模型和连接配置
"""
from sqlalchemy import create_engine, Column, String, Text, DateTime, Enum, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import uuid

# 创建数据库引擎（使用SQLite）
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_cases.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基础类
Base = declarative_base()


class PriorityEnum(str, enum.Enum):
    """优先级枚举"""
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class CaseTypeEnum(str, enum.Enum):
    """测试类型枚举"""
    FUNCTIONAL = "功能测试"
    INTERFACE = "接口测试"
    PERFORMANCE = "性能测试"


class CaseStatusEnum(str, enum.Enum):
    """用例状态枚举"""
    DRAFT = "draft"           # 草稿
    APPROVED = "approved"     # 已审核
    DEPRECATED = "deprecated" # 已废弃


class Module(Base):
    """功能模块表 - 管理员手动配置"""
    __tablename__ = "modules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)  # 模块名称
    description = Column(Text, nullable=True)  # 模块描述
    sort_order = Column(Integer, default=0)  # 排序
    is_active = Column(String(10), default="true")  # 是否启用
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class Requirement(Base):
    """需求表 - 用户提交的需求"""
    __tablename__ = "requirements"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_type = Column(String(20), nullable=False)  # figma/text
    figma_file_id = Column(String(100), nullable=True)  # Figma文件ID
    figma_node_id = Column(String(100), nullable=True)  # Figma节点ID
    content = Column(Text, nullable=False)  # 需求内容
    raw_data = Column(Text, nullable=True)  # Figma原始数据（JSON）
    module_id = Column(String(36), ForeignKey("modules.id"), nullable=False)  # 关联功能模块
    status = Column(String(20), default="active")  # active/processed/archived
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    module = relationship("Module")


class TestCase(Base):
    """测试用例表"""
    __tablename__ = "test_cases"
    
    auto_id = Column(Integer, primary_key=True, autoincrement=True)  # 自增ID，用于排序
    id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))  # UUID，业务ID
    case_id = Column(String(20), nullable=False, index=True)  # TC001, TC002...
    module_id = Column(String(36), ForeignKey("modules.id"), nullable=False)  # 关联功能模块
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=True)  # 关联需求
    case_name = Column(String(200), nullable=False)  # 用例名称
    precondition = Column(Text, nullable=True)  # 前置条件
    steps = Column(Text, nullable=False)  # 测试步骤
    expected_result = Column(Text, nullable=False)  # 预期结果
    priority = Column(String(10), nullable=False, default="P1")  # P0/P1/P2
    case_type = Column(String(20), nullable=False, default="功能测试")  # 功能/接口/性能
    
    # 来源信息
    source = Column(String(20), nullable=False, default="ai")  # ai/manual
    ai_model = Column(String(50), nullable=True)  # 生成使用的模型
    
    # 人工修订标记
    is_edited = Column(String(10), default="false")  # true/false，标记是否被人工修订过
    edited_fields = Column(Text, nullable=True)  # JSON格式，记录哪些字段被修改过
    edit_reason = Column(Text, nullable=True)  # 修订原因
    original_values = Column(Text, nullable=True)  # JSON格式，记录修订前的原始值（字段名: 原始值）
    
    # 质量评分
    quality_score = Column(Integer, nullable=True)  # 1-5分
    
    # 状态
    status = Column(String(20), nullable=False, default="draft")  # draft/approved/deprecated
    
    # 创建和更新信息
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    module = relationship("Module")
    requirement = relationship("Requirement")


def create_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
