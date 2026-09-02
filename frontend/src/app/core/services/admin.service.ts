import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { AdminComentario, AdminFavorito, AdminUsuario } from '../../models/admin.model';

@Injectable({ providedIn: 'root' })
export class AdminService {
  constructor(private readonly http: HttpClient) {}

  listarUsuarios(): Observable<AdminUsuario[]> {
    return this.http.get<AdminUsuario[]>('/auth/admin/users');
  }

  alterarPapel(usuarioId: number, role: string): Observable<AdminUsuario> {
    return this.http.patch<AdminUsuario>(`/auth/admin/users/${usuarioId}/role`, { role });
  }

  listarComentarios(): Observable<AdminComentario[]> {
    return this.http.get<AdminComentario[]>('/admin/comments');
  }

  removerComentario(id: number): Observable<void> {
    return this.http.delete<void>(`/admin/comments/${id}`);
  }

  listarFavoritos(): Observable<AdminFavorito[]> {
    return this.http.get<AdminFavorito[]>('/admin/favorites');
  }

  removerFavorito(id: number): Observable<void> {
    return this.http.delete<void>(`/admin/favorites/${id}`);
  }
}
