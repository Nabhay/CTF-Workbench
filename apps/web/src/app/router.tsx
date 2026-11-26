import { createBrowserRouter, RouterProvider } from "react-router-dom";

import { HealthScreen } from "@/features/health/HealthScreen";

const router = createBrowserRouter([
  { path: "/", element: <HealthScreen /> },
  { path: "/health", element: <HealthScreen /> },
  { path: "*", element: <NotFoundScreen /> },
]);

function NotFoundScreen() {
  return (
    <main className="min-h-screen bg-chassis px-6 py-16 text-paper">
      <p className="font-mono text-sm text-mute">No page at this path.</p>
      <h1 className="mt-4 text-3xl font-semibold">This route is not in the workbench yet.</h1>
      <a className="mt-8 inline-block text-lamp underline decoration-edge underline-offset-4" href="/">
        Back to bench check
      </a>
    </main>
  );
}

export function AppRouter() {
  return <RouterProvider router={router} />;
}
