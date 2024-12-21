"use client";

import React, { useState } from 'react';
import { Save, ArrowLeft, Send } from 'lucide-react';

interface Statement {
    title: string;
    university: string;
    faculty: string;
    content: string;
}

interface StatementEditorPageProps {
    id?: string;  // 新規作成時はidがないのでoptionalに
    initialData?: any;  // 初期データの型は実際のデータ構造に合わせて定義してください
}

const StatementEditorPage: React.FC<StatementEditorPageProps> = ({id,initialData}) => {
  const [formData, setFormData] = useState({
    title: '第一志望大学志望理由書',
    university: '東京大学',
    faculty: '理学部',
    content: ''
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Save statement:', formData);
  };

  return (
    <div className="h-[calc(100vh-32px)] flex flex-col bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button className="p-2 hover:bg-gray-100 rounded-full">
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">志望理由書編集</h1>
              <p className="text-sm text-gray-500">下書きを保存しました - 2024/12/21 10:30</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button className="flex items-center px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
              <Save className="h-5 w-5 mr-2" />
              保存
            </button>
            <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
              <Send className="h-5 w-5 mr-2" />
              添削リクエスト
            </button>
          </div>
        </div>
      </header>

      {/* エディタ本体 */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <form onSubmit={handleSubmit} className="space-y-6 bg-white p-6 rounded-lg shadow">
            {/* 基本情報 */}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                  タイトル
                </label>
                <input
                  type="text"
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleChange}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>

              <div>
                <label htmlFor="university" className="block text-sm font-medium text-gray-700">
                  志望大学
                </label>
                <input
                  type="text"
                  id="university"
                  name="university"
                  value={formData.university}
                  onChange={handleChange}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>

              <div>
                <label htmlFor="faculty" className="block text-sm font-medium text-gray-700">
                  学部・学科
                </label>
                <input
                  type="text"
                  id="faculty"
                  name="faculty"
                  value={formData.faculty}
                  onChange={handleChange}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
            </div>

            {/* 本文エディタ */}
            <div>
              <label htmlFor="content" className="block text-sm font-medium text-gray-700">
                本文
              </label>
              <div className="mt-1">
                <textarea
                  id="content"
                  name="content"
                  rows={15}
                  value={formData.content}
                  onChange={handleChange}
                  placeholder="志望理由を入力してください..."
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
              <p className="mt-2 text-sm text-gray-500">
                文字数: {formData.content.length} 文字
              </p>
            </div>

            {/* ガイドライン */}
            <div className="bg-blue-50 rounded-md p-4">
              <h3 className="text-sm font-medium text-blue-800">作成のポイント</h3>
              <ul className="mt-2 text-sm text-blue-700 list-disc list-inside">
                <li>学びたい内容を具体的に記述する</li>
                <li>志望動機が明確に伝わるようにする</li>
                <li>高校時代の経験と結びつける</li>
                <li>将来の展望について触れる</li>
              </ul>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
};

export default StatementEditorPage;