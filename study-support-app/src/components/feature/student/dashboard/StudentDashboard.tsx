"use client";

import React, { useEffect, useState } from 'react';
import { Calendar, GraduationCap, BookOpen, FileText, BrainCircuit } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { applicationApi } from '@/lib/api-client';
import { useQuery } from '@tanstack/react-query';
import { ApplicationDetailResponse } from '@/components/feature/student/application/ApplicationList';
import { subscriptionService } from '@/services/subscriptionService';
import { AxiosResponse } from 'axios';
import { Subscription } from '@/types/subscription';
import Link from 'next/link';

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
    <div className="p-4 sm:p-6">
      <h1 className="text-2xl sm:text-3xl font-bold mb-6 sm:mb-8">ダッシュボード</h1>

      {/* AIチャット分析 */}
      <div className="bg-white p-4 sm:p-6 rounded-xl shadow mb-6 sm:mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 sm:mb-6 gap-4">
          <div>
            <h2 className="text-lg sm:text-xl font-semibold mb-2">AIチャット分析</h2>
            <p className="text-sm text-gray-600">AIとの対話から分析されたあなたの特徴</p>
          </div>
          <Link
            href="/student/chat/self-analysis"
            className="w-full sm:w-auto px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition flex items-center justify-center gap-2"
          >
            <span>AIチャットを開始</span>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          <div className="bg-orange-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-3">
              <h3 className="font-medium text-orange-800">あなたの強み</h3>
            </div>
            <p className="text-sm text-gray-600 mb-3">AIとの対話から分析された、あなたの得意分野や特徴的な能力です。</p>
            <div className="flex flex-wrap gap-2">
              {data?.aiAnalysis.strengths.map((item, i) => (
                <span key={i} className="bg-white text-orange-800 text-xs px-3 py-1.5 rounded-full border border-orange-200">
                  {item}
                </span>
              ))}
            </div>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-3">
              <h3 className="font-medium text-blue-800">興味分野</h3>
            </div>
            <p className="text-sm text-gray-600 mb-3">あなたが関心を持っている分野や、深く学びたいと考えている領域です。</p>
            <div className="flex flex-wrap gap-2">
              {data?.aiAnalysis.interests.map((item, i) => (
                <span key={i} className="bg-white text-blue-800 text-xs px-3 py-1.5 rounded-full border border-blue-200">
                  {item}
                </span>
              ))}
            </div>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-3">
              <h3 className="font-medium text-gray-800">最近のトピック</h3>
            </div>
            <p className="text-sm text-gray-600 mb-3">最近のAIとの対話で話題になった、あなたの関心事や検討中のテーマです。</p>
            <div className="flex flex-wrap gap-2">
              {data?.aiAnalysis.recentTopics.map((item, i) => (
                <span key={i} className="bg-white text-gray-800 text-xs px-3 py-1.5 rounded-full border border-gray-200">
                  {item}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* おすすめコンテンツと志望理由書 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-6 sm:mb-8">
        {/* おすすめコンテンツ */}
        <div className="bg-white p-4 sm:p-6 rounded-xl shadow">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 sm:mb-6 gap-4">
            <div>
              <h2 className="text-lg sm:text-xl font-semibold mb-2">おすすめコンテンツ</h2>
              <p className="text-sm text-gray-600">あなたに最適な学習コンテンツ</p>
            </div>
            <Link
              href="/student/contents"
              className="w-full sm:w-auto text-sm bg-gray-50 text-gray-600 hover:bg-gray-100 px-4 py-2 rounded-lg flex items-center justify-center gap-2 font-medium transition-colors whitespace-nowrap"
            >
              すべてのコンテンツを確認する
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </Link>
          </div>
          <div className="space-y-3 sm:space-y-4">
            {data?.recommendations.map(item => (
              <div key={item.id} className="bg-gray-50 p-3 sm:p-4 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-medium">{item.title}</p>
                  <span className="text-xs px-2 py-1 bg-gray-200 rounded-full">
                    {item.type === 'content' ? 'コンテンツ' :
                     item.type === 'quiz' ? 'クイズ' : 'コース'}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <span>所要時間: 30分</span>
                  <span>•</span>
                  <span>難易度: 中級</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 志望理由書 */}
        <div className="bg-white p-4 sm:p-6 rounded-xl shadow">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 sm:mb-6 gap-4">
            <div>
              <h2 className="text-lg sm:text-xl font-semibold mb-2">志望理由書作成状況</h2>
              <p className="text-sm text-gray-600">AIアシスタントが作成プロセスをサポートします</p>
            </div>
          </div>
          <div className="bg-gradient-to-r from-teal-50 to-blue-50 rounded-lg p-4 sm:p-6 mb-4 sm:mb-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-2">
                <h3 className="font-medium text-teal-800">自己分析と志望理由書の作成</h3>
                <p className="text-sm text-gray-600">あなたの志望校合格への道筋を明確にしましょう</p>
              </div>
              <Link
                href="/statement"
                className="w-full sm:w-auto px-6 py-2.5 bg-gradient-to-r from-teal-500 to-teal-600 text-white rounded-lg hover:from-teal-600 hover:to-teal-700 transition shadow-sm flex items-center justify-center gap-2 whitespace-nowrap"
              >
                <span>作成を開始</span>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </Link>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
            <div className="bg-gray-50 p-3 rounded-lg text-center">
              <p className="text-sm text-gray-600 mb-1">作成済み</p>
              <p className="text-lg sm:text-xl font-semibold text-gray-800">0</p>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg text-center">
              <p className="text-sm text-gray-600 mb-1">下書き</p>
              <p className="text-lg sm:text-xl font-semibold text-gray-800">0</p>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg text-center">
              <p className="text-sm text-gray-600 mb-1">添削待ち</p>
              <p className="text-lg sm:text-xl font-semibold text-gray-800">0</p>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg text-center">
              <p className="text-sm text-gray-600 mb-1">完了</p>
              <p className="text-lg sm:text-xl font-semibold text-gray-800">0</p>
            </div>
          </div>
        </div>
      </div>
      {/* 予定イベントと志望校状況 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-6 sm:mb-8">
        {/* 予定イベント */}
        <div className="bg-white p-4 sm:p-6 rounded-xl shadow">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 sm:mb-6 gap-4">
            <div>
              <h2 className="text-lg sm:text-xl font-semibold mb-2">予定イベント</h2>
              <p className="text-sm text-gray-600">今後の予定を確認しましょう</p>
            </div>
            <Link
              href="/events"
              className="w-full sm:w-auto text-sm bg-gray-50 text-gray-600 hover:bg-gray-100 px-4 py-2 rounded-lg flex items-center justify-center gap-2 font-medium transition-colors whitespace-nowrap"
            >
              すべての予定を確認する
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </Link>
          </div>
          <div className="space-y-3 sm:space-y-4">
            {data?.events.map(event => (
              <div key={event.id} className="flex items-start p-3 sm:p-4 bg-gray-50 rounded-lg">
                <div className="min-w-[100px]">
                  <p className="text-sm text-gray-600">{event.date}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {event.type === 'deadline' ? '提出期限' :
                     event.type === 'exam' ? '試験' : 'イベント'}
                  </p>
                </div>
                <div className="flex-1">
                  <p className="font-medium">{event.title}</p>
                  {event.type === 'deadline' && (
                    <p className="text-sm text-red-600 mt-1">提出期限が近づいています</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 志望校状況 */}
        <div className="bg-white p-4 sm:p-6 rounded-xl shadow">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 sm:mb-6 gap-4">
            <div>
              <h2 className="text-lg sm:text-xl font-semibold mb-2">志望校状況</h2>
              <p className="text-sm text-gray-600">志望校の出願状況を確認しましょう</p>
            </div>
            <Link
              href="/student/application"
              className="w-full sm:w-auto text-sm bg-gray-50 text-gray-600 hover:bg-gray-100 px-4 py-2 rounded-lg flex items-center justify-center gap-2 font-medium transition-colors whitespace-nowrap"
            >
              志望校一覧を確認する
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </Link>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 sm:p-6 mb-4 sm:mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-sm text-gray-600">志望校数</p>
                <p className="text-2xl sm:text-3xl font-semibold mt-1">{data?.applications.count}<span className="text-base ml-1 font-normal">校</span></p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600">出願書類</p>
                <p className="text-2xl sm:text-3xl font-semibold mt-1">0<span className="text-base ml-1 font-normal">件</span></p>
              </div>
            </div>
          </div>
          {data?.applications.nextDeadline ? (
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-2">次の提出期限</p>
              <div className="space-y-2">
                <p className="font-medium">{data?.applications.nextDeadline?.university}</p>
                <div className="flex items-center justify-between">
                  <p className="text-sm">{data?.applications.nextDeadline?.document}</p>
                  <p className="text-sm text-red-600">{data?.applications.nextDeadline?.date}まで</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-600">現在期限の近い提出書類はありません</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
