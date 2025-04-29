"use client";

import { useEffect, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { Content } from '@/types/content';
import { contentAPI } from '@/services/api';
import { useRouter } from 'next/navigation';
import { SlideViewer } from './SlideViewer';

interface Props {
  id: string;
}

const ContentDetailPage = ({ id }: Props) => {
  const router = useRouter();
  const [content, setContent] = useState<Content | null>(null);

  useEffect(() => {
    const fetchContent = async () => {
      try {
        const data = await contentAPI.getContent(id);
        setContent(data);
      } catch (error) {
        console.error('Failed to fetch content:', error);
      }
    };
    fetchContent();
  }, [id]);

  if (!content) return null;

  const renderContent = () => {
    switch (content.content_type) {
      case 'video':
        return (
          <div className="relative w-full pt-[56.25%]">
            <iframe
              className="absolute top-0 left-0 w-full h-full"
              src={content.url}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        );
      case 'slide':
        return (
          <SlideViewer
            url={content.url}
            title={content.title}
            provider={content.provider as 'google' | 'slideshare' | 'speakerdeck'}
            presenterNotes={content.presenter_notes}
          />
        );
      case 'pdf':
        return (
          <div className="relative w-full pt-[141.42%]">
            <iframe
              className="absolute top-0 left-0 w-full h-full"
              src={content.url}
            />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <button
          onClick={() => router.back()}
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          戻る
        </button>
        <h1 className="text-2xl font-bold text-gray-900">
          {content.title}
        </h1>
      </div>

      <div className="bg-white rounded-lg shadow-sm mb-6 p-6">
        {renderContent()}
      </div>

      {content.description && (
        <p className="text-gray-700 mb-6">
          {content.description}
        </p>
      )}
    </div>
  );
};

export default ContentDetailPage; 