// Login page uses the root layout providers
// This empty layout ensures login page doesn't have sidebar
export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
