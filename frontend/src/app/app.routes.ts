import { Routes } from '@angular/router';

import { authGuard } from './core/guards/auth.guard';
import { guestGuard } from './core/guards/guest.guard';
import { AppShell } from './layout/app-shell/app-shell';

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () => import('./features/auth/login/login').then((m) => m.Login),
  },
  {
    path: 'registro',
    canActivate: [guestGuard],
    loadComponent: () => import('./features/auth/register/register').then((m) => m.Register),
  },
  {
    path: '',
    component: AppShell,
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () => import('./features/catalog/catalog').then((m) => m.Catalog),
      },
      {
        path: 'favoritos',
        loadComponent: () => import('./features/favorites/favorites').then((m) => m.Favorites),
      },
      {
        path: 'comentarios',
        loadComponent: () => import('./features/comments/comments').then((m) => m.Comments),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
