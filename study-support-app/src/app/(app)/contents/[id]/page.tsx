import ContentDetailPage from '@/components/content/ContentDetailPage';

export default function Page({ params }: { params: { id: string } }) {
  return <ContentDetailPage id={params.id} />;
} 