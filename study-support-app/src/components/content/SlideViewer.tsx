"use client";

import { useState } from 'react';
import { Maximize2, Minimize2, MessageSquare } from 'lucide-react';
import { getSlideProviderInfo } from '@/lib/slide';

interface SlideViewerProps {
  url: string;
  title: string;
  provider?: 'google' | 'slideshare' | 'speakerdeck';
  presenterNotes?: string[];
}

export const SlideViewer = ({ 
  url, 
  title, 
  provider = 'google',
  presenterNotes = []
}: SlideViewerProps) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showNotes, setShowNotes] = useState(false);
  const [currentSlide, setCurrentSlide] = useState(0);

  const { embedUrl } = getSlideProviderInfo(url, provider);

  const toggleFullscreen = () => {
    const element = document.getElementById('slide-container');
    if (!element) return;

    if (!isFullscreen) {
      if (element.requestFullscreen) {
        element.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
    setIsFullscreen(!isFullscreen);
  };

  const handleSlideChange = (direction: 'prev' | 'next') => {
    if (direction === 'prev' && currentSlide > 0) {
      setCurrentSlide(currentSlide - 1);
    } else if (direction === 'next' && currentSlide < presenterNotes.length - 1) {
      setCurrentSlide(currentSlide + 1);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'ArrowRight') {
      handleSlideChange('next');
    } else if (e.key === 'ArrowLeft') {
      handleSlideChange('prev');
    }
  };

  return (
    <div 
      id="slide-container"
      className={`relative w-full ${isFullscreen ? 'h-screen' : ''}`}
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      <div className="flex flex-col lg:flex-row gap-4">
        {/* スライド表示エリア */}
        <div className="flex-1">
          <div className="relative aspect-[16/9]">
            <iframe
              src={embedUrl}
              title={title}
              className="absolute top-0 left-0 w-full h-full"
              allowFullScreen
              onLoad={() => setIsLoading(false)}
            />
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
              </div>
            )}
          </div>

          {/* コントロールバー */}
          <div className="mt-2 flex items-center justify-between px-4 py-2 bg-gray-100 rounded-md">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => handleSlideChange('prev')}
                disabled={currentSlide === 0}
                className="p-2 hover:bg-gray-200 rounded-full disabled:opacity-50"
              >
                ←
              </button>
              <span className="text-sm">
                スライド {currentSlide + 1} / {presenterNotes.length}
              </span>
              <button
                onClick={() => handleSlideChange('next')}
                disabled={currentSlide === presenterNotes.length - 1}
                className="p-2 hover:bg-gray-200 rounded-full disabled:opacity-50"
              >
                →
              </button>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowNotes(!showNotes)}
                className="p-2 hover:bg-gray-200 rounded-full"
                title="発表者ノートの表示/非表示"
              >
                <MessageSquare className="h-5 w-5" />
              </button>
              <button
                onClick={toggleFullscreen}
                className="p-2 hover:bg-gray-200 rounded-full"
                title="全画面表示"
              >
                {isFullscreen ? (
                  <Minimize2 className="h-5 w-5" />
                ) : (
                  <Maximize2 className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* 発表者ノート */}
        {showNotes && presenterNotes.length > 0 && (
          <div className="lg:w-1/3 bg-gray-50 p-4 rounded-md">
            <h3 className="text-lg font-medium mb-2">発表者ノート</h3>
            <div className="prose prose-sm">
              {presenterNotes[currentSlide]}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}; 