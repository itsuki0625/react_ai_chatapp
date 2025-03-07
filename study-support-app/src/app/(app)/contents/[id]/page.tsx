import ContentDetailPage from '@/components/content/ContentDetailPage';

interface PageProps {
  params: {
    id: string;
  };
}

export default async function Page({ params }: PageProps) {
  const id = await Promise.resolve(params.id);
  return <ContentDetailPage id={id} />;
} 