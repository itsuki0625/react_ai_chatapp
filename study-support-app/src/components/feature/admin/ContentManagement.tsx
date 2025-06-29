"use client";

import { useState, useEffect, useCallback } from 'react';
import Image from 'next/image';
import { useSession } from "next-auth/react";
import { 
  Plus, 
  Edit2, 
  Trash2, 
  Video, 
  FileText, 
  Presentation,
  LayoutGrid,
  List,
  Settings,
  BookOpen
} from 'lucide-react';
import { 
  Content, 
  FormContentType, 
  BackendContentType, 
  ContentCategoryInfo, 
  ContentCategoryCreate,
  ContentCategoryUpdate
} from '@/types/content';
import { contentAPI } from '@/lib/api';
import { Dialog } from '@/components/ui/dialog';
import { getSlideProviderInfo } from '@/lib/slide';
import { useSnackbar } from 'notistack';

interface ContentFormData {
  title: string;
  description: string;
  url: string;
  content_type: FormContentType;
  thumbnail_url?: string;
  category_id?: string;
  tags?: string;
  provider?: 'google' | 'slideshare' | 'speakerdeck';
  presenter_notes?: string[];
  duration?: string;
  is_premium?: boolean;
  author?: string;
  difficulty?: string;
  provider_item_id?: string;
}

const initialContentFormData: ContentFormData = {
  title: '',
  description: '',
  url: '',
  content_type: 'VIDEO',
  thumbnail_url: '',
  category_id: '',
  tags: '',
  duration: '',
  difficulty: '',
  is_premium: false,
  author: '',
  provider_item_id: '',
};

interface CategoryFormData {
  id?: string;
  name: string;
  description: string;
  display_order: number;
  icon_url?: string;
  is_active: boolean;
}

const initialCategoryFormData: CategoryFormData = {
  name: '',
  description: '',
  display_order: 0,
  icon_url: '',
  is_active: true,
};

const parseOptionalInt = (value?: string): number | undefined => {
  if (value === undefined || value === null || String(value).trim() === '') {
    return undefined;
  }
  const num = parseInt(String(value), 10);
  return isNaN(num) ? undefined : num;
};

