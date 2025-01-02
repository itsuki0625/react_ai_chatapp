export const getSlideProviderInfo = (url: string, provider: 'google' | 'slideshare' | 'speakerdeck') => {
  switch (provider) {
    case 'google':
      // Google Slides ID を抽出
      const googleMatch = url.match(/[-\w]{25,}/);
      const googleId = googleMatch ? googleMatch[0] : '';
      return {
        embedUrl: `https://docs.google.com/presentation/d/${googleId}/preview`,
        thumbnailUrl: `https://docs.google.com/presentation/d/${googleId}/export/png?pageid=p1`
      };

    case 'slideshare':
      // SlideShare ID を抽出
      const slideshareMatch = url.match(/slideshare\.net\/.*\/(.*)/);
      const slideshareId = slideshareMatch ? slideshareMatch[1] : '';
      return {
        embedUrl: `https://www.slideshare.net/slideshow/embed_code/${slideshareId}`,
        thumbnailUrl: `https://www.slideshare.net/${slideshareId}/slide/1.jpg`
      };

    case 'speakerdeck':
      // SpeakerDeck ID を抽出
      const speakerdeckMatch = url.match(/speakerdeck\.com\/.*\/(.*)/);
      const speakerdeckId = speakerdeckMatch ? speakerdeckMatch[1] : '';
      return {
        embedUrl: `https://speakerdeck.com/player/${speakerdeckId}`,
        thumbnailUrl: `https://speakerdeck.com/presentations/${speakerdeckId}/slide_0.jpg`
      };

    default:
      return {
        embedUrl: url,
        thumbnailUrl: ''
      };
  }
}; 