"use client";

import React from 'react';
import { LoginForm } from './LoginForm';

const LoginPage = () => {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">ログイン</h1>
      <LoginForm />
    </div>
  );
};

export default LoginPage;