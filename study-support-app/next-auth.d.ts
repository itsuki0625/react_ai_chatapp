import NextAuth, { DefaultSession, DefaultUser } from "next-auth";
import { JWT, DefaultJWT } from "next-auth/jwt";

// Userインターフェースをauth.tsのauthorizeの返り値に合わせる
declare module "next-auth" {
  interface User extends DefaultUser {
    role?: string[] | string; // authorizeからの入力は配列か文字列の可能性
    status?: string;
    permissions?: string[];
    isTeacher?: boolean; // authorizeで設定されていれば含める
    // accessToken?: string; // authorizeの返り値には含めず、jwtコールバックでtokenに追加される想定
    refreshToken?: string;
    accessTokenExpires?: number;
  }

  // Sessionインターフェースをauth.tsのsessionコールバックの最終形に合わせる
  interface Session extends DefaultSession {
    user: {
      id: string;
      role: string; // sessionコールバックで単一文字列に正規化される
      status: string;
      isAdmin: boolean; // sessionコールバックで追加される
      isTeacher: boolean; // sessionコールバックで追加される
      isStudent: boolean; // sessionコールバックで追加される
      permissions?: string[];
      // DefaultSession['user'] の他のプロパティ（name, email, image）も必要なら含める
    } & Pick<DefaultSession["user"], 'name' | 'email' | 'image'>; // 必要な標準プロパティのみ選択的に結合
    accessToken?: string; // sessionコールバックで追加される
    error?: string;
  }
}

// JWTインターフェースをauth.tsのjwtコールバックの最終形に合わせる
declare module "next-auth/jwt" {
  interface JWT extends DefaultJWT {
    id?: string;
    role?: string[] | string; // APIからの入力は配列か文字列の可能性
    status?: string;
    permissions?: string[];
    isTeacher?: boolean; // authorizeから引き継ぐ場合
    accessToken?: string;
    refreshToken?: string;
    accessTokenExpires?: number;
    error?: string;
  }
} 