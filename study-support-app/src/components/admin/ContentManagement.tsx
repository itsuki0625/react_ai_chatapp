"use client";

import { useState, useEffect } from 'react';
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
import { Content, ContentType } from '@/types/content';
import { contentAPI } from '@/services/api';
import { Dialog } from '@/components/common/Dialog';
import { getSlideProviderInfo } from '@/lib/slide';

interface ContentFormData {
  title: string;
  description: string;
  url: string;
  content_type: ContentType;
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

export const ContentManagement = () => {
  const [contents, setContents] = useState<Content[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<ContentFormData>(initialFormData);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const fetchContents = async () => {
    try {
      const data = await contentAPI.getContents();
      setContents(data);
    } catch (error) {
      console.error('Failed to fetch contents:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (editingId) {
        await contentAPI.updateContent(editingId, formData);
      } else {
        await contentAPI.createContent(formData);
      }
      setShowForm(false);
      setFormData(initialFormData);
      setEditingId(null);
      fetchContents();
    } catch (error) {
      console.error('Failed to save content:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = (content: Content) => {
    setFormData({
      title: content.title,
      description: content.description || '',
      url: content.url,
      content_type: content.content_type,
      thumbnail_url: content.thumbnail_url || '',
      category: content.category || '',
      tags: content.tags || '',
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

  const getContentTypeIcon = (type: ContentType) => {
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
      
      // スライドの場合、プロバイダーに応じてサムネイルを自動設定
      if (prev.content_type === 'SLIDE' && prev.provider) {
        const { thumbnailUrl } = getSlideProviderInfo(url, prev.provider);
        if (thumbnailUrl) {
          newData.thumbnail_url = thumbnailUrl;
        }
      }
      
      return newData;
    });
  };

  // 初期ロード時にコンテンツを取得
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
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {contents.map((content) => (
              <div
                key={content.id}
                className="border rounded-lg p-3 hover:shadow-md transition-shadow"
              >
                <div className="aspect-video relative mb-2">
                  <img
                    src={content.thumbnail_url || '/placeholder.png'}
                    alt={content.title}
                    className="w-full h-full object-cover rounded"
                  />
                  <div className="absolute top-2 right-2 flex space-x-2">
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
                  {getContentTypeIcon(content.content_type)}
                  <h3 className="font-medium text-gray-900 text-sm">{content.title}</h3>
                </div>
                {content.description && (
                  <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                    {content.description}
                  </p>
                )}
                <div className="flex flex-wrap gap-1">
                  {content.category && (
                    <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                      {content.category}
                    </span>
                  )}
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
                <div className="flex-shrink-0 w-16 h-16 mr-4">
                  <img
                    src={content.thumbnail_url || '/placeholder.png'}
                    alt={content.title}
                    className="w-full h-full object-cover rounded"
                  />
                </div>
                <div className="flex-grow min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {getContentTypeIcon(content.content_type)}
                    <h3 className="font-medium text-gray-900 truncate">
                      {content.title}
                    </h3>
                  </div>
                  {content.description && (
                    <p className="text-sm text-gray-600 truncate">
                      {content.description}
                    </p>
                  )}
                  <div className="flex items-center gap-2 mt-1">
                    {content.category && (
                      <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                        {content.category}
                      </span>
                    )}
                    <span className="text-xs text-gray-500">
                      {new Date(content.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="flex-shrink-0 ml-4 flex items-center space-x-2">
                  <button
                    onClick={() => handleEdit(content)}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    <Edit2 className="h-4 w-4 text-gray-600" />
                  </button>
                  <button
                    onClick={() => handleDelete(content.id)}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    <Trash2 className="h-4 w-4 text-red-600" />
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
                    content_type: e.target.value as ContentType,
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
                  <img
                    src={formData.thumbnail_url}
                    alt="サムネイルプレビュー"
                    className="w-48 h-auto border rounded"
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