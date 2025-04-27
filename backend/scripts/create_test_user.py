#!/usr/bin/env python3
"""
テストユーザーを作成するスクリプト
"""
import sys
import os

# 必要なパスをPYTHONPATHに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.database.database import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.crud.user import get_user_by_email

def create_test_users():
    """
    さまざまなロールを持つテストユーザーを作成する
    """
    db = SessionLocal()
    try:
        # テストユーザー情報
        test_users = [
            {
                "email": "test@example.com",
                "password": "password",
                "full_name": "テストユーザー",
                "role_name": "user",
                "permissions": ["read"]
            },
            {
                "email": "admin@example.com",
                "password": "admin123",
                "full_name": "管理者ユーザー",
                "role_name": "admin",
                "permissions": ["read", "write", "admin"]
            },
            {
                "email": "teacher@example.com",
                "password": "teacher123",
                "full_name": "講師ユーザー",
                "role_name": "teacher", 
                "permissions": ["read", "write", "teacher"]
            },
            {
                "email": "student@example.com", 
                "password": "student123", 
                "full_name": "生徒テスト", 
                "role_name": "student", 
                "permissions": ["read", "student"]
            }
        ]
            
        # 各ロールの作成（まだ存在しない場合）
        roles = {}
        for user_data in test_users:
            role_name = user_data["role_name"]
            if role_name not in roles:
                # ロールが存在するか確認
                role = db.query(Role).filter(Role.name == role_name).first()
                if not role:
                    role = Role(
                        name=role_name, 
                        permissions=user_data["permissions"]
                    )
                    db.add(role)
                    db.commit()
                    db.refresh(role)
                    print(f"ロール '{role_name}' を作成しました")
                roles[role_name] = role
        
        # テストユーザーの作成
        for user_data in test_users:
            email = user_data["email"]
            # すでに存在する場合は作成しない
            existing_user = get_user_by_email(db, email=email)
            if existing_user:
                print(f"ユーザー '{email}' はすでに存在します (ロール: {user_data['role_name']})")
                continue
                
            # ユーザーの作成
            role = roles[user_data["role_name"]]
            user = User(
                email=email,
                hashed_password=get_password_hash(user_data["password"]),
                full_name=user_data["full_name"],
                role_id=role.id
            )
            
            # DBに保存
            db.add(user)
            db.commit()
            
            print(f"ユーザー '{email}' を作成しました (ロール: {user_data['role_name']}, パスワード: {user_data['password']})")
            
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users() 