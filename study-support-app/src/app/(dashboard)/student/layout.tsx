import { AppLayout } from '@/components/layout/AppLayout';
import { GoogleAnalytics } from '@/components/common/GoogleAnalytics';

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
