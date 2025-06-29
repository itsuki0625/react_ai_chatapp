"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { signOut } from 'next-auth/react';
import { PersonalStatementResponse } from '@/types/personal_statement';
import { getStatements, deleteStatement } from '@/services/statementService';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { PlusCircle, Edit, Trash2, FileText } from 'lucide-react';
import { useAuthHelpers } from '@/lib/authUtils';
import { formatDate } from '@/lib/utils';
import { toast } from 'sonner';

const StatementListPage: React.FC = () => {
    const queryClient = useQueryClient();
    const { hasPermission, isLoading: isAuthLoading } = useAuthHelpers();
    const router = useRouter();

    const { data: statements, isLoading: isLoadingStatements, error } = useQuery<PersonalStatementResponse[], Error>({
        queryKey: ['statements'],
        queryFn: getStatements,
        enabled: !isAuthLoading && hasPermission('statement_manage_own'),
        retry: false,
    });

    const deleteMutation = useMutation<void, Error, string>({ 
        mutationFn: deleteStatement, 
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['statements'] });
            alert('志望理由書を削除しました。');
        },
        onError: (error) => {
            alert(`削除に失敗しました: ${error.message}`);
        }
    });

    useEffect(() => {
        const handleAuthError = async () => {
            toast.error('認証エラーが発生しました。ログインページに遷移します。');
            await signOut({ redirect: false });
            router.push('/login?status=logged_out');
        };

        if (error) {
            console.error("Error fetching statements:", error);
            if (error.message === 'Unauthorized (401)' || error.message === 'Authentication required.') {
                handleAuthError();
            } else {
                toast.error(`データの取得にエラーが発生しました: ${error.message}`);
            }
        }
    }, [error, router]);

    if (process.env.NODE_ENV === 'production') {
        return (
            <div className="flex h-full w-full items-center justify-center">
                <p className="text-xl">開発中です。公開までお待ちください。</p>
            </div>
        );
    }

    const handleDelete = (id: string) => {
        if (confirm('この志望理由書を削除してもよろしいですか？')) {
            deleteMutation.mutate(id);
        }
    };

    if (isAuthLoading || isLoadingStatements) {
        return <div className="text-center p-4">データを読み込み中...</div>;
    }

    if (!hasPermission('statement_manage_own')) {
        return <div className="text-center p-4 text-red-600">このページにアクセスする権限がありません。</div>;
    }

    if (error && error.message !== 'Unauthorized (401)' && error.message !== 'Authentication required.') {
        return <div className="text-center p-4 text-red-600">データの取得にエラーが発生しました。</div>;
    }

    const validStatements = Array.isArray(statements) ? statements : [];

    return (
        <div className="container mx-auto p-4 md:p-6 lg:p-8">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">志望理由書一覧</h1>
                {hasPermission('statement_manage_own') && (
                     <Link href="/statement/new">
                         <Button>
                             <PlusCircle className="mr-2 h-4 w-4" /> 新規作成
                         </Button>
                     </Link>
                 )}
            </div>

            {validStatements.length === 0 ? (
                <Card className="text-center py-10">
                    <CardHeader>
                        <FileText className="mx-auto h-12 w-12 text-gray-400" />
                        <CardTitle className="mt-4">志望理由書がありません</CardTitle>
                        <CardDescription>まだ志望理由書を作成していません。「新規作成」ボタンから始めましょう。</CardDescription>
                    </CardHeader>
                    {hasPermission('statement_manage_own') && (
                        <CardFooter className="justify-center">
                             <Link href="/statement/new">
                                 <Button>新規作成</Button>
                             </Link>
                        </CardFooter>
                    )}
                </Card>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {validStatements.map((statement) => (
                        <Card key={statement.id} className="flex flex-col">
                            <CardHeader>
                                <CardTitle className="truncate">{statement.university_name || '大学未定'}</CardTitle>
                                <CardDescription className="truncate">{statement.department_name || '学部未定'}</CardDescription>
                            </CardHeader>
                            <CardContent className="flex-grow">
                                <p className="text-sm text-gray-600 line-clamp-3 mb-2" title={statement.content}>
                                    {statement.content || '内容がありません'}
                                </p>
                                <div className="text-xs text-gray-500 space-x-2">
                                     <span>ステータス: <Badge variant={statement.status === 'completed' ? 'default' : 'secondary'}>{statement.status}</Badge></span>
                                     <span>最終更新: {formatDate(statement.updated_at)}</span>
                                 </div>
                            </CardContent>
                            <CardFooter className="flex justify-end space-x-2 border-t pt-4 mt-auto">
                                {hasPermission('statement_manage_own') && (
                                    <Link href={`/statement/${statement.id}/edit`}>
                                        <Button variant="outline" size="sm">
                                            <Edit className="mr-1 h-4 w-4" />編集
                                        </Button>
                                    </Link>
                                )} 
                                {hasPermission('statement_manage_own') && (
                                    <Button
                                        variant="destructive"
                                        size="sm"
                                        onClick={() => handleDelete(statement.id)}
                                        disabled={deleteMutation.isPending}
                                    >
                                        <Trash2 className="mr-1 h-4 w-4" />削除
                                    </Button>
                                )}
                                {hasPermission('statement_review_respond') && (
                                    <Link href={`/statement/review/${statement.id}`}> 
                                        <Button variant="secondary" size="sm">
                                             レビューする
                                         </Button>
                                     </Link>
                                 )}
                            </CardFooter>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
};

export default StatementListPage;