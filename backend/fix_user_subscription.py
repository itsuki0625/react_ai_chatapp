#!/usr/bin/env python3

"""
フリープランユーザーのサブスクリプション情報を修正するスクリプト
"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_engine
from sqlalchemy import text
import logging

# ログの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """フリープランユーザーのサブスクリプション情報を修正"""
    try:
        async with AsyncSession(async_engine) as db:
            # 1. 現在の状況を確認
            logger.info("現在のユーザー・サブスクリプション状況を確認中...")
            result = await db.execute(text('''
                SELECT 
                    u.email,
                    u.status as user_status,
                    r.name as role_name,
                    s.id as subscription_id,
                    sp.name as plan_name,
                    s.status as subscription_status,
                    s.is_active
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN roles r ON ur.role_id = r.id
                LEFT JOIN subscriptions s ON u.id = s.user_id AND s.is_active = true
                LEFT JOIN subscription_plans sp ON s.plan_id = sp.id
                WHERE u.email = 'test1@test.com'
            '''))
            rows = result.fetchall()
            
            print('=== test1@test.com の現在の状況 ===')
            for row in rows:
                print(f'Email: {row.email}')
                print(f'User Status: {row.user_status}')
                print(f'Role: {row.role_name}')
                print(f'Subscription ID: {row.subscription_id}')
                print(f'Plan Name: {row.plan_name}')
                print(f'Subscription Status: {row.subscription_status}')
                print(f'Is Active: {row.is_active}')
                print('---')
            
            # 2. フリープランのIDを取得
            free_plan_result = await db.execute(text('''
                SELECT id, name FROM subscription_plans WHERE name = 'フリー'
            '''))
            free_plan_row = free_plan_result.fetchone()
            
            if not free_plan_row:
                logger.error("フリープランが見つかりません")
                return
            
            free_plan_id = free_plan_row.id
            logger.info(f"フリープランID: {free_plan_id}")
            
            # 3. test1@test.com ユーザーのIDを取得
            user_result = await db.execute(text('''
                SELECT id FROM users WHERE email = 'test1@test.com'
            '''))
            user_row = user_result.fetchone()
            
            if not user_row:
                logger.error("test1@test.com ユーザーが見つかりません")
                return
            
            user_id = user_row.id
            logger.info(f"ユーザーID: {user_id}")
            
            # 4. 既存のアクティブサブスクリプションを無効化
            logger.info("既存のアクティブサブスクリプションを無効化中...")
            await db.execute(text('''
                UPDATE subscriptions 
                SET is_active = false, updated_at = NOW()
                WHERE user_id = :user_id AND is_active = true
            '''), {'user_id': user_id})
            
            # 5. フリープランのサブスクリプションを作成
            logger.info("フリープランのサブスクリプションを作成中...")
            await db.execute(text('''
                INSERT INTO subscriptions (
                    id, user_id, plan_id, status, is_active, 
                    current_period_start, current_period_end,
                    created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), :user_id, :plan_id, 'active', true,
                    NOW(), NOW() + INTERVAL '1 year',
                    NOW(), NOW()
                )
            '''), {
                'user_id': user_id,
                'plan_id': free_plan_id
            })
            
            await db.commit()
            logger.info("サブスクリプション情報の修正が完了しました")
            
            # 6. 修正後の状況を確認
            logger.info("修正後の状況を確認中...")
            result_after = await db.execute(text('''
                SELECT 
                    u.email,
                    r.name as role_name,
                    sp.name as plan_name,
                    s.status as subscription_status,
                    s.is_active
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN roles r ON ur.role_id = r.id
                LEFT JOIN subscriptions s ON u.id = s.user_id AND s.is_active = true
                LEFT JOIN subscription_plans sp ON s.plan_id = sp.id
                WHERE u.email = 'test1@test.com'
            '''))
            rows_after = result_after.fetchall()
            
            print('\n=== 修正後の状況 ===')
            for row in rows_after:
                print(f'Email: {row.email}')
                print(f'Role: {row.role_name}')
                print(f'Plan Name: {row.plan_name}')
                print(f'Subscription Status: {row.subscription_status}')
                print(f'Is Active: {row.is_active}')
            
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 