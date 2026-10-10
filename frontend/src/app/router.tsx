import { createBrowserRouter, type RouteObject } from "react-router";

import { PublicOnly, RequireAuth } from "@/features/auth";
import { HomePage } from "@/pages/home/home-page";
import { InvitationPage } from "@/pages/invitation/invitation-page";
import { LoginPage } from "@/pages/login/login-page";
import { NotFoundPage } from "@/pages/not-found/not-found-page";
import { InvitationsPage } from "@/pages/organization/invitations-page";
import { MembersPage } from "@/pages/organization/members-page";
import { OrganizationNewPage } from "@/pages/organization-new/organization-new-page";
import { RegisterPage } from "@/pages/register/register-page";

import { AppLayout } from "./app-layout";

// Маршруты и права доступа - по frontend/docs/architecture/routes.md
export const routes: RouteObject[] = [
  {
    element: <PublicOnly />,
    children: [
      { path: "/login", element: <LoginPage /> },
      { path: "/register", element: <RegisterPage /> },
    ],
  },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: "/", element: <HomePage /> },
          { path: "/organizations/new", element: <OrganizationNewPage /> },
          { path: "/organizations/:orgId/members", element: <MembersPage /> },
          { path: "/organizations/:orgId/invitations", element: <InvitationsPage /> },
          { path: "/invitations/:token", element: <InvitationPage /> },
        ],
      },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
];

export const router = createBrowserRouter(routes);
