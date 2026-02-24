# db/session.py
#首先安装pip install PyMySQL

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# MySQL 连接字符串（使用 PyMySQL 驱动）
#SQLALCHEMY_DATABASE_URL = "mysql+pymysql://username:password@localhost/dbname"
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://xiaoxin:Nihao123!@localhost/ssq"

# 创建 SQLAlchemy 引擎
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# 创建 SessionLocal 类，用于创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基础模型类
Base = declarative_base()
