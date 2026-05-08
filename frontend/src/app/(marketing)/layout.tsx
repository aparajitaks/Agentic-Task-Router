/**
 * frontend/src/app/(marketing)/layout.tsx
 *
 * WHY IT EXISTS:
 * Marketing pages need a different layout than the dashboard.
 * No sidebar, simple navigation, and a focus on high-quality presentation.
 */

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="bg-background min-h-screen">
      {children}
    </div>
  );
}
