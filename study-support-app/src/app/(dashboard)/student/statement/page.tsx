"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { PersonalStatement, StatementStatus, convertToPersonalStatement } from '@/types/statement';
import { getStatements, deleteStatement } from '@/services/statementService';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { PlusCircle, Edit, Trash2, FileText, MessageSquare, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const StatementListPage: React.FC = () => {
    const router = useRouter();
    const [statements, setStatements] = useState<PersonalStatement[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // データを取得
    useEffect(() => {
        const fetchStatements = async () => {
            try {
                setLoading(true);
                setError(null);
                const apiStatements = await getStatements();
                const convertedStatements = apiStatements.map(convertToPersonalStatement);
                setStatements(convertedStatements);
            } catch (err) {
                console.error('Failed to fetch statements:', err);
                setError(err instanceof Error ? err.message : 'データの取得に失敗しました');
                toast.error('志望理由書の取得に失敗しました');
            } finally {
                setLoading(false);
            }
        };

        fetchStatements();
    }, []);

    const handleDelete = async (id: string) => {
        if (confirm('この志望理由書を削除してもよろしいですか？')) {
            try {
                await deleteStatement(id);
                setStatements(prev => prev.filter(stmt => stmt.id !== id));
                toast.success('志望理由書を削除しました。');
            } catch (err) {
                console.error('Failed to delete statement:', err);
                toast.error('削除に失敗しました');
            }
        }
    };

    const getStatusVariant = (status: StatementStatus) => {
        switch (status) {
            case StatementStatus.DRAFT:
                return 'secondary';
            case StatementStatus.REVIEW:
                return 'default';
            case StatementStatus.REVIEWED:
                return 'outline';
            case StatementStatus.FINAL:
                return 'default';
            default:
                return 'secondary';
        }
    };

    const getStatusText = (status: StatementStatus) => {
        switch (status) {
            case StatementStatus.DRAFT:
                return '下書き';
            case StatementStatus.REVIEW:
                return 'レビュー中';
            case StatementStatus.REVIEWED:
                return 'レビュー済み';
            case StatementStatus.FINAL:
                return '完成版';
            default:
                return status;
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('ja-JP', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    return (
        <div className="container mx-auto p-4 md:p-6 lg:p-8">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">志望理由書一覧</h1>
                <Link href="/student/statement/new">
                    <Button disabled={loading}>
                        <PlusCircle className="mr-2 h-4 w-4" /> 新規作成
                    </Button>
                </Link>
            </div>

            {loading ? (
                <Card className="text-center py-10">
                    <CardHeader>
                        <Loader2 className="mx-auto h-12 w-12 text-gray-400 animate-spin" />
                        <CardTitle className="mt-4">読み込み中...</CardTitle>
                        <CardDescription>志望理由書を取得しています</CardDescription>
                    </CardHeader>
                </Card>
            ) : error ? (
                <Card className="text-center py-10">
                    <CardHeader>
                        <FileText className="mx-auto h-12 w-12 text-red-400" />
                        <CardTitle className="mt-4 text-red-600">エラーが発生しました</CardTitle>
                        <CardDescription>{error}</CardDescription>
                    </CardHeader>
                    <CardFooter className="justify-center">
                        <Button onClick={() => window.location.reload()}>
                            再読み込み
                        </Button>
                    </CardFooter>
                </Card>
            ) : statements.length === 0 ? (
                <Card className="text-center py-10">
                    <CardHeader>
                        <FileText className="mx-auto h-12 w-12 text-gray-400" />
                        <CardTitle className="mt-4">志望理由書がありません</CardTitle>
                        <CardDescription>まだ志望理由書を作成していません。「新規作成」ボタンから始めましょう。</CardDescription>
                    </CardHeader>
                    <CardFooter className="justify-center">
                        <Link href="/student/statement/new">
                            <Button>新規作成</Button>
                        </Link>
                    </CardFooter>
                </Card>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {statements.map((statement) => (
                        <Card key={statement.id} className="flex flex-col hover:shadow-lg transition-shadow">
                            <CardHeader>
                                <CardTitle className="truncate">{statement.title}</CardTitle>
                                <CardDescription className="truncate">
                                    {statement.universityName} - {statement.departmentName}
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="flex-grow">
                                <p className="text-sm text-gray-600 line-clamp-3 mb-4" title={statement.content}>
                                    {statement.content || '内容がありません'}
                                </p>
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between text-xs">
                                        <Badge variant={getStatusVariant(statement.status)}>
                                            {getStatusText(statement.status)}
                                        </Badge>
                                        <span className="text-gray-500">
                                            {statement.wordCount}文字
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between text-xs text-gray-500">
                                        <span>最終更新: {formatDate(statement.updatedAt)}</span>
                                        {statement.feedbackCount > 0 && (
                                            <div className="flex items-center">
                                                <MessageSquare className="w-3 h-3 mr-1" />
                                                <span>{statement.feedbackCount}件</span>
                                            </div>
                                        )}
                                    </div>
                                    {statement.submissionDeadline && (
                                        <div className="text-xs text-orange-600">
                                            締切: {formatDate(statement.submissionDeadline)}
                                        </div>
                                    )}
                                    {statement.keywords.length > 0 && (
                                        <div className="flex flex-wrap gap-1 mt-2">
                                            {statement.keywords.slice(0, 3).map((keyword, index) => (
                                                <span 
                                                    key={index}
                                                    className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded"
                                                >
                                                    {keyword}
                                                </span>
                                            ))}
                                            {statement.keywords.length > 3 && (
                                                <span className="text-xs text-gray-500">
                                                    +{statement.keywords.length - 3}
                                                </span>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </CardContent>
                            <CardFooter className="flex justify-end space-x-2 border-t pt-4 mt-auto">
                                <Link href={`/student/statement/${statement.id}/edit`}>
                                    <Button variant="outline" size="sm">
                                        <Edit className="mr-1 h-4 w-4" />編集
                                    </Button>
                                </Link>
                                <Button
                                    variant="destructive"
                                    size="sm"
                                    onClick={() => handleDelete(statement.id)}
                                >
                                    <Trash2 className="mr-1 h-4 w-4" />削除
                                </Button>
                            </CardFooter>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
};

export default StatementListPage;