export const ContentManagement = () => {
  const { data: session } = useSession();
  const [contents, setContents] = useState<Content[]>([]);
  const [showContentForm, setShowContentForm] = useState(false);
  const [contentFormData, setContentFormData] = useState<ContentFormData>(initialContentFormData);
  const [editingContentId, setEditingContentId] = useState<string | null>(null);
  const [contentViewMode, setContentViewMode] = useState<'grid' | 'list'>('grid');
  const [dbCategoriesForContentForm, setDbCategoriesForContentForm] = useState<ContentCategoryInfo[]>([]);
  const [adminCategories, setAdminCategories] = useState<ContentCategoryInfo[]>([]);
  const [showCategoryForm, setShowCategoryForm] = useState(false);
  const [categoryFormData, setCategoryFormData] = useState<CategoryFormData>(initialCategoryFormData);
  const [editingCategoryId, setEditingCategoryId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'contents' | 'categories'>('contents');
  const [isLoading, setIsLoading] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  const handleGenerateThumbnailFromGoogleDrive = () => {
    if (contentFormData.thumbnail_url) {
      const shareUrl = contentFormData.thumbnail_url;
      const fileIdRegex1 = /drive\.google\.com\/file\/d\/([a-zA-Z0-9_-]+)\/view/;
      const fileIdRegex2 = /drive\.google\.com\/open\?id=([a-zA-Z0-9_-]+)/;
      
      let fileId = null;
      const match1 = shareUrl.match(fileIdRegex1);
      if (match1 && match1[1]) {
        fileId = match1[1];
      } else {
        const match2 = shareUrl.match(fileIdRegex2);
        if (match2 && match2[1]) {
          fileId = match2[1];
        }
      }

      if (fileId) {
        const thumbnailUrl = `https://drive.google.com/uc?export=view&id=${fileId}`;
        setContentFormData(prev => ({ ...prev, thumbnail_url: thumbnailUrl }));
      } else {
        alert("入力されたURLは有効なGoogle Drive共有リンクの形式ではないか、URLが空です。");
      }
    } else {
      alert("Google Drive共有リンクをサムネイルURL欄に入力してください。");
    }
  };

  const fetchContents = useCallback(async () => {
    try {
      const data = await contentAPI.getContents();
      setContents(data as Content[]);
    } catch (error) {
      console.error('Failed to fetch contents:', error);
      setContents([]);
    }
  }, []);

  const fetchCategoriesForContentForm = useCallback(async () => {
    try {
      const categories = await contentAPI.getContentCategories();
      setDbCategoriesForContentForm(categories);
    } catch (error) {
      console.error('Failed to fetch categories for content form:', error);
      setDbCategoriesForContentForm([]);
    }
  }, []);

  const fetchAdminCategories = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await contentAPI.getAllContentCategories(); 
      setAdminCategories(data);
    } catch (error) {
      console.error('Error fetching admin categories:', error);
      enqueueSnackbar(`カテゴリー情報の取得中にエラーが発生しました: ${error instanceof Error ? error.message : '不明なエラー'}`, { variant: 'error' });
      setAdminCategories([]);
    } finally {
      setIsLoading(false);
    }
  }, [enqueueSnackbar]);

  const handleContentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    if (!session?.user?.id) {
       console.error("ユーザーIDが取得できません。ログイン状態を確認してください。");
       setIsLoading(false);
       alert("ログインセッションが無効です。再度ログインしてください。");
       return;
    }

    const payload = {
      ...contentFormData,
      content_type: contentFormData.content_type.toLowerCase() as BackendContentType,
      tags: contentFormData.tags ? contentFormData.tags.split(',').map(tag => tag.trim()).filter(tag => tag) : [],
      created_by_id: session.user.id as string,
      duration: parseOptionalInt(contentFormData.duration),
      difficulty: parseOptionalInt(contentFormData.difficulty),
      is_premium: contentFormData.is_premium || false,
      provider: contentFormData.provider,
      provider_item_id: contentFormData.provider_item_id,
    };

    const submitData = {
      ...payload,
      category_id: payload.category_id === '' ? undefined : payload.category_id,
    };

    try {
      if (editingContentId) {
        await contentAPI.updateContent(editingContentId, submitData as Partial<Content>);
      } else {
        await contentAPI.createContent(submitData as Omit<Content, 'id' | 'created_at' | 'updated_at'>);
      }
      setShowContentForm(false);
      setContentFormData(initialContentFormData);
      setEditingContentId(null);
      fetchContents();
      enqueueSnackbar(editingContentId ? 'コンテンツを更新しました' : 'コンテンツを作成しました', { variant: 'success' });
    } catch (error) {
      console.error('Failed to save content:', error);
      enqueueSnackbar(`コンテンツの保存に失敗しました。${error instanceof Error ? error.message : '不明なエラー'}`, { variant: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleContentEdit = async (id: string) => {
    try {
      setIsLoading(true);
      const content = await contentAPI.getContent(id);
      console.log('Fetched content for editing:', content);
      if (content) {
        let formProvider: 'google' | 'slideshare' | 'speakerdeck' | undefined = undefined;
        if (content.provider && ['google', 'slideshare', 'speakerdeck'].includes(content.provider)) {
          formProvider = content.provider as 'google' | 'slideshare' | 'speakerdeck';
        }

        setContentFormData({
          title: content.title,
          description: content.description || '',
          url: content.url,
          content_type: content.content_type.toUpperCase() as FormContentType, 
          thumbnail_url: content.thumbnail_url || '',
          category_id: content.category_info ? content.category_info.id : '',
          tags: content.tags ? content.tags.join(', ') : '', 
          duration: content.duration !== null && content.duration !== undefined ? String(content.duration) : '',
          is_premium: content.is_premium || false,
          author: content.author || '',
          difficulty: content.difficulty !== null && content.difficulty !== undefined ? String(content.difficulty) : '',
          provider: formProvider,
          provider_item_id: content.provider_item_id || '',
        });
        setEditingContentId(id);
        setShowContentForm(true);
      } else {
        enqueueSnackbar('コンテンツの読み込みに失敗しました。', { variant: 'error' });
      }
    } catch (error) {
      console.error("Failed to fetch content for editing:", error);
      enqueueSnackbar('編集のためにコンテンツを読み込めませんでした。', { variant: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleContentDelete = async (id: string) => {
    if (!confirm('このコンテンツを削除してもよろしいですか？')) return;
    setIsLoading(true);
    try {
      await contentAPI.deleteContent(id);
      fetchContents();
      enqueueSnackbar('コンテンツを削除しました', { variant: 'success' });
    } catch (error) {
      console.error('Failed to delete content:', error);
      enqueueSnackbar('コンテンツの削除に失敗しました', { variant: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const getContentTypeIcon = (type: FormContentType) => {
    switch (type) {
      case 'VIDEO':
        return <Video className="h-5 w-5" />;
      case 'SLIDE':
        return <Presentation className="h-5 w-5" />;
      case 'PDF':
        return <FileText className="h-5 w-5" />;
      default:
        return null;
    }
  };

  const handleContentUrlChange = (url: string) => {
    setContentFormData(prev => {
      const newData = { ...prev, url };
      if (prev.content_type === 'SLIDE' && prev.provider) {
        const { thumbnailUrl } = getSlideProviderInfo(url, prev.provider);
        if (thumbnailUrl) {
          newData.thumbnail_url = thumbnailUrl;
        }
      }
      return newData;
    });
  };

  const handleCategorySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    const submitData: ContentCategoryCreate | ContentCategoryUpdate = {
      name: categoryFormData.name,
      description: categoryFormData.description || null,
      display_order: Number(categoryFormData.display_order),
      icon_url: categoryFormData.icon_url || null,
      is_active: categoryFormData.is_active,
    };
    const { name, ...updatePayload } = submitData;

    try {
      if (editingCategoryId) {
        await contentAPI.updateContentCategory(editingCategoryId, updatePayload as ContentCategoryUpdate);
        enqueueSnackbar('カテゴリーを更新しました', { variant: 'success' });
      } else {
        await contentAPI.createContentCategory(submitData as ContentCategoryCreate);
        enqueueSnackbar('カテゴリーを作成しました', { variant: 'success' });
      }
      setShowCategoryForm(false);
      setCategoryFormData(initialCategoryFormData);
      setEditingCategoryId(null);
      fetchAdminCategories();
    } catch (error) {
      console.error('Failed to save category:', error);
      enqueueSnackbar(`カテゴリーの保存に失敗しました。${error instanceof Error ? error.message : '不明なエラー'}`, { variant: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditCategory = (category: ContentCategoryInfo) => {
    setEditingCategoryId(category.id);
    setCategoryFormData({
      id: category.id,
      name: category.name,
      description: category.description || '',
      display_order: category.display_order ?? 0,
      icon_url: category.icon_url || '',
      is_active: category.is_active ?? true,
    });
    setShowCategoryForm(true);
  };

  const handleDeleteCategory = async (categoryId: string) => {
    if (!confirm(`このカテゴリーを削除してもよろしいですか？\n関連するコンテンツがある場合、カテゴリーの関連付けが解除されます。(コンテンツ自体は削除されません)`)) {
      return;
    }
    setIsLoading(true);
    try {
      await contentAPI.deleteContentCategory(categoryId);
      enqueueSnackbar('カテゴリーを削除しました', { variant: 'success' });
      fetchAdminCategories(); // 一覧を再取得
    } catch (error) {
      console.error('Failed to delete category:', error);
      enqueueSnackbar(`カテゴリーの削除に失敗しました。${error instanceof Error ? error.message : '不明なエラー'}`, { variant: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'contents') {
      fetchContents();
      fetchCategoriesForContentForm();
    } else if (activeTab === 'categories') {
      fetchAdminCategories();
    }
  }, [activeTab, fetchContents, fetchCategoriesForContentForm, fetchAdminCategories]);

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">学習コンテンツ管理</h2>
        </div>
        <div className="flex border-b">
          <button
            onClick={() => setActiveTab('contents')}
            className={`flex items-center px-4 py-3 text-sm font-medium focus:outline-none 
              ${
                activeTab === 'contents'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
          >
            <BookOpen className="h-5 w-5 mr-2" />
            コンテンツ
          </button>
          <button
            onClick={() => setActiveTab('categories')}
            className={`flex items-center px-4 py-3 text-sm font-medium focus:outline-none 
              ${
                activeTab === 'categories'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
          >
            <Settings className="h-5 w-5 mr-2" />
            カテゴリー
          </button>
        </div>
      </div>

      {activeTab === 'contents' && (
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">コンテンツ一覧・編集</h3>
            <div className="flex items-center space-x-4">
              <div className="flex items-center bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setContentViewMode('grid')}
                  className={`p-1 rounded ${
                    contentViewMode === 'grid' 
                      ? 'bg-white shadow text-blue-600' 
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  title="グリッド表示"
                >
                  <LayoutGrid className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setContentViewMode('list')}
                  className={`p-1 rounded ${
                    contentViewMode === 'list' 
                      ? 'bg-white shadow text-blue-600' 
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  title="リスト表示"
                >
                  <List className="h-4 w-4" />
                </button>
              </div>
              <button
                onClick={() => {
                  setContentFormData(initialContentFormData);
                  setEditingContentId(null);
                  setShowContentForm(true);
                }}
                className="flex items-center px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                新規コンテンツ作成
              </button>
            </div>
          </div>
          {isLoading && <p>コンテンツを読み込み中...</p>}
          {!isLoading && contents.length === 0 && <p>登録されているコンテンツはありません。</p>}
          {!isLoading && contents.length > 0 && (
            <> 
              {contentViewMode === 'grid' ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {contents.map((content) => (
                    <div
                      key={content.id}
                      className="border rounded-lg p-3 hover:shadow-md transition-shadow flex flex-col"
                    >
                      <div className="aspect-video relative mb-2">
                        {content.thumbnail_url && (
                          <Image
                          src={`/api/image-proxy?url=${encodeURIComponent(content.thumbnail_url)}`}
                          alt={content.title}
                          fill
                          style={{ objectFit: 'cover' }}
                          className="rounded"
                        />
                        )}
                        {!content.thumbnail_url && (
                          <div className="w-full h-full bg-gray-200 flex items-center justify-center rounded">
                            <span className="text-gray-500">No Image</span>
                          </div>
                        )}
                        <div className="absolute top-2 right-2 flex space-x-1">
                          <button
                            onClick={() => handleContentEdit(content.id)}
                            className="p-1 bg-white rounded-full shadow hover:bg-gray-100"
                          >
                            <Edit2 className="h-4 w-4 text-gray-600" />
                          </button>
                          <button
                            onClick={() => handleContentDelete(content.id)}
                            className="p-1 bg-white rounded-full shadow hover:bg-gray-100"
                          >
                            <Trash2 className="h-4 w-4 text-red-600" />
                          </button>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 mb-1">
                        {getContentTypeIcon(content.content_type.toUpperCase() as FormContentType)}
                        <h3 className="font-medium text-gray-900 text-sm flex-grow line-clamp-1">{content.title}</h3>
                      </div>
                      {content.description && (
                        <p className="text-xs text-gray-600 mb-2 line-clamp-2 flex-grow">
                          {content.description}
                        </p>
                      )}
                      <div className="flex flex-wrap gap-1 mt-auto pt-1">
                        {content.category_info && (
                          <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                            {content.category_info.description || content.category_info.name}
                          </span>
                        )}
                        {Array.isArray(content.tags)
                          ? content.tags.map((tag: string, index: number) => (
                              <span key={index} className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                                {tag}
                              </span>
                            ))
                          : null
                        }
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {contents.map((content) => (
                    <div
                      key={content.id}
                      className="py-3 flex items-center hover:bg-gray-50"
                    >
                      <div className="flex-shrink-0 w-16 h-10 relative mr-4">
                        {content.thumbnail_url && (
                          <Image
                          src={`/api/image-proxy?url=${encodeURIComponent(content.thumbnail_url)}`}
                          alt={content.title}
                          fill
                          style={{ objectFit: 'cover' }}
                          className="rounded"
                        />
                        )}
                        {!content.thumbnail_url && (
                          <div className="w-full h-full bg-gray-200 flex items-center justify-center rounded">
                            <span className="text-xs text-gray-500">No Img</span>
                          </div>
                        )}
                      </div>
                      <div className="flex-grow min-w-0 mr-4">
                        <div className="flex items-center gap-2 mb-1">
                          {getContentTypeIcon(content.content_type.toUpperCase() as FormContentType)}
                          <h3 className="font-medium text-gray-900 truncate">
                            {content.title}
                          </h3>
                        </div>
                        {content.description && (
                          <p className="text-sm text-gray-600 line-clamp-1">
                            {content.description}
                          </p>
                        )}
                      </div>
                      <div className="flex-shrink-0 w-32 mr-4">
                        {content.category_info && (
                          <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                            {content.category_info.description || content.category_info.name}
                          </span>
                        )}
                      </div>
                      <div className="flex-shrink-0 w-48 mr-4 flex flex-wrap gap-1">
                        {Array.isArray(content.tags)
                          ? content.tags.slice(0, 3).map((tag: string, index: number) => (
                              <span key={index} className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                                {tag}
                              </span>
                            ))
                          : null
                        }
                        {Array.isArray(content.tags) && content.tags.length > 3 && (
                          <span className="text-xs text-gray-500">...</span>
                        )}
                      </div>
                      <div className="flex-shrink-0 flex space-x-2">
                        <button
                          onClick={() => handleContentEdit(content.id)}
                          className="p-1 text-gray-500 hover:text-gray-700"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleContentDelete(content.id)}
                          className="p-1 text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'categories' && (
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">カテゴリー設定</h3>
            <button
              onClick={() => {
                setCategoryFormData(initialCategoryFormData);
                setEditingCategoryId(null);
                setShowCategoryForm(true);
              }}
              className="flex items-center px-4 py-2 text-sm text-white bg-green-600 rounded-md hover:bg-green-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              新規カテゴリー作成
            </button>
          </div>
          {isLoading && activeTab === 'categories' && <p>カテゴリー情報を読み込み中...</p>}
          {!isLoading && adminCategories.length === 0 && activeTab === 'categories' && <p>登録されているカテゴリーはありません。</p>}
          {!isLoading && adminCategories.length > 0 && activeTab === 'categories' && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">日本語名</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">英語名(識別子)</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">表示順</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">有効</th>
                    <th scope="col" className="relative px-6 py-3">
                      <span className="sr-only">操作</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {adminCategories.map((category) => (
                    <tr key={category.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{category.description || '-'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{category.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{category.display_order ?? '-'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {category.is_active ? (
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                            有効
                          </span>
                        ) : (
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                            無効
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                        <button 
                          onClick={() => handleEditCategory(category)} 
                          className="text-indigo-600 hover:text-indigo-900"
                          title="編集"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button 
                          onClick={() => handleDeleteCategory(category.id)} 
                          className="text-red-600 hover:text-red-900"
                          title="削除"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <Dialog open={showContentForm} onClose={() => setShowContentForm(false)}>
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {editingContentId ? 'コンテンツを編集' : '新規コンテンツ'}
          </h3>
          <form onSubmit={handleContentSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                タイトル
              </label>
              <input
                type="text"
                value={contentFormData.title}
                onChange={(e) =>
                  setContentFormData({ ...contentFormData, title: e.target.value })
                }
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                説明
              </label>
              <textarea
                value={contentFormData.description}
                onChange={(e) =>
                  setContentFormData({ ...contentFormData, description: e.target.value })
                }
                rows={3}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                URL
              </label>
              <input
                type="url"
                value={contentFormData.url}
                onChange={(e) => handleContentUrlChange(e.target.value)}
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                コンテンツタイプ
              </label>
              <select
                value={contentFormData.content_type}
                onChange={(e) =>
                  setContentFormData({
                    ...contentFormData,
                    content_type: e.target.value as FormContentType,
                  })
                }
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="VIDEO">動画</option>
                <option value="SLIDE">スライド</option>
                <option value="PDF">PDF</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                サムネイルURL
              </label>
              <div className="mt-1 flex rounded-md shadow-sm">
                <input
                  type="text"
                  name="thumbnail_url"
                  id="thumbnail_url"
                  className="focus:ring-indigo-500 focus:border-indigo-500 flex-1 block w-full rounded-none rounded-l-md sm:text-sm border-gray-300"
                  value={contentFormData.thumbnail_url || ''}
                  onChange={(e) => setContentFormData({ ...contentFormData, thumbnail_url: e.target.value })}
                  placeholder="https://example.com/image.jpg または Google Drive共有リンク"
                />
                <button
                  type="button"
                  onClick={handleGenerateThumbnailFromGoogleDrive}
                  className="inline-flex items-center px-3 py-2 border border-l-0 border-gray-300 bg-gray-50 text-gray-500 hover:bg-gray-100 rounded-r-md text-sm"
                  title="Google Drive共有リンクから変換"
                >
                  変換
                </button>
              </div>
              {contentFormData.thumbnail_url && contentFormData.thumbnail_url.startsWith('https://drive.google.com/uc?export=view&id=') && (
                <div className="mt-2">
                  <Image 
                    src={`/api/image-proxy?url=${encodeURIComponent(contentFormData.thumbnail_url)}`}
                    alt="Thumbnail Preview" 
                    width={160} 
                    height={90} 
                    style={{ objectFit: 'cover' }}
                    onError={() => console.warn("サムネイル画像の読み込みに失敗しました。URLを確認してください。")} 
                  />
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                カテゴリー
              </label>
              <select
                value={contentFormData.category_id || ''}
                onChange={(e) =>
                  setContentFormData({ ...contentFormData, category_id: e.target.value })
                }
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="">カテゴリーを選択してください</option>
                {dbCategoriesForContentForm.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.description || category.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                タグ（カンマ区切り）
              </label>
              <input
                type="text"
                value={contentFormData.tags}
                onChange={(e) =>
                  setContentFormData({ ...contentFormData, tags: e.target.value })
                }
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            {contentFormData.content_type === 'SLIDE' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    プロバイダー
                  </label>
                  <select
                    value={contentFormData.provider}
                    onChange={(e) => {
                      const provider = e.target.value as 'google' | 'slideshare' | 'speakerdeck';
                      setContentFormData(prev => {
                        const { thumbnailUrl } = getSlideProviderInfo(prev.url, provider);
                        return {
                          ...prev,
                          provider,
                          thumbnail_url: (provider !== 'google' && thumbnailUrl) ? thumbnailUrl : prev.thumbnail_url
                        };
                      });
                    }}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="">プロバイダーを選択</option>
                    <option value="google">Google Slides</option>
                    <option value="slideshare">SlideShare</option>
                    <option value="speakerdeck">SpeakerDeck</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    発表者ノート（1行1スライド）
                  </label>
                  <textarea
                    value={contentFormData.presenter_notes?.join('\n')}
                    onChange={(e) =>
                      setContentFormData({
                        ...contentFormData,
                        presenter_notes: e.target.value.split('\n'),
                      })
                    }
                    rows={5}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    placeholder="各行に各スライドの発表者ノートを入力してください"
                  />
                </div>
              </>
            )}

            <div>
              <label htmlFor="provider_item_id" className="block text-sm font-medium text-gray-700">
                プロバイダーアイテムID (任意)
              </label>
              <input
                type="text"
                name="provider_item_id"
                id="provider_item_id"
                value={contentFormData.provider_item_id || ''}
                onChange={(e) =>
                  setContentFormData({ ...contentFormData, provider_item_id: e.target.value })
                }
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                placeholder="例: Google SlidesのファイルIDなど"
              />
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                type="button"
                onClick={() => setShowContentForm(false)}
                className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
              >
                キャンセル
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isLoading && editingContentId === null ? '作成中...' : isLoading && editingContentId !== null ? '更新中...' : editingContentId ? '更新' : '作成'}
              </button>
            </div>
          </form>
        </div>
      </Dialog>

      <Dialog open={showCategoryForm} onClose={() => setShowCategoryForm(false)}>
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {editingCategoryId ? 'カテゴリーを編集' : '新規カテゴリー'}
          </h3>
          <form onSubmit={handleCategorySubmit} className="space-y-4">
            <div>
              <label htmlFor="categoryName" className="block text-sm font-medium text-gray-700">
                英語名 (必須・重複不可・変更不可)
              </label>
              <input
                id="categoryName"
                type="text"
                value={categoryFormData.name}
                onChange={(e) =>
                  setCategoryFormData({ ...categoryFormData, name: e.target.value })
                }
                required
                disabled={!!editingCategoryId}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>

            <div>
              <label htmlFor="categoryDescription" className="block text-sm font-medium text-gray-700">
                日本語名 (表示名)
              </label>
              <input
                id="categoryDescription"
                type="text"
                value={categoryFormData.description}
                onChange={(e) =>
                  setCategoryFormData({ ...categoryFormData, description: e.target.value })
                }
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            <div>
              <label htmlFor="categoryDisplayOrder" className="block text-sm font-medium text-gray-700">
                表示順 (必須・数値)
              </label>
              <input
                id="categoryDisplayOrder"
                type="number"
                value={categoryFormData.display_order}
                onChange={(e) =>
                  setCategoryFormData({ ...categoryFormData, display_order: parseInt(e.target.value, 10) || 0 })
                }
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            <div>
              <label htmlFor="categoryIconUrl" className="block text-sm font-medium text-gray-700">
                アイコンURL (任意)
              </label>
              <input
                id="categoryIconUrl"
                type="url"
                value={categoryFormData.icon_url || ''}
                onChange={(e) =>
                  setCategoryFormData({ ...categoryFormData, icon_url: e.target.value })
                }
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            <div className="flex items-center">
              <input
                id="categoryIsActive"
                type="checkbox"
                checked={categoryFormData.is_active}
                onChange={(e) =>
                  setCategoryFormData({ ...categoryFormData, is_active: e.target.checked })
                }
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="categoryIsActive" className="ml-2 block text-sm text-gray-900">
                有効にする
              </label>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                type="button"
                onClick={() => {
                  setShowCategoryForm(false);
                  setCategoryFormData(initialCategoryFormData);
                  setEditingCategoryId(null);
                }}
                className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
              >
                キャンセル
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isLoading && editingCategoryId === null ? '作成中...' : isLoading && editingCategoryId !== null ? '更新中...' : editingCategoryId ? '更新' : '作成'}
              </button>
            </div>
          </form>
        </div>
      </Dialog>
    </div>
  );
}; 