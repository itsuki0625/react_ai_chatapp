"use client";

import { useState, useEffect } from 'react';
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
  List
} from 'lucide-react';
import { Content, FormContentType, BackendContentType, ContentCategory } from '@/types/content';
import { contentAPI } from '@/services/api';
import { Dialog } from '@/components/common/Dialog';
import { getSlideProviderInfo } from '@/lib/slide';

interface ContentFormData {
  title: string;
  description: string;
  url: string;
  content_type: FormContentType;
  thumbnail_url?: string;
  category?: string;
  tags?: string;
  provider?: 'google' | 'slideshare' | 'speakerdeck';
  presenter_notes?: string[];
}

const initialFormData: ContentFormData = {
  title: '',
  description: '',
  url: '',
  content_type: 'VIDEO',
  thumbnail_url: '',
  category: '',
  tags: '',
};

const categoryMap: { [key: string]: string } = {
  "自己分析": "self_analysis",
  "入試情報": "admissions",
  "学術・教養": "academic",
  "大学情報": "university_info",
  "キャリア": "career",
  "その他": "other",
};

const reverseCategoryMap: { [key: string]: string } = Object.fromEntries(
  Object.entries(categoryMap).map(([key, value]) => [value, key])
);

export const ContentManagement = () => {
  const { data: session } = useSession();
  const [contents, setContents] = useState<Content[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<ContentFormData>(initialFormData);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const fetchContents = async () => {
    try {
      const data = await contentAPI.getContents();
      setContents(data as Content[]);
    } catch (error) {
      console.error('Failed to fetch contents:', error);
      setContents([]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    if (!session?.user?.id) {
       console.error("ユーザーIDが取得できません。ログイン状態を確認してください。");
       setIsLoading(false);
       alert("ログインセッションが無効です。再度ログインしてください。");
       return;
    }

    const payload = {
      ...formData,
      content_type: formData.content_type.toLowerCase() as BackendContentType,
      category: (categoryMap[formData.category || ''] || 'other') as ContentCategory,
      tags: formData.tags ? formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag) : [],
      created_by_id: session.user.id as string,
    };

    const { provider, ...submitData } = payload;

    try {
      if (editingId) {
        const updatePayload = { ...submitData };
        await contentAPI.updateContent(editingId, updatePayload);
      } else {
        await contentAPI.createContent(submitData);
      }
      setShowForm(false);
      setFormData(initialFormData);
      setEditingId(null);
      fetchContents();
    } catch (error) {
      console.error('Failed to save content:', error);
      alert(`コンテンツの保存に失敗しました。
${error instanceof Error ? error.message : '不明なエラー'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = (content: Content) => {
    setFormData({
      title: content.title,
      description: content.description || '',
      url: content.url,
      content_type: content.content_type.toUpperCase() as FormContentType,
      thumbnail_url: content.thumbnail_url || '',
      category: reverseCategoryMap[content.category || ''] || '',
      tags: Array.isArray(content.tags) ? content.tags.join(', ') : '',
    });
    setEditingId(content.id);
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('このコンテンツを削除してもよろしいですか？')) return;

    try {
      await contentAPI.deleteContent(id);
      fetchContents();
    } catch (error) {
      console.error('Failed to delete content:', error);
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
    }
  };

  const handleUrlChange = (url: string) => {
    setFormData(prev => {
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

  useEffect(() => {
    fetchContents();
  }, []);

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-medium text-gray-900">コンテンツ管理</h2>
          <div className="flex items-center space-x-4">
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-1 rounded ${
                  viewMode === 'grid' 
                    ? 'bg-white shadow text-blue-600' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                title="グリッド表示"
              >
                <LayoutGrid className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-1 rounded ${
                  viewMode === 'list' 
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
                setFormData(initialFormData);
                setEditingId(null);
                setShowForm(true);
              }}
              className="flex items-center px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              新規作成
            </button>
          </div>
        </div>
      </div>

      <div className="p-6">
        {viewMode === 'grid' ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {contents.map((content) => (
              <div
                key={content.id}
                className="border rounded-lg p-3 hover:shadow-md transition-shadow flex flex-col"
              >
                <div className="aspect-video relative mb-2">
                  <Image
                    src={content.thumbnail_url || '/placeholder.png'}
                    alt={content.title}
                    layout="fill"
                    objectFit="cover"
                    className="rounded"
                  />
                  <div className="absolute top-2 right-2 flex space-x-1">
                    <button
                      onClick={() => handleEdit(content)}
                      className="p-1 bg-white rounded-full shadow hover:bg-gray-100"
                    >
                      <Edit2 className="h-4 w-4 text-gray-600" />
                    </button>
                    <button
                      onClick={() => handleDelete(content.id)}
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
                  {content.category && (
                    <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                      {reverseCategoryMap[content.category] || content.category}
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
                <div className="flex-shrink-0 w-16 h-10 mr-4">
                  <Image
                    src={content.thumbnail_url || '/placeholder.png'}
                    alt={content.title}
                    layout="fill"
                    objectFit="cover"
                    className="rounded"
                  />
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
                  {content.category && (
                    <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                      {reverseCategoryMap[content.category] || content.category}
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
                    onClick={() => handleEdit(content)}
                    className="p-1 text-gray-500 hover:text-gray-700"
                  >
                    <Edit2 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(content.id)}
                    className="p-1 text-red-500 hover:text-red-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Dialog open={showForm} onClose={() => setShowForm(false)}>
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {editingId ? 'コンテンツを編集' : '新規コンテンツ'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                タイトル
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
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
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
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
                value={formData.url}
                onChange={(e) => handleUrlChange(e.target.value)}
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                コンテンツタイプ
              </label>
              <select
                value={formData.content_type}
                onChange={(e) =>
                  setFormData({
                    ...formData,
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
              <input
                type="url"
                value={formData.thumbnail_url}
                onChange={(e) =>
                  setFormData({ ...formData, thumbnail_url: e.target.value })
                }
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
              {formData.thumbnail_url && (
                <div className="mt-2">
                  <p className="text-xs text-gray-500 mb-1">プレビュー:</p>
                  <Image
                    src={formData.thumbnail_url}
                    alt="サムネイルプレビュー"
                    width={160}
                    height={90}
                    objectFit="cover"
                    className="rounded border"
                  />
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                カテゴリー
              </label>
              <input
                type="text"
                value={formData.category}
                onChange={(e) =>
                  setFormData({ ...formData, category: e.target.value })
                }
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                タグ（カンマ区切り）
              </label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) =>
                  setFormData({ ...formData, tags: e.target.value })
                }
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            {formData.content_type === 'SLIDE' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    プロバイダー
                  </label>
                  <select
                    value={formData.provider}
                    onChange={(e) => {
                      const provider = e.target.value as 'google' | 'slideshare' | 'speakerdeck';
                      setFormData(prev => {
                        const { thumbnailUrl } = getSlideProviderInfo(prev.url, provider);
                        return {
                          ...prev,
                          provider,
                          thumbnail_url: thumbnailUrl || prev.thumbnail_url
                        };
                      });
                    }}
                    required
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
                    value={formData.presenter_notes?.join('\n')}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
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

            <div className="flex justify-end space-x-3 mt-6">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
              >
                キャンセル
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isLoading ? '保存中...' : '保存'}
              </button>
            </div>
          </form>
        </div>
      </Dialog>
    </div>
  );
}; 