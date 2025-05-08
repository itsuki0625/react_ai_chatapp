import NextAuth, { DefaultSession, DefaultUser } from "next-auth";
import { JWT, DefaultJWT } from "next-auth/jwt";

// Userインターフェースをauth.tsのauthorizeの返り値に合わせる
declare module "next-auth" {
  interface User extends DefaultUser {
    role?: string[] | string; // authorizeからの入力は配列か文字列の可能性
    status?: string;
    permissions?: string[];
    isTeacher?: boolean; // authorizeで設定されていれば含める
    grade?: string;
    prefecture?: string;
    profile_image_url?: string | null;
    // accessToken?: string; // authorizeの返り値には含めず、jwtコールバックでtokenに追加される想定
    refreshToken?: string;
    accessTokenExpires?: number;
  }

  // Sessionインターフェースをauth.tsのsessionコールバックの最終形に合わせる
  interface Session extends DefaultSession {
    user: {
      id: string;
      name?: string | null;
      email?: string | null;
      image?: string | null;
      role: string; // sessionコールバックで単一文字列に正規化される
      status: string;
      isAdmin: boolean; // sessionコールバックで追加される
      isTeacher: boolean; // sessionコールバックで追加される
      isStudent: boolean; // sessionコールバックで追加される
      permissions?: string[];
      grade?: string;
      prefecture?: string;
      profile_image_url?: string | null;
      // ★ session コールバックで追加されるプロパティ
      accessToken?: string;
      refreshToken?: string;
      accessTokenExpires?: number;
      // DefaultSession['user'] の他のプロパティ（name, email, image）も必要なら含める
    } & Pick<DefaultSession["user"], 'name' | 'email' | 'image'>; // 必要な標準プロパティのみ選択的に結合
    // accessToken?: string; // ★ 削除: user オブジェクト内に移動
    error?: "RefreshAccessTokenError"; // トークンリフレッシュエラー用
    errorDetail?: string; // エラー詳細を追加
    expires: string; // ISO 8601 date string
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
    grade?: string;
    prefecture?: string;
    profile_image_url?: string | null;
    error?: "RefreshAccessTokenError"; // トークンリフレッシュエラー用
    errorDetail?: string; // エラー詳細を追加
    iat: number;
    exp: number;
    jti: string;
  }
} 