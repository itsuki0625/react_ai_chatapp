import ContentDetailPage from '@/components/feature/student/content/ContentDetailPage';

export default function Page({ params }: { params: { id: string } }) {
  return <ContentDetailPage id={params.id} />;
} 