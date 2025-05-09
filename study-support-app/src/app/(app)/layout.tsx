import { AppLayout } from '@/components/layout/AppLayout';
import { GoogleAnalytics } from '@/components/GoogleAnalytics';

export default function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <GoogleAnalytics />
      <AppLayout>{children}</AppLayout>
    </>
  );
}
