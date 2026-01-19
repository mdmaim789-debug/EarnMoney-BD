from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class WithdrawalStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class TaskType(enum.Enum):
    YOUTUBE = "youtube"
    TELEGRAM = "telegram"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WEBSITE = "website"
    APP_INSTALL = "app_install"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    balance = Column(Float, default=0.0)
    total_earned = Column(Float, default=0.0)
    total_withdrawn = Column(Float, default=0.0)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    referral_code = Column(String(50), unique=True, index=True)
    is_banned = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_ad_watch = Column(DateTime, nullable=True)
    ads_watched_today = Column(Integer, default=0)
    last_daily_reset = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    referrals = relationship("User", backref="referrer", remote_side=[id])
    earnings = relationship("Earning", back_populates="user")
    withdrawals = relationship("Withdrawal", back_populates="user")

class Earning(Base):
    __tablename__ = "earnings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    earning_type = Column(String(50), nullable=False)  # ad, task, referral, bonus
    description = Column(String(255), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="earnings")
    task = relationship("Task", back_populates="earnings")

class Withdrawal(Base):
    __tablename__ = "withdrawals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(String(20), nullable=False)  # bkash, nagad, rocket
    account_number = Column(String(20), nullable=False)
    status = Column(Enum(WithdrawalStatus), default=WithdrawalStatus.PENDING)
    admin_note = Column(Text, nullable=True)
    approved_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="withdrawals")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(Enum(TaskType), nullable=False)
    reward = Column(Float, nullable=False)
    url = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)
    max_completions = Column(Integer, nullable=True)
    current_completions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    earnings = relationship("Earning", back_populates="task")
    completions = relationship("TaskCompletion", back_populates="task")

class TaskCompletion(Base):
    __tablename__ = "task_completions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    task = relationship("Task", back_populates="completions")

class Settings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
