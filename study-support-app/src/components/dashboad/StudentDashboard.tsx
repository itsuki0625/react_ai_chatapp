"use client";

import React, { useEffect, useState } from 'react';
import { Calendar, GraduationCap, BookOpen, FileText, BrainCircuit } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { applicationApi } from '@/lib/api-client';
import { useQuery } from '@tanstack/react-query';
import { ApplicationDetailResponse } from '@/components/application/ApplicationList';
import { subscriptionService } from '@/services/subscriptionService';
import { AxiosResponse } from 'axios';
import { Subscription } from '@/types/subscription';

interface DashboardData {
  progress: {
    completedTasks: number;
    totalTasks: number;
    courses: { id: string; title: string; progress: number }[];
  };
  events: { id: string; title: string; date: string; type: string }[];
  applications: {
    count: number;
    nextDeadline: { university: string; document: string; date: string } | null;
  };
  recommendations: { type: string; title: string; id: string }[];
  aiAnalysis: {
    strengths: string[];
    interests: string[];
    recentTopics: string[];
  };
}

export const StudentDashboard = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useQuery<AxiosResponse<ApplicationDetailResponse[]>, Error, ApplicationDetailResponse[]>({ 
    queryKey: ['applications'], 
    queryFn: applicationApi.getApplications,
    select: (response) => response.data
  });
  useQuery<Subscription | null>({ 
    queryKey: ['subscription'], 
    queryFn: subscriptionService.getUserSubscription
  });

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // バックエンドの実装に合わせてAPIを変更
        // Statement、Applicationなどの既存エンドポイントからデータを取得する
        const applicationsResponse = await applicationApi.getApplications();
        
        // 取得したデータからダッシュボードデータを構築
        const applications = applicationsResponse.data || [];
        
        // ダッシュボードデータを構築
        setData({
          progress: {
            completedTasks: 24,
            totalTasks: 50,
            courses: [
              { id: '1', title: '現代文の読解力強化', progress: 65 },
              { id: '2', title: '数学III - 微分積分', progress: 40 },
              { id: '3', title: '英語リスニング', progress: 75 },
            ]
          },
          events: [
            { id: '1', title: '東京大学オープンキャンパス', date: '2023-08-15', type: 'event' },
            { id: '2', title: '志望理由書提出期限', date: '2023-09-10', type: 'deadline' },
            { id: '3', title: '模擬試験', date: '2023-07-30', type: 'exam' },
          ],
          applications: {
            count: Array.isArray(applications) ? applications.length : 0,
            nextDeadline: applications.length > 0 ? {
              university: applications[0].university_name,
              document: applications[0].documents?.[0]?.name ?? '書類',
              date: applications[0].documents?.[0]?.deadline ?? '未定'
            } : null
          },
          recommendations: [
            { type: 'content', title: '総合型選抜のための小論文対策', id: '101' },
            { type: 'quiz', title: '英語長文読解テスト', id: '203' },
            { type: 'course', title: '志望理由書の書き方講座', id: '305' },
          ],
          aiAnalysis: {
            strengths: ['論理的思考', '文章表現力', '情報整理能力'],
            interests: ['社会問題', '経済学', '国際関係'],
            recentTopics: ['大学研究', '学部選択', '自己分析']
          }
        });

      } catch (error) {
        console.error('ダッシュボードデータの取得に失敗しました:', error);
        
        // エラー時のフォールバックデータ
        setData({
          progress: {
            completedTasks: 24,
            totalTasks: 50,
            courses: [
              { id: '1', title: '現代文の読解力強化', progress: 65 },
              { id: '2', title: '数学III - 微分積分', progress: 40 },
              { id: '3', title: '英語リスニング', progress: 75 },
            ]
          },
          events: [
            { id: '1', title: '東京大学オープンキャンパス', date: '2023-08-15', type: 'event' },
            { id: '2', title: '志望理由書提出期限', date: '2023-09-10', type: 'deadline' },
            { id: '3', title: '模擬試験', date: '2023-07-30', type: 'exam' },
          ],
          applications: {
            count: 3,
            nextDeadline: {
              university: '東京大学',
              document: '志望理由書',
              date: '2023-09-10'
            }
          },
          recommendations: [
            { type: 'content', title: '総合型選抜のための小論文対策', id: '101' },
            { type: 'quiz', title: '英語長文読解テスト', id: '203' },
            { type: 'course', title: '志望理由書の書き方講座', id: '305' },
          ],
          aiAnalysis: {
            strengths: ['論理的思考', '文章表現力', '情報整理能力'],
            interests: ['社会問題', '経済学', '国際関係'],
            recentTopics: ['大学研究', '学部選択', '自己分析']
          }
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-8">ダッシュボード</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* 学習進捗 */}
        <div className="bg-white p-6 rounded-xl shadow">
          <div className="flex items-center mb-4">
            <BookOpen className="h-6 w-6 mr-2 text-blue-600" />
            <h2 className="text-xl font-semibold">学習進捗</h2>
          </div>
          <div className="mb-4">
            <div className="flex justify-between mb-1">
              <span>全体の進捗</span>
              <span>{data?.progress.completedTasks}/{data?.progress.totalTasks} タスク</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-blue-600 h-2.5 rounded-full" 
                style={{ width: `${(data?.progress.completedTasks || 0) / (data?.progress.totalTasks || 1) * 100}%` }}
              ></div>
            </div>
          </div>
          <div className="space-y-3">
            {data?.progress.courses.map(course => (
              <div key={course.id}>
                <div className="flex justify-between text-sm mb-1">
                  <span>{course.title}</span>
                  <span>{course.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div 
                    className="bg-green-600 h-1.5 rounded-full" 
                    style={{ width: `${course.progress}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
          <button 
            onClick={() => router.push('/contents')}
            className="mt-4 text-sm text-blue-600 hover:text-blue-800"
          >
            すべての学習コンテンツを見る →
          </button>
        </div>

        {/* 予定イベント */}
        <div className="bg-white p-6 rounded-xl shadow">
          <div className="flex items-center mb-4">
            <Calendar className="h-6 w-6 mr-2 text-purple-600" />
            <h2 className="text-xl font-semibold">予定イベント</h2>
          </div>
          <div className="space-y-4">
            {data?.events.map(event => (
              <div key={event.id} className="flex items-start">
                <div className={`
                  min-w-10 h-10 flex items-center justify-center rounded-full mr-3
                  ${event.type === 'deadline' ? 'bg-red-100 text-red-600' : 
                    event.type === 'exam' ? 'bg-yellow-100 text-yellow-600' : 
                    'bg-blue-100 text-blue-600'}
                `}>
                  {event.type === 'deadline' ? '期限' : event.type === 'exam' ? '試験' : 'イベ'}
                </div>
                <div>
                  <p className="font-medium">{event.title}</p>
                  <p className="text-sm text-gray-600">{event.date}</p>
                </div>
              </div>
            ))}
          </div>
          <button 
            className="mt-4 text-sm text-purple-600 hover:text-purple-800"
          >
            すべての予定を見る →
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* 志望校状況 */}
        <div className="bg-white p-6 rounded-xl shadow">
          <div className="flex items-center mb-4">
            <GraduationCap className="h-6 w-6 mr-2 text-indigo-600" />
            <h2 className="text-xl font-semibold">志望校状況</h2>
          </div>
          <p className="text-3xl font-bold mb-4">{data?.applications.count}<span className="text-base ml-1 font-normal">校</span></p>
          
          {data?.applications.nextDeadline ? (
            <div className="border-t pt-4">
              <p className="text-sm text-gray-600 mb-1">次の提出期限</p>
              <p className="font-medium">{data.applications.nextDeadline.university}</p>
              <p className="text-sm">{data.applications.nextDeadline.document}</p>
              <p className="text-sm text-red-600">{data.applications.nextDeadline.date}まで</p>
            </div>
          ) : (
            <p className="text-sm text-gray-600">現在期限の近い提出書類はありません</p>
          )}
          
          <button 
            onClick={() => router.push('/application')}
            className="mt-4 text-sm text-indigo-600 hover:text-indigo-800"
          >
            志望校管理へ →
          </button>
        </div>

        {/* おすすめコンテンツ */}
        <div className="bg-white p-6 rounded-xl shadow">
          <div className="flex items-center mb-4">
            <BookOpen className="h-6 w-6 mr-2 text-emerald-600" />
            <h2 className="text-xl font-semibold">おすすめコンテンツ</h2>
          </div>
          <div className="space-y-3">
            {data?.recommendations.map(item => (
              <div key={item.id} className="border-b pb-2 last:border-0">
                <p className="font-medium">{item.title}</p>
                <p className="text-xs text-gray-600">
                  {item.type === 'content' ? 'コンテンツ' : 
                   item.type === 'quiz' ? 'クイズ' : 'コース'}
                </p>
              </div>
            ))}
          </div>
          <button 
            onClick={() => router.push('/contents')}
            className="mt-4 text-sm text-emerald-600 hover:text-emerald-800"
          >
            すべてのコンテンツを見る →
          </button>
        </div>

        {/* AIチャット分析 */}
        <div className="bg-white p-6 rounded-xl shadow">
          <div className="flex items-center mb-4">
            <BrainCircuit className="h-6 w-6 mr-2 text-orange-600" />
            <h2 className="text-xl font-semibold">AIチャット分析</h2>
          </div>
          <div className="mb-4">
            <p className="text-sm font-medium mb-1">あなたの強み</p>
            <div className="flex flex-wrap gap-2">
              {data?.aiAnalysis.strengths.map((item, i) => (
                <span key={i} className="bg-orange-100 text-orange-800 text-xs px-2 py-1 rounded-full">
                  {item}
                </span>
              ))}
            </div>
          </div>
          <div className="mb-4">
            <p className="text-sm font-medium mb-1">興味分野</p>
            <div className="flex flex-wrap gap-2">
              {data?.aiAnalysis.interests.map((item, i) => (
                <span key={i} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                  {item}
                </span>
              ))}
            </div>
          </div>
          <div>
            <p className="text-sm font-medium mb-1">最近のトピック</p>
            <div className="flex flex-wrap gap-2">
              {data?.aiAnalysis.recentTopics.map((item, i) => (
                <span key={i} className="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded-full">
                  {item}
                </span>
              ))}
            </div>
          </div>
          <button 
            onClick={() => router.push('/chat')}
            className="mt-4 text-sm text-orange-600 hover:text-orange-800"
          >
            AIチャットを開始する →
          </button>
        </div>
      </div>

      {/* 志望理由書 */}
      <div className="bg-white p-6 rounded-xl shadow mb-8">
        <div className="flex items-center mb-4">
          <FileText className="h-6 w-6 mr-2 text-teal-600" />
          <h2 className="text-xl font-semibold">志望理由書作成状況</h2>
        </div>
        <div className="flex flex-col md:flex-row md:items-center justify-between">
          <div>
            <p className="mb-2">自己分析と志望理由書の作成で、あなたの志望校合格への道筋を明確にしましょう。</p>
            <p className="text-sm text-gray-600">AIアシスタントが作成プロセスをサポートします。</p>
          </div>
          <button 
            onClick={() => router.push('/statement')}
            className="mt-4 md:mt-0 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition"
          >
            志望理由書を作成する
          </button>
        </div>
      </div>
    </div>
  );
}; 