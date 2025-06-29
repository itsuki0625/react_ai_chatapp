import NextAuth from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { NEXTAUTH_CONFIG } from './config';
import { authorizeUser } from './handlers';
import { jwtCallback, sessionCallback } from './callbacks';
import { Credentials } from './types';

// NextAuth設定
export const authConfig = {
  ...NEXTAUTH_CONFIG,
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "メールアドレス", type: "email" },
        password: { label: "パスワード", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }
        
        const credentialsData: Credentials = {
          email: credentials.email as string,
          password: credentials.password as string,
        };
        
        return await authorizeUser(credentialsData);
      }
    })
  ],
  callbacks: {
    jwt: jwtCallback,
    session: sessionCallback,
  },
};

// NextAuthインスタンスを作成してエクスポート
export const { handlers, auth, signIn, signOut } = NextAuth(authConfig);

// 型定義と関数を再エクスポート
// export * from './types';
// export * from './utils';
// export * from './config'; 