'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from "@/components/ui/button";
// Input は未使用のためコメントアウト
// import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
// Select関連、Linterエラーは無視して進める（後で確認）
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"; 
import { X } from 'lucide-react';
import { useSession, signOut } from 'next-auth/react';
// toast関連、Linterエラーは無視して進める（後で確認）
import { toast } from 'sonner'; 

// 仮のデータ型 (バックエンドのスキーマに合わせる)
interface DesiredDepartmentInput {
  department_id: string; // UUID
  admission_method_id: string; // UUID
}

interface DesiredSchoolInput {
  university_id: string; // UUID
  preference_order: number;
  desired_departments: DesiredDepartmentInput[];
}

// APIからのレスポンス型 (バックエンドのスキーマに合わせる)
interface DepartmentResponse {
    id: string; // UUID
    name: string;
    // 他に必要な学部情報があれば追加
}

interface UniversityResponse {
    id: string; // UUID
    name: string;
    departments: DepartmentResponse[];
    // 他に必要な大学情報があれば追加
}

interface AdmissionMethodResponse {
    id: string; // UUID
    name: string;
    // 他に必要な入試方式情報があれば追加
}

const TargetSchoolSetupPage = () => {
  const router = useRouter();
  const { data: session, status } = useSession();
  // ユーザーが追加した志望校のリスト
  const [desiredSchools, setDesiredSchools] = useState<DesiredSchoolInput[]>([]);
  // 現在フォームで編集中の志望校情報
  const [currentSchool, setCurrentSchool] = useState<Partial<DesiredSchoolInput>>({
     university_id: '', 
     desired_departments: [{ department_id: '', admission_method_id: '' }] 
  });
  const [isLoading, setIsLoading] = useState(false);

  // 選択肢データ用のState
  const [universitiesData, setUniversitiesData] = useState<UniversityResponse[]>([]);
  const [admissionMethodsData, setAdmissionMethodsData] = useState<AdmissionMethodResponse[]>([]);
  const [isFetchingOptions, setIsFetchingOptions] = useState(true); // 選択肢取得中のローディング
  const [fetchError, setFetchError] = useState<string | null>(null); // 選択肢取得エラー

  // データ取得 Effect
  useEffect(() => {
    const fetchOptions = async () => {
      setIsFetchingOptions(true);
      setFetchError(null);

      // ★★★ アクセストークンの取得 (要確認・修正) ★★★
      const accessToken = session?.user?.accessToken;
      if (!accessToken) {
        setFetchError('認証情報が見つかりません。ログインし直してください。');
        toast.error('認証情報が見つかりません。再度ログインしてください。');
        await signOut({ redirect: false });
        router.push('/login');
        setIsFetchingOptions(false);
        return;
      }

      const headers = { 
        'Authorization': `Bearer ${accessToken}`
      };

      try {
        const [univResponse, admResponse] = await Promise.all([
          fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/universities/`, { headers }),
          fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/admissions/`, { headers })
        ]);

        if (univResponse.status === 401 || admResponse.status === 401) {
            toast.error('認証セッションが無効になりました。再度ログインしてください。');
            await signOut({ redirect: false });
            router.push('/login');
            setIsFetchingOptions(false);
            return;
        }

        if (!univResponse.ok || !admResponse.ok) {
            let errorMsg = '選択肢データの取得に失敗しました。';
            if (!univResponse.ok) {
                 const errData = await univResponse.json().catch(() => ({}));
                 errorMsg = `大学リスト取得エラー: ${errData.detail || univResponse.statusText}`;
            } else if (!admResponse.ok) {
                 const errData = await admResponse.json().catch(() => ({}));
                 errorMsg = `入試方式リスト取得エラー: ${errData.detail || admResponse.statusText}`;
            }
          throw new Error(errorMsg);
        }

        const univData: UniversityResponse[] = await univResponse.json();
        const admData: AdmissionMethodResponse[] = await admResponse.json();
        
        // 想定: univData は [{id, name, departments: [{id, name}]}] の形式
        // 想定: admData は [{id, name}] の形式
        setUniversitiesData(univData);
        setAdmissionMethodsData(admData);

      } catch (error: any) {
        console.error("Failed to fetch options:", error);
        setFetchError(error.message || '選択肢の取得中に不明なエラーが発生しました。');
        toast.error(fetchError || '選択肢データの取得に失敗しました。')
      } finally {
        setIsFetchingOptions(false);
      }
    };

    // セッションが読み込まれてからフェッチを実行
    if (status === "authenticated" && session) {
      fetchOptions();
    }
  // status と session が変更されたときにも再実行 (ログイン/ログアウト時など)
  }, [status, session, router, fetchError]); 

  // 現在入力中の大学IDを更新
  const handleCurrentUniversityChange = (value: string) => {
    setCurrentSchool(prev => ({
       ...prev,
       university_id: value,
       // 大学が変わったら学部選択もリセット
       desired_departments: [{ department_id: '', admission_method_id: '' }] 
    }));
  };

  // 現在入力中の学部/入試方式情報を更新
  const handleDepartmentChange = (index: number, field: keyof DesiredDepartmentInput, value: string) => {
    const updatedDepartments = [...(currentSchool.desired_departments || [])];
    if (updatedDepartments[index]) {
      updatedDepartments[index] = { ...updatedDepartments[index], [field]: value };
      setCurrentSchool(prev => ({ ...prev, desired_departments: updatedDepartments }));
    }
  };

  // 新しい学部入力欄を追加
  const addDepartmentField = () => {
    const newDepartments = [...(currentSchool.desired_departments || []), { department_id: '', admission_method_id: '' }];
    setCurrentSchool(prev => ({ ...prev, desired_departments: newDepartments }));
  };

  // 学部入力欄を削除
  const removeDepartmentField = (index: number) => {
    const newDepartments = (currentSchool.desired_departments || []).filter((_, i) => i !== index);
    // 最後の学部が削除された場合は空のフィールドを1つ残す
    if (newDepartments.length === 0) {
        newDepartments.push({ department_id: '', admission_method_id: '' });
    }
    setCurrentSchool(prev => ({ ...prev, desired_departments: newDepartments }));
  };

  // 現在入力中の情報を志望校リストに追加
  const addDesiredSchool = () => {
    // バリデーション
    if (!currentSchool.university_id) {
      toast.warning('大学を選択してください。');
      return;
    }
    if (!currentSchool.desired_departments || currentSchool.desired_departments.length === 0 || 
        !currentSchool.desired_departments.every(d => d.department_id && d.admission_method_id)) {
      toast.warning('少なくとも1つの学部と入試方式を選択してください。');
      return;
    }
    // 既に同じ大学がリストにあるかチェック (任意)
    // if (desiredSchools.some(school => school.university_id === currentSchool.university_id)) {
    //   toast.warning('この大学は既に追加されています。');
    //   return;
    // }

    const newSchool: DesiredSchoolInput = {
      university_id: currentSchool.university_id,
      preference_order: desiredSchools.length + 1, // 順位を自動設定
      desired_departments: currentSchool.desired_departments.filter(d => d.department_id && d.admission_method_id), // 未入力の組は除外
    };
    setDesiredSchools([...desiredSchools, newSchool]);
    // 入力フォームをリセット
    setCurrentSchool({ university_id: '', desired_departments: [{ department_id: '', admission_method_id: '' }] });
  };

  // 志望校リストから削除
  const removeDesiredSchool = (index: number) => {
    const updatedSchools = desiredSchools.filter((_, i) => i !== index);
    // 削除後に preference_order を再設定
    const reorderedSchools = updatedSchools.map((school, i) => ({ ...school, preference_order: i + 1 }));
    setDesiredSchools(reorderedSchools);
  };

  // 保存処理
  const handleSave = async () => {
    if (desiredSchools.length === 0) {
        // リストが空の場合はスキップと同じ動作
        router.push('/dashboard');
        return;
    }
    setIsLoading(true);
    try {
      // ★★★ アクセストークンの取得 (ProfileSetupPage と同様に要確認・修正) ★★★
      const accessToken = session?.user?.accessToken;
      if (!accessToken) {
          toast.error('認証情報が見つかりません。再度ログインしてください。');
          await signOut({ redirect: false });
          router.push('/login');
          setIsLoading(false);
          return;
      }

      const headers = {
         'Content-Type': 'application/json',
         'Authorization': `Bearer ${accessToken}` // ★認証ヘッダーを追加
      };
      
      // バックエンドに一括登録APIがない場合、個別にPOSTリクエストを送る
      const results = await Promise.all(desiredSchools.map(school => 
        fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/desired-schools/`, {
          method: 'POST',
          headers: headers, // 認証ヘッダーを含む
          body: JSON.stringify(school),
        })
      ));

      // ★ 401 エラーチェック (いずれか一つでも401ならログアウト)
      const unauthorizedRequest = results.find(res => res.status === 401);
      if (unauthorizedRequest) {
          toast.error('認証セッションが無効になりました。再度ログインしてください。');
          await signOut({ redirect: false });
          router.push('/login');
          setIsLoading(false);
          return;
      }

      // 全てのリクエストが成功したかチェック
      const failedRequests = results.filter(res => !res.ok);
      if (failedRequests.length > 0) {
        // エラー処理 (最初のエラーを表示する例)
        const firstError = await failedRequests[0].json();
        const failedSchoolIndex = results.findIndex(res => !res.ok);
        // ★★★ 表示用に大学名を取得 (universitiesData を参照) ★★★
        const failedSchoolName = universitiesData.find(u => u.id === desiredSchools[failedSchoolIndex]?.university_id)?.name || '不明な大学';
        throw new Error(`志望校「${failedSchoolName}」の登録に失敗: ${firstError.detail || '不明なエラー'}`);
      }

      toast.success('志望校情報を保存しました。');
      router.push('/dashboard'); // ダッシュボードへ遷移
    } catch (error: any) {
      console.error("Desired school save error:", error);
      toast.error(error.message || '志望校情報の保存中にエラーが発生しました。');
    } finally {
      setIsLoading(false);
    }
  };

  // スキップ処理
  const handleSkip = () => {
    router.push('/dashboard');
  };

  // 認証状態チェック
  if (status === "loading" || isFetchingOptions) {
    return <div className="flex justify-center items-center min-h-screen">Loading...</div>;
  }
  if (status === "unauthenticated" || !session) {
    router.push('/login');
    return null;
  }
  if (fetchError) {
      return (
          <div className="flex flex-col justify-center items-center min-h-screen text-red-600">
              <p>エラーが発生しました: {fetchError}</p>
              <Button onClick={() => window.location.reload()} className="mt-4">再読み込み</Button>
          </div>
      );
  }

  // --- JSX --- //
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      {/* 入力フォームカード */}
      <Card className="w-full max-w-2xl mb-8">
        <CardHeader>
          <CardTitle>志望校設定</CardTitle>
          <CardDescription>志望する大学・学部・入試方式を追加してください。後からでも変更・追加できます。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 大学選択 */}
          <div className="grid gap-1.5">
            <Label htmlFor="university">大学</Label>
            <Select onValueChange={handleCurrentUniversityChange} value={currentSchool.university_id || ''}>
              <SelectTrigger id="university">
                <SelectValue placeholder="大学を選択" />
              </SelectTrigger>
              <SelectContent>
                {/* ★ APIから取得したデータを使用 */}
                {universitiesData.map((univ) => (
                  <SelectItem key={univ.id} value={univ.id}>{univ.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* 学部・入試方式入力 */}
          <div className="space-y-4">
            <Label>学部・入試方式</Label>
            {(currentSchool.desired_departments || []).map((dept, index) => (
              <div key={index} className="flex items-center space-x-2 p-2 border rounded">
                <div className="flex-1 grid grid-cols-2 gap-2">
                  {/* 学部選択 (選択された大学に基づいてフィルタリング) */}
                  <Select 
                    onValueChange={(value: string) => handleDepartmentChange(index, 'department_id', value)}
                    value={dept.department_id || ''}
                    disabled={!currentSchool.university_id || universitiesData.find(u => u.id === currentSchool.university_id)?.departments.length === 0} // 大学未選択または学部データがない場合は非活性
                  >
                    <SelectTrigger><SelectValue placeholder={currentSchool.university_id ? "学部を選択" : "先に大学を選択"} /></SelectTrigger>
                    <SelectContent>
                      {/* ★ 選択中の大学の学部リストを使用 */}
                      {universitiesData.find(u => u.id === currentSchool.university_id)?.departments.map((d) => (
                        <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {/* 入試方式選択 */}
                  <Select 
                    onValueChange={(value: string) => handleDepartmentChange(index, 'admission_method_id', value)}
                    value={dept.admission_method_id || ''}
                  >
                    <SelectTrigger><SelectValue placeholder="入試方式を選択" /></SelectTrigger>
                    <SelectContent>
                      {/* ★ APIから取得したデータを使用 */}
                      {admissionMethodsData.map((a) => (
                        <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {/* 削除ボタン (学部が複数ある場合のみ表示) */}
                {(currentSchool.desired_departments?.length ?? 0) > 1 && (
                    <Button variant="ghost" size="icon" onClick={() => removeDepartmentField(index)}>
                      <X className="h-4 w-4" />
                    </Button>
                )}
              </div>
            ))}
            {/* 学部追加ボタン */}
            <Button variant="outline" size="sm" onClick={addDepartmentField}>+ 学部/方式を追加</Button>
          </div>

          {/* 志望リストに追加ボタン */}
          <div className="text-right">
             <Button onClick={addDesiredSchool}>志望リストに追加</Button>
          </div>
        </CardContent>
      </Card>

      {/* 登録済み志望校リスト表示カード */}
      {desiredSchools.length > 0 && (
        <Card className="w-full max-w-2xl">
          <CardHeader>
            <CardTitle>登録済み志望校リスト ({desiredSchools.length}件)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {desiredSchools.map((school, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded bg-white">
                <div>
                    {/* ★ ヘルパー関数で名前を表示 */}
                    <p className="font-semibold">{school.preference_order}. {universitiesData.find(u => u.id === school.university_id)?.name || '不明な大学'}</p>
                    <ul className="list-disc list-inside text-sm text-gray-600 ml-4">
                      {(school.desired_departments || []).map((dept, deptIndex) => (
                         <li key={deptIndex}>
                            {/* ★ ヘルパー関数で名前を表示 */} 
                            {universitiesData.find(u => u.id === school.university_id)?.departments.find(d => d.id === dept.department_id)?.name || '不明な学部'} 
                            ({admissionMethodsData.find(a => a.id === dept.admission_method_id)?.name || '不明な方式'})
                         </li>
                      ))}
                    </ul>
                </div>
                {/* リストからの削除ボタン */}
                <Button variant="ghost" size="icon" onClick={() => removeDesiredSchool(index)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
      
      {/* 下部の完了/スキップボタン */} 
      <div className="w-full max-w-2xl flex justify-between mt-8">
          <Button variant="outline" onClick={handleSkip} disabled={isLoading}>
            {desiredSchools.length > 0 ? '完了してスキップ' : 'スキップ'} 
          </Button>
          <Button onClick={handleSave} disabled={isLoading || desiredSchools.length === 0}>
            {isLoading ? '保存中...' : `保存して完了 (${desiredSchools.length}件)`}
          </Button>
      </div>

    </div>
  );
};

export default TargetSchoolSetupPage; 