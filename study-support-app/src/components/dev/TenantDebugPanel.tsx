'use client';

import { useState } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { tenantConfig, isDebugMode } from '@/lib/config/tenant';
import { 
  Settings,
  Database,
  Users,
  BarChart,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  X
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';

export default function TenantDebugPanel() {
  const { 
    useMockData, 
    toggleMockData, 
    currentSchool, 
    currentUser, 
    loading, 
    error,
    refreshData 
  } = useTenant();
  
  const [isVisible, setIsVisible] = useState(false);
  
  // 開発環境以外では表示しない
  if (!isDebugMode()) {
    return null;
  }
  
  if (!isVisible) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <Button
          onClick={() => setIsVisible(true)}
          variant="outline"
          size="sm"
          className="bg-orange-500 text-white hover:bg-orange-600"
        >
          <Settings className="h-4 w-4" />
        </Button>
      </div>
    );
  }
  
  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-sm">
      <Card className="shadow-lg border-orange-200">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">
              🏫 テナント機能デバッグ
            </CardTitle>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setIsVisible(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <CardDescription className="text-xs">
            開発環境専用ツール
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* API モード切り替え */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">API モード</span>
              <Switch
                checked={!useMockData}
                onCheckedChange={toggleMockData}
                className="scale-75"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Database className="h-3 w-3" />
              <Badge 
                variant={useMockData ? "secondary" : "default"}
                className="text-xs"
              >
                {useMockData ? "Mock データ" : "実 API"}
              </Badge>
            </div>
            {useMockData && (
              <Alert className="py-2">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="text-xs">
                  現在はMockデータを使用中です
                </AlertDescription>
              </Alert>
            )}
          </div>
          
          {/* 現在のユーザー情報 */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Users className="h-3 w-3" />
              <span className="text-xs font-medium">現在のユーザー</span>
            </div>
            {currentUser ? (
              <div className="text-xs space-y-1">
                <div>名前: {currentUser.full_name}</div>
                <div>ロール: {currentUser.roles?.join(', ')}</div>
                <div>学校: {currentSchool?.name || '未選択'}</div>
              </div>
            ) : (
              <div className="text-xs text-gray-500">未ログイン</div>
            )}
          </div>
          
          {/* 接続状態 */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <BarChart className="h-3 w-3" />
              <span className="text-xs font-medium">接続状態</span>
            </div>
            <div className="flex items-center space-x-2">
              {loading ? (
                <Badge variant="secondary" className="text-xs">
                  読み込み中...
                </Badge>
              ) : error ? (
                <Badge variant="destructive" className="text-xs">
                  <AlertCircle className="h-3 w-3 mr-1" />
                  エラー
                </Badge>
              ) : (
                <Badge variant="default" className="text-xs">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  正常
                </Badge>
              )}
            </div>
            {error && (
              <Alert className="py-2">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="text-xs">
                  {error}
                </AlertDescription>
              </Alert>
            )}
          </div>
          
          {/* 設定情報 */}
          <div className="space-y-2">
            <div className="text-xs font-medium">設定</div>
            <div className="text-xs space-y-1 text-gray-600">
              <div>API URL: {tenantConfig.apiBaseUrl}</div>
              <div>環境: {process.env.NODE_ENV}</div>
              <div>キャッシュ: {tenantConfig.enableCaching ? '有効' : '無効'}</div>
            </div>
          </div>
          
          {/* アクション */}
          <div className="space-y-2">
            <Button 
              onClick={refreshData} 
              variant="outline" 
              size="sm" 
              className="w-full text-xs"
              disabled={loading}
            >
              <RefreshCw className="h-3 w-3 mr-2" />
              データを再取得
            </Button>
            
            <Button 
              onClick={() => {
                localStorage.clear();
                window.location.reload();
              }}
              variant="outline" 
              size="sm" 
              className="w-full text-xs text-red-600 hover:text-red-700"
            >
              キャッシュクリア & リロード
            </Button>
          </div>
          
          {/* 機能フラグ */}
          <div className="space-y-2">
            <div className="text-xs font-medium">機能フラグ</div>
            <div className="space-y-1">
              <div className="flex justify-between items-center text-xs">
                <span>学校管理者</span>
                <Badge 
                  variant={tenantConfig.enableSchoolAdmin ? "default" : "secondary"} 
                  className="text-xs"
                >
                  {tenantConfig.enableSchoolAdmin ? "有効" : "無効"}
                </Badge>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span>先生機能</span>
                <Badge 
                  variant={tenantConfig.enableTeacherFeatures ? "default" : "secondary"} 
                  className="text-xs"
                >
                  {tenantConfig.enableTeacherFeatures ? "有効" : "無効"}
                </Badge>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span>分析機能</span>
                <Badge 
                  variant={tenantConfig.enableAnalytics ? "default" : "secondary"} 
                  className="text-xs"
                >
                  {tenantConfig.enableAnalytics ? "有効" : "無効"}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
