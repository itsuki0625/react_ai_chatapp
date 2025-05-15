import React from 'react';
import { Content } from '@/types/content';
import { Video, Presentation, FileText } from 'lucide-react';
import Image from 'next/image';

interface ContentListProps {
  contents: Content[];
  onContentClick: (content: Content) => void;
}

const ContentList: React.FC<ContentListProps> = ({ contents, onContentClick }) => {
  const getContentIcon = (type: string) => {
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

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {contents.map((content) => (
        <div
          key={content.id}
          className="bg-white rounded-lg shadow-sm overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => onContentClick(content)}
        >
          <div className="aspect-video relative bg-gray-100">
            <Image
              src={content.thumbnail_url || '/placeholder.png'}
              alt={content.title}
              className="object-cover"
              fill
              sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            />
          </div>
          <div className="p-4">
            <div className="flex items-center gap-2 mb-2">
              {getContentIcon(content.content_type)}
              <h3 className="text-lg font-medium text-gray-900">
                {content.title}
              </h3>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              {content.description}
            </p>
            <div className="flex flex-wrap gap-2">
              {content.category_info && (
                <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                  {content.category_info.description || content.category_info.name}
                </span>
              )}
              {content.tags && content.tags.map((tag: string) => (
                <span
                  key={tag}
                  className="px-2 py-1 text-xs font-medium border border-gray-200 text-gray-600 rounded-full"
                >
                  {tag.trim()}
                </span>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ContentList; 