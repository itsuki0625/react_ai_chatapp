"use client";

import { useState, useEffect } from 'react';
import { Content, ContentType } from '@/types/content';
import { contentAPI } from '@/services/api';
import ContentList from '@/components/content/ContentList';
import { useRouter } from 'next/navigation';

const ContentsPage = () => {
  const [contents, setContents] = useState<Content[]>([]);
  const [selectedType, setSelectedType] = useState<ContentType | 'ALL'>('ALL');
  const router = useRouter();

  useEffect(() => {
    const fetchContents = async () => {
      try {
        const data = await contentAPI.getContents(
          selectedType === 'ALL' ? undefined : selectedType
        );
        setContents(data);
      } catch (error) {
        console.error('Failed to fetch contents:', error);
      }
    };

    fetchContents();
  }, [selectedType]);

  const handleContentClick = (content: Content) => {
    router.push(`/contents/${content.id}`);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        学習コンテンツ
      </h1>

      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8" aria-label="コンテンツタイプ">
          {[
            { label: 'すべて', value: 'ALL' },
            { label: '動画', value: 'VIDEO' },
            { label: 'スライド', value: 'SLIDE' },
            { label: 'PDF', value: 'PDF' }
          ].map((tab) => (
            <button
              key={tab.value}
              onClick={() => setSelectedType(tab.value as ContentType | 'ALL')}
              className={`pb-4 px-1 ${
                selectedType === tab.value
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <ContentList 
        contents={contents} 
        onContentClick={handleContentClick} 
      />
    </div>
  );
};

export default ContentsPage; 