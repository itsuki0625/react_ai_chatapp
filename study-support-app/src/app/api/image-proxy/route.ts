import { NextRequest, NextResponse } from 'next/server';
import fetch from 'node-fetch'; // node-fetchをインストールする必要があります

export async function GET(req: NextRequest) {
  const url = req.nextUrl.searchParams.get('url');

  if (!url || typeof url !== 'string') {
    return NextResponse.json({ error: 'Image URL is required' }, { status: 400 });
  }

  try {
    const externalRes = await fetch(url);

    if (!externalRes.ok) {
      console.error(`Error fetching image from ${url}: ${externalRes.status} ${externalRes.statusText}`);
      return NextResponse.json({ error: `Failed to fetch image: ${externalRes.statusText}` }, { status: externalRes.status });
    }

    // externalRes.bodyがNode.jsのReadableStreamであることを期待
    // App RouterのNextResponse.jsonやNextResponse.textとは異なり、
    // ストリームを直接レスポンスボディとして扱う場合は、Responseオブジェクトを直接生成する
    if (externalRes.body) {
      const headers = new Headers();
      const contentType = externalRes.headers.get('content-type');
      if (contentType) {
        headers.set('Content-Type', contentType);
      }
      // キャッシュコントロールを設定 (任意ですが、推奨)
      headers.set('Cache-Control', 'public, max-age=3600, s-maxage=604800, stale-while-revalidate');
      
      // @ts-ignore ReadableStreamをResponseのbodyに渡す
      return new Response(externalRes.body, {
        status: externalRes.status,
        statusText: externalRes.statusText,
        headers: headers,
      });
    } else {
      throw new Error('Image response body is null');
    }

  } catch (error) {
    console.error('Error in image proxy:', error);
    return NextResponse.json({ error: 'Failed to proxy image' }, { status: 500 });
  }
} 