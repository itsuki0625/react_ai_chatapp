'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { uploadUserIcon, deleteUserIcon } from '@/services/userService';
import { useUserStore } from '@/store/userStore'; // Zustandストアなどを使用する場合
// import { getCloudFrontUrl } from '@/utils/cloudfront'; // CloudFront不使用のためコメントアウト

export default function SettingsPage() {
  const { data: session, update: updateSession } = useSession();
  const { user, setUser } = useUserStore(); // Zustandストアからユーザー情報と更新関数を取得
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  // 初期アイコンURLを設定 (CloudFront未使用のため、キーを直接使うかnull)
  useEffect(() => {
    // S3 オブジェクトキーを直接 previewUrl に設定 (表示できない可能性がある)
    // 表示ロジックは AvatarImage の onError や Fallback に依存
    setPreviewUrl(user?.profile_image_url ?? null);

    // selectedFileが変更されたらプレビューを生成/クリア
    if (selectedFile) {
        const reader = new FileReader();
        reader.onloadend = () => {
            setPreviewUrl(reader.result as string);
        };
        reader.readAsDataURL(selectedFile);
    } else {
        // ファイル選択が解除されたらDBの値に戻す
         setPreviewUrl(user?.profile_image_url ?? null);
    }

  }, [user?.profile_image_url, selectedFile]);


  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // ファイルタイプのバリデーション (例)
      const allowedTypes = ['image/png', 'image/jpeg', 'image/gif'];
      if (!allowedTypes.includes(file.type)) {
          toast({
              variant: 'destructive',
              title: 'エラー',
              description: '許可されていないファイル形式です。(PNG, JPG, GIFのみ)',
          });
          setSelectedFile(null);
          setPreviewUrl(user?.profile_image_url ?? null); // 元の画像に戻す
          if (fileInputRef.current) fileInputRef.current.value = ""; // input値をクリア
          return;
      }
      // ファイルサイズのバリデーション (例: 5MB)
      const maxSize = 5 * 1024 * 1024;
      if (file.size > maxSize) {
           toast({
              variant: 'destructive',
              title: 'エラー',
              description: 'ファイルサイズが大きすぎます。(5MBまで)',
          });
          setSelectedFile(null);
          setPreviewUrl(user?.profile_image_url ?? null); // 元の画像に戻す
          if (fileInputRef.current) fileInputRef.current.value = ""; // input値をクリア
          return;
      }

      setSelectedFile(file);
      // プレビューURL生成はuseEffectで行う
    } else {
      setSelectedFile(null);
      // プレビューURLリセットもuseEffectで行う
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsLoading(true);
    try {
      const updatedUser = await uploadUserIcon(selectedFile);
      setUser(updatedUser); // Zustandストアを更新
      // await updateSession({ user: updatedUser }); // NextAuthセッション更新 (必要なら)

      toast({ title: '成功', description: 'アイコンを更新しました。' });
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = ""; // input値をクリア
      // プレビュー更新はuseEffectに任せる
    } catch (error) {
      console.error('Icon upload failed:', error);
      toast({
        variant: 'destructive',
        title: 'エラー',
        description: error instanceof Error ? error.message : 'アイコンのアップロードに失敗しました。',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!user?.profile_image_url) return;
    setIsLoading(true);
    try {
      const updatedUser = await deleteUserIcon();
      setUser(updatedUser);
      // await updateSession({ user: updatedUser }); // NextAuthセッション更新 (必要なら)

      toast({ title: '成功', description: 'アイコンを削除しました。' });
      setPreviewUrl(null);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (error) {
      console.error('Icon delete failed:', error);
       toast({
        variant: 'destructive',
        title: 'エラー',
        description: error instanceof Error ? error.message : 'アイコンの削除に失敗しました。',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  // ユーザー名がない場合などのフォールバック文字
  const fallbackChar = user?.name?.charAt(0)?.toUpperCase() ?? 'U';

  return (
    <div className="space-y-6 p-4 md:p-6">
      {/* パスワード変更へのリンクなどを残す場合 */}
      {/* <div><Link href="/settings/password">パスワード変更</Link></div> */}

      <h3 className="text-lg font-medium">プロフィールアイコン</h3>
      <div className="flex items-center space-x-4">
        <Avatar className="h-20 w-20 cursor-pointer" onClick={handleAvatarClick}>
          {/* previewUrlがS3キーの場合、そのままでは表示されない可能性があるため注意 */}
          {/* onError で fallback を表示させる想定 */}
          <AvatarImage src={previewUrl ?? undefined} alt={user?.name ?? 'User'} />
          <AvatarFallback>{fallbackChar}</AvatarFallback>
        </Avatar>
        <Input
          type="file"
          accept="image/png, image/jpeg, image/gif" // accept 属性を修正
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
        />
        <div className="flex flex-col space-y-2">
           <Button onClick={handleAvatarClick} variant="outline" size="sm" disabled={isLoading}>
            画像を選択
          </Button>
          {selectedFile && (
            <Button onClick={handleUpload} size="sm" disabled={isLoading}>
              {isLoading ? 'アップロード中...' : 'アイコンを更新'}
            </Button>
          )}
          {/* 既存アイコンがあり、新規ファイル未選択の場合に削除ボタン表示 */}
          {user?.profile_image_url && !selectedFile && (
            <Button onClick={handleDelete} variant="destructive" size="sm" disabled={isLoading}>
              {isLoading ? '削除中...' : 'アイコンを削除'}
            </Button>
          )}
        </div>
      </div>
       {selectedFile && (
          <p className="text-sm text-muted-foreground">
            選択中のファイル: {selectedFile.name}
          </p>
        )}

      {/* 他の設定項目があればここに追加 */}

    </div>
  );
}