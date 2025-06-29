'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from "@/components/ui/button";
// Input は現時点で使用されていないためコメントアウト
// import { Input } from "@/components/ui/input"; 
import { Label } from "@/components/ui/label";
// Select関連のコンポーネントをshadcn/uiからインポート
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"; // Linterエラーが発生しているが、パスは正しいはず。後で確認。
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useSession, signOut } from 'next-auth/react';
import { toast } from 'sonner'; // Linterエラーが発生しているが、インストール済みのはず。後で確認。

// 都道府県リスト (例)
const prefectures = [
  "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
  "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
  "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
  "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
  "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
  "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
  "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
];

const ProfileSetupPage = () => {
  const router = useRouter();
  const { data: session, update, status } = useSession(); // status もここで取得
  const [grade, setGrade] = useState<string>('');
  const [prefecture, setPrefecture] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSave = async () => {
    setIsLoading(true);
    try {
      const userId = session?.user?.id; // セッションからユーザーIDを取得 (★Sessionの型定義を確認)
      if (!userId) {
        toast.error('ユーザー情報が見つかりません。再度ログインしてください。');
        router.push('/login');
        setIsLoading(false); // ローディング解除
        return;
      }
      
      // ★★★ 実際のSession型に合わせて accessToken の取得方法を確認・修正 ★★★
      // next-authのデフォルトではJWTトークンは直接sessionオブジェクトに含まれないことが多い
      // callbacksでsessionに含めるか、getServerSession/getTokenなど別の方法で取得する必要がある場合あり
      const accessToken = session?.user?.accessToken; // 型定義が正しいため直接アクセス
      if (!accessToken) {
          toast.error('認証情報が見つかりません。再度ログインしてください。');
          router.push('/login');
          setIsLoading(false); // ローディング解除
          return;
      }

      // API呼び出し
      // ★★★ バックエンドのユーザー更新APIのエンドポイントを確認 (/users/me or /users/{userId}) ★★★
      // 現状は /user-settings を使っているはず
              const response = await fetch(`/api/v1/auth/user-settings`, { // ★ エンドポイントを修正
        method: 'PUT', // ★ PUT に修正
        headers: {
           'Content-Type': 'application/json',
           'Authorization': `Bearer ${accessToken}`
         },
        body: JSON.stringify({ 
            // エンドポイントが受け付ける形式で送信
            name: session?.user?.name, // nameフィールドを使用
            grade: grade || null,
            prefecture: prefecture || null
         })
      });

      // ★★★ エラーハンドリング強化 ★★★
      if (response.status === 401) {
          toast.error('認証セッションが無効になりました。再度ログインしてください。');
          await signOut({ redirect: false }); // セッション情報をクリア
          router.push('/login');
          setIsLoading(false);
          return;
      }

      if (!response.ok) {
         const errorData = await response.json().catch(() => ({ detail: '不明なエラーが発生しました。' }));
         console.error('API エラーレスポンス:', response.status, errorData);
         throw new Error(errorData.detail || `プロフィールの更新に失敗しました。(${response.status})`);
      }

      const updatedUserData = await response.json(); // 更新後のユーザーデータを取得

      toast.success('プロフィール情報を更新しました。');

      // --- セッション情報更新 (NextAuth) --- 
      try {
        // バックエンドでの更新後、引数なしで update() を呼び出し、
        // サーバーから最新のセッション情報を取得して更新する
        console.log('セッション更新を開始...');
        await update(); 
        console.log('セッション更新完了');
      } catch (updateError) {
          console.error("Session update error:", updateError);
          // 失敗した場合でも続行するが、ユーザーにリロードを促す
          toast.warning("セッション情報の更新に失敗しました。ページをリロードすると最新情報が反映されます。");
      }
      // --- ここまでセッション情報更新 ---

      // 次のステップ（志望校設定）へ遷移
      router.push('/target-schools/setup');
    } catch (error: any) {
      console.error("Profile update error:", error);
      toast.error(error.message || 'プロフィールの更新中にエラーが発生しました。');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = () => {
    // スキップして次のステップ（志望校設定）へ遷移
    router.push('/target-schools/setup');
  };

  // セッションデータのロード状態をチェック
  if (status === "loading") {
    return <div className="flex justify-center items-center min-h-screen">Loading...</div>; // ローディング表示を中央寄せ
  }

  // 未認証ならログインページへリダイレクト
  if (status === "unauthenticated" || !session) {
     // リダイレクトはuseEffect内で行うのがよりReact的だが、ここではシンプルに実行
     router.push('/login'); 
     return null; 
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>プロフィール設定</CardTitle>
          <CardDescription>任意で情報を入力してください。後からでも変更できます。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid w-full items-center gap-1.5">
            <Label htmlFor="grade">学年</Label>
            <Select onValueChange={setGrade} value={grade}>
              <SelectTrigger id="grade">
                <SelectValue placeholder="学年を選択" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="高校1年生">高校1年生</SelectItem>
                <SelectItem value="高校2年生">高校2年生</SelectItem>
                <SelectItem value="高校3年生">高校3年生</SelectItem>
                <SelectItem value="既卒生">既卒生</SelectItem>
                <SelectItem value="その他">その他</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid w-full items-center gap-1.5">
            <Label htmlFor="prefecture">都道府県</Label>
            <Select onValueChange={setPrefecture} value={prefecture}>
              <SelectTrigger id="prefecture">
                <SelectValue placeholder="都道府県を選択" />
              </SelectTrigger>
              <SelectContent style={{ maxHeight: '200px', overflowY: 'auto' }}> {/* ドロップダウンの高さ制限 */} 
                {prefectures.map((pref) => (
                  <SelectItem key={pref} value={pref}>{pref}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {/* 他のプロフィール項目もここに追加可能 */}
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button variant="outline" onClick={handleSkip} disabled={isLoading}>
            スキップ
          </Button>
          <Button onClick={handleSave} disabled={isLoading}>
            {isLoading ? '保存中...' : '保存して次へ'}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default ProfileSetupPage; 