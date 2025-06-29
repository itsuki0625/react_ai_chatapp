import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { MessageSquare, Users, Bell, Settings, Calendar, BookOpen, Trophy, Star, Clock, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import Link from 'next/link';

export default function CommunicationPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        {/* ヘッダーセクション */}
        <div className="mb-8 text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Users className="h-8 w-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">学習コミュニティ</h1>
            <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-200">
              開発中
            </Badge>
          </div>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            同じ目標を持つ仲間と繋がり、一緒に成長できる学習コミュニティです。
            現在開発中の機能をご紹介します。
          </p>
        </div>

        {/* 開発中機能の紹介 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {/* ディスカッションフォーラム */}
          <Card className="border-2 border-dashed border-gray-300 bg-gray-50/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-blue-600" />
                ディスカッションフォーラム
                <Badge variant="outline" className="text-xs">近日公開</Badge>
              </CardTitle>
              <CardDescription>
                志望校別・分野別のディスカッション
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span>志望校別の情報交換</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span>入試対策の相談</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span>勉強法の共有</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span>質問・回答機能</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 勉強会・イベント */}
          <Card className="border-2 border-dashed border-gray-300 bg-gray-50/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-green-600" />
                勉強会・イベント
                <Badge variant="outline" className="text-xs">開発中</Badge>
              </CardTitle>
              <CardDescription>
                オンライン勉強会やイベントの開催
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>オンライン勉強会</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>模擬面接セッション</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>志望理由書添削会</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>専門家による講座</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 学習グループ */}
          <Card className="border-2 border-dashed border-gray-300 bg-gray-50/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-purple-600" />
                学習グループ
                <Badge variant="outline" className="text-xs">企画中</Badge>
              </CardTitle>
              <CardDescription>
                少人数での集中学習グループ
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  <span>志望校別グループ</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  <span>科目別学習グループ</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  <span>進捗共有機能</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  <span>相互サポート</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* ランキング・実績 */}
          <Card className="border-2 border-dashed border-gray-300 bg-gray-50/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="h-5 w-5 text-yellow-600" />
                ランキング・実績
                <Badge variant="outline" className="text-xs">設計中</Badge>
              </CardTitle>
              <CardDescription>
                学習実績の可視化とモチベーション向上
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                  <span>学習時間ランキング</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                  <span>貢献度ポイント</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                  <span>バッジ・称号システム</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                  <span>月間MVP表彰</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* メンター制度 */}
          <Card className="border-2 border-dashed border-gray-300 bg-gray-50/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Star className="h-5 w-5 text-indigo-600" />
                メンター制度
                <Badge variant="outline" className="text-xs">検討中</Badge>
              </CardTitle>
              <CardDescription>
                先輩学生や専門家からの個別指導
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
                  <span>先輩学生メンター</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
                  <span>専門家による指導</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
                  <span>1対1相談セッション</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
                  <span>進路相談サポート</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* リアルタイム学習 */}
          <Card className="border-2 border-dashed border-gray-300 bg-gray-50/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-red-600" />
                リアルタイム学習
                <Badge variant="outline" className="text-xs">構想中</Badge>
              </CardTitle>
              <CardDescription>
                リアルタイムでの共同学習体験
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                  <span>同時学習セッション</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                  <span>画面共有機能</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                  <span>リアルタイムQ&A</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                  <span>集中タイマー機能</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 現在利用可能な機能 */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">現在ご利用いただける機能</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* AIチャット */}
            <Card className="hover:shadow-lg transition-shadow border-green-200 bg-green-50/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-green-600" />
                  AIチャット
                  <Badge variant="default" className="bg-green-600">利用可能</Badge>
                </CardTitle>
                <CardDescription>
                  学習支援AIとの1対1チャット
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 mb-4">
                  <Link href="/chat/self-analysis">
                    <Button variant="outline" className="w-full justify-start">
                      自己分析AI
                    </Button>
                  </Link>
                  <Link href="/chat/admission">
                    <Button variant="outline" className="w-full justify-start">
                      総合型選抜AI
                    </Button>
                  </Link>
                  <Link href="/chat/study-support">
                    <Button variant="outline" className="w-full justify-start">
                      学習支援AI
                    </Button>
                  </Link>
                  <Link href="/chat/faq">
                    <Button variant="outline" className="w-full justify-start">
                      FAQチャット
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>

            {/* お知らせ・通知 */}
            <Card className="hover:shadow-lg transition-shadow border-blue-200 bg-blue-50/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5 text-blue-600" />
                  お知らせ・通知
                  <Badge variant="default" className="bg-blue-600">利用可能</Badge>
                </CardTitle>
                <CardDescription>
                  重要なお知らせや通知の確認
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Link href="/notifications">
                    <Button variant="outline" className="w-full justify-start">
                      通知一覧
                    </Button>
                  </Link>
                  <Link href="/settings">
                    <Button variant="outline" className="w-full justify-start">
                      <Settings className="h-4 w-4 mr-2" />
                      通知設定
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* 開発ロードマップ */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-gray-600" />
              開発ロードマップ
            </CardTitle>
            <CardDescription>
              学習コミュニティ機能の開発予定をお知らせします
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="flex items-start gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <div className="w-0.5 h-8 bg-green-200"></div>
                </div>
                <div>
                  <h4 className="font-semibold text-green-700">フェーズ1: 基盤機能（完了）</h4>
                  <p className="text-sm text-gray-600">AIチャット、通知システム、ユーザー管理</p>
                </div>
              </div>
              
              <div className="flex items-start gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <div className="w-0.5 h-8 bg-blue-200"></div>
                </div>
                <div>
                  <h4 className="font-semibold text-blue-700">フェーズ2: コミュニティ基盤（開発中）</h4>
                  <p className="text-sm text-gray-600">ディスカッションフォーラム、基本的な投稿・返信機能</p>
                  <Badge variant="outline" className="mt-1 text-xs">2024年Q2予定</Badge>
                </div>
              </div>
              
              <div className="flex items-start gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                  <div className="w-0.5 h-8 bg-orange-200"></div>
                </div>
                <div>
                  <h4 className="font-semibold text-orange-700">フェーズ3: 学習グループ（企画中）</h4>
                  <p className="text-sm text-gray-600">小グループ機能、勉強会・イベント開催</p>
                  <Badge variant="outline" className="mt-1 text-xs">2024年Q3予定</Badge>
                </div>
              </div>
              
              <div className="flex items-start gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                </div>
                <div>
                  <h4 className="font-semibold text-purple-700">フェーズ4: 高度な機能（検討中）</h4>
                  <p className="text-sm text-gray-600">メンター制度、ランキング、リアルタイム学習</p>
                  <Badge variant="outline" className="mt-1 text-xs">2024年Q4以降</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* フィードバック募集 */}
        <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
          <CardHeader>
            <CardTitle className="text-center">ご意見・ご要望をお聞かせください</CardTitle>
            <CardDescription className="text-center">
              より良い学習コミュニティを作るため、皆様のご意見をお待ちしています
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-sm text-gray-600 mb-4">
              どのような機能があったら学習がもっと楽しくなりますか？<br />
              ご意見・ご要望は設定ページのお問い合わせフォームからお送りください。
            </p>
            <Link href="/settings">
              <Button className="bg-blue-600 hover:bg-blue-700">
                フィードバックを送る
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